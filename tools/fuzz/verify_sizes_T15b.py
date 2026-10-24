#!/usr/bin/env python3
"""Before/after default result comparison for widened test-host CLI bounds."""
import copy, importlib, json, os, shutil, sys, time
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
sys.dont_write_bytecode=True
from core import evaluate, sha, save_corpus, load_corpus
from geometry import sample, require_host
from run import ROOT, main_checkout
from sweep_T15b import S,E,WORKER,PLUGINS,write,category,reduce_witness

def main():
    name=sys.argv[1];s=S/('default-'+name);s.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
    cls=importlib.import_module('adapters.'+name).Adapter
    # Imported adapter replacements need their old bound restored as well.
    original_write=Path.write_text
    original_read=Path.read_text
    def legacy_text(path,*args,**kwargs):
        text=original_read(path,*args,**kwargs)
        if path.is_relative_to(ROOT/'tools/fuzz/harnesses'):
            text=text.replace('w>4096||h>4096','w>256||h>256').replace('W>4096||H>4096','W>256||H>256')
        return text
    def legacy_write(path, text, *args, **kwargs):
        if path.suffix=='.cpp' and path.is_relative_to(s):
            text=text.replace('w>4096||h>4096','w>256||h>256').replace('w > 4096 || h > 4096','w > 256 || h > 256')
        return original_write(path,text,*args,**kwargs)
    allrows={};provenances={}
    for phase in ('before','after'):
        stage=s/phase;stage.mkdir(exist_ok=True)
        a=cls(SimpleNamespace(main=main_checkout(),worker=WORKER,max_size=256,case_timeout=10))
        if phase=='before':
            with patch.object(Path,'read_text',legacy_text),patch.object(Path,'write_text',legacy_write):
                provenances[phase]=a.prepare(stage,time.monotonic()+300)
        else:provenances[phase]=a.prepare(stage,time.monotonic()+300)
        rows=[]
        for i in range(10):
            c=a.generate(2026,i);r=evaluate(a,c,stage,time.monotonic()+50)
            rows.append(r)
        allrows[phase]=rows
    result=dict(cases=10,both_routes=True,identical=allrows['before']==allrows['after'],results=allrows,provenance=provenances)
    write(E/(name+'-default-regression.json'),result)
    # Three depth anchors (where the original supports them) also exercise
    # standard replay when the sweep has no mismatch/refusal witness.
    summary=json.loads((E/(name+'-summary.json')).read_text())
    a.max_size=summary['maximum'];a.size_max_height=summary['height_maximum'];a.size_sampler='odd-even-v1'
    anchors=[];attempts={}
    with (E/(name+'-cases.jsonl')).open() as rows:
        for line in rows:
            row=json.loads(line);depth=row['case']['depth']
            if row['category']!='E' or depth in [x['depth'] for x in anchors] or attempts.get(depth,0)>=3:continue
            attempts[depth]=attempts.get(depth,0)+1
            c=sample(a.generate(row['case']['seed'],row['case']['index']),'realistic')
            assert sha(c['pixels'])==row['input_sha256']
            require_host(a,c);r=evaluate(a,c,stage,time.monotonic()+50)
            assert r['routes'][summary['route']]==row['result']['routes'][summary['route']], (name,depth,'anchor changed')
            if any(o['status']=='budget' for o in r.get('oracles',{'primary':r['oracle']}).values()):continue
            corpus=ROOT/'tests/fuzz_corpus'/name/'T15b-odd-even-realistic';corpus.mkdir(parents=True,exist_ok=True)
            path=corpus/('anchor-PF'+str(depth)+'.json')
            provenance=provenances['after'];provenance['case_timeout_seconds']=10
            save_corpus(path,a,c,c,r,dict(attempts=0,accepted=[],anchor=True),provenance)
            anchors.append(dict(depth=depth,path=str(path.relative_to(ROOT))))
    if name=='olmdistancegradation':
        retained={(w['first_seed'],w['first_index']) for w in summary['witnesses']}
        for line in (E/(name+'-cases.jsonl')).read_text().splitlines():
            row=json.loads(line);spec=row['case']
            if row['category'] not in ('M','R') or (spec['seed'],spec['index']) in retained:continue
            original=sample(a.generate(spec['seed'],spec['index']),'realistic');require_host(a,original)
            reduced,reduction=reduce_witness(a,original,'smart',row['failure_class'],stage)
            attr={};r=evaluate(a,reduced,stage,time.monotonic()+50,attr)
            assert not any(o['status']=='budget' for o in r.get('oracles',{'primary':r['oracle']}).values())
            path=ROOT/'tests/fuzz_corpus'/name/'T15b-odd-even-realistic'/('seed%d-case%d.json'%(spec['seed'],spec['index']))
            save_corpus(path,a,original,reduced,r,reduction,provenances['after'])
            summary['witnesses'].append(dict(failure_class=row['failure_class'],first_seed=spec['seed'],first_index=spec['index'],geometry=reduced['geometry'],result=r,refusals=attr,reduction=reduction,path=str(path.relative_to(ROOT))))
    summary['anchors']=anchors;write(E/(name+'-summary.json'),summary)
    if name=='olmkirakira':
        import struct
        path=ROOT/'tests/fuzz_corpus/olmkirakira/T15b-odd-even-realistic/b0e34d548337.json'
        c,_=load_corpus(path,a);require_host(a,c)
        finite=copy.deepcopy(c);finite['pixels']=c['pixels'][:12]+struct.pack('<f',0.5)
        write(E/'olmkirakira-nonfinite-boundary.json',dict(
            operation='replace only blue qNaN 0x7fc12345 with finite 0.5; all parameters and geometry unchanged',
            before_input_sha256=sha(c['pixels']),after_input_sha256=sha(finite['pixels']),
            before=evaluate(a,c,stage,time.monotonic()+50),after=evaluate(a,finite,stage,time.monotonic()+50)))
    if name=='olmdirectionalblur' and summary['witnesses']:
        import struct, math
        c,_=load_corpus(ROOT/summary['witnesses'][0]['path'],a);require_host(a,c)
        finite=copy.deepcopy(c)
        values=[v[0] for v in struct.iter_unpack('<f',c['pixels'])]
        finite['pixels']=b''.join(struct.pack('<f',v if math.isfinite(v) else 0.5) for v in values)
        write(E/'olmdirectionalblur-nonfinite-boundary.json',dict(
            operation='replace nonfinite source lanes with finite 0.5; all parameters and geometry unchanged',
            replaced_lanes=sum(not math.isfinite(v) for v in values),
            before_input_sha256=sha(c['pixels']),after_input_sha256=sha(finite['pixels']),
            before=evaluate(a,c,stage,time.monotonic()+50),after=evaluate(a,finite,stage,time.monotonic()+50)))
    if name=='radialblur' and summary['witnesses']:
        import struct, math
        c,_=load_corpus(ROOT/summary['witnesses'][0]['path'],a);require_host(a,c)
        finite=copy.deepcopy(c);data=bytearray(c['pixels']);replaced=0
        for offset in range(0,len(data),16):
            value=struct.unpack_from('<f',data,offset)[0]
            if not math.isfinite(value):struct.pack_into('<f',data,offset,0.5);replaced+=1
        finite['pixels']=bytes(data)
        write(E/'radialblur-nonfinite-boundary.json',dict(
            operation='replace only nonfinite alpha lanes by 0.5; same RGB, parameters and geometry',
            replaced_lanes=replaced,before_input_sha256=sha(c['pixels']),after_input_sha256=sha(finite['pixels']),
            before=evaluate(a,c,stage,time.monotonic()+50),after=evaluate(a,finite,stage,time.monotonic()+50)))
    shutil.rmtree(s)
    print(name,'default identical',result['identical'],flush=True)
    if not result['identical']:raise SystemExit(1)
if __name__=='__main__':main()
