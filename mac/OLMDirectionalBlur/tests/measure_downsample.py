#!/usr/bin/env python3
"""Run the unchanged F52 sampler with a selectable seed and ticket-local scratch."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/fuzz'))
import measure_F52
from adapters.olmdirectionalblur import Adapter
p = argparse.ArgumentParser()
p.add_argument('--seed', type=int, default=1)
p.add_argument('--n', type=int, default=100)
p.add_argument('--label', default='candidate')
a = p.parse_args()
original_generate = Adapter.generate
Adapter.generate = lambda self, seed, index: original_generate(self, a.seed, index)
measure_F52.S = ROOT / 'orchestra/state/P01b-directionalblur-downsample' / f'{a.label}-seed{a.seed}'
sys.argv = ['measure_F52.py', '--plugin', 'olmdirectionalblur', '--n', str(a.n)]
measure_F52.main()

# F52 itself fixes its summary seed to 1; retain the actual override in evidence.
summary = measure_F52.S / 'olmdirectionalblur/summary.json'
report = json.loads(summary.read_text())
report['seed'] = a.seed
report['dependencies']['core/dblur_generic_budget.h'] = measure_F52.sha((ROOT / 'core/dblur_generic_budget.h').read_bytes())
summary.write_text(json.dumps(report, indent=2) + '\n')
