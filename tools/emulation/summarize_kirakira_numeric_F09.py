#!/usr/bin/env python3
"""Retain compact F09 evidence from the commands documented in its report."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args = p.parse_args()
    def read(name):
        return json.loads((args.scratch/(name+'.json')).read_text())
    result = dict(schema='olm-kira-F09-numeric-evidence/1',campaigns={},changes={},replays={})
    for family in ('production','gateoff'):
        before,after = [read(phase+'-'+family) for phase in ('before','after')]
        for phase,data in [('before',before),('after',after)]:
            assert data['completed']==300 and data['status']=='complete'
            result['campaigns'][phase+'-'+family] = {k:data[k] for k in
                ('summary','provenance','completed','jobs','seed','status')}
            result['campaigns'][phase+'-'+family]['result_digest'] = digest([r['result'] for r in data['cases']])
        changed = []
        for old,new in zip(before['cases'],after['cases']):
            assert old['index']==new['index']
            for route in ('classic','smart'):
                a,b = old['result']['routes'][route],new['result']['routes'][route]
                assert a['status']!='exact' or b['status']=='exact'
                if a!=b:
                    changed.append(dict(index=old['index'],route=route,before=a,after=b))
        result['changes'][family]=changed
    for family in ('production','gateoff'):
        data = read('replay-'+family)
        rows = []
        for row in data['replays']:
            saved = json.loads(Path(row['path']).read_text())
            rows.append(dict(path=row['path'],matches_saved=row['matches_saved'],
                before=saved['result'],after=row['result']))
        result['replays'][family] = rows
    result['traces'] = {phase:read(phase+'-trace') for phase in ('before','after')}
    assert all(r['trace_public_exact'] for data in result['traces'].values() for r in data['rows'])
    result['corpus_sample_audit'] = read('corpus-audit')
    assert not any(r['changed_not_to_exact'] for r in result['corpus_sample_audit']['rows'])
    result['fast_tests_log'] = (args.scratch/'fast-tests.log').read_text()
    result['rejected_all_depth_corpus_log'] = (args.scratch/'all-depth-corpus-audit.log').read_text()
    for phase in ('before','after'):
        result['traces'][phase]['report_sha256'] = hashlib.sha256((args.scratch/(phase+'-trace.json')).read_bytes()).hexdigest()
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('retained 4 campaigns, 2 corpus replays, 18 bound stage traces and 78 sample audits')


if __name__ == '__main__':
    main()
