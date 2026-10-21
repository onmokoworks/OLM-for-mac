#!/usr/bin/env python3
"""Re-render saved corpora at both source revisions; audit each changed sample.

Production replay preserves all guards. Diagnostic replay bypasses only final
tuple admission; it compares the Classic outputs (Smart has the same arithmetic
and is independently checked by triage_kirakira.py --sanitizers).
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from trace_kirakira_numeric_F09 import (ROOT, build_mac, default_worker,
    load_corpus, main_checkout, olmkirakira, raw_diff, sha)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--before-source',type=Path,required=True)
    p.add_argument('--after-source',type=Path,default=olmkirakira.SOURCE)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args = p.parse_args()
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch))
    options = SimpleNamespace(max_size=256,case_timeout=60,main=main_checkout(),worker=default_worker())
    deadline = time.monotonic()+1800
    report = dict(before_source_sha256=sha(args.before_source.read_bytes()),
        after_source_sha256=sha(args.after_source.read_bytes()),rows=[])
    for corpus,gate_off in [('olmkirakira',False),('olmkirakira_gate_off_T06',True)]:
        before = build_mac(args.before_source,args.scratch/(corpus+'-before'),options,deadline,gate_off)
        after = build_mac(args.after_source,args.scratch/(corpus+'-after'),options,deadline,gate_off)
        for path in sorted((ROOT/'tests/fuzz_corpus'/corpus).glob('*.json')):
            case,saved = load_corpus(path,after)
            directory = args.scratch/(corpus+'-'+path.stem); directory.mkdir(exist_ok=True)
            oracle,reference = after.oracle(case,directory,deadline)
            routes = ['classic','smart'] if not gate_off else ['classic']
            for route in routes:
                old,oldraw,*_ = before.candidate(case,directory,route,deadline)
                new,newraw,*_ = after.candidate(case,directory,route,deadline)
                unit = case['depth']//8
                changed = [i for i in range(0,len(oldraw),unit) if oldraw[i:i+unit]!=newraw[i:i+unit]]
                away = [i//unit for i in changed if newraw[i:i+unit]!=reference[i:i+unit]]
                row = dict(corpus=corpus,index=case['index'],route=route,oracle=oracle,
                    before=old,after=new,before_sha256=sha(oldraw),after_sha256=sha(newraw),
                    reference_sha256=sha(reference),changed_samples=len(changed),changed_not_to_exact=away,
                    before_diff=raw_diff(reference,oldraw,case['depth']) if old['status']=='ok' and reference!=oldraw else None,
                    after_diff=raw_diff(reference,newraw,case['depth']) if new['status']=='ok' and reference!=newraw else None)
                report['rows'].append(row)
                args.report.parent.mkdir(parents=True,exist_ok=True)
                args.report.write_text(json.dumps(report,indent=2)+'\n')
                assert old['status']==new['status']
                assert len(oldraw)==len(newraw)
                assert oracle['status']=='ok' and not away, row
                if changed:
                    print(corpus,case['index'],route,'changed_samples',len(changed),'all now exact',flush=True)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(len(report['rows']),'route replays; zero changed samples away from exact')


if __name__ == '__main__':
    main()
