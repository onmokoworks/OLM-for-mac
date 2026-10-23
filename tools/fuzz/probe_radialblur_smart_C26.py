#!/usr/bin/env python3
"""Scratch-only C26 admission experiments, bound to original campaign hashes."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace
sys.dont_write_bytecode = True
from adapters.radialblur import Adapter, public
from core import sha, raw_diff
from verify_radialblur_smart_C06 import ROOT, MAIN, WORKER


def candidate_source(experiment):
    source = public.SOURCE.read_text()
    if experiment == 'centers32':
        old = 'std::is_same<PixelT, PF_Pixel8>::value ||\n\t\t(std::is_same<PixelT, PF_Pixel16>::value && info.blur_type == 1);'
        new = 'std::is_same<PixelT, PF_Pixel8>::value || std::is_same<PixelT, PF_PixelFloat>::value ||\n\t\t(std::is_same<PixelT, PF_Pixel16>::value && info.blur_type == 1);'
    elif experiment == 'finite-rotation':
        old = 'GenericRadialInputIsSDR<PF_PixelFloat>(input));'
        new = 'GenericRadialInputIsFinite<PF_PixelFloat>(input));'
    elif experiment == 'budget':
        old = 'return bytes <= kMaxBytes && work <= kMaxWork;'
        new = 'return bytes <= kMaxBytes; // Diagnostic only: retain memory bound.'
    else:
        raise ValueError(experiment)
    assert source.count(old) == 1
    return source.replace(old, new)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--experiment', choices=('centers32','finite-rotation','budget'), required=True)
    ap.add_argument('--campaign', type=Path)
    ap.add_argument('--snapshot-only', action='store_true')
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C26-radial-smart-r4')
    out.mkdir(parents=True, exist_ok=False)
    source = candidate_source(args.experiment)
    snapshot = out/'experiment.cpp'
    snapshot.write_text(source)
    snapshot.with_suffix('.h').write_bytes(public.SOURCE.with_suffix('.h').read_bytes())
    if args.snapshot_only:
        print(snapshot)
        return
    if args.campaign is None:
        ap.error('--campaign is required unless --snapshot-only is set')
    public.SOURCE = snapshot
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out), OLM_RADIAL_CANDIDATE_SANITIZE='1')
    adapter = Adapter(SimpleNamespace(main=MAIN,worker=WORKER,max_size=256,case_timeout=60))
    deadline = time.monotonic()+7200
    report = dict(experiment=args.experiment, provenance=adapter.prepare(out,deadline), rows=[])
    campaign = json.loads(args.campaign.read_text())
    report['campaign_sha256'] = sha(args.campaign.read_bytes())
    for row in campaign['cases']:
        before = row['result']['routes']['smart']; oracle = row['result']['oracles']['smart']
        if not args.all and not (before['status']=='refusal' and oracle['status']=='ok'): continue
        case = adapter.generate(campaign['seed'],row['index'])
        assert sha(case['pixels']) == row['input_sha256']
        actual, raw, guards = adapter.candidate(case,out,'smart',deadline)
        status = actual['status']
        if status == 'ok': status = ('exact' if sha(raw)==oracle.get('raw_sha256') else 'mismatch') if oracle['status']=='ok' else 'uncompared'
        entry = dict(index=row['index'],before=before,oracle=oracle,after=dict(actual,status=status,raw_sha256=sha(raw)),guards=guards)
        if status == 'mismatch':
            observed, reference = adapter.oracle(case,out,deadline,'smart')
            assert observed['status']=='ok' and sha(reference)==oracle['raw_sha256']
            entry['diff']=raw_diff(reference,raw,case['depth'])
        report['rows'].append(entry)
        print(row['index'],before['status'],'->',status,entry.get('diff',''),flush=True)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.rmtree(out/'build')


if __name__ == '__main__': main()
