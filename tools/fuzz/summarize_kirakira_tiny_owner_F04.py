#!/usr/bin/env python3
"""Compact the F04 reproducible campaigns without blessing corpus changes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    read = lambda name: json.loads((args.scratch/(name+'.json')).read_text())
    names = ('before', 'after', 'request', 'owner', 'owner-tuples')
    campaigns = {n: read(n) for n in names}
    results = {n: [c['result'] for c in r['cases']] for n,r in campaigns.items()}
    assert results['before'] == results['after']
    tiny = [c['index'] for c in campaigns['before']['cases']
            if any('request-not-admitted' in g for g in c['refusal_guards'].get('smart', []))]
    compact = {}
    for name, report in campaigns.items():
        compact[name] = {k:report[k] for k in ('summary','provenance','completed','status')}
        compact[name]['results_sha256'] = digest(results[name])
        compact[name]['guards'] = dict(Counter(g.split('@')[0] for c in report['cases']
            for route in c.get('refusal_guards', {}).values() for g in route))
        compact[name]['tiny_smart'] = dict(Counter(c['result']['routes']['smart']['status']
            for c in report['cases'] if c['index'] in tiny))
    corpus_before, corpus_after = read('corpus-before'), read('corpus-after')
    assert corpus_before['replays'] == corpus_after['replays']
    production_corpus = []
    for row in corpus_after['replays']:
        saved = json.loads((ROOT/row['path']).read_text())
        production_corpus.append(dict(path=row['path'], index=saved['index'],
            saved=saved['result'], before=row['result'], after=row['result'],
            matches_saved=row['matches_saved']))
    triage = json.loads((ROOT/'reports/fuzz/olmkirakira_triage_T06.json').read_text())
    cluster_ids = {c['corpus']: f'C{i:02}' for i,c in enumerate(triage['clusters'],1)}
    clusters = []
    for row in read('clusters')['replays']:
        saved = json.loads((ROOT/row['path']).read_text())
        clusters.append(dict(cluster=cluster_ids[Path(row['path']).name], path=row['path'],
            index=saved['index'], geometry=saved['case']['geometry'], depth=saved['case']['depth'],
            before=saved['result'], after=row['result'], matches_saved=row['matches_saved']))
    old = [c['result'] for c in triage['experiments']['all']['cases']]
    after = results['owner-tuples']
    assert all(a['routes']['classic'] == b['routes']['classic'] for a,b in zip(old, after))
    assert all(a['oracle'] == b['oracle'] for a,b in zip(old, after))
    assert all(a['routes']['classic']['raw_sha256'] == a['routes']['smart']['raw_sha256'] for a in after)
    traces = {}
    for name in ('request','owner','owner-tuples','clusters'):
        rows = read(name+'-details')
        traces[name] = [dict(r,trace=[re.sub(r'0x[0-9a-f]+','<address>',v) for v in r['trace']])
                        for r in rows if r['route']=='smart' and r['index'] in (8,78,116,148)]
    files = ['tools/fuzz/probe_kirakira_tiny_owner_F04.py',
             'tools/fuzz/summarize_kirakira_tiny_owner_F04.py',
             'tools/emulation/probe_kirakira_tiny_pre_geometry_F04.py',
             'tools/emulation/aex_loader.py','tools/emulation/aex_witness.py']
    files += [str(p.relative_to(ROOT)) for p in (ROOT/'core').glob('kirakira*.h')]
    evidence = dict(schema='olm-kira-F04-tiny-owner/1',
        campaigns=compact, request_guard_indices=tiny,
        production_results_before=results['before'], gate_off_results=after,
        production_results_unchanged=len(results['before']),
        production_corpus=production_corpus, cluster_replay=clusters,
        geometry_traces=traces, aex_pre_geometry=read('aex-pre-geometry'),
        original_T06_classic_and_oracle_unchanged=len(after),
        gate_off_classic_smart_output_hashes_equal=len(after),
        dependencies_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},
        tests={n:(args.scratch/(n+'.log')).read_text() for n in ('fast-tests','fast-subset')},
        limitations=['Scratch candidate only; production and both corpora unchanged.',
                    'No outside-port numerical cause proved; no first differing numerical stage claimed.',
                    'No native AE, Windows UCRT, ROI or tile compatibility claim.'])
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(production_results_unchanged=len(results['before']),
        tiny=compact['owner-tuples']['tiny_smart'],
        cluster_changes=sum(not c['matches_saved'] for c in clusters)),sort_keys=True))


if __name__ == '__main__':
    main()
