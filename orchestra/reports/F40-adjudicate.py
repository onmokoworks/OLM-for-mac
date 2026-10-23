#!/usr/bin/env python3
"""Read-only provenance inventory. Writes only F40 report artifacts; no test imports."""
import ast, collections, hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'orchestra/reports'
BASE='cf195175ee4cd11a40401e882e3b1664d7f3a676'
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT).decode()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
tracked=set(git('ls-tree','-r','--name-only',BASE).splitlines())
f36=json.loads((OUT/'F36-command-triage.json').read_text())
old=json.loads((OUT/'F36-binding-candidates.json').read_text())
rows=[r for r in f36['commands'] if r['category'] in ('b','d')]
hashre=re.compile(r'\b[0-9a-f]{64}\b')
texts={}
def read(p):
 if p not in texts:texts[p]=git('show',BASE+':'+p) if p in tracked else ''
 return texts[p]
def refs(p):
 s=read(p); found=set()
 # Literal repository paths, including missing historical references.
 for q in re.findall(r'''["']([^"'\n]+)["']''',s):
  if q in tracked and q.endswith(('.py','.json','.cpp','.h','.md')):found.add(q)
 if p.endswith('.py'):
  try:
   for n in ast.walk(ast.parse(s)):
    names=[x.name for x in n.names] if isinstance(n,ast.Import) else [n.module or ''] if isinstance(n,ast.ImportFrom) else []
    for name in names:
     for q in (name.replace('.','/')+'.py','tools/emulation/'+name+'.py','refs/scripts/'+name+'.py'):
      if q in tracked:found.add(q)
  except SyntaxError:pass
 return found
for r in rows:
 seeds=set()
 for c in r['command']:
  p=c if c.endswith('.py') else c.replace('.','/')+'.py'
  if p in tracked: seeds.add(p)
 # Two levels retain consumer + its referenced evidence, without importing execution.
 deps=set(seeds)
 for _ in range(2):deps |= set().union(*(refs(p) for p in list(deps))) if deps else set()
 r['consumer_files']=sorted(seeds);r['inspected_files']=sorted(deps)
 r['literal_hashes']=sorted(set(hashre.findall('\n'.join(read(p) for p in deps))))
paths={x['path'] for x in old['source_bindings']} | set().union(*(set(r['inspected_files']) for r in rows))
# Read git's actual per-file blob history. No checkout or build, one child process at a time.
index=collections.defaultdict(list); history={}; current={}; blobs={}
for p in sorted(paths):
 if p not in tracked:continue
 current[p]=sha(ROOT/p)
 log=git('log','--format=COMMIT:%H:%s','--raw','--no-abbrev',BASE,'--',p)
 changes=[];commit=None
 for line in log.splitlines():
  if line.startswith('COMMIT:'):commit=line.split(':',2)[1:];continue
  if not line.startswith(':'):continue
  parts=line.split();blob=parts[3]
  if set(blob)=={'0'}:continue
  if blob not in blobs:
   data=subprocess.check_output(['git','cat-file','blob',blob],cwd=ROOT)
   blobs[blob]=hashlib.sha256(data).hexdigest()
  h=blobs[blob]
  entry={'commit':commit[0],'subject':commit[1],'sha256':h}
  changes.append(entry)
  index[h].append({'path':p,'commit':commit[0]})
 history[p]=changes
print('indexed',len(history),'files',len(blobs),'historical blobs',flush=True)
merges=[]; introduced={}
for line in git('log','--first-parent','--merges','--reverse','--format=%H %s',BASE).splitlines():
 m,subject=line.split(' ',1)
 if not re.search(r'orch/|Merge [FCI]\d',subject):continue
 merges.append({'commit':m,'subject':subject})
 for c in git('rev-list',m+'^1..'+m+'^2').splitlines(): introduced.setdefault(c,{'commit':m,'subject':subject})
for changes in history.values():
 for c in changes:c['reviewed_merge']=introduced.get(c['commit'])
for r in rows:
 matches=[]
 for h in r.pop('literal_hashes'):
  for p in sorted({x['path'] for x in index.get(h,[]) }):
   if h==current[p]:continue
   hist=history[p]; positions=[i for i,x in enumerate(hist) if x['sha256']==h]
   if not positions:continue
   # Changes following the most recent matching historical content, newest first.
   delta=hist[:min(positions)]
   matches.append({'path':p,'bound':h,'current':current[p], 'changes_since_bound':delta,'bound_occurrences':[f for f in r['inspected_files'] if h in read(f)]})

 # Explicit JSON path/hash records are stronger evidence than heuristic variable names.
 def walk_records(v):
  if isinstance(v,dict):
   if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str):yield v['path'],v['sha256']
   for x in v.values():yield from walk_records(x)
  elif isinstance(v,list):
   for x in v:yield from walk_records(x)
 for f in r['inspected_files']:
  if not f.endswith('.json'):continue
  try:records=list(walk_records(json.loads(read(f))))
  except ValueError:continue
  for p,h in records:
   if p not in current or h==current[p] or not hashre.fullmatch(h):continue
   if any(x['path']==p and x['bound']==h for x in matches):continue
   hist=history[p];positions=[i for i,x in enumerate(hist) if x['sha256']==h]
   record={'path':p,'bound':h,'current':current[p],'changes_since_bound':hist[:min(positions)] if positions else [],'bound_occurrences':[f]}
   if not positions:record.update(unresolved='Explicit path/hash pin absent from reachable file blob history; exact transition cannot be attributed.',current_last_change=hist[0] if hist else None)
   matches.append(record)
 lane_plugins={'blur':'OLMBlur','colorkeep':'ColorKeep','colorkey':'OLMColorKey','directionalblur':'OLMDirectionalBlur','distancegradation':'OLMDistanceGradation','kirakira':'OLMKiraKira','radialblur':'OLMRadialBlur'}
 plugin=lane_plugins.get(r['lane'])
 source=f'mac/{plugin}/{plugin}.cpp' if plugin else None
 if source in current:
  candidates={}
  for f in r['inspected_files']:
   if not f.endswith('.py') or source not in read(f):continue
   tree=ast.parse(read(f))
   for node in ast.walk(tree):
    if not isinstance(node,ast.Assign):continue
    names={t.id for t in node.targets if isinstance(t,ast.Name)}
    if not names.intersection({'SOURCE_SHA','SOURCE_SHA256','EXPECTED','EXPECTED_IDENTITIES','EXPECTED_IDENTITY'}):continue
    try:value=ast.literal_eval(node.value)
    except (ValueError,TypeError):continue
    vals=[value] if isinstance(value,str) else [value.get(k) for k in ('source','production_source','production_source_sha256','source_sha256')] if isinstance(value,dict) else []
    for h in vals:
     if isinstance(h,str) and hashre.fullmatch(h):candidates.setdefault(h,[]).append(f)
  for h,occ in candidates.items():
   if h==current[source] or any(x['bound']==h and x['path']==source for x in matches):continue
   matches.append({'path':source,'bound':h,'current':current[source],'changes_since_bound':[], 'bound_occurrences':sorted(set(occ)), 'unresolved':'Literal source pin absent from reachable file blob history. Current last change is known; exact transition from bound content cannot be attributed.', 'current_last_change':history[source][0]})
 r['mapped_stale_bindings']=matches
 r['mapping_scope']='Static literal discovery; not a claim every discovered binding is the first failing assertion.'
installed=[]
for x in old['installed']:
 x=dict(x);p=Path(x['binary']);x['current']=sha(p) if p.is_file() else None
 x['build_commit']='UNKNOWN: untracked installed binary; receipt is not build provenance'
 for e in x['evidence']:e['reviewed_merge']=introduced.get(e['introduced_by'].split()[0])
 installed.append(x)
result={'base':BASE,'scope':'F36 72 class-b and 38 class-d commands; historical logs are F36, hashes freshly measured in F40', 'counts':dict(collections.Counter(r['category'] for r in rows)), 'commands':rows,'installed':installed,'file_history':history,'reviewed_merges':merges}
(OUT/'F40-adjudication.json').write_text(json.dumps(result,indent=2)+'\n')
print('commands',len(rows),'mapped',sum(bool(r['mapped_stale_bindings']) for r in rows),'binding occurrences',sum(len(r['mapped_stale_bindings']) for r in rows),flush=True)
