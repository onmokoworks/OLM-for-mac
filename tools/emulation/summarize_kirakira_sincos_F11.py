#!/usr/bin/env python3
"""Bind F11 leaf, caller, campaign and corpus observations into a compact report."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args = p.parse_args()
    read = lambda name: json.loads((args.scratch/(name+'.json')).read_text())
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = dict(schema='olm-kira-F11-sincos/1',leaf=read('leaf-verified'),
        source_hashes={name:sha(ROOT/name) for name in [
            'mac/OLMKiraKira/OLMKiraKira.cpp','core/kirakira_sincos.h',
            'core/kirakira_sincos_tables.h','tools/emulation/probe_kirakira_sincos_F11.py']},
        before_source_sha256=sha(args.scratch/'before.cpp'),campaigns={},replays={})
    for route in ['prod','gateoff']:
        before,after = read('before-'+route),read('final-'+route)
        assert before['completed']==after['completed']==300
        changed = []; regressions = []
        old = {r['index']:r for r in before['cases']}
        for new in after['cases']:
            prior = old[new['index']]
            for command in ['classic','smart']:
                a,b = prior['result']['routes'][command],new['result']['routes'][command]
                if a['status']=='exact' and b['status']!='exact':
                    regressions.append(dict(index=new['index'],route=command))
                if a!=b:
                    changed.append(dict(index=new['index'],route=command,before=a,after=b))
        assert not regressions
        report['campaigns'][route] = dict(before=before['summary'],after=after['summary'],
            provenance_before=before['provenance'],provenance_after=after['provenance'],
            changed=changed,exact_regressions=regressions)
        replay = read('final-replay-'+route)
        report['replays'][route] = dict(completed=replay['completed'],
            matches_saved=sum(r['matches_saved'] for r in replay['replays']),rows=replay['replays'])
    audit = read('final-audit-both')
    assert len(audit['rows'])==140
    assert all(not r['changed_not_to_exact'] for r in audit['rows'])
    report['corpus_sample_audit'] = audit
    report['traces'] = dict(before=read('before-trace'),after=read('final-trace'))
    assert all(r['trace_public_exact'] and r['final_diff'] is None for r in report['traces']['after']['rows'])
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('leaf',report['leaf']['cases'],'geometry',report['leaf']['geometry']['cases'],
          'audited routes',len(audit['rows']),'changed samples',sum(r['changed_samples'] for r in audit['rows']))
    print('campaign exact regressions: 0; corpus changed samples away from exact: 0')


if __name__ == '__main__':
    main()
