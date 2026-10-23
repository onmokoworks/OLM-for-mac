#!/usr/bin/env python3
"""Recheck generated oracle status drift with a 60-second limit; preserve campaigns."""
import importlib
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace
from core import sha
ROOT = Path(__file__).resolve().parents[2]
S = ROOT/'orchestra/state/F44-integrate-ms-float'
D = S/'status-rechecks'
D.mkdir(exist_ok=True)
os.environ.update(TMPDIR=str(D), TMP=str(D), TEMP=str(D), PYTHONDONTWRITEBYTECODE='1', OLM_UCRT_FMA='1')
rows = []
for path in sorted(S.glob('*-seed*.json')):
    if path.name.startswith('before-'): continue
    before, after = (json.loads(p.read_text()) for p in (S/('before-'+path.name), path))
    for x,y in zip(before['cases'],after['cases']):
        old = x['result'].get('oracles', {'smart':x['result']['oracle']})
        new = y['result'].get('oracles', {'smart':y['result']['oracle']})
        for route in old:
            a,b = old[route], new[route]
            if a['status'] == b['status']: continue
            results = []
            for name in ['worker-F32-deep', 'worker-F44-msfloat']:
                worker = Path.home()/'.cache/olm-emu'/name/'aex-guest-worker'
                adapter = importlib.import_module('adapters.'+after['plugin']).Adapter(SimpleNamespace(main=ROOT.parent.parent, worker=worker, max_size=256, case_timeout=60))
                assert sha(adapter.aex.read_bytes()) == before['provenance']['aex_sha256'] == after['provenance']['aex_sha256']
                case = adapter.generate(y['seed'], y['index'])
                assert sha(case['pixels']) == x['input_sha256'] == y['input_sha256']
                started = time.monotonic()
                result, raw = adapter.oracle(case, D, time.monotonic()+120, route=route)
                if result['status'] == 'ok': result['raw_sha256'] = sha(raw)
                results.append({'worker':name, 'worker_sha256':sha(worker.read_bytes()), 'result':result, 'elapsed_seconds':time.monotonic()-started})
            rows.append({'campaign':path.stem, 'case':y['index'], 'route':route, 'input_sha256':x['input_sha256'], 'original_before':{k:v for k,v in a.items() if k!='diagnostic'}, 'original_after':{k:v for k,v in b.items() if k!='diagnostic'}, 'rechecks':results})
            print(path.stem, y['index'], route, [(r['result']['status'],r['result'].get('raw_sha256')) for r in results], flush=True)
(ROOT/'orchestra/reports/F44-evidence/status-rechecks.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(r['rechecks'][0]['result']['status']=='ok' and r['rechecks'][1]['result']['status']=='ok' and r['rechecks'][0]['result']['raw_sha256']==r['rechecks'][1]['result']['raw_sha256'] for r in rows), 'Unresolved status drift'
