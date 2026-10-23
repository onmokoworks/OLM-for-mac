#!/usr/bin/env python3
"""Sanitized final-source replay against hash-bound completed campaign outputs."""
import argparse
import json
import os
from pathlib import Path
import shutil
import time
from types import SimpleNamespace
from verify_kirakira_admission_F10 import ROOT, adapter_class, olmkirakira, main_checkout, default_worker, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign', type=Path, action='append', required=True)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT / 'orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    options = SimpleNamespace(max_size=256, case_timeout=60, main=main_checkout(), worker=default_worker())
    deadline = time.monotonic() + 3600
    adapter = adapter_class(olmkirakira.SOURCE)(options)
    build = scratch / 'build'; build.mkdir()
    directory = scratch / 'case'; directory.mkdir()
    report = dict(source_sha256=sha(olmkirakira.SOURCE.read_bytes()), campaigns=[], status='running')
    try:
        adapter.binary, _ = adapter.build(build, deadline)
        for path in args.campaign:
            baseline = json.loads(path.read_text())
            assert baseline['status'] == 'complete' and baseline['completed'] == 300
            rows = []
            for old in baseline['cases']:
                case = adapter.generate(old['seed'], old['index'])
                assert sha(case['pixels']) == old['input_sha256']
                for field in ('geometry', 'depth', 'parameters', 'input_padding', 'output_padding'):
                    assert case[field] == old[field]
                for route in ('classic', 'smart'):
                    prior = old['result']['routes'][route]
                    result, raw, *_ = adapter.candidate(case, directory, route, deadline)
                    assert result['status'] in ('ok', 'refusal'), result
                    digest = sha(raw) if result['status'] == 'ok' else None
                    if prior['status'] == 'refusal':
                        if result['status'] == 'ok':
                            oracle = old['result']['oracles'][route]
                            assert route == 'smart' and oracle['status'] == 'ok' and digest == oracle['raw_sha256']
                    else:
                        assert result['status'] == 'ok' and digest == prior['raw_sha256'], (old['index'], route)
                    rows.append(dict(index=old['index'], route=route, before=prior['status'],
                                     after=result['status'], raw_sha256=digest))
            report['campaigns'].append(dict(path=str(path), seed=baseline['cases'][0]['seed'], rows=rows))
        report['status'] = 'passed'
    finally:
        shutil.rmtree(build, ignore_errors=True)
        shutil.rmtree(directory, ignore_errors=True)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('PASS', sum(len(r['rows']) for r in report['campaigns']), 'sanitized routes')


if __name__ == '__main__': main()
