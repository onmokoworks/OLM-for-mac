"""Original-AEX checks for expanded requests, empty results and extent/aspect."""
import copy
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from adapters.colorkeep import Adapter
from core import evaluate, save_corpus
from geometry import sample, require_host
from run import main_checkout
S = ROOT/'orchestra/state/P02a-colorkeep-geometry/boundaries'
S.mkdir(parents=True, exist_ok=True)
os.environ['TMPDIR'] = str(S)
a = Adapter(SimpleNamespace(main=main_checkout(), worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker', max_size=256, case_timeout=10))
a.env.update(TMPDIR=str(S), TMP=str(S), TEMP=str(S))
deadline = time.monotonic()+600
provenance = a.prepare(S, deadline)
rows = []
for depth in (8,16,32):
    for i in range(100):
        base = sample(a.generate(20261025,i),'realistic')
        if base['depth']==depth and min(base['geometry'])>1: break
    w,h = base['geometry']
    for label,rect in [('expanded',[-3,-2,w+4,h+5]), ('empty',[w+1,h+1,w+3,h+3]), ('tile',[1,1,w,h])]:
        for aspect in ([1,1],[4,3]):
            c = copy.deepcopy(base)
            c.update(request_rect=rect, extent_hint=[w-1,h-1,w,h], pixel_aspect=aspect)
            require_host(a,c)
            result = evaluate(a,c,S,deadline)
            rows.append(dict(depth=depth,label=label,aspect=aspect,result=result))
            assert result['routes']['smart']['status']=='exact', rows[-1]
            target=ROOT/'tests/fuzz_corpus/colorkeep_realistic_P02a'/f'boundary_{depth}_{label}_{aspect[0]}.json'
            save_corpus(target,a,c,c,result,{'accepted':[],'attempts':0},provenance)
(S/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
print(len(rows),'Smart exact boundary cases')
