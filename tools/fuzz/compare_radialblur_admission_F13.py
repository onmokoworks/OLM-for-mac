#!/usr/bin/env python3
"""Audit F13's fuzz preservation and monotonic corpus rebaseline evidence."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def table(counter):
    return [dict(route=r, before=b, after=a, count=n) for (r,b,a),n in sorted(counter.items())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['before', 'after', 'corpus-before', 'corpus-after', 'report']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--saved-revision', default='1408f2374500ece3d98c439ef9f9f66cb6e7efd7')
    args = parser.parse_args()
    before, after, corpus_before, corpus_after = [json.loads(p.read_text()) for p in
        [args.before, args.after, args.corpus_before, args.corpus_after]]
    for campaign in [before, after]:
        assert campaign['completed'] == campaign['requested'] == 300
        assert campaign['seed'] == 1 and campaign['jobs'] == 2
        assert campaign['status'] == 'complete'
    assert before['provenance']['worker_sha256'] == after['provenance']['worker_sha256']
    fuzz = Counter()
    exact_hashes = 0
    changed = []
    for old, new in zip(before['cases'], after['cases']):
        assert old['index'] == new['index']
        assert old['input_sha256'] == new['input_sha256']
        assert old['parameters'] == new['parameters']
        for name in ['depth', 'geometry', 'input_padding', 'output_padding']:
            assert old[name] == new[name]
        assert old['result']['oracle']['status'] == new['result']['oracle']['status']
        assert old['result']['oracle'].get('raw_sha256') == new['result']['oracle'].get('raw_sha256')
        for route in ['classic', 'smart']:
            b, a = [row['result']['routes'][route] for row in [old,new]]
            fuzz[route,b['status'],a['status']] += 1
            if b['status'] == 'exact':
                assert a['status'] == 'exact' and a['raw_sha256'] == b['raw_sha256']
                exact_hashes += 1
            if b != a:
                assert old['index'] == 89 and b['status'] == 'mismatch' and a['status'] == 'refusal'
                changed.append(dict(index=old['index'], route=route, before=b, after=a))
    assert len(changed) == 2
    measured, saved = Counter(), Counter()
    corpus_rows = []
    assert corpus_before['completed'] == corpus_after['completed'] == 35
    for old, new in zip(corpus_before['replays'], corpus_after['replays']):
        assert Path(old['path']).name == Path(new['path']).name
        assert old['result'] == new['result']
        # Bind stale expectations to the starting revision so this audit also
        # reproduces after rebaseline_corpus.py has updated the checked-out files.
        path = 'tests/fuzz_corpus/radialblur/'+Path(old['path']).name
        archive = json.loads(subprocess.check_output(
            ['git', 'show', args.saved_revision+':'+path], cwd=ROOT))
        row = dict(path=old['path'], routes={})
        for route in ['classic', 'smart']:
            b, a = [r['result']['routes'][route]['status'] for r in [old,new]]
            s = archive['result']['routes'][route]['status']
            assert s == a or a == 'exact', (old['path'],route,s,a)
            measured[route,b,a] += 1
            saved[route,s,a] += 1
            row['routes'][route] = dict(saved=s, before=b, after=a)
        corpus_rows.append(row)
    report = dict(fuzz_transitions=table(fuzz), preserved_exact_hashes=exact_hashes,
        fuzz_changes=changed, corpus_measured_transitions=table(measured),
        corpus_saved_transitions=table(saved), corpus_rows=corpus_rows,
        before_source_sha256=before['provenance']['source_sha256'],
        after_source_sha256=after['provenance']['source_sha256'])
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('F13_AUDIT', exact_hashes, 'exact hashes preserved;', len(changed), 'target routes refused; corpus 35 unchanged')


if __name__ == '__main__':
    main()
