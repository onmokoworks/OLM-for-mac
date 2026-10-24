"""Retain P04d cropped checkout witnesses, with both routes' observed results."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.colorkeep import Adapter
from core import save_corpus,sha
from geometry import sample
from run import main_checkout
S=ROOT/'orchestra/state/P04d-colorkeep-cropped-checkout'
C=ROOT/'tests/fuzz_corpus/colorkeep/P04d-cropped-checkout'
C.mkdir(parents=True,exist_ok=True)
a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker',max_size=256,case_timeout=10))
for seed in (1,20261025):
    report=json.loads((S/f'realistic-v2-{seed}.json').read_text())
    for row in report['cases']:
        assert row['result']['routes']['smart']['status']=='exact'
        c=sample(a.generate(seed,row['index']),'realistic-v2')
        assert sha(c['pixels'])==row['input_sha256']
        save_corpus(C/f"seed{seed}-case{row['index']:03d}.json",a,c,c,row['result'],{'accepted':[],'attempts':0},report['provenance'])
print('saved',len(list(C.glob('*.json'))))
