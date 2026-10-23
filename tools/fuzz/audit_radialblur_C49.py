#!/usr/bin/env python3
"""Reproduce C49 scratch-only Smart admission and host-boundary experiments."""
import argparse
from collections import Counter
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from adapters.radialblur import Adapter, ROOT, public
from core import sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', type=Path)
    parser.add_argument('--generate-seed', type=int, help='Generate a fresh sanitized n300 Smart campaign instead of replaying hashes')
    parser.add_argument('--experiment', choices=['override-work', 'resolved-work', 'none-host', 'production'], required=True)
    parser.add_argument('--indices', help='Comma-separated subset; omitted means entire campaign')
    parser.add_argument('--retry-oracle', action='store_true')
    parser.add_argument('--revision', help='Read source from this revision for a baseline experiment')
    parser.add_argument('--budget-metrics', action='store_true')
    parser.add_argument('--probe-raw-watch', action='store_true', help='Probe retained-worker raw-session watch support without building a candidate')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C49-radial-smart-r9')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out), OLM_RADIAL_CANDIDATE_SANITIZE='1')
    if args.generate_seed is None:
        if args.campaign is None:
            parser.error('--campaign or --generate-seed is required')
        opener = gzip.open if args.campaign.suffix == '.gz' else open
        with opener(args.campaign, 'rt') as stream:
            campaign = json.load(stream)
    source = public.SOURCE
    if args.revision or args.experiment in ('override-work', 'resolved-work'):
        body = (subprocess.check_output(['git','show',args.revision+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=ROOT).decode()
                if args.revision else source.read_text())
        if args.experiment in ('override-work', 'resolved-work'):
            old = ('((smart_render && !unverified_override) || work <= kMaxWork)'
                   if args.experiment == 'override-work' else 'work = std::max(work, offset_work);')
            assert body.count(old) == 1
            body = body.replace(old, '(smart_render || work <= kMaxWork)' if args.experiment == 'override-work'
                                else 'work = smart_render ? offset_work : std::max(work, offset_work);')
        body = re.sub(r'^#include "([^\"]+)"', lambda m: '#include "'+str((source.parent/m[1]).resolve())+'"', body, flags=re.MULTILINE)
        snapshot = out/'experiment.cpp'
        snapshot.write_text(body)
        snapshot.with_suffix('.h').write_bytes(source.with_suffix('.h').read_bytes())
        for name in ('OLMRadialBlur.h', 'OLMRadialBlur_Strings.h', 'OLMRadialBlur_Strings.cpp'):
            (out/name).symlink_to(source.parent/name)
        public.SOURCE = snapshot
    if args.experiment == 'none-host':
        # Model an absent layer, not a made-up source copy or zero-filled image.
        body = public.initial.HARNESS.read_text()
        old = '    if(slot||id||!request->preserve_rgb_of_zero_alpha'
        assert body.count(old) == 1
        body = body.replace(old, '    if(slot==OLMRADIALBLUR_NOISE_LAYER && id==slot) { ++g_pre; *result={}; return 0; }\n'+old)
        old = '    if(slot)return 711;'
        assert body.count(old) == 1
        body = body.replace(old, '    if(slot==OLMRADIALBLUR_NOISE_LAYER) { ++g_pixel_out; *v=nullptr; return 0; }\n'+old)
        old = 'if(slot)return 712;'
        assert body.count(old) == 1
        body = body.replace(old, 'if(slot && slot!=OLMRADIALBLUR_NOISE_LAYER)return 712;')
        harness = out/'none_host.cpp'
        harness.write_text(body)
        public.initial.HARNESS = harness
    if args.budget_metrics:
        body = public.initial.HARNESS.read_text()
        marker = '    const auto info=InfoFromParams(params,w,h);'
        assert body.count(marker)==1
        body = body.replace(marker, marker+'''
    size_t budget_bytes=0; uint64_t budget_work=0;
    const bool budget_ok=CheckedRadialGenericBudget(w,h,depth,info,true,&budget_bytes,&budget_work);
    fprintf(stderr,"BUDGET %d %zu %llu\\n",(int)budget_ok,budget_bytes,(unsigned long long)budget_work);
''')
        harness=out/'budget_host.cpp'
        harness.write_text(body)
        public.initial.HARNESS=harness
    if args.generate_seed is not None:
        Adapter.routes=('smart',)
        Adapter.oracle_routes={'smart':'smart'}
        sys.argv=[sys.argv[0],'--plugin','radialblur','--n','300','--seed',str(args.generate_seed),
                  '--jobs','1','--shrink-attempts','0','--scratch',str(out/'work'),
                  '--report',str(out/'campaign.json'),'--corpus',str(out/'corpus')]
        import run
        return run.main()
    main_root = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT
    adapter = Adapter(SimpleNamespace(main=main_root, max_size=256, case_timeout=60,
        worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker'))
    adapter.routes = ('smart',)
    adapter.oracle_routes = {'smart': 'smart'}
    deadline = time.monotonic()+1800
    if args.probe_raw_watch:
        adapter.session_arguments=lambda case,directory:['--watch','function=0xb150,arg=rcx,size=64,occurrence=1']
        case=adapter.generate(campaign['seed'],int(args.indices or '17'))
        oracle,raw=adapter.oracle(case,out,deadline,'smart')
        result=dict(worker_sha256=sha(adapter.worker.read_bytes()),input_sha256=sha(case['pixels']),
                    seed=campaign['seed'],index=case['index'],oracle=oracle,output_bytes=len(raw))
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(dict(status=oracle['status'],output_bytes=len(raw))))
        return 0
    report = dict(experiment=args.experiment, campaign_sha256=sha(args.campaign.read_bytes()),
                  provenance=adapter.prepare(out, deadline), seed=campaign['seed'], rows=[])
    selected = set(map(int, args.indices.split(','))) if args.indices else None
    try:
        for row in campaign['cases']:
            index = row['index']
            if selected is not None and index not in selected:
                continue
            case = adapter.generate(campaign['seed'], index)
            assert sha(case['pixels']) == row['input_sha256']
            before = row['result']['routes']['smart']
            oracle = row['result'].get('oracles', {}).get('smart', row['result'].get('oracle'))
            recorded_oracle = oracle
            elapsed = None
            if args.retry_oracle:
                started = time.monotonic()
                oracle, reference = adapter.oracle(case, out, deadline, 'smart')
                oracle = dict(oracle, raw_sha256=sha(reference) if reference else None)
                elapsed = time.monotonic()-started
            actual, raw, guards = adapter.candidate(case, out, 'smart', deadline)
            after = dict(actual, raw_sha256=sha(raw) if raw else None)
            if actual['status'] == 'ok':
                after['status'] = ('exact' if sha(raw) == oracle['raw_sha256'] else 'mismatch') if oracle['status']=='ok' else 'uncompared'
            report['rows'].append(dict(index=index, input_sha256=row['input_sha256'], before=before,
                after=after, guards=guards, oracle=oracle, recorded_oracle=recorded_oracle, oracle_seconds=elapsed))
            report['counts'] = dict(Counter(r['after']['status'] for r in report['rows']))
            report['lost_exact'] = [r['index'] for r in report['rows'] if r['before']['status']=='exact' and
                (r['after']['raw_sha256'] != r['before']['raw_sha256'] or r['after']['status'] != 'exact')]
            report['sanitizer_failures'] = [r['index'] for r in report['rows'] if r['after'].get('sanitizer')]
            (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({k:report[k] for k in ('experiment','counts','lost_exact','sanitizer_failures')}))
    finally:
        shutil.rmtree(out/'build', ignore_errors=True)
    return int(bool(report['lost_exact'] or report['sanitizer_failures'] or report['counts'].get('mismatch')))


if __name__ == '__main__':
    raise SystemExit(main())
