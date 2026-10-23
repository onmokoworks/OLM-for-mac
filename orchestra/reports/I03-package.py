#!/usr/bin/env python3
"""Package measured I03 evidence without binaries, dependencies, or build trees."""
import hashlib,json,shutil,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'orchestra/reports'; S=ROOT/'orchestra/state/I03-integration-check'
paths=set()
for ext in ('*.json','*.jsonl','*.log'):
    paths.update(S.glob(ext))
for folder in ('fixtures','F51','witnesses','generated-evidence'):
    for p in (S/folder).rglob('*'):
        if p.is_file() and not p.is_symlink() and p.suffix in ('.json','.jsonl','.log','.patch'): paths.add(p)
for folder in S.glob('*bisect*'):
    if folder.is_dir():
        for ext in ('*.json','*.jsonl','*.log'): paths.update(folder.glob(ext))
for p in (S/'bundles').rglob('*'):
    if p.is_file() and p.suffix in ('.log','.json') and 'xcode' not in p.relative_to(S/'bundles').parts:paths.add(p)
archive=OUT/'I03-evidence.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
    for p in sorted(paths): tar.add(p,arcname=str(p.relative_to(S)),recursive=False)
manifest={'archive':archive.name,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'files':len(paths),'witnesses':len(list((S/'witnesses').rglob('*.json'))),'members':[{'path':str(p.relative_to(S)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]}
(OUT/'I03-artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for name in ('classification','cached-bundles'):
    shutil.copy2(S/(name+'.json'),OUT/('I03-'+name+'.json'))
summary=json.loads((S/'summary.json').read_text())
summary['gates']['generic']['failures']=[{'test':r['test'],'status':r['status'],'exit_code':r.get('exit_code')} for r in summary['gates']['generic']['failures']]
(OUT/'I03-results.json').write_text(json.dumps(summary,indent=2)+'\n')
for folder in sorted((S/'witnesses').iterdir()):
    files=sorted(folder.glob('*.json'))
    if files:
        dest=OUT/'I03-witnesses'/folder.name;dest.mkdir(parents=True,exist_ok=True);shutil.copy2(files[0],dest/files[0].name)
print(json.dumps({k:v for k,v in manifest.items() if k!='members'}))
