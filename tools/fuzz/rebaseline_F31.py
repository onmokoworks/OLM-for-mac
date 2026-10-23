#!/usr/bin/env python3
"""Only rebaseline saved reference hashes demonstrated in the F30 A/B evidence.

Default is an audit; --apply calls the existing corpus rebaseline tool. No
candidate-only drift, unrelated historical drift, or unproved reference change
is eligible. Git retains the original result/provenance.
"""
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/F31-port-ucrtmath-switch-oracle'
OUT=ROOT/'orchestra/reports/F31-evidence'
proof=json.loads((ROOT/'tools/emulation/aexcompat_patches/F30-evidence/measurements.json').read_text())
qualified={(x['label'],Path(str(x['case'])).name):x for x in proof['changes'] if x['pair']=='default->f30' and x['label'].endswith('-replay')}
updates=[];skipped=[]
for path in sorted(S.glob('*-replay.json')):
    if path.name.startswith('before-'):continue
    report=json.loads(path.read_text())
    assert report['status']=='replay_complete' and report['completed']==report['requested']
    for row in report['replays']:
        case=Path(row['path']);saved=json.loads(case.read_text())
        old=saved['result'].get('oracles',{'smart':saved['result']['oracle']})
        new=row['result'].get('oracles',{'smart':row['result']['oracle']})
        changed=[r for r in old if old[r].get('raw_sha256')!=new[r].get('raw_sha256')]
        if not changed:continue
        evidence=qualified.get((path.stem,case.name))
        reason=None
        if not evidence:reason='not in demonstrated F30 reference changes'
        elif any(old[r].get('raw_sha256')!=evidence['before']['oracles'][r].get('raw_sha256') or new[r].get('raw_sha256')!=evidence['after']['oracles'][r].get('raw_sha256') for r in changed):reason='reference hashes do not match F30 A/B evidence'
        if reason:
            skipped.append({'case':str(case.relative_to(ROOT)),'reason':reason});continue
        focused=dict(report,completed=1,requested=1,replays=[row])
        target=S/('rebaseline-'+case.name)
        target.write_text(json.dumps(focused,indent=2)+'\n')
        causes=sorted({x['cause'] for x in proof['changes'] if x['label']==path.stem and Path(str(x['case'])).name==case.name and x['pair'] in ('default->f29','f29->f30')})
        entry={'case':str(case.relative_to(ROOT)),'cause':causes,'changed_routes':changed,'before':old,'after':new}
        updates.append(entry)
        if '--apply' in sys.argv:
            result=subprocess.run([sys.executable,str(ROOT/'tools/fuzz/rebaseline_corpus.py'),'--plugin',saved['plugin'],'--corpus',str(case.parent),'--report',str(target)],capture_output=True,text=True)
            (S/('rebaseline-'+case.stem+'.log')).write_text(result.stdout+result.stderr)
            if result.returncode:raise RuntimeError('Rebaseline refused: '+case.name)
OUT.mkdir(exist_ok=True)
manifest=OUT/('rebaseline.json' if '--apply' in sys.argv else 'rebaseline-audit.json')
if '--apply' in sys.argv and manifest.exists():
    prior=json.loads(manifest.read_text())
    known={x['case'] for x in updates}
    updates=[x for x in prior.get('updates',[]) if x['case'] not in known]+updates
manifest.write_text(json.dumps({'applied':'--apply' in sys.argv,'updates':updates,'skipped':skipped},sort_keys=True,indent=2)+'\n')
print('qualified',len(updates),'unqualified reference changes',len(skipped))
