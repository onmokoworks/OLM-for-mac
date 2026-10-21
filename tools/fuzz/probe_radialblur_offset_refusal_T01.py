#!/usr/bin/env python3
"""Retain a corpus witness's refusal trace, which directory replay omits."""
import argparse
import json
import os
from pathlib import Path
import shutil
import time

from adapters.radialblur import Adapter, ROOT
from core import load_corpus, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--main', type=Path,
                        default=Path('/Users/onmk/Documents/Projects/Personal/OLM as'))
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--case-timeout', type=float, default=10)
    parser.add_argument('--max-size', type=int, default=256)
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state/T01-radial-offset-promote')
    assert not os.environ.get('OLM_RADIAL_CANDIDATE_BYPASS')
    scratch.mkdir(parents=True, exist_ok=False)
    adapter = Adapter(args)
    deadline = time.monotonic() + 300
    try:
        provenance = adapter.prepare(scratch, deadline)
        case, saved = load_corpus(args.corpus, adapter)
        oracle, expected = adapter.oracle(case, scratch, deadline)
        routes = {}
        for route in adapter.routes:
            result, raw, guards = adapter.candidate(case, scratch, route, deadline)
            routes[route] = dict(result=result, refusal_guards=guards,
                                 raw_sha256=sha(raw) if raw else None,
                                 exact=oracle['status'] == 'ok' and
                                       result['status'] == 'ok' and raw == expected)
        report = dict(schema='radialblur.offset-refusal-trace/1',
                      provenance=provenance, corpus=str(args.corpus),
                      input_sha256=saved['input_sha256'],
                      case={k: v for k, v in case.items() if k != 'pixels'},
                      oracle=oracle, oracle_raw_sha256=sha(expected), routes=routes)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
        print(json.dumps(dict(oracle=oracle, routes=routes), sort_keys=True))
    finally:
        shutil.rmtree(scratch)


if __name__ == '__main__':
    main()
