#!/usr/bin/env python3
"""Retain completed F54b observations and verify complete saved-corpus coverage."""
import collections
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRATCH = ROOT / 'orchestra/state/F54b-aexcompat-numeric-patches-upstream'
OUT = ROOT / 'orchestra/reports/F54b-evidence'
PLUGINS = ['olmblur','colorkeep','olmcolorkey','olmdirectionalblur','olmdistancegradation',
           'olmkirakira','olmsmoother2','olmtoondilate','radialblur','olmsmoother']


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    worker = Path.home() / '.cache/olm-emu/worker-F54b/aex-guest-worker'
    baseline = Path.home() / '.cache/olm-emu/worker-F53-geom/aex-guest-worker'
    expected = collections.defaultdict(set)
    for path in (ROOT/'tests/fuzz_corpus').glob('*/**/*.json'):
        data = json.loads(path.read_text())
        plugin = data['plugin']
        for route in (['classic'] if plugin=='olmsmoother' else ['classic','smart']):
            expected[plugin].add(str(path.relative_to(ROOT/'tests/fuzz_corpus'))+'/'+route)
    summary = dict(worker_sha256=sha(worker), baseline_sha256=sha(baseline), plugins={})
    with gzip.open(OUT/'corpus-results.jsonl.gz','wt') as stream:
        for plugin in PLUGINS:
            directory = SCRATCH/f'corpus-{plugin}-final'
            measured = json.loads((directory/'summary.json').read_text())
            assert measured['worker_sha256']==summary['worker_sha256']
            assert measured['baseline_sha256']==summary['baseline_sha256']
            seen = set()
            counts = collections.Counter()
            for line in (directory/'results.jsonl').open():
                row = json.loads(line)
                assert row['case'] not in seen
                seen.add(row['case'])
                counts[row['category']] += 1
                stream.write(json.dumps(dict(plugin=plugin, **row))+'\n')
            assert seen == expected[plugin], (plugin, len(seen), len(expected[plugin]))
            assert len(seen) == measured['cases']
            for key,value in counts.items():
                assert measured[key] == value
            summary['plugins'][plugin] = dict(cases=len(seen), **counts,
                                             aex_sha256=measured['aex_sha256'])
    summary['totals'] = {key:sum(p.get(key,0) for p in summary['plugins'].values())
                         for key in ['cases','exact_ok','matching_non_success','byte_difference','status_difference']}
    summary['verification_sources'] = {str(p.relative_to(ROOT)): sha(p) for p in [
        ROOT/'tools/emulation/aexcompat_patches/verify_F54b.py', ROOT/'tools/fuzz/core.py',
        ROOT/'tools/fuzz/geometry.py', *sorted((ROOT/'tools/fuzz/adapters').glob('*.py')),
        *sorted((ROOT/'tools/fuzz/declarations').glob('*.json'))]}
    (OUT/'corpus-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    measurements=[]
    for plugin in PLUGINS:
        path=SCRATCH/f'4k-{plugin}-final/results.jsonl'
        rows=[json.loads(line) for line in path.open()]
        measurement_summary=json.loads((path.parent/'summary.json').read_text())
        assert measurement_summary['worker_sha256']==summary['worker_sha256']
        assert measurement_summary['aex_sha256']==summary['plugins'][plugin]['aex_sha256']
        assert len(rows)==3
        # These are single-worker measurements; no equivalence claim is made
        # from the inherited driver's equal:false placeholder.
        measurements.extend(dict(plugin=plugin, **row) for row in rows)
    (OUT/'4k-results.json').write_text(json.dumps(dict(worker_sha256=summary['worker_sha256'],rows=measurements),indent=2)+'\n')
    control=[json.loads(line) for line in (SCRATCH/'4k-olmblur-F54-control/results.jsonl').open()]
    control_summary=json.loads((SCRATCH/'4k-olmblur-F54-control/summary.json').read_text())
    (OUT/'4k-F54-control.json').write_text(json.dumps(dict(summary=control_summary,rows=control),indent=2)+'\n')
    print(json.dumps(summary['totals']))


if __name__=='__main__':
    main()
