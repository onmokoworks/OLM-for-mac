#!/usr/bin/env python3
"""C53b bounded Smart campaigns, preserved corpus, and sanitizer replay."""
import argparse
import gzip
import json
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace
sys.dont_write_bytecode=True
from adapters.radialblur import Adapter, public, ROOT
from core import sha


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--seed',type=int)
    ap.add_argument('--replay',type=Path)
    ap.add_argument('--sanitize-campaign',type=Path)
    ap.add_argument('--witnesses',action='store_true',help='Verify all ten C49 hashes on final O2 and ASan/UBSan builds')
    ap.add_argument('--admit-nonfinite',action='store_true',help='Scratch-only gate removal before qualification')
    args=ap.parse_args()
    out=args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C53b-radial-trace-worker')
    out.mkdir(parents=True,exist_ok=False)
    os.environ.update(TMPDIR=str(out),TMP=str(out),TEMP=str(out),OLM_TEST_JOBS='1')
    if args.admit_nonfinite and 'static bool GenericRadialInputIsFinite(' in public.SOURCE.read_text():
        from probe_radialblur_C44 import source_for
        original=public.SOURCE
        body=source_for('gate-only',original.read_text())
        import re
        body=re.sub(r'^#include "([^" ]+)"',lambda m:'#include "'+str((original.parent/m[1]).resolve())+'"',body,flags=re.M)
        source=out/'admitted.cpp';source.write_text(body)
        source.with_suffix('.h').write_bytes(original.with_suffix('.h').read_bytes())
        for name in ('OLMRadialBlur.h','OLMRadialBlur_Strings.h','OLMRadialBlur_Strings.cpp'):
            (out/name).symlink_to(original.parent/name)
        public.SOURCE=source
    if args.witnesses:
        report=dict(builds=[],cases=[])
        deadline=time.monotonic()+1800
        try:
            for sanitized in (False,True):
                os.environ.update(OLM_RADIAL_CANDIDATE_SANITIZE=str(int(sanitized)),
                    ASAN_OPTIONS='halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
                directory=out/('san' if sanitized else 'o2');directory.mkdir()
                adapter=Adapter(SimpleNamespace(main=ROOT.parent.parent,max_size=256,case_timeout=60,
                    worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker'))
                report['builds'].append(adapter.prepare(directory,deadline))
                for seed,indices in ((1,(17,89,238,247)),(105,(25,105,148,185,255,291))):
                    with gzip.open(ROOT/f'orchestra/reports/C49-evidence/seed{seed}.json.gz','rt') as f:
                        campaign=json.load(f)
                    for index in indices:
                        saved=next(r for r in campaign['cases'] if r['index']==index)
                        case=adapter.generate(seed,index)
                        assert sha(case['pixels'])==saved['input_sha256']
                        prior=saved['result']
                        oracle=prior.get('oracles',{}).get('smart',prior.get('oracle'))
                        result,raw,guards=adapter.candidate(case,directory,'smart',deadline)
                        exact=result['status']=='ok' and sha(raw)==oracle['raw_sha256'] and not result.get('sanitizer')
                        report['cases'].append(dict(seed=seed,index=index,sanitized=sanitized,
                            input_sha256=sha(case['pixels']),output_sha256=sha(raw),result=result,guards=guards,exact=exact))
                        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
                shutil.rmtree(directory/'build')
        finally:
            for path in out.rglob('build'):
                if path.is_dir():shutil.rmtree(path)
        print(json.dumps(dict(cases=len(report['cases']),exact=sum(r['exact'] for r in report['cases']))))
        return not all(r['exact'] for r in report['cases'])
    if args.sanitize_campaign:
        os.environ.update(OLM_RADIAL_CANDIDATE_SANITIZE='1', ASAN_OPTIONS='halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        opener=gzip.open if args.sanitize_campaign.suffix=='.gz' else open
        with opener(args.sanitize_campaign,'rt') as f: campaign=json.load(f)
        adapter=Adapter(SimpleNamespace(main=ROOT.parent.parent,max_size=256,case_timeout=60,
            worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker'))
        deadline=time.monotonic()+3600
        report=dict(provenance=adapter.prepare(out,deadline),cases=[],failures=[])
        try:
            for row in campaign['cases']:
                case=adapter.generate(campaign['seed'],row['index'])
                assert sha(case['pixels'])==row['input_sha256']
                result,raw,guards=adapter.candidate(case,out,'smart',deadline)
                before=row['result'].get('routes',{}).get('smart',row['result'].get('candidate'))
                # Smart-only campaign uses the singular candidate schema.
                expected=before.get('raw_sha256')
                same=(result['status']=='ok' and sha(raw)==expected) if before['status'] in ('ok','exact','mismatch','uncompared') else result['status']==before['status']
                ok=same and not result.get('sanitizer')
                item=dict(index=row['index'],input_sha256=sha(case['pixels']),result=result,guards=guards,
                          raw_sha256=sha(raw),matches_campaign=ok)
                report['cases'].append(item)
                if not ok:report['failures'].append(row['index'])
            (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        finally:shutil.rmtree(out/'build',ignore_errors=True)
        print(json.dumps(dict(cases=len(report['cases']),failures=report['failures'])))
        return bool(report['failures'])
    if not args.replay:
        Adapter.routes=('smart',)
        Adapter.oracle_routes={'smart':'smart'}
    argv=['run.py','--plugin','radialblur','--jobs','1','--scratch',str(out/'work'),
          '--report',str(out/'campaign.json'),'--corpus',str(out/'corpus'),'--shrink-attempts','0']
    if args.replay:argv+=['--replay',str(args.replay)]
    else:
        assert args.seed is not None
        argv+=['--seed',str(args.seed),'--n','300']
    sys.argv=argv
    import run
    try:return run.main()
    finally:
        for path in (out/'work').rglob('build'):
            if path.is_dir():shutil.rmtree(path)

if __name__=='__main__':raise SystemExit(main())
