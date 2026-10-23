#!/usr/bin/env python3
"""Audit retained C47 measurements against the preceding DG campaigns."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'orchestra/reports/C47-evidence'


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def main():
    for name, digest in read(EVIDENCE / 'manifest.json').items():
        assert hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest() == digest, name
    summaries = []
    for seed, baseline in (
        (1, 'orchestra/reports/C43-evidence/fresh1.json.gz'),
        (104, 'orchestra/reports/S01-wide-mismatch-sweep/olmdistancegradation_seed104.json.gz'),
    ):
        old, new = read(ROOT / baseline), read(EVIDENCE / f'seed{seed}.json.gz')
        assert old['completed'] == new['completed'] == 300
        assert old['generator_version'] == new['generator_version']
        previous = {r['index']: r for r in old['cases']}
        transitions = []
        for row in new['cases']:
            before = previous[row['index']]
            for key in ('input_sha256', 'geometry', 'depth', 'parameters',
                        'input_padding', 'output_padding', 'profile'):
                assert before[key] == row[key], (seed, row['index'], key)
            a, b = before['result']['routes']['smart'], row['result']['routes']['smart']
            assert b['status'] != 'mismatch'
            if a['status'] == 'exact':
                assert b['status'] == 'exact' and a['raw_sha256'] == b['raw_sha256']
            if a['status'] != b['status']:
                transitions.append([row['index'], a['status'], b['status']])
        summaries.append(dict(seed=seed, summary=new['summary'],
                              exact_losses=0, transitions=transitions))
    before = read(EVIDENCE / 'trace-before.json.gz')['rows'][0]
    after = read(EVIDENCE / 'trace-after.json.gz')['rows'][0]
    assert before['input_sha256'] == after['input_sha256']
    assert before['oracle_sha256'] == after['oracle_sha256'] == after['mac_sha256']
    assert before['mac_pre_hex'] == before['mac_post_hex']
    assert before['pre_diff']['different_words'] == 0
    assert before['post_diff']['different_words'] > 0
    assert before['output_diff']['different_words'] > 0
    for stage in ('pre_diff', 'post_diff', 'output_diff'):
        assert after[stage]['different_words'] == 0
    corpus = read(EVIDENCE / 'corpus.json.gz')
    assert corpus['completed'] == corpus['requested'] == len(corpus['replays'])
    assert corpus['replay_matches_saved']
    assert all(r['matches_saved'] for r in corpus['replays'])
    print(json.dumps(dict(campaigns=summaries, corpus=corpus['completed'],
                          witness_exact=True, acceptance_met=True), indent=2))


if __name__ == '__main__':
    main()
