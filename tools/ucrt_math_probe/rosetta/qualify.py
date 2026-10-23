#!/usr/bin/env python3
"""Seeded shared-input qualification. Stream results; never accept fault output."""
import argparse, json, pathlib, random, struct, subprocess, sys, time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from probe import Probe, DEFAULT_DLL, FUNCTIONS

def bits(x): return struct.unpack('<I',struct.pack('<f',x))[0]
def corpus(fn,n):
    rng=random.Random(0xF27B)
    for i in range(n):
        # Broad normal finite domains avoiding overflow/domain-error OS paths.
        if fn=='expf': a,b=bits(rng.uniform(-80,80)),0
        elif fn=='powf': a,b=bits(2**rng.uniform(-10,10)),bits(rng.uniform(-8,8))
        else:
            a=rng.getrandbits(32)
            while a&0x7f800000==0x7f800000: a=rng.getrandbits(32)
            b=rng.getrandbits(32)
            while b&0x7f800000==0x7f800000: b=rng.getrandbits(32)
        yield a,b

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--oracle',required=True,type=pathlib.Path);ap.add_argument('--out',required=True,type=pathlib.Path);ap.add_argument('--count',type=int,default=100000);args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True);summary=[]
    for fn in FUNCTIONS:
        start=time.monotonic(); inp=args.out/(fn+'.in'); ref=args.out/(fn+'.unicorn');native=args.out/(fn+'.native');err=args.out/(fn+'.stderr')
        with inp.open('w') as f:
            for a,b in corpus(fn,args.count):f.write(f'{a:08x} {b:08x}\n')
        with inp.open() as f,native.open('w') as out,err.open('w') as e:
            rc=subprocess.run([str(args.oracle.resolve()),str(DEFAULT_DLL),'0',fn],stdin=f,stdout=out,stderr=e).returncode
        row=dict(function=fn,count=args.count,native_exit=rc)
        if rc:row['failure']=err.read_text();summary.append(row);print(json.dumps(row),flush=True);continue
        p=Probe();p.set_mode(0);mismatch=0;first=None;done=0
        with ref.open('w') as f,native.open() as native_out:
            for a,b in corpus(fn,args.count):
                try:r=p.call(fn,(a,b) if fn in ('atan2f','powf') else (a,))
                except RuntimeError as e:row['unicorn_failure']=str(e);break
                f.write(f'{r:08x}\n');actual=int(next(native_out),16);done+=1
                if actual!=r:
                    mismatch+=1
                    if first is None:first=dict(a=f'{a:08x}',b=f'{b:08x}',unicorn=f'{r:08x}',native=f'{actual:08x}')
        row.update(compared=done,mismatches=mismatch,first_mismatch=first,seconds=time.monotonic()-start);summary.append(row);print(json.dumps(row),flush=True)
    (args.out/'qualification.json').write_text(json.dumps(summary,indent=2)+'\n')
    return 0 if all(r.get('compared')==args.count and r.get('mismatches')==0 for r in summary) else 1
if __name__=='__main__':sys.exit(main())
