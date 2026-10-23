#!/usr/bin/env python3
"""Archive or restore C57 evidence with an uncompressed SHA256 manifest."""
import argparse,gzip,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'orchestra/reports/C57-evidence'
FILES=['audit.json','controls/report.json','invalid-host/report.json','invalid-host-recheck/report.json','witnesses/report.json',
       'retry57003-228/report.json','static/original.asm','static/static.json','trace-builder/report.json','corpus/campaign.json']
FILES += [f'{kind}{seed}/{name}' for seed in (1,105,57003) for kind,name in [('seed','campaign.json'),('san','report.json')]]
FILES += [f'trace-builder/{seed}-{index}/{name}' for seed,index in ((1,248),(105,158),(105,214)) for name in ('trace.json','watches.json','output.raw')]
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--state',type=Path,required=True);ap.add_argument('--restore',action='store_true');a=ap.parse_args()
    state=a.state.resolve();assert state.is_relative_to(ROOT/'orchestra/state/C57-radial-missing-layer')
    if a.restore:
        state.mkdir(parents=True,exist_ok=False)
        manifest=json.loads((EVIDENCE/'manifest.json').read_text())
        for name,sha in manifest.items():
            p=state/name;p.parent.mkdir(parents=True,exist_ok=True)
            with gzip.open(EVIDENCE/(name+'.gz'),'rb') as src,p.open('wb') as dst:shutil.copyfileobj(src,dst)
            assert digest(p)==sha,name
        print('Restored and hash-verified',len(manifest),'files')
        return
    EVIDENCE.mkdir(parents=True,exist_ok=True);manifest={}
    for name in FILES+sorted(p.name for p in state.glob('*.log')):
        src=state/name;assert src.is_file(),src
        dst=EVIDENCE/(name+'.gz');dst.parent.mkdir(parents=True,exist_ok=True)
        with src.open('rb') as inp,dst.open('wb') as f:
            with gzip.GzipFile(fileobj=f,mode='wb',mtime=0,filename='') as gz:shutil.copyfileobj(inp,gz)
        manifest[name]=digest(src)
    (EVIDENCE/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print('Archived',len(manifest),'files')
if __name__=='__main__':main()
