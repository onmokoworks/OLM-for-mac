#!/usr/bin/env python3
"""Compare actual Universal bundle slices using the standalone F47d suite host."""
import argparse
import collections
import importlib
import json
import os
from pathlib import Path
import struct
import time
from types import SimpleNamespace

from core import command, load_corpus, sha
from verify_F47d import PLUGINS, ROOT

STATE=ROOT/'orchestra/state/F51-x86_64-slice-equivalence'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, default=STATE)
    parser.add_argument('--bundles', type=Path)
    parser.add_argument('--plugins', nargs='+', choices=PLUGINS, default=list(PLUGINS))
    parser.add_argument('--n', type=int, default=300)
    parser.add_argument('--jobs', type=int, choices=[1], default=1)
    parser.add_argument('--skip-corpus', action='store_true')
    parser.add_argument('--case-timeout', type=float, default=30)
    parser.add_argument('--host', type=Path, default=Path.home()/'.cache/olm-emu/worker-F51-x86host/plugin-host')
    args=parser.parse_args()
    state=args.state.resolve(); state.mkdir(parents=True, exist_ok=True)
    bundles=(args.bundles or STATE/'bundles').resolve()
    worker=args.host.resolve()
    main=ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT
    options=SimpleNamespace(main=main, worker=worker, max_size=256, case_timeout=args.case_timeout)
    env={k:v for k,v in os.environ.items() if not k.startswith(('OLM','DBLUR','COLORKEEP'))}
    env.update(TMPDIR=str(state), TMP=str(state), TEMP=str(state))
    totals=collections.Counter(); plugin_totals={}
    manifest={'host_sha256':sha(worker.read_bytes()), 'bundles':{}, 'n':args.n,
              'seed':1, 'max_size':256, 'timeout':args.case_timeout,
              'host_contract':'F47d shared suites, declarations from retained AEX PARAMS_SETUP; full frame, packed output, rounded input padding; Kira default ramps'}
    with (state/'cases.jsonl').open('w') as rows:
        for plugin in args.plugins:
            adapter=importlib.import_module('adapters.'+plugin).Adapter(options)
            declarations=adapter.declarations if plugin=='radialblur' else adapter.binding['parameters']
            types=[0]+[d['param_type'] for d in declarations]
            assert [d['slot'] for d in declarations]==list(range(1,len(types)))
            decl=state/'declarations.txt'; decl.write_text(' '.join(map(str,[len(types),*types])))
            executable=bundles/'xcode'/PLUGINS[plugin]/'products'/(PLUGINS[plugin]+'.plugin')/'Contents/MacOS'/PLUGINS[plugin]
            manifest['bundles'][plugin]=sha(executable.read_bytes())
            penv=dict(env)
            if plugin=='olmkirakira': penv['OLM_NATIVE_PARAMETER_PROFILE']='kirakira-default-ramps'
            def cases():
                for i in range(args.n): yield f'seed1/{i}',adapter.generate(1,i)
                if not args.skip_corpus:
                    for path in sorted((ROOT/'tests/fuzz_corpus').rglob('*.json')):
                        saved=json.loads(path.read_text())
                        if saved['plugin']!=plugin: continue
                        adapter.max_size=saved['max_size']
                        case,_=load_corpus(path,adapter)
                        yield str(path.relative_to(ROOT)),case
                    adapter.max_size=256
            counts=collections.Counter()
            for identity,case in cases():
                config=state/'parameters.txt'
                config.write_text(''.join(f"{p['slot']} {p['kind']} "+(' '.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value']))+'\n' for p in case['parameters']))
                outputs=[]; results=[]
                for arch in ('arm64','x86_64'):
                    refusal=state/'refusal.txt'; refusal.unlink(missing_ok=True)
                    status,out,err=command(['/usr/bin/arch','-'+arch,worker,executable,*case['geometry'],case['depth'],case['input_padding'],int(plugin!='olmsmoother'),decl,config],
                        data=case['pixels'], timeout=args.case_timeout, deadline=time.monotonic()+args.case_timeout,
                        env=dict(penv,OLM_REFUSAL_TRACE=str(refusal)))
                    result=dict(process=status, refusal=refusal.read_text().splitlines() if refusal.exists() else [])
                    expected=case['geometry'][0]*case['geometry'][1]*case['depth']//8*4
                    trace=err.decode(errors='replace')
                    if status['status']=='ok' and len(out)==4+expected and 'unsupported/invalid callback:' not in trace and 'F47c counters' in trace:
                        result.update(error=struct.unpack('<i',out[:4])[0],sha256=sha(out[4:]))
                        result['status']='render' if result['error']==0 else 'refuse'
                        outputs.append(out[4:])
                    else:
                        result.update(status='host_error',diagnostic=trace[-2000:])
                        outputs.append(None)
                    results.append(result)
                    if result['status']=='host_error':
                        (state/(plugin+'-'+arch+'-error.log')).write_bytes(err)
                a,b=results
                equal=(a['status']==b['status'] and a['status']!='host_error' and a['error']==b['error'] and a['refusal']==b['refusal'] and outputs[0]==outputs[1])
                verdict=('equal_'+a['status']) if equal else 'difference'
                row=dict(plugin=plugin,case=identity,depth=case['depth'],geometry=case['geometry'],input_sha256=sha(case['pixels']),
                    parameters_sha256=sha(config.read_bytes()),verdict=verdict,arm64=a,x86_64=b)
                if not equal and outputs[0] is not None and outputs[1] is not None:
                    row['first_byte']=next((i for i,(x,y) in enumerate(zip(*outputs)) if x!=y),None)
                rows.write(json.dumps(row,sort_keys=True)+'\n'); rows.flush()
                counts[verdict]+=1; totals[verdict]+=1
            plugin_totals[plugin]=dict(counts)
            print(plugin,dict(counts),flush=True)
    manifest.update(totals=dict(totals),plugins=plugin_totals)
    (state/'summary.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('TOTAL',dict(totals),flush=True)
    return int(totals['difference']!=0)

if __name__=='__main__': raise SystemExit(main())
