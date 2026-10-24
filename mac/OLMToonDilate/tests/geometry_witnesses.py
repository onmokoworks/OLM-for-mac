#!/usr/bin/env python3
"""P02e labelled Smart geometry corpus, using the registered F52c oracle."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import time
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/fuzz'))
from adapters.olmtoondilate import Adapter
from core import evaluate, save_corpus
from geometry import sample, require_host
from run import main_checkout
S = ROOT / 'orchestra/state/P02e-toondilate-geometry/witnesses'
C = ROOT / 'tests/fuzz_corpus/olmtoondilate_P02e_realistic'
S.mkdir(parents=True, exist_ok=True)
C.mkdir(parents=True, exist_ok=True)
a = Adapter(SimpleNamespace(main=main_checkout(), worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker', max_size=256, case_timeout=10))
a.routes = ('smart',)
a.env.update(TMPDIR=str(S), TMP=str(S), TEMP=str(S))
require_host(a, sample(a.generate(1, 0), 'realistic'))
deadline = time.monotonic() + 1200
provenance = a.prepare(S, deadline)
cases = [(f'seed{seed}_{i:03d}', sample(a.generate(seed, i), 'realistic'))
         for seed in (1, 20261024) for i in range(100)]
# Independently visible seed/frontier: DOUBLE values on either side of a
# float32 integer boundary. Expanded and empty requests negotiate via PreRender.
for depth in (8, 16, 32):
    for radius in (6.00000001, 5.99999999, 2.01):
        for rect in ([0,0,17,11], [3,2,9,7], [-3,-2,20,13], [20,20,21,21]):
            c = sample(a.generate(1, 0), 'realistic')
            opaque = {8:(255,11,33,55),16:(32768,1001,3003,5005),32:(1,.125,.25,.5)}[depth]
            transparent = {8:(0,2,4,6),16:(0,22,44,66),32:(0,.03125,.0625,.09375)}[depth]
            fmt = {8:'4B',16:'<4H',32:'<4f'}[depth]
            c.update(depth=depth, geometry=[17,11], full_geometry=[34,33],
                     downsample=[[1,2],[1,3]], parameters=[dict(slot=1,kind='s',value=radius)],
                     pixels=b''.join(struct.pack(fmt, *(opaque if i==0 else transparent)) for i in range(187)),
                     request_rect=rect, extent_hint=[2,3,7,9], pixel_aspect=[10,11],
                     rowbytes_padding=3, input_padding=3, output_padding=3)
            cases.append((f'boundary_{len(cases):03d}', c))
rows=[]
for name,c in cases:
    result=evaluate(a,c,S,deadline)
    save_corpus(C/(name+'.json'),a,c,c,result,dict(accepted=[]),provenance)
    rows.append(dict(name=name,result=result))
    print(name,result['routes']['smart']['status'],flush=True)
(S/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(r['result']['routes']['smart']['status']=='exact' for r in rows)
