#!/usr/bin/env python3
"""Bind F12 active Alpha/box stages to the original public AEX output.

Uses the F09 original-binary trace scaffold, with no numerical detours, and
production admission on the instrumented Mac public entry point.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from trace_kirakira_numeric_F09 import (
    ROOT, build_mac, default_worker, load_corpus, main_checkout,
    olmkirakira, original_trace, raw_diff, sha)
from verify_kirakira_admission_F12 import matrix_cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch),
                      OLM_KK_PROCESS_ATTACH_DIAGNOSTIC='1',
                      OLM_KK_MANUAL_CRT_INITIALIZERS_DIAGNOSTIC='1')
    deadline = time.monotonic()+3600
    options = SimpleNamespace(max_size=256, case_timeout=180, main=main_checkout(), worker=default_worker())
    adapter = build_mac(olmkirakira.SOURCE, scratch/'build', options, deadline, False)
    path = next((ROOT/'tests/fuzz_corpus/olmkirakira_gate_off_T06').glob('seed1_case000003_*.json'))
    target, _ = load_corpus(path, adapter)
    independent = next(c for c in matrix_cases(adapter) if c['depth'] == 32)
    for p in independent['parameters']:
        if p['slot'] in (13, 19, 25, 31, 37):
            p['value'] = 0
        elif p['slot'] in (10, 16, 22, 28, 34):
            p['value'] = 3
    cases = [('C28', target), ('F10-seed2-127', adapter.generate(2, 127)),
             ('independent-PF32', independent)]
    report = dict(schema='olm-kira-F12-active-trace/1', rows=[], status='running',
                  source_sha256=sha(olmkirakira.SOURCE.read_bytes()),
                  aex_sha256=sha(adapter.aex.read_bytes()), worker_sha256=sha(adapter.worker.read_bytes()))

    def save():
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')

    try:
        for label, case in cases:
            directory = scratch/label
            directory.mkdir(exist_ok=True)
            adapter.env['F09_TRACE'] = str(directory)
            oracle, reference = adapter.oracle(case, directory, deadline)
            candidate, raw, *_ = adapter.candidate(case, directory, 'classic', deadline)
            original = original_trace(case, adapter.aex)
            stages = original['stages']
            assert oracle['status'] == candidate['status'] == 'ok'
            assert bytes.fromhex(stages['output']) == reference == raw, (label, original.get('error'))
            paired = {}
            for name in ('source', 'seed', 'ray0', 'ray1', 'ray2', 'ray3', 'ray4', 'glow', 'composed'):
                aex = bytes.fromhex(stages[name])
                mac = (directory/(name+'.raw')).read_bytes()
                paired[name] = dict(exact=aex == mac, aex_sha256=sha(aex), mac_sha256=sha(mac),
                                    diff=None if aex == mac else raw_diff(aex, mac, 32))
                assert aex == mac, (label, name, paired[name])
            report['rows'].append(dict(label=label, depth=case['depth'], geometry=case['geometry'],
                parameters=case['parameters'], input_sha256=sha(case['pixels']),
                output_sha256=sha(raw), paired=paired, aex_geometry=original['geometry'],
                abi_leaf_exact=True, public_binding_exact=True))
            save()
            print(label, 'all nine stages exact; production output bound to public AEX', flush=True)
        report['status'] = 'passed'
        save()
    except BaseException as exc:
        report.update(status='failed', error=repr(exc))
        save()
        raise
    finally:
        shutil.rmtree(scratch/'build', ignore_errors=True)
        for label, _ in cases:
            shutil.rmtree(scratch/label, ignore_errors=True)


if __name__ == '__main__':
    main()
