"""Create the final report from completed campaigns, never from estimates."""
import json,hashlib,re,datetime
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def identity(p):return {'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
names=['seed-20261112-final','seed-20261113-final'];runs=[read(root/'validation'/n/'summary.json') for n in names]
assert all(r['complete'] for r in runs)
assert len({r['candidate']['sha256'] for r in runs})==1
assert all(not v['mismatched'] and not v['candidate_failure'] and not v['tool_error'] for r in runs for v in r['routes'].values())
for r in runs:
 for key in ['reference','candidate','harness','tool']:assert identity(Path(r[key]['path']))['sha256']==r[key]['sha256']
worker=read(root/'worker-identity.json');assert identity(Path(worker['path']))['sha256']==worker['sha256']
unit=read(root/'unit-test-report.json');assert all(identity(root/p)['sha256']==digest for p,digest in unit['source_sha256'].items())
counts=[];failures=[];checks={};downs={};cases=[]
for name,r in zip(names,runs):
 directory=root/'validation'/name
 for route,c in r['routes'].items():
  rows=[x for x in r['results'] if x['route']==route]
  counts.append({'seed':r['seed'],'route':route,**{k:c[k] for k in ['cases_run','exact','mismatched','reference_unrenderable','reference_timeout','candidate_failure']},'random_exact':sum(x['status']=='exact' and x['case']>=3 for x in rows)})
 for row in r['results']:
  base=Path(row['source_directory']) if 'source_directory' in row else directory/row['directory']
  manifest=read(base/'case.json');case=manifest['case'];route=row['route']
  if row['status']=='exact':
   key=f"{route}/{case['downsample']}";downs[key]=downs.get(key,0)+1
   proc=read(directory/row['directory']/'candidate.process.json');details=json.loads(proc['stdout'])
   assert details['plugin_sha256']==r['candidate']['sha256']
   for key in ['passed','guard_bytes_intact','output_pixels_valid','param_checkouts_balanced','suite_leases_balanced','handle_lifetimes_balanced','world_lifetimes_balanced']:
    value=details.get(key);checks.setdefault(key,{});checks[key][str(value)]=checks[key].get(str(value),0)+1
   cases.append({'seed':r['seed'],'case':row['case'],'route':route,'source_manifest':identity(base/'case.json'),'final_diff':identity(directory/row['directory']/'diff.json')})
  elif row['status'].startswith('reference_'):
   proc=read(base/'reference.process.json');text=proc['stderr']+proc['stdout'];errors={k:re.findall('"'+k+'"\\s*:\\s*([^,}]+)',text)[:1] for k in ['smart_render_error','last_seh_exception_code']}
   controls={a['slot']:a.get('value') for a in case['assignments']}
   failures.append({'seed':r['seed'],'case':row['case'],'route':route,'status':row['status'],'size':case['size'],'downsample':case['downsample'],'blur_mode':controls[11],'blur_size':controls[12],'elapsed_seconds':proc['elapsed_seconds'],'returncode':proc['returncode'],'errors':errors,'process':identity(base/'reference.process.json')})
for route in runs[0]['routes']:assert sum(c['random_exact'] for c in counts if c['route']==route)>=200
assert all(identity(root/p)['sha256']==digest for p,digest in unit['fixture_sha256'].items())
inventory_path=root/'validation/final-inventory/summary.json'
inventory=read(inventory_path);assert inventory['identical'];assert inventory['candidate']['sha256']==runs[0]['candidate']['sha256']
assert read(root/'pipl-comparison.json')['exact']
report={'schema_version':1,'completed_at':datetime.datetime.now().isoformat(),'identity':{k:runs[0][k] for k in ['reference','candidate','harness','tool']},'worker':worker,'inventory':identity(inventory_path),'native_provenance':[read(root/'tests'/n) for n in ['native-ipp-provenance.json','native-gaussian-provenance.json']],'counts':counts,'downsample_exact':downs,'host_checks':checks,'reference_failures':failures,'passed_cases':cases,'unit_tests':unit,'pipl':read(root/'pipl-comparison.json'),'campaigns':[identity(root/'validation'/n/'summary.json') for n in names],'scope':'Windows x64 AEXCompat Smart8/16/32 CPU; native IPP index 4 and OpenCV AVX2/FMA. Not native AE; macOS not built.'}
(root/'validation-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
lines=['## Final measured results','', '| Seed | Route | Exact | Random exact | Reference errors | Reference timeouts | Mismatches / candidate failures |','| --- | --- | ---: | ---: | ---: | ---: | --- |']
for c in counts:lines.append(f"| {c['seed']} | {c['route']} | {c['exact']} | {c['random_exact']} | {c['reference_unrenderable']} | {c['reference_timeout']} | {c['mismatched']} / {c['candidate_failure']} |")
lines+=['','All successful original outputs are bit-exact with the final candidate. Original','failures and timeouts are excluded from pass and random-case totals. Downsample','1, 1/2, and 1/4 were exercised at every depth. Full per-case manifests, original','failure reasons, exact output hashes and host lifetime checks are recorded in','`validation-report.json`.','', '### Binary identities','', '| Binary | SHA-256 |','| --- | --- |']
for k,v in report['identity'].items():lines.append(f"| {k} | `{v['sha256']}` |")
lines.append(f"| worker | `{worker['sha256']}` |")
lines+=['','### Excluded original cases','','| Seed | Status | Case indices | Observed reason |','| --- | --- | --- | --- |']
for seed in sorted({f['seed'] for f in failures}):
 for status in ['reference_unrenderable','reference_timeout']:
  group=[f for f in failures if f['seed']==seed and f['status']==status]
  ids=sorted({f['case'] for f in group})
  if ids:
   reason='Median: SMART_RENDER returns 512, SEH code 0' if status=='reference_unrenderable' and all(f['blur_mode']==4 and f['errors']['smart_render_error']==['512'] for f in group) else '300-second reference process deadline' if status=='reference_timeout' else 'See per-case diagnostic fields in validation-report.json'
   lines.append(f"| {seed} | {status} | {', '.join(map(str,ids))} | {reason} |")
lines+=['','The final candidate is `validation/DistanceGradation-v4.aex`; the same DLL is in',r'`D:\olm-rs-target\P-dgrad\release\olm_distance_gradation.dll`.','', 'The second direct campaign uses `--cases 83 --seed 20261113`; all other render', 'options match the 203-case first campaign. Final first-seed qualification:', '', '```powershell', 'python rust/plugins/olm-distance-gradation/tests/requalify_candidate.py --source rust/plugins/olm-distance-gradation/validation/seed-20261112-v2 --candidate rust/plugins/olm-distance-gradation/validation/DistanceGradation-v4.aex --out rust/plugins/olm-distance-gradation/validation/seed-20261112-final', '```','']
p=root/'VALIDATION.md';text=p.read_text(encoding='utf-8').split('## Final measured results')[0];p.write_text(text.rstrip()+'\n\n'+'\n'.join(lines),encoding='utf-8')
print(json.dumps(counts,indent=2));print('downsample exact',downs)
