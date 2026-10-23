#!/usr/bin/env python3
"""Aggregate sampled fixture children; counts exclude the command itself."""
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/I02-integration-finish'
lanes={}
for n in ast.walk(ast.parse((ROOT/'scripts/run_olm_mac_fixed_fixture_regression_20260805.py').read_text())):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Lane':
        lane=ast.literal_eval(n.args[0])
        for c in n.args[1].elts:
            tail=[ast.literal_eval(v) for v in c.elts[1:]]
            lanes[' '.join(tail)]=lane
stats={}
for path in sorted(S.glob('*-samples.jsonl')):
    if path.name not in ('release-samples.jsonl','fixtures-samples.jsonl'): continue
    with path.open() as f:
        for line in f:
            sample=json.loads(line); rows={r['pid']:r for r in sample['processes']}
            runners={p for p,r in rows.items() if 'run_olm_mac_fixed_fixture_regression_20260805.py' in r['command']}
            for p,r in rows.items():
                if r['ppid'] not in runners: continue
                command=next((c for c in lanes if r['command'].endswith(' '+c)),r['command'])
                key=command
                ids={p}
                while True:
                    new=ids|{q for q,v in rows.items() if v['ppid'] in ids}
                    if new==ids: break
                    ids=new
                group=[rows[q] for q in ids]
                item=stats.setdefault(key,dict(stages=[],lane=lanes.get(command),command=command,samples=0,max_descendants=0,max_python=0,max_rss_kib=0))
                if path.stem not in item['stages']: item['stages'].append(path.stem)
                item['samples']+=1
                item['max_descendants']=max(item['max_descendants'],len(ids)-1)
                item['max_python']=max(item['max_python'],sum('python' in v['command'].lower() for v in group))
                item['max_rss_kib']=max(item['max_rss_kib'],sum(v['rss_kib'] for v in group))
result=sorted(stats.values(),key=lambda r:(-r['max_descendants'],-r['max_rss_kib'],r['command']))
(S/'process-ranking.json').write_text(json.dumps(result,indent=2)+'\n')
for r in result[:10]: print(json.dumps(r))
