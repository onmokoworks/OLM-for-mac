"""Real hub validation: leave-one-plugin-out and a one-constant temporary PE edit."""
import argparse
from collections import Counter
import copy
from pathlib import Path
import struct
import tempfile

import capstone as cs
from capstone import x86_const as x
from binary import Image
from funcdb import (Client, DEFAULT_DB, DEFAULT_ORIGINALS, HERE, PLUGINS, build, collect,
                    digest, encoded, exact_key, log, lookup, read, save)


def library(record):
    p=copy.deepcopy(record)
    fingerprints={}
    for f in p['functions']:
        fp=f.pop('fingerprint')
        key=digest(encoded(fp))
        fingerprints[key]=fp
        f['fingerprint_id']=key
    return dict(schema=1,normalizer='test',programs=[p],fingerprints=fingerprints,mappings=[],evidence=[])


def synthetic(client, cache, out, db=None):
    path=DEFAULT_ORIGINALS/'OLMBlur.aex'
    before=Image(path)
    original,_=collect(client,path,cache,'OLMBlur')
    entries={before.base+int(f['rva'],16) for f in original['functions']}
    chosen=None
    for f in sorted(original['functions'],key=lambda f:int(f['rva'],16)):
        if f['fingerprint']['instructions']<10:
            continue
        instructions=before.recover(before.base+int(f['rva'],16),f['size'],entries)
        for ins in instructions or []:
            if (ins.mnemonic=='cmp' and ins.imm_size==1 and ins.operands[-1].type==x.X86_OP_IMM
                    and 0<ins.operands[-1].imm<100):
                chosen=f,ins
                break
        if chosen:
            break
    if not chosen:
        raise AssertionError('No bounded CMP-immediate fixture found')
    function,ins=chosen
    offset=before.pe.get_offset_from_rva(ins.address-before.base)+ins.imm_offset
    changed=bytearray(before.data)
    changed[offset]+=1
    temp_root=Path('D:/olm-rs-ghidra/temp').resolve()
    temp_root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='funcdb-',dir=temp_root) as tmp:
        temp=Path(tmp).resolve()
        if temp.parent!=temp_root:
            raise ValueError('Unexpected temporary directory scope')
        patched=temp/'OLMBlur-constant-patch.aex'
        patched.write_bytes(changed)
        new,_=collect(client,patched,cache)
        old_by={f['rva']:f for f in original['functions']}
        new_by={f['rva']:f for f in new['functions']}
        assert old_by.keys()==new_by.keys(), 'Synthetic edit changed discovered function set'
        changed_functions=[rva for rva in old_by if exact_key(old_by[rva]['fingerprint'])!=exact_key(new_by[rva]['fingerprint'])]
        assert changed_functions==[function['rva']],changed_functions
        report=lookup(db or library(original),new)
        work={f['rva']:f for f in report['port_work']}
        assert work[function['rva']]['kind']=='fuzzy',work[function['rva']]
        assert report['counts'].get('exact')==len(original['functions'])-1,report['counts']
        save(out/'synthetic-lookup.json.gz',report)
        result=dict(original_sha256=before.sha256,modified_sha256=new['sha256'],
                    modified_file_offset=offset,modified_instruction_rva=hex(ins.address-before.base),
                    expected_changed_rva=function['rva'],actual_changed_rvas=changed_functions,
                    functions=len(original['functions']),lookup_counts=report['counts'],
                    changed_match=work[function['rva']],hub_program=new['program'])
    assert not temp.exists(), 'Temporary binary not removed'
    assert Image(path).sha256==before.sha256,'Original unexpectedly changed'
    result['temporary_binary_removed']=True
    result['original_unchanged']=True
    save(out/'synthetic.json',result)
    log(str({k:v for k,v in result.items() if k!='changed_match'}))
    return result


def holdouts(client,cache,out):
    results=[]
    for program in sorted(PLUGINS):
        # Exercise the real build path; the omitted binary is never added to
        # this database, including its mappings and fingerprint-only entries.
        db=build(client,DEFAULT_ORIGINALS,cache,exclude=[program])
        assert program not in {p['program'] for p in db['programs']}
        record,_=collect(client,DEFAULT_ORIGINALS/(program+'.aex'),cache,program)
        report=lookup(db,record)
        assert report['counts'].get('exact',0)>0,(program,report['counts'])
        assert all(c['program']!=program for f in report['port_work'] for c in f['candidates'])
        save(out/(program+'-holdout.json.gz'),report)
        shared=[f for f in report['port_work'] if f['kind']=='exact' and not f['tiny']]
        assert shared,program+' has only tiny matches'
        result=dict(program=program,counts=report['counts'],non_tiny_shared=len(shared),
                    shared_bytes=sum(f['size'] for f in shared),
                    holdout_database_sha256=digest(encoded(db)),
                    sample=sorted(shared,key=lambda f:-f['size'])[:3])
        results.append(result)
        save(out/'holdouts.json',results)
        log(f'{program} holdout: {report["counts"]}; non-tiny shared={len(shared)}')
    return results


def relocation(client,cache,out):
    original_path=DEFAULT_ORIGINALS/'OLMBlur.aex'
    image=Image(original_path)
    old,_=collect(client,original_path,cache,'OLMBlur')
    # Patch only PE relocation entries and ImageBase, as triage's relocation
    # validator does. pefile.relocate_image also rewrites import RVAs on this PE.
    rebased=bytearray(image.data)
    after=0x190000000
    for address,width in image.relocations.items():
        offset=image.pe.get_offset_from_rva(address-image.base)
        fmt='<Q' if width==8 else '<I'
        value=struct.unpack_from(fmt,rebased,offset)[0]+after-image.base
        struct.pack_into(fmt,rebased,offset,value % (1<<(width*8)))
    struct.pack_into('<Q',rebased,image.pe.OPTIONAL_HEADER.get_field_absolute_offset('ImageBase'),after)
    temp_root=Path('D:/olm-rs-ghidra/temp').resolve()
    temp_root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='funcdb-rebase-',dir=temp_root) as tmp:
        temp=Path(tmp).resolve()
        assert temp.parent==temp_root
        path=temp/'OLMBlur-rebased.aex'
        path.write_bytes(rebased)
        assert Image(path).imports, 'Rebase fixture lost its imports'
        new,_=collect(client,path,cache)
        a={f['rva']:exact_key(f['fingerprint']) for f in old['functions']}
        b={f['rva']:exact_key(f['fingerprint']) for f in new['functions']}
        assert a==b, 'Rebase changed normalized fingerprints'
        result=dict(original_sha256=old['sha256'],rebased_sha256=new['sha256'],
                    original_image_base=old['image_base'],rebased_image_base=new['image_base'],
                    equal_functions=len(a),hub_program=new['program'])
    assert not temp.exists()
    result['temporary_binary_removed']=True
    save(out/'relocation.json',result)
    log(str(result))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',default='http://127.0.0.1:8766')
    p.add_argument('--db',type=Path,default=DEFAULT_DB)
    p.add_argument('--cache',type=Path,default=HERE/'local/cache')
    p.add_argument('--out',type=Path,default=HERE/'runs/verified')
    p.add_argument('--synthetic-only',action='store_true')
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    c=Client(args.url)
    if not args.synthetic_only:
        holdouts(c,args.cache,args.out)
    synthetic(c,args.cache,args.out,read(args.db) if args.db.exists() else None)
    relocation(c,args.cache,args.out)


if __name__=='__main__':
    main()
