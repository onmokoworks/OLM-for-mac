"""Retain ticket logs/reports and register generated performance bundles."""
import pathlib,json,gzip,shutil,hashlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[3];S=R/'orchestra/state/P05c-blur-colorkey-smoother-performance';E=R/'orchestra/reports/P05c-evidence'
label,name,source=sys.argv[1:];cache=pathlib.Path.home()/'.cache/olm-emu'
for p in sorted(S.glob(label+'-*')):
 if p.is_file() and p.suffix in ('.json','.log','.txt'):
  with p.open('rb') as src,gzip.open(E/(p.name+'.gz'),'wb') as dst:shutil.copyfileobj(src,dst)
 if p.is_dir() and p.name in [label+'-timing-before',label+'-timing-after']:
  for f in p.glob('matrix*'):shutil.copyfile(f,E/(p.name+'-'+f.name))
 if p.is_dir() and ('-units-' in p.name or '-functions-' in p.name) and (p/'summary.json').exists():
  shutil.copyfile(p/'summary.json',E/(p.name+'.json'))
  with gzip.open(E/(p.name+'-logs.json.gz'),'wt') as f:json.dump([dict(file=q.name,text=q.read_text()) for q in sorted(p.glob('*.log'))],f)
records=[]
for stage in ['before','after']:
 identity='P05c-'+label+('-before' if stage=='before' else '')
 target=cache/identity;target.mkdir(exist_ok=True)
 shutil.copytree(S/(label+'-'+stage)/'xcode'/name/'products'/(name+'.plugin'),target/'xcode'/name/'products'/(name+'.plugin'),dirs_exist_ok=True)
 host=target/'plugin-host'
 if not host.exists():host.symlink_to(cache/'P00b/plugin-host')
 exe=target/'xcode'/name/'products'/(name+'.plugin')/'Contents/MacOS'/name
 data=(R/source).read_bytes() if stage=='after' else subprocess.check_output(['git','show','00b91897d2fee8ba1b100af4f83dff6adeacbad2:'+source],cwd=R)
 record=dict(name=identity,bundles_path=str(target),worker_path=str(host),worker_sha256=hashlib.sha256(host.read_bytes()).hexdigest(),bundle_sha256={name:hashlib.sha256(exe.read_bytes()).hexdigest()},source_path=source,source_sha256=hashlib.sha256(data).hexdigest(),capability='P05c SDK-host performance candidate; not an AEX oracle')
 (target/'build.json').write_text(json.dumps(record,indent=2)+'\n');records.append(record)
idx=json.loads((cache/'INDEX.json').read_text());names={x['name'] for x in records};idx['links']=[x for x in idx['links'] if x['name'] not in names]+records
(cache/'INDEX.json').write_text(json.dumps(idx,indent=2)+'\n');(E/(label+'-cache.json')).write_text(json.dumps(records,indent=2)+'\n')
