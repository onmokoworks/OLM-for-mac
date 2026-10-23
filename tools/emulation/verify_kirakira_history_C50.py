#!/usr/bin/env python3
"""Replay S01 Smart history under sanitizers against its retained F46 hashes."""
import argparse
from collections import Counter
import gzip
import json
import os
from pathlib import Path
import shutil
import time
from types import SimpleNamespace
from verify_kirakira_admission_F10 import (
    ROOT, adapter_class, main_checkout, default_worker, olmkirakira, sha)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=olmkirakira.SOURCE)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    s = args.scratch.resolve()
    assert s.is_relative_to(ROOT/'orchestra/state')
    s.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(s), TMP=str(s), TEMP=str(s))
    options = SimpleNamespace(max_size=256, case_timeout=180, main=main_checkout(), worker=default_worker())
    a = adapter_class(args.source)(options)
    d = time.monotonic()+3600
    r = dict(status='running', source_sha256=sha(args.source.read_bytes()),
             worker_sha256=sha(options.worker.read_bytes()), rows=[], histories={})
    def save():
        r['counts'] = dict(Counter(x['status'] for x in r['rows']))
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(r, indent=2, sort_keys=True)+'\n')
    try:
        (s/'build').mkdir(); a.binary, _ = a.build(s/'build', d)
        (s/'case').mkdir()
        for seed in range(101,105):
            path = ROOT/f'orchestra/reports/S01-wide-mismatch-sweep/olmkirakira_seed{seed}.json.gz'
            with gzip.open(path) as stream: history = json.load(stream)
            assert history['provenance']['worker_sha256'] == r['worker_sha256']
            r['histories'][str(seed)] = dict(path=str(path.relative_to(ROOT)), sha256=sha(path.read_bytes()))
            for old in history['cases']:
                case = a.generate(seed, old['index'])
                assert sha(case['pixels']) == old['input_sha256']
                for key in ('depth','geometry','parameters','input_padding','output_padding'):
                    assert case[key] == old[key], (seed,old['index'],key)
                result, raw, *_ = a.candidate(case, s/'case', 'smart', d)
                before = old['result']['routes']['smart']
                oracle = old['result']['oracles']['smart']
                assert result['status'] in ('ok','refusal'), result
                if result['status'] == 'ok':
                    assert oracle['status'] == 'ok' and sha(raw) == oracle['raw_sha256'], (seed,old['index'],result)
                    if before['status'] == 'exact': assert sha(raw) == before['raw_sha256']
                else:
                    assert before['status'] == 'refusal', (seed,old['index'],before,result)
                r['rows'].append(dict(seed=seed,index=old['index'],before=before['status'],
                    status='exact' if result['status']=='ok' else 'refusal',raw_sha256=sha(raw)))
            save(); print(seed, r['counts'], flush=True)
        r['status']='passed'; save()
    except BaseException as exc:
        r.update(status='failed',error=repr(exc));save();raise
    finally:
        for name in ('build','case'): shutil.rmtree(s/name,ignore_errors=True)


if __name__ == '__main__': main()
