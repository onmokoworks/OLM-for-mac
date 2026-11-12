"""Bind final counts to the frozen candidate; never count interrupted campaigns."""
from pathlib import Path
from collections import Counter
import hashlib,json
HERE=Path(__file__).resolve().parent
candidate=hashlib.sha256((HERE/'OLMSmoother2-verified.aex').read_bytes()).hexdigest()
rows=[]
identities=None
for seed in [20261116,20261117]:
    folder=HERE/f'campaign-{seed}'
    summary=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
    assert summary['candidate']['sha256']==candidate
    current={k:summary[k] for k in ['harness','reference','candidate','tool']}
    if identities is None:identities=current
    else:assert current==identities,'Campaign identities changed between seeds'
    assert summary['jobs']==3 and summary['complete']
    for route in ['smart8','smart16','smart32']:
        counts=Counter();scales=Counter();random_scales=Counter();failures=[]
        for result in summary['results']:
            if result['route']!=route:continue
            counts[result['status']]+=1
            case=json.loads((folder/result['directory']/'case.json').read_text())['case']
            if result['status']=='exact':
                scales[case['downsample']]+=1
                if case['index']>=3:random_scales[case['downsample']]+=1
            else:failures.append(result)
        rows.append({'seed':seed,'route':route,'counts':dict(counts),
                     'exact_by_downsample':dict(scales),'random_exact_by_downsample':dict(random_scales),
                     'failures':failures,'summary':str(folder/'summary.json')})
totals={}
for route in ['smart8','smart16','smart32']:
    matching=[r for r in rows if r['route']==route]
    counts=Counter();scales=Counter();random_scales=Counter()
    for r in matching:
        counts.update(r['counts']);scales.update(r['exact_by_downsample']);random_scales.update(r['random_exact_by_downsample'])
    totals[route]={'counts':dict(counts),'exact_by_downsample':dict(scales),
                   'random_exact_by_downsample':dict(random_scales),'random_exact':sum(random_scales.values())}
passed=all(v['random_exact']>=200 and set(v['counts'])=={'exact'} for v in totals.values())
result={'candidate_sha256':candidate,'identities':identities,'required_campaign_passed':passed,'rows':rows,'totals':totals}
(HERE/'campaign-summary.json').write_text(json.dumps(result,indent=2)+'\n')
report=json.loads((HERE/'validation-report.json').read_text())
report['oracle']=result
report['status']='verified_windows_aexcompat' if passed else 'campaign_incomplete_or_failed'
from validate import identity
for artifact in report['sources']:
    artifact.update(identity(artifact['path']))
for name in ['run_campaign.py','summarize_campaign.py']:
    item=identity(HERE/name)
    if not any(x['path']==item['path'] for x in report['sources']):report['sources'].append(item)
item=identity(HERE.parents[2]/'core/olm_sha256_rows.h')
if not any(x['path']==item['path'] for x in report['cpp_reference_sources']):report['cpp_reference_sources'].append(item)
(HERE/'validation-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':passed,'totals':totals},indent=2))
if not passed:raise SystemExit(1)
