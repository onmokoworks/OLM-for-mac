#!/usr/bin/env python3
"""Compact, asserted F17 route census evidence from reproducible campaign reports."""
import argparse
from collections import Counter
import json
from pathlib import Path
from core import sha

PLUGINS = ('olmblur','olmdistancegradation','olmtoondilate','olmsmoother2',
           'olmdirectionalblur','olmcolorkey','colorkeep','olmkirakira','radialblur')


def load(p):
    return json.loads(p.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    evidence = {'schema':'olm-route-oracle-audit/1', 'plugins':{}}
    for plugin in PLUGINS:
        before = args.scratch/f'before-{plugin}.json'
        after = args.scratch/f'paired-{plugin}{"-offset" if plugin == "radialblur" else ""}.json'
        b,a = load(before),load(after)
        assert b['completed'] == a['completed'] == 300
        assert b['seed'] == a['seed'] == 1 and b['jobs'] == a['jobs'] == 2
        assert b['provenance']['worker_sha256'] == a['provenance']['worker_sha256']
        transitions = Counter()
        smart_oracle_changes = []
        for x,y in zip(b['cases'],a['cases']):
            assert x['index'] == y['index'] and x['input_sha256'] == y['input_sha256']
            for route in ('classic','smart'):
                v,w = x['result']['routes'][route],y['result']['routes'][route]
                assert {k:z for k,z in v.items() if k not in ('status','diff')} == {k:z for k,z in w.items() if k not in ('status','diff')}, (plugin,x['index'],route)
                transitions[route,v['status'],w['status']] += 1
            v,w = x['result']['oracle'],y['result']['oracles']['smart']
            if (v['status'],v.get('raw_sha256')) != (w['status'],w.get('raw_sha256')):
                smart_oracle_changes.append(x['index'])
        first = {}
        for route in ('classic','smart'):
            row = next((r for r in a['cases'] if r['result']['routes'][route]['status']=='mismatch'),None)
            first[route] = None if row is None else {k:row[k] for k in ('index','geometry','depth','input_sha256','parameters','result')}
        corpus = []
        for path in sorted((root/'tests/fuzz_corpus'/plugin).glob('*.json')):
            data = load(path)
            update = data.get('route_oracle_update')
            if update:
                corpus.append({'file':path.name,'input_sha256':data['input_sha256'],
                               'before':update['previous_result'],'after':data['result']})
        evidence['plugins'][plugin] = {
            'before':b['summary'], 'after':a['summary'],
            'before_provenance':b['provenance'], 'after_provenance':a['provenance'],
            'before_report_sha256':sha(before.read_bytes()), 'after_report_sha256':sha(after.read_bytes()),
            'unchanged_inputs':300, 'unchanged_candidate_results_excluding_comparison':600,
            'smart_oracle_changed_indices':smart_oracle_changes,
            'transitions':[{'route':r,'before':v,'after':w,'count':n} for (r,v,w),n in sorted(transitions.items())],
            'first_mismatch':first, 'corpus':corpus}
        print(plugin, 'before', b['summary'], 'after', a['summary'], 'migrated',len(corpus))
    # v1 has no second original route; its pairing and corpus are unchanged.
    v1 = load(args.scratch/'before-olmsmoother.json')
    evidence['unchanged_single_owner'] = {'plugin':'olmsmoother','summary':v1['summary'],
        'provenance':v1['provenance'],'pairing':{'classic':'classic','smart':'classic'},
        'reason':'original advertises Classic only; Mac Smart is an explicit wrapper comparison'}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
