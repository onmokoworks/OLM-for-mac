#!/usr/bin/env python3
"""Rebaseline only Kira cases newly exact between two complete ticket replays.

Existing saved-result drift which is identical before/after is left intact.
The existing migration tool preserves result/provenance history and checks
oracle identity. Inputs, reductions and generator identities never change.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before-replay', type=Path, required=True)
    parser.add_argument('--after-replay', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--ticket', default='C29-kira-smart-r7', help='Production rebaseline history ticket')
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT / 'orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    before, after = (json.loads(p.read_text()) for p in (args.before_replay, args.after_replay))
    for report in (before, after):
        assert report['plugin'] == 'olmkirakira' and report['status'] == 'replay_complete'
        assert report['completed'] == report['requested'] == len(report['replays'])
    old = {str(Path(r['path']).resolve()): r for r in before['replays']}
    new = {str(Path(r['path']).resolve()): r for r in after['replays']}
    assert old.keys() == new.keys()
    selected, transitions, inputs = [], [], {}
    corpus = ROOT / 'tests/fuzz_corpus/olmkirakira_gate_off_T06'
    for path, row in new.items():
        a, b = old[path]['result'], row['result']
        assert a['oracle'] == b['oracle'] and a.get('oracles') == b.get('oracles')
        assert a['routes']['classic'] == b['routes']['classic']
        if a == b:
            continue
        assert a['routes']['smart']['status'] == 'refusal'
        assert b['routes']['smart']['status'] == 'exact'
        file = Path(path)
        assert file.is_relative_to(corpus)
        saved = json.loads(file.read_text())
        assert saved['result'] in (a, b), (path, 'unrelated saved-result drift')
        inputs[path] = {k: v for k, v in saved.items()
                        if k not in ('result', 'provenance', 'rebaseline_history')}
        transitions.append(dict(path=str(file.relative_to(ROOT)), before='refusal', after='exact',
                                raw_sha256=b['routes']['smart']['raw_sha256'],
                                already_applied=saved['result'] == b))
        selected.append(row)
    proposal = copy.deepcopy(after)
    proposal['replays'] = selected
    proposal['completed'] = proposal['requested'] = len(selected)
    proposal['C29_selection'] = dict(before_replay=str(args.before_replay),
                                    after_replay=str(args.after_replay), transitions=transitions)
    proposal_path = scratch / 'selected-replay.json'
    proposal_path.write_text(json.dumps(proposal, indent=2, sort_keys=True) + '\n')
    if args.apply and selected:
        subprocess.run([sys.executable, str(ROOT / 'tools/fuzz/rebaseline_corpus.py'),
                        '--plugin', 'olmkirakira', '--corpus', str(corpus),
                        '--report', str(proposal_path),
                        '--production-rebaseline', args.ticket], check=True)
        for path, expected in inputs.items():
            saved = json.loads(Path(path).read_text())
            assert expected == {k: v for k, v in saved.items()
                                if k not in ('result', 'provenance', 'rebaseline_history')}
            assert saved['result'] == new[path]['result']
    summary = dict(applied=args.apply, transitions=transitions,
                   before_saved_matches=sum(r['matches_saved'] for r in before['replays']),
                   after_saved_matches_before_migration=sum(r['matches_saved'] for r in after['replays']))
    (scratch / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    print(json.dumps(summary, sort_keys=True))


if __name__ == '__main__':
    main()
