"""Validate and summarize final acceptance, replay, units, timing and identities."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[3];E=R/'orchestra/reports/P05a-evidence';S=R/'orchestra/state/P05a-directionalblur-performance'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
rows=[]
for label in ['default-1','realistic-1','realistic-2053','realistic-v2-1','realistic-v2-2053','odd-even-2026','odd-even-2027']:
 d=json.loads((E/(label+'.json')).read_text());c=d['summary'];assert d['completed']==d['requested']
 refusal=0
 for case in d['cases']:
  r=case['result'];o=r.get('oracles',{}).get('smart',r['oracle'])
  refusal+=r['routes']['smart']['status']=='refusal' and o['status']=='ok'
 assert c.get('smart_mismatch',0)==(1 if label=='realistic-2053' else 0) and not refusal,(label,c,refusal)
 rows.append(dict(label=label,n=d['completed'],smart_exact=c.get('smart_exact',0),smart_uncompared=c.get('smart_uncompared',0),smart_mismatch=c.get('smart_mismatch',0),mac_only_refusals=refusal))
prior=json.loads((R/'orchestra/reports/P04b2-evidence/default-1.json').read_text())
current=json.loads((E/'default-1.json').read_text())
old={c['index']:c['result']['routes']['smart']['status'] for c in prior['cases']}
regressed=[c['index'] for c in current['cases'] if old[c['index']]=='exact' and c['result']['routes']['smart']['status']!='exact']
assert not regressed,regressed
boundary=json.loads((E/'boundary-check.json').read_text())
assert len(boundary)==6
assert all(r['result']['routes']['smart']['status']=='mismatch' for r in boundary)
assert len({r['result']['routes']['smart']['raw_sha256'] for r in boundary})==1
assert len({r['result']['oracle']['raw_sha256'] for r in boundary})==1
bundle=json.loads((E/'bundle-realistic-v2-2053.json').read_text())
assert bundle['summary']['smart_exact']==100 and bundle['summary']['pixel_mismatch_cases']==0
replays=[]
for p in sorted(E.glob('replay-*.json')):
 if p.name=='replay-commands.json':continue
 d=json.loads(p.read_text());assert d['replay_matches_saved'],p
 replays.append(dict(file=p.name,count=len(d['replays']),matches=True))
before=json.loads((E/'units-before.json').read_text());after=json.loads((E/'units-after.json').read_text())
assert [(r['file'],r['returncode']) for r in before]==[(r['file'],r['returncode']) for r in after]
files=['core/dblur_float.h','core/dblur_rotate.cpp','core/dblur_rowdriver.cpp','mac/OLMDirectionalBlur/Mac/OLMDirectionalBlur.xcodeproj/project.pbxproj']
result=dict(status='blocked',blocking_case='realistic-v1 seed 2053 index 9; inherited parent mismatch',campaigns=rows,default_exact_to_nonexact=regressed,bundle_smart_exact=bundle['summary']['smart_exact'],replays=replays,replay_count=sum(r['count'] for r in replays),unit_files=len(after),unit_pass=sum(r['returncode']==0 for r in after),unit_exit_changes=0,source_sha256={p:sha(R/p) for p in files},memory_pressure=subprocess.check_output(['memory_pressure'],text=True).strip().splitlines()[-1],machine=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string','hw.memsize'],text=True).strip().splitlines())
exe=S/'final2/xcode/OLMDirectionalBlur/products/OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur'
if exe.exists():result['bundle_sha256']=sha(exe)
(E/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
