#!/usr/bin/env python3
"""Run unchanged F52 sampler for Blur with an explicit seed and ticket scratch."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/fuzz'))
import measure_F52 as measurement
from adapters.olmblur import Adapter
from core import save_corpus, sha

parser = argparse.ArgumentParser()
parser.add_argument('--seed', type=int, default=1)
parser.add_argument('--save-witnesses', action='store_true')
args = parser.parse_args()
measurement.S = ROOT / 'orchestra/state/P01a-blur-downsample' / f'seed{args.seed}'
generate = Adapter.generate
Adapter.generate = lambda self, seed, index: generate(self, args.seed, index)
evaluate = measurement.evaluate
seen = set()
def recording_evaluate(adapter, case, directory, deadline, attr):
    result = evaluate(adapter, case, directory, deadline, attr)
    key = (case['depth'], tuple(map(tuple, case['downsample'])), case['parameters'][4]['value'])
    boundary = case['parameters'][0]['value'] * case['downsample'][0][0] / case['downsample'][0][1] < 1
    if args.save_witnesses and (key not in seen or boundary) and case['downsample'] != ((1,1),(1,1)):
        corpus = ROOT / 'tests/fuzz_corpus/olmblur_downsample_P01a'
        corpus.mkdir(parents=True, exist_ok=True)
        save_corpus(corpus / f"seed{args.seed}_case{case['index']:06}.json", adapter, case, case, result,
                    {'accepted': [], 'attempts': 0},
                    {'worker_path': str(adapter.worker), 'worker_sha256': sha(adapter.worker.read_bytes()),
                     'case_timeout_seconds': 10})
        seen.add(key)
    return result
measurement.evaluate = recording_evaluate
sys.argv = ['measure_F52.py', '--plugin', 'olmblur', '--n', '100']
measurement.main()
summary = measurement.S / 'olmblur/summary.json'
report = json.loads(summary.read_text())
report['seed'] = args.seed
summary.write_text(json.dumps(report, indent=2)+'\n')
