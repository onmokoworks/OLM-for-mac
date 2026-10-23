#!/usr/bin/env python3
"""Stream retained C53b qualification and paired planes to compressed evidence."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[2]


def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--state',type=Path,required=True)
    args=ap.parse_args();s=args.state.resolve();out=ROOT/'orchestra/reports/C53b-evidence'
    assert s.is_relative_to(ROOT/'orchestra/state/C53b-radial-trace-worker')
    out.mkdir(parents=True,exist_ok=True);manifest={}
    def keep(p,name):
        dest=out/(name+'.gz')
        with p.open('rb') as src,dest.open('wb') as dst,gzip.GzipFile(fileobj=dst,mode='wb',mtime=0) as gz:
            shutil.copyfileobj(src,gz,1024*1024)
        manifest[dest.name]=dict(uncompressed_sha256=digest(p),uncompressed_bytes=p.stat().st_size)
    for run in ('trace-full','trace-rotation','trace-callsite'):
        d=json.loads((s/run/'report.json').read_text())
        keep(s/run/'report.json',run+'-report.json')
        for row in d['cases']:
            assert row['bound']
            # Full Rotation capture supersedes the two-context-only full-run row.
            if run=='trace-full' and row['seed']==105 and row['index']==148:continue
            trace=s/run/row['trace_file']
            keep(trace,f"{run}-{row['seed']}-{row['index']}.json")
    runs=('mac-baseline4','mac-sse-stages','mac-prepass','mac-scatter','mac-final','mac-rotation','mac-rotation-fix',
          'san1','san1-fixed','san105','san54321','final-witnesses')
    for run in runs:
        keep(s/run/'report.json',run+'-report.json')
        if (s/run/'experiment.cpp').exists():keep(s/run/'experiment.cpp',run+'-source.cpp')
    for run in ('mac-final','mac-rotation-fix'):
        for directory in (s/run).iterdir():
            if not directory.is_dir() or '-' not in directory.name:continue
            if run=='mac-final' and directory.name=='105-148':continue
            for p in directory.glob('*.bin'):
                keep(p,f'mac-{directory.name}-{p.name}')
    for seed in (1,105,54321):
        keep(s/f'seed{seed}/campaign.json',f'seed{seed}.json')
        keep(s/f'seed{seed}/admitted.cpp',f'seed{seed}-qualified-source.cpp')
    keep(s/'corpus/campaign.json','corpus.json')
    for run in ('reproduce-mac','reproduce-trace'):
        keep(s/run/'report.json',run+'-report.json')
    for p in s.glob('compare-*.json'):keep(p,p.name)
    for name in ('audit.json','preservation-final.json','memory-pressure.txt'):
        keep(s/name,name)
    for p in s.glob('*.log'):
        if p.name != 'archive.log':keep(p,p.name)
    keep(Path.home()/'.cache/olm-emu/worker-C53b-trace/build.json','worker-build.json')
    for name in ('stages.asm','static.json'):
        p=out/name;manifest[name]=dict(uncompressed_sha256=digest(p),uncompressed_bytes=p.stat().st_size)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(files=len(manifest),compressed_bytes=sum(p.stat().st_size for p in out.iterdir()))))

if __name__=='__main__':main()
