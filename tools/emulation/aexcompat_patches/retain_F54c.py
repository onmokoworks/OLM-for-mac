#!/usr/bin/env python3
"""Retain portable F54c digests/counts; exclude raw/hex image captures."""
import gzip, hashlib, json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/F54c-aexcompat-resident-watches'
OUT=ROOT/'orchestra/reports/F54c-evidence'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    worker=Path.home()/'.cache/olm-emu/worker-F54c'
    build=json.loads((worker/'build.json').read_text());assert sha(worker/'aex-guest-worker')==build['worker_sha256']
    shutil.copy2(worker/'build.json',OUT/'build.json')
    for name in ('r06-summary.json','cropped-1-summary.json','cropped-2-summary.json','4k-summary.json','entry-boundary-summary.json','corpus-summary.json','corpus-results.jsonl.gz'):
        shutil.copy2(S/name,OUT/name)
    for folder in ('initial-radialblur','corpus-radialblur-isolated'):
        if not (S/folder/'summary.json').exists():continue
        shutil.copy2(S/folder/'summary.json',OUT/(folder+'-summary.json'))
        with gzip.open(OUT/(folder+'-results.jsonl.gz'),'wt') as out:
            with (S/folder/'results.jsonl').open() as source:
                shutil.copyfileobj(source,out)
    corpus=json.loads((S/'corpus-summary.json').read_text())
    assert len(corpus['plugins'])==10
    assert all(p['worker_sha256']==build['worker_sha256'] for p in corpus['plugins'].values())
    stages=json.loads((S/'r06-summary.json').read_text());assert len(stages)==17 and all(r['exact'] for r in stages)
    for name in ('build-final.log','tests-reviewed.log','r06.log','geometry.log','4k-callsite.log','entry-probe.log','corpus.log'):
        with gzip.open(OUT/(name+'.gz'),'wt') as f:
            f.write((S/name).read_text().replace(str(Path.home()),'<HOME>'))
    summary=dict(source_head=build['head'],worker_sha256=build['worker_sha256'],r06_cases=len(stages),r06_snapshots=sum(len(r['captures']) for r in stages),r06_snapshot_bytes=sum(c['bytes'] for r in stages for c in r['captures']),corpus_totals=corpus['totals'],files={p.name:sha(p) for p in sorted(OUT.iterdir()) if p.name!='manifest.json'})
    summary['status']='differences' if corpus['totals']['byte_difference'] or corpus['totals']['status_difference'] else 'equal'
    (OUT/'manifest.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary['corpus_totals']))
if __name__=='__main__':main()
