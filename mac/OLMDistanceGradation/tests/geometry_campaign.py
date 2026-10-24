#!/usr/bin/env python3
"""DistanceGradation-only F52c campaign; preserves raw comparisons in ticket scratch."""
import argparse, collections, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
import measure_F52c
from adapters.olmdistancegradation import Adapter
p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=1);p.add_argument('--n',type=int,default=100);p.add_argument('--label',default='candidate');p.add_argument('--corpus',action='store_true')
a=p.parse_args()
generate=Adapter.generate
Adapter.generate=lambda self,seed,index:generate(self,a.seed,index)
measure_F52c.S=ROOT/'orchestra/state/P02b-distancegradation-geometry'/a.label/f'seed{a.seed}'
sys.argv=['measure_F52c.py','--plugin','olmdistancegradation','--n',str(a.n),'--jobs','1']
measure_F52c.main()
rows=[json.loads(s) for s in (measure_F52c.S/'campaigns/olmdistancegradation/results.jsonl').read_text().splitlines()]
summary={}
for route in ('classic','smart'):
    summary[route]=dict(collections.Counter(
        r['result']['routes'][route]['status'] if r['result']['oracles'][route]['status']=='ok' else 'unavailable'
        for r in rows))
folder=measure_F52c.S/'campaigns/olmdistancegradation'
(folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
if a.corpus:
    from core import save_corpus
    from geometry import sample
    from types import SimpleNamespace
    from run import main_checkout
    adapter=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10))
    provenance=json.loads((folder/'provenance.json').read_text())
    corpus=ROOT/'tests/fuzz_corpus/olmdistancegradation_realistic_P02b';corpus.mkdir(exist_ok=True)
    for row in rows:
        case=sample(generate(adapter,a.seed,row['case']['index']),'realistic')
        save_corpus(corpus/f"seed{a.seed}_case{case['index']:06d}.json",adapter,case,case,row['result'],
                    {'accepted':[],'attempts':0,'label':'P02b realistic-v1 geometry'},provenance)
