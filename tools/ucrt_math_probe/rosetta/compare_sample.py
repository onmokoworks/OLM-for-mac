#!/usr/bin/env python3
"""Stream pairwise counts and at most 1000 mismatches/pair from qualified samples."""
import argparse,contextlib,itertools,json,pathlib,subprocess,time

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apple',required=True);ap.add_argument('--amd',required=True,type=pathlib.Path);ap.add_argument('--corpus',required=True,type=pathlib.Path);args=ap.parse_args();rows=[]
 for fn in ('expf','atan2f','sinf','cosf','powf'):
  start=time.monotonic()
  with (args.corpus/(fn+'.in')).open() as inp,(args.corpus/(fn+'.apple')).open('w') as out:subprocess.run([args.apple,fn],stdin=inp,stdout=out,check=True)
  for mode in ('off','fma'):
   with (args.corpus/(fn+'.in')).open() as inp,(args.corpus/(fn+'.amd-'+mode)).open('w') as out:subprocess.run([args.apple,fn,str((args.amd/('amd-'+mode+'.dylib')).resolve())],stdin=inp,stdout=out,check=True)
  labels=['native','fma','apple','amd-off','amd-fma'];pairs=list(itertools.combinations(range(len(labels)),2));counts=[0]*len(pairs);first=[None]*len(pairs);n=0
  with contextlib.ExitStack() as stack:
   files=[stack.enter_context((args.corpus/(fn+'.'+suffix)).open()) for suffix in ['in',*labels]]
   mismatch=stack.enter_context((args.corpus/(fn+'.mismatches.jsonl')).open('w'))
   for inputs,*values in zip(*files,strict=True):
    values=[v.strip() for v in values];n+=1
    for k,(i,j) in enumerate(pairs):
     if values[i]!=values[j]:
      counts[k]+=1
      event=dict(pair=[labels[i],labels[j]],inputs=inputs.strip(),outputs=[values[i],values[j]])
      if first[k] is None:first[k]=event
      if counts[k]<=1000:mismatch.write(json.dumps(event)+'\n')
  rows.append(dict(function=fn,count=n,seconds=time.monotonic()-start,pairs=[dict(pair=[labels[i],labels[j]],matches=n-counts[k],rate=(n-counts[k])/n,first_mismatch=first[k]) for k,(i,j) in enumerate(pairs)]))
 (args.corpus/'comparison.json').write_text(json.dumps(dict(apple_arch='x86_64 under Rosetta',scope='100k qualified samples/function, NOT exhaustive',results=rows),indent=2)+'\n')
 print("PASS: compared five engines on",sum(r["count"] for r in rows),"shared function inputs; sample results saved")
if __name__=='__main__':main()
