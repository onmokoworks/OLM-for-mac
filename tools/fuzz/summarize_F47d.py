#!/usr/bin/env python3
"""Retain per-case hash/trace evidence and compare the paired render routes."""
import argparse
import hashlib
from collections import Counter
import json
from pathlib import Path
from verify_F47d import PLUGINS, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, default=ROOT/'orchestra/state/F47d-native-plugin-all')
    parser.add_argument('--output', type=Path, default=ROOT/'orchestra/reports/F47d-evidence')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for plugin in PLUGINS:
        bundle = json.loads((args.state/(plugin+'-plugin-bundle.json')).read_text())
        source = json.loads((args.state/(plugin+'-source.json')).read_text())
        route = 'classic' if plugin == 'olmsmoother' else 'smart'
        source_cases = {c['index']:c for c in source['cases']}
        rows = []
        for case in bundle['cases']:
            other = source_cases[case['index']]
            for key in ('input_sha256', 'parameters', 'geometry', 'depth'):
                assert case[key] == other[key], (plugin, case['index'], key)
            br, sr = case['result'], other['result']
            b, s = br['routes'][route], sr['routes'][route]
            oracle = br.get('oracles', {}).get(route, br['oracle'])
            source_oracle = sr.get('oracles', {}).get(route, sr['oracle'])
            bh, sh = b.get('raw_sha256'), s.get('raw_sha256')
            if bh and sh:
                classification = 'same-output-as-source' if bh == sh else 'unresolved-bundle-source-difference'
            elif b['status'] in ('reject', 'refusal') and s['status'] in ('reject', 'refusal'):
                classification = 'same-refusal-as-source'
            elif b['status'] == s['status'] == 'budget':
                classification = 'same-timeout-as-source'
            else:
                classification = 'unresolved-bundle-source-difference'
            guards = case.get('refusal_guards', {}).get(route, [])
            if (plugin == 'colorkeep' and case['depth'] == 32 and
                    any('world-flags-or-bounds' in guard for guard in guards)):
                classification = 'real-bug-colorkeep-world-flag-contract'
            if 'unsupported/invalid callback:' in b.get('native_trace', ''):
                classification = 'bridge-unsupported-or-invalid-callback'
            if bh and sh and bh == sh and b['status'] == 'mismatch':
                classification = 'real-bug-existing-source-mismatch'
            if oracle.get('raw_sha256') and source_oracle.get('raw_sha256'):
                assert oracle['raw_sha256'] == source_oracle['raw_sha256'], (plugin, case['index'], 'AEX output changed')
            rows.append(dict(index=case['index'], depth=case['depth'], geometry=case['geometry'],
                input_sha256=case['input_sha256'], classification=classification,
                oracle=oracle, source_oracle=source_oracle, bundle=b, source=s,
                refusal_guards=case.get('refusal_guards')))
        summary = dict(route=route, completed=len(rows),
            depth_counts=dict(Counter(r['depth'] for r in rows)),
            oracle_counts=dict(Counter(r['oracle']['status'] for r in rows)),
            bundle_counts=dict(Counter(r['bundle']['status'] for r in rows)),
            source_counts=dict(Counter(r['source']['status'] for r in rows)),
            classifications=dict(Counter(r['classification'] for r in rows)),
            first_mismatch=next((dict(index=r['index'], diff=r['bundle'].get('diff'))
                for r in rows if r['bundle']['status']=='mismatch'),None))
        evidence = dict(summary=summary,
            bundle_report_sha256=hashlib.sha256((args.state/(plugin+'-plugin-bundle.json')).read_bytes()).hexdigest(),
            source_report_sha256=hashlib.sha256((args.state/(plugin+'-source.json')).read_bytes()).hexdigest(),
            bundle_provenance=bundle['provenance'],
            source_provenance=source['provenance'], cases=rows)
        (args.output/(plugin+'.json')).write_text(json.dumps(evidence, indent=2)+'\n')
        summaries[plugin] = summary
        print(plugin, summary)
    (args.output/'summary.json').write_text(json.dumps(summaries, indent=2)+'\n')


if __name__ == '__main__':
    main()
