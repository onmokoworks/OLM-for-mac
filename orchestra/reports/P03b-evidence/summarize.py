"""Summarize actual reports; never classify an unavailable oracle as exact."""
import collections,gzip,json,re,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/P03b-nonfinite-hdr-admission'
out={}
for name,short in [('olmdirectionalblur','directional'),('olmdistancegradation','dg'),('olmkirakira','kira'),('radialblur','radial')]:
 for suffix in ('-default-before.json','-units-before.log'):
  target=S/(short+suffix);saved=Path(__file__).parent/target.name
  if not target.exists():
   if saved.exists():shutil.copyfile(saved,target)
   elif Path(str(saved)+'.gz').exists():
    with gzip.open(str(saved)+'.gz','rb') as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
 row={};out[name]=row
 before=S/(short+'-default-before.json');after=S/(short+'-default-after.json')
 if before.exists() and after.exists():
  b=json.loads(before.read_text());a=json.loads(after.read_text());changes=[];regressions=[];availability=[];candidate_changes=[]
  assert b['completed']==a['completed']==300
  for x,y in zip(b['cases'],a['cases']):
   assert (x['index'],x['input_sha256'])==(y['index'],y['input_sha256'])
   for route,old in x['result']['routes'].items():
    new=y['result']['routes'][route]
    if (old.get('error'),old.get('raw_sha256'))!=(new.get('error'),new.get('raw_sha256')):
     candidate_changes.append([x['index'],route])
    if (old['status'],old.get('raw_sha256'))!=(new['status'],new.get('raw_sha256')):
     changes.append([x['index'],route,old['status'],new['status']])
    if old['status']=='exact' and (new['status']!='exact' or old['raw_sha256']!=new.get('raw_sha256')):
     oracle=y['result'].get('oracles',{}).get(route,{})
     if new['status']=='uncompared' and oracle.get('status')=='budget' and old['raw_sha256']==new.get('raw_sha256'):
      availability.append(dict(index=x['index'],route=route,reason=oracle,unchanged_candidate_sha256=old['raw_sha256']))
     else:regressions.append([x['index'],route])
  row['default']=dict(before=b['summary'],after=a['summary'],status_hash_changes=changes,candidate_hash_error_changes=candidate_changes,exact_regressions=regressions,oracle_availability_losses=availability)
  assert not regressions, (name,regressions)
 sweep=S/('sweep-'+name+'-summary.json')
 if sweep.exists():row['sweep']=json.loads(sweep.read_text())['counts']
 matrix=S/('directional-matrix.json' if short=='directional' else 'matrix-'+name+'.json')
 if matrix.exists():row['matrix']=dict(collections.Counter(r['result']['routes']['smart']['status'] for r in json.loads(matrix.read_text())['rows']))
 unit_b=S/(short+'-units-before.log');unit_a=S/(short+'-units-after.log')
 if unit_b.exists() and unit_a.exists():
  b=unit_b.read_text();a=unit_a.read_text()
  row['units']=dict(before=re.findall(r'Ran \d+ tests|FAILED \([^\n]+|OK[^\n]*',b),after=re.findall(r'Ran \d+ tests|FAILED \([^\n]+|OK[^\n]*',a),same_failure_names=re.findall(r'^(?:ERROR|FAIL): .+$',b,re.M)==re.findall(r'^(?:ERROR|FAIL): .+$',a,re.M))
  assert row['units']['same_failure_names'], name
 replay=S/('replay-summary-'+name+'.json')
 if replay.exists():row['corpora']=json.loads(replay.read_text())
 elif short=='directional':
  row['corpora']=[]
  for suffix in ('default','P02j','T15b'):
   p=S/('directional-replay-'+suffix+'.json')
   if p.exists():
    d=json.loads(p.read_text());row['corpora'].append(dict(directory=suffix,completed=d['completed'],replay_matches_saved=d['replay_matches_saved']))
(S/'summary.json').write_text(json.dumps(out,indent=2))
for name,r in out.items():
 print(name,'sweep',r.get('sweep'),'matrix',r.get('matrix'),'regressions',r.get('default',{}).get('exact_regressions'),'corpora',[(c['completed'],c['replay_matches_saved']) for c in r.get('corpora',[])],'units',r.get('units',{}).get('same_failure_names'))
