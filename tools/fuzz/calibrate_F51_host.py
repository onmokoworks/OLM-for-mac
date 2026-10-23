#!/usr/bin/env python3
"""Cross-check standalone arm64 outputs with the retained F47d shared-arena host."""
import argparse
import json
from pathlib import Path
import time
from types import SimpleNamespace
from adapters.plugin_bundle import Adapter
from core import sha
from verify_F47d import ROOT, PLUGINS

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rows', type=Path, nargs='+', required=True)
    p.add_argument('--bundles', type=Path, required=True)
    p.add_argument('--state', type=Path, default=ROOT/'orchestra/state/F51-x86_64-slice-equivalence/calibration')
    p.add_argument('--worker', type=Path, default=Path.home()/'.cache/olm-emu/worker-F47d/aex-guest-worker')
    args=p.parse_args(); args.state.mkdir(parents=True,exist_ok=True)
    records={}
    for path in args.rows:
        with path.open() as f:
            for line in f:
                r=json.loads(line)
                if r['case'] in ('seed1/0','seed1/1','seed1/2'):
                    records[(r['plugin'],r['case'])]=r
    results=[]
    missing=[(plugin,f'seed1/{i}') for plugin in PLUGINS for i in range(3)
             if (plugin,f'seed1/{i}') not in records]
    if missing: raise ValueError('Run slice comparisons to completion first: '+repr(missing))
    for plugin,name in PLUGINS.items():
        options=SimpleNamespace(main=ROOT.parent.parent,worker=args.worker,max_size=256,case_timeout=30,
                                plugin=plugin,plugin_bundle=args.bundles/'xcode'/name/'products'/(name+'.plugin'))
        adapter=Adapter(options)
        work=args.state/plugin; work.mkdir(exist_ok=True)
        adapter.prepare(work,time.monotonic()+60)
        for i in range(3):
            case=adapter.generate(1,i)
            if plugin=='olmsmoother' and case['depth']==32: continue  # F47d AEX setup rejects before bundle dispatch.
            result,raw,*guards=adapter.candidate(case,work,adapter.routes[0],time.monotonic()+40)
            before=records[(plugin,f'seed1/{i}')]['arm64']
            equal=result['status']=='ok' and before['status']=='render' and sha(raw)==before['sha256']
            row=dict(plugin=plugin,index=i,depth=case['depth'],equal=equal,standalone_sha256=before.get('sha256'),
                     shared_arena_sha256=sha(raw),status=result['status'])
            (work/f'{i}.json').write_text(json.dumps(result,indent=2)+'\n')
            results.append(row); print(plugin,i,equal,result['status'],flush=True)
    summary=dict(worker_sha256=sha(args.worker.read_bytes()),results=results)
    (args.state/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return int(not all(r['equal'] for r in results))

if __name__=='__main__': raise SystemExit(main())
