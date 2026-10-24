"""Stream measured evidence into the committed report directory after validation."""
import gzip,hashlib,json,shutil
from pathlib import Path
E=Path(__file__).resolve().parent;R=E.parents[2];S=R/'orchestra/state/P03b-nonfinite-hdr-admission'
for p in sorted(S.iterdir()):
 if not p.is_file() or p.suffix not in ('.json','.jsonl','.log','.txt'):continue
 if p.suffix in ('.log','.txt') or p.name in ('summary.json','leaves.json','dg-conversion.json') or p.name.endswith('-summary.json'):
  shutil.copyfile(p,E/p.name)
 else:
  with p.open('rb') as src,(E/(p.name+'.gz')).open('wb') as raw:
   with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as dst:shutil.copyfileobj(src,dst)
manifest={}
for p in sorted(E.iterdir()):
 if not p.is_file() or p.name=='sha256.json':continue
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 manifest[p.name]=h.hexdigest()
(E/'sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
