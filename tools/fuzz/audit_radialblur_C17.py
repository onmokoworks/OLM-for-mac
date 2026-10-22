#!/usr/bin/env python3
"""Collect C17's negative experiments and verified boundaries without promoting them."""
import argparse
from collections import Counter
import ctypes
import hashlib
import json
from pathlib import Path
import math
import struct
import subprocess
import sys
sys.dont_write_bytecode=True
import capstone
import pefile
from verify_radialblur_smart_C06 import ROOT, MAIN, WORKER


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--state',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();state=args.state.resolve()
    assert state.is_relative_to(ROOT/'orchestra/state/C17-radial-smart-r3')
    assert args.output.resolve().is_relative_to(ROOT)
    bindings={}
    def read(name):
        path=state/name;raw=path.read_bytes();bindings[name]=hashlib.sha256(raw).hexdigest()
        return json.loads(raw)
    base=read('base.json');verify=read('production-verify/report.json');replay=read('replay.json')
    assert base['completed']==300 and base['summary']['smart_exact']==241
    assert base['summary'].get('smart_mismatch',0)==0 and base['summary']['smart_refusal']==59
    assert verify['status']=='pass' and len(verify['campaigns'][0]['rows'])==300
    assert verify['smoke']['tests']==8 and not verify['failures']
    source=ROOT/'mac/OLMRadialBlur/OLMRadialBlur.cpp'
    assert source.read_bytes()==subprocess.check_output(['git','show','dd7d8fa1:mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=ROOT)
    census=Counter();refusals=[]
    for row in base['cases']:
        if row['result']['routes']['smart']['status']=='refusal' and row['result']['oracles']['smart']['status']=='ok':
            guard=','.join(g.split('@')[0] for g in row.get('refusal_guards',{}).get('smart',[])) or 'host'
            census[guard]+=1;refusals.append(row)
    experiments={}
    for name in ('centers16','centers16-hostexp','type3-zero','type3-zero-span'):
        r=read(name+'/report.json')
        assert all(not row['after'].get('sanitizer') for row in r['rows'])
        experiments[name]=dict(provenance=r['provenance'],counts=dict(Counter(q['after']['status'] for q in r['rows'])),
            changed=[q for q in r['rows'] if q['after']['status']!='refusal'])
    matrices={}
    for name in ('centers16-independent','centers16-hostexp-independent'):
        r=read(name+'/report.json')
        matrices[name]=dict(provenance=r['provenance'],status=r['status'],failures=r['failures'],
            references=len(r['independent']),renders=sum(len(q['layouts']) for q in r['independent']),
            exact=sum(l['exact'] for q in r['independent'] for l in q['layouts']),
            clean=sum(l['clean'] for q in r['independent'] for l in q['layouts']),
            negative_rows=[q for q in r['independent'] if not all(l['exact'] for l in q['layouts'])])
    traces={name:read(name+'/report.json') for name in ('rotation-weights-trace2','rotation-hostexp-trace','type3-trace')}
    traces['type3-zoom-trace2']=read('type3-zoom-trace2/report.json')
    original=traces['rotation-weights-trace2'];diagnostic=traces['rotation-hostexp-trace']
    assert all(p['different_words']==0 for p in diagnostic['planes'].values())
    diff=original['weights']['inner_fade']['first_differences'][0]
    f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
    bits=lambda v:struct.pack('<f',v).hex()
    denominator=f32(f32(10.*10.)*f32(.111111119389534));denominator=f32(f32(denominator+denominator)+1.e-5)
    exponent=f32(-64.*f32(1./denominator))
    host=ctypes.CDLL(None).expf;host.argtypes=[ctypes.c_float];host.restype=ctypes.c_float
    assert bits(host(exponent))==diff['native_f32_le_hex']=='a5ed653d'
    assert bits(math.exp(exponent))==diff['mac_f32_le_hex']=='a4ed653d'
    imports=WORKER.parents[2]/'crates/aex-guest-worker/src/x64/imports.rs'
    assert 'install_float_import(unicorn, stub, "expf", f32::exp)?;' in imports.read_text()
    aex=MAIN/'aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex'
    pe=pefile.PE(str(aex));decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
    static={}
    for label,start,end in [('float_handle_allocation',0x45a0,0x4630),('span_composer_type3',0x65c0,0x6650),('weight_scalar_tail',0xb760,0xb7b5)]:
        static[label]=[dict(rva=hex(i.address-pe.OPTIONAL_HEADER.ImageBase),bytes=i.bytes.hex(),instruction=i.mnemonic+' '+i.op_str)
            for i in decoder.disasm(pe.get_data(start,end-start),pe.OPTIONAL_HEADER.ImageBase+start)]
    corpus=[]
    for row in replay['replays']:
        saved=json.loads(Path(row['path']).read_text())['result']['routes']['smart'];actual=row['result']['routes']['smart']
        assert saved['status']==actual['status']=='exact' and saved['raw_sha256']==actual['raw_sha256']
        corpus.append(dict(path=str(Path(row['path']).resolve().relative_to(ROOT)),before=saved,after=actual,matches_saved_all_routes=row['matches_saved']))
    assert len(corpus)==35
    for path in (source,ROOT/'core/dblur_noise.h',WORKER,aex,imports):
        bindings[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    report=dict(status='blocked',production_changed=False,baseline=dict(provenance=base['provenance'],summary=base['summary'],elapsed_seconds=base['elapsed_seconds'],
        exact_rows=[dict(index=r['index'],input_sha256=r['input_sha256'],smart=r['result']['routes']['smart']) for r in base['cases'] if r['result']['routes']['smart']['status']=='exact'],
        rendered_refusal_census=dict(census),rendered_refusals=refusals),experiments=experiments,matrices=matrices,traces=traces,
        exp_boundary=dict(exponent_le_hex=bits(exponent),host_expf=bits(host(exponent)),double_exp_cast=bits(math.exp(exponent))),
        production_verification=verify,corpus=corpus,static=static,bindings=bindings)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('AUDIT baseline 241/0/59; production 300 same/clean; smoke 8; corpus Smart 35 identical')
    print('CORPUS all-route saved matches',sum(r['matches_saved_all_routes'] for r in corpus))
    print('EXPERIMENTS',{k:v['counts'] for k,v in experiments.items()})


if __name__=='__main__':main()
