#!/usr/bin/env python3
"""Independent missing-layer controls; never count original failures as exact."""
import argparse,json,os,random,shutil,struct,sys,time
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
from adapters.radialblur import Adapter,ROOT,public
from core import sha

def cases(adapter):
    rng=random.Random(57057)
    for w,h in ((1,1),(7,1),(7,5)):
        for depth in (8,16,32):
            top=255 if depth==8 else 32768
            vals=[rng.randint(0,top) for _ in range(w*h*4)]
            pixels=b''.join(struct.pack('<'+{8:'B',16:'H',32:'f'}[depth],v if depth!=32 else v/32768) for v in vals)
            for mode in (1,2):
                for nv in (0.,1.,53.25,100.):
                    ps=adapter.defaults(w,h)
                    controls={1:mode,4:7,5:2,6:2,7:3,10:4,12:1,13:2,20:1.25,22:67.5,24:nv,25:3}
                    for p in ps:
                        if p['slot'] in controls:p['value']=controls[p['slot']]
                    yield dict(depth=depth,geometry=[w,h],parameters=ps,pixels=pixels,input_padding=3,output_padding=5)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--invalid-host',action='store_true');args=ap.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'orchestra/state/C57-radial-missing-layer');out.mkdir(parents=True,exist_ok=False)
    os.environ.update(TMPDIR=str(out),TMP=str(out),TEMP=str(out),OLM_RADIAL_CANDIDATE_SANITIZE='1',ASAN_OPTIONS='halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    if args.invalid_host:
        body=public.initial.HARNESS.read_text()
        old='if(slot==OLMRADIALBLUR_NOISE_LAYER) { ++g_pixel_out; *v=&g_empty_noise; return 0; }'
        new='if(slot==OLMRADIALBLUR_NOISE_LAYER) {\n        const char *mode=getenv("C57_INVALID_HOST");\n        if(mode && strcmp(mode,"error")==0)return 711;\n        ++g_pixel_out;\n        g_empty_noise={};\n        if(mode && strcmp(mode,"nodata")==0) {g_empty_noise.width=g_input->width;g_empty_noise.height=g_input->height;}\n        *v=(mode && strcmp(mode,"null")==0)?nullptr:&g_empty_noise; return 0;\n    }'
        assert body.count(old)==1
        harness=out/'invalid_host.cpp';harness.write_text(body.replace(old,new));public.initial.HARNESS=harness
    adapter=Adapter(SimpleNamespace(main=(ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT),max_size=256,case_timeout=20,worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker'))
    deadline=time.monotonic()+2400
    report=dict(provenance=adapter.prepare(out,deadline),cases=[])
    if args.invalid_host:
        try:
            for mode in ('null','nodata','error'):
                adapter.env['C57_INVALID_HOST']=mode
                for seed,index in ((1,248),(105,158),(105,214)):
                    result,raw,guards=adapter.candidate(adapter.generate(seed,index),out,'smart',deadline)
                    report['cases'].append(dict(mode=mode,seed=seed,index=index,result=result,guards=guards))
            (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            assert all(r['result']['status']=='refusal' and not r['result'].get('sanitizer') for r in report['cases'])
            print('9 invalid-host refusals, no sanitizer diagnostics')
        finally:shutil.rmtree(out/'build',ignore_errors=True)
        return
    try:
        for i,case in enumerate(cases(adapter)):
            d=out/str(i);d.mkdir()
            oracle,expected=adapter.oracle(case,d,deadline,'smart')
            result,raw,guards=adapter.candidate(case,d,'smart',deadline)
            status=('exact' if result['status']=='ok' and raw==expected else 'mismatch') if oracle['status']=='ok' else 'uncompared'
            row=dict(index=i,depth=case['depth'],geometry=case['geometry'],parameters=case['parameters'],input_sha256=sha(case['pixels']),oracle=oracle,result=result,guards=guards,oracle_sha256=sha(expected),output_sha256=sha(raw),status=status)
            report['cases'].append(row);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print(i,status,flush=True)
    finally:shutil.rmtree(out/'build',ignore_errors=True)
    from collections import Counter
    print(dict(Counter(r['status'] for r in report['cases'])))
    assert not any(r['status']=='mismatch' or r['result'].get('sanitizer') for r in report['cases'])
if __name__=='__main__':main()
