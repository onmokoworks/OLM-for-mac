#!/usr/bin/env python3
"""Archive P05b measured evidence without binaries or generated build trees."""
import gzip,hashlib,json,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P05b-radialblur-rotation-performance'
E=Path(__file__).resolve().parent
summary={'campaigns':{},'replays':{},'timings':{},'source_sha256':{}}
for label in ['default','realistic-1','realistic-fresh','odd-2026','odd-2027','replay-default','replay-realistic','replay-odd','replay-P05b']:
 p=S/(label+'.json')
 if not p.exists():continue
 data=json.loads(p.read_text())
 with p.open('rb') as src,gzip.open(E/(label+'.json.gz'),'wb') as dst:shutil.copyfileobj(src,dst)
 if label.startswith('replay'):
  summary['replays'][label]={'completed':data['completed'],'matches_saved':data['replay_matches_saved'],
    'nonmatching':[r['path'] for r in data['replays'] if not r['matches_saved']]}
 else:summary['campaigns'][label]=data['summary']
for label in ['before','after','simd-eighth','simd-large']:
 rows=[json.loads(line) for line in (S/label/'matrix.jsonl').read_text().splitlines()]
 summary['timings'][label]=[{k:r.get(k) for k in ['situation','depth','status','wall_seconds','result']} for r in rows]
 for name in ['matrix.jsonl','matrix-manifest.json','profile.sample.txt']:
  p=S/label/name
  if p.exists():
   with p.open('rb') as src,gzip.open(E/(label+'-'+name+'.gz'),'wb') as dst:shutil.copyfileobj(src,dst)
for name in ['units-before-sdk.log','units-after.log','simd-unit-final.log','simd-unit-x86.log','before.sample.txt','after.sample.txt','simd-hot.asm','unit-comparison.json','verify-commands.json','witnesses/results.json','bundle-compare/results.json','bundle-compare/build.log']:
 p=S/name
 if p.exists():
  with p.open('rb') as src,gzip.open(E/(name.replace('/','-')+'.gz'),'wb') as dst:shutil.copyfileobj(src,dst)
for name in ['mac/OLMRadialBlur/OLMRadialBlur.cpp','mac/OLMRadialBlur/RadialScatterSIMD.h']:
 summary['source_sha256'][name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
old=json.loads(gzip.decompress((ROOT/'orchestra/reports/P03b-evidence/radial-default-after.json.gz').read_bytes()))
new=json.loads((S/'default.json').read_text())
summary['default_baseline']={'source_sha256':old['provenance']['source_sha256'],'summary':old['summary']}
changes=[]
for b,a in zip(old['cases'],new['cases']):
 x=b['result']['routes']['smart'];y=a['result']['routes']['smart']
 if x['status']=='exact' and (y['status']!='exact' or x.get('raw_sha256')!=y.get('raw_sha256')):
  changes.append({'index':b['index'],'before':x,'after':y})
summary['default_exact_regressions']=changes
summary['unit_failures']={}
for label in ['before-sdk','after']:
 text=(S/f'units-{label}.log').read_text()
 summary['unit_failures'][label]={'footer':re.findall(r'^(?:Ran .*|FAILED .*|OK.*)$',text,re.M),
    'names':sorted(set(re.findall(r'^(?:FAIL|ERROR): (.*)$',text,re.M)))}
summary['unit_failure_name_sets_equal']=summary['unit_failures']['before-sdk']['names']==summary['unit_failures']['after']['names']
for name in ['P00b','P05b-radialblur-rotation-performance','P05b-radialblur-simd']:
 p=Path.home()/'.cache/olm-emu'/name/'build.json'
 shutil.copy2(p,E/(name+'-build.json'))
(E/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('archived',len(list(E.iterdir())),'files')
