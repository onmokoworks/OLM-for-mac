#!/usr/bin/env python3
"""Bind resident F49 rotation captures to F46 and compare the public Mac stages."""
import gzip,json,math,os,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmdirectionalblur import Adapter
from core import sha,raw_diff
from probe_directionalblur_c02_stages import TracedAdapter
S=ROOT/'orchestra/state/F49-dblur-nonfinite-pf32'
CACHE=Path.home()/'.cache/olm-emu'
def main():
 S.mkdir(parents=True,exist_ok=True)
 os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S));tempfile.tempdir=str(S)
 args=SimpleNamespace(main=ROOT.parent.parent,max_size=256,case_timeout=120,worker=CACHE/'worker-F46-pow/aex-guest-worker',core_ref=None,gate_off=False,nonfinite_off=False)
 base=Adapter(args);args.worker=CACHE/'worker-F49-trace-v2/aex-guest-worker';traced=Adapter(args)
 mac=TracedAdapter(args);deadline=time.monotonic()+1800
 report={'base_sha256':sha(base.worker.read_bytes()),'trace_sha256':sha(traced.worker.read_bytes()),'cases':[]}
 report['source_hashes']={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [Path(__file__),ROOT/'core/x86_float.h',*sorted((ROOT/'core').glob('dblur*')),ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp']}
 with tempfile.TemporaryDirectory(prefix='mac_',dir=S) as tmp:
  report['mac_build']=mac.prepare(Path(tmp),deadline)
  for seed in (1,104):
   campaign=json.load(gzip.open(ROOT/f'orchestra/reports/C51-evidence/seed{seed}.json.gz'))
   for row in campaign['cases']:
    if row['result']['routes']['smart']['status']!='refusal':continue
    index=row['index'];d=S/f'{seed}-{index}';d.mkdir(exist_ok=True)
    case=base.generate(seed,index);assert sha(case['pixels'])==row['input_sha256']
    w,h=case['geometry'];span=2+int(math.sqrt(w*w+h*h)*.5);ww=w+(span-w//2)*2;wh=h+(span-h//2)*2
    tracepath=d/'trace.json';traced.env.update(AEXCOMPAT_F49_TRACE=str(tracepath),AEXCOMPAT_F49_BYTES=str(ww*wh*16))
    a,reference=base.oracle(case,d,deadline,'smart');b,capture=traced.oracle(case,d,deadline,'smart')
    result={'seed':seed,'index':index,'geometry':case['geometry'],'work_geometry':[ww,wh],'input_sha256':sha(case['pixels']),'base':a,'traced':b,'output_sha256':sha(reference),'trace_output_sha256':sha(capture),'bound':reference==capture and a['status']==b['status']=='ok'}
    assert sha(reference)==row['result']['oracles']['smart']['raw_sha256'],result
    report['cases'].append(result)
    (S/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
    assert result['bound'],result
    trace=json.loads(tracepath.read_text());witnesses=trace['memory_witnesses']
    result['witness_count']=len(witnesses);result['trace_configuration']=trace['trace_configuration']
    mac.env['OLM_C02_TRACE']=str(d)
    c,raw,guards=mac.candidate(case,d,'smart',deadline);result['mac']=c;result['final_diff']=raw_diff(reference,raw,32)
    result['stages']={}
    for wid,stage,when,occ in [('rotation-input','populated','before',0),('rotation-output','rotated','after',0),('rotation-input','inverse-input','before',-1),('rotation-output','writer-plane','after',-1)]:
     witness=[t for t in witnesses if t['watch_id']==wid][occ]
     snap=witness[when];assert snap['status']=='captured';data=bytes.fromhex(snap['hex']);assert len(data)==ww*wh*16
     (d/f'aex-{stage}').write_bytes(data)
     other=(d/stage).read_bytes();assert len(other)==len(data)
     result['stages'][stage]=raw_diff(data,other,32)
    (S/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    assert result['final_diff']['different_bytes']==0 and all(v['different_bytes']==0 for v in result['stages'].values()),result
 assert len(report['cases'])==4
if __name__=='__main__':main()
