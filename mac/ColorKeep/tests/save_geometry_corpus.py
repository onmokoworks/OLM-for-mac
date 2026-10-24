"""Retain labelled exact realistic-v1 witnesses from completed campaign reports."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from adapters.colorkeep import Adapter
from core import save_corpus, sha
from geometry import sample
from run import main_checkout
S = ROOT/'orchestra/state/P02a-colorkeep-geometry'
C = ROOT/'tests/fuzz_corpus/colorkeep_realistic_P02a'
C.mkdir(parents=True, exist_ok=True)
a = Adapter(SimpleNamespace(main=main_checkout(), worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker', max_size=256, case_timeout=10))
for name in ('final-real1', 'final-real2'):
    report = json.loads((S/(name+'.json')).read_text())
    # Retain every sampled depth, scale, aspect and ROI; Classic results remain
    # recorded independently and are not promoted to the Smart contract.
    for row in report['cases']:
        assert row['result']['routes']['smart']['status'] == 'exact'
        c = sample(a.generate(row['seed'], row['index']), 'realistic')
        assert sha(c['pixels']) == row['input_sha256']
        save_corpus(C/f"seed{c['seed']}_case{c['index']:06d}.json", a, c, c,
                    row['result'], {'accepted': [], 'attempts': 0}, report['provenance'])
print('Saved', len(list(C.glob('*.json'))), 'realistic-v1 witnesses')
