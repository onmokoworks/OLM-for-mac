#!/usr/bin/env python3
"""U04 extension: per-row ColorKey toggles, independent ramps, Distance predicates, negatives."""
import argparse, gzip, hashlib, itertools, json, os, subprocess
from pathlib import Path
from capture import MAIN, sessions

def matrix():
    for name,plugin,request in sessions():
        if not name.endswith('-update'):continue
        if plugin=='OLMColorKey':
            for p,c,r,use,replace in itertools.product([0,1],repeat=5):
                # Every palette row independently visits all toggle predicates.
                for i in range(25):
                    request['updates'].append([f'p@7={p}',f'p@8={c}',f'p@23={r}','p@22=25',f'p@{24+8*i}={use}',f'p@{25+8*i}={replace}'])
        if plugin=='OLMKiraKira':
            request['updates'] += [[f'p@{s}={v}' for s,v in zip([13,19,25,31,37],values)] for values in itertools.product([0,1],repeat=5)]
        if plugin=='DistanceGradation':
            request['updates'] += [[f'p@{s}={v}' for s,v in zip([2,5,6,9,11],values)] for values in itertools.product([1,2,3],[1,2,3],[0,1],[1,2,3,4],[1,2,3,4,5])]
        yield name,plugin,request
    yield 'Smoother-update','OLMSmoother',{'updates':[[],['p@1=0'],['p@1=1']]}
    yield 'ToonDilate-update','OLMToonDilate',{'updates':[[],['p@1=0'],['p@1=10']]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--worker',type=Path,default=Path('/Users/onmk/.cache/olm-emu/worker-U03-ui/aex-guest-worker'));args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True);manifest=[]
    for name,plugin,req in matrix():
        raw=args.output/(name+'.jsonl'); request_hashes=[]
        with raw.open('w') as out:
            for batch,start in enumerate(range(0,len(req['updates']),200)):
                request=args.output/(name+f'.batch{batch}.request.json')
                request.write_text(json.dumps({'current_time':7,'time_scale':24,'updates':req['updates'][start:start+200]},indent=2)+'\n')
                request_hashes.append(hashlib.sha256(request.read_bytes()).hexdigest())
                with (args.output/(name+f'.batch{batch}.log')).open('w') as err:
                    run=subprocess.run([str(args.worker),'ui-session',str(MAIN/'plugins_2025'/(plugin+'.aex')),str(request.resolve())],stdout=out,stderr=err,env={**os.environ,'TMPDIR':str(args.output.resolve())},timeout=600)
                assert run.returncode==0,(name,batch,run.returncode)
        count=0
        with raw.open('rb') as src,(args.output/(name+'.jsonl.gz')).open('wb') as dst,gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as gz:
            for line in src:
                assert json.loads(line)['event']['selector_error']==0
                gz.write(line);count+=1
        manifest.append({'name':name,'events':count,'request_sha256':request_hashes,'original_sha256':hashlib.sha256((MAIN/'plugins_2025'/(plugin+'.aex')).read_bytes()).hexdigest(),'compressed_sha256':hashlib.sha256((args.output/(name+'.jsonl.gz')).read_bytes()).hexdigest()})
        raw.unlink();print(name,count,flush=True)
    (args.output/'manifest.json').write_text(json.dumps({'worker_sha256':hashlib.sha256(args.worker.read_bytes()).hexdigest(),'sessions':manifest},indent=2)+'\n')
if __name__=='__main__':main()
