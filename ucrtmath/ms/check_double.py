#!/usr/bin/env python3
"""Bounded arm64 versus pinned Rosetta comparison; at most two processes."""
import argparse, hashlib, json, os, pathlib, subprocess, time, math, struct
ROOT=pathlib.Path(__file__).resolve().parents[2]
STATE=ROOT/'orchestra/state/F43b-ucrtmath-ms-double-trig-exp'
DLL=pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
def bits(x):return struct.unpack('<Q',struct.pack('<d',x))[0]
def boundaries(fn):
    # Merge small integer intervals, then stream words without a corpus-sized set.
    exact=[0,1,2,0xfffffffffffff,0x10000000000000,0x7fefffffffffffff,
           0x7ff0000000000000,0x7ff0000000000001,0x7ff8000000000000,0x7fffffffffffffff]
    intervals=[(v,v) for v in exact]
    def window(x,radius=128):
        u=bits(x)&0x7fffffffffffffff
        intervals.append((max(0,u-radius),min(0x7ff0000000000000,u+radius)))
    for x in [2**-27,2**-26,2**-13,math.pi/4,500000.,20000000.]:window(x)
    # Dense subnormal windows, including both sides of the normal boundary.
    for e in range(-1074,-1021):window(math.ldexp(1.0,e))
    if fn=='exp':
        for h in ['0x1.62e42fefa39efp+9','-0x1.74046dfefd9d0p+9','-0x1.74910d52d3051p+9']:
            window(float.fromhex(h),4096)
        for x in [-745.,-744.,-710.,-709.,-708.,710.]:window(x)
        # Every integer reduction boundary in the non-saturated input interval.
        for n in range(-68800,65537):window(n*float.fromhex('0x1.62e42fefa39efp-7'),4)
    else:
        for n in range(1,4097):window(n*math.pi/2)
        for e in range(13,1024):window(math.ldexp(math.pi/2,e))
    merged=[]
    for lo,hi in sorted(intervals):
        if merged and lo<=merged[-1][1]+1:merged[-1]=(merged[-1][0],max(hi,merged[-1][1]))
        else:merged.append((lo,hi))
    for sign in [0,0x8000000000000000]:
        for lo,hi in merged:
            for u in range(lo,hi+1):yield u|sign
def main():
    p=argparse.ArgumentParser();p.add_argument('--full',action='store_true');p.add_argument('--function',choices=['sin','cos','exp']);p.add_argument('--kind',choices=['random','range','boundary']);p.add_argument('--count',type=int);p.add_argument('--no-build',action='store_true');a=p.parse_args()
    STATE.mkdir(parents=True,exist_ok=True);build=STATE/'build';build.mkdir(exist_ok=True)
    env=dict(os.environ,TMPDIR=str(STATE),PYTHONDONTWRITEBYTECODE='1')
    if not a.no_build:
        with (STATE/'build.log').open('w') as log:
            commands=[['sh',str(ROOT/'ucrtmath/build.sh'),str(build)],['clang','-arch','arm64','-O2','-ffp-contract=off','-fno-fast-math','-I'+str(ROOT/'ucrtmath/include'),str(ROOT/'ucrtmath/ms/double_native.c'),str(build/'libucrtmath.a'),'-o',str(build/'double_native')],['clang','-arch','x86_64','-O2','-Wno-deprecated-declarations',str(ROOT/'ucrtmath/ms/double_compare.c'),'-o',str(build/'double_compare')]]
            for cmd in commands:subprocess.run(cmd,env=env,stdout=log,stderr=log,check=True)
    for fn in ([a.function] if a.function else ['sin','cos','exp']):
        for kind in ([a.kind] if a.kind else ['boundary','random','range']):
            source=None
            if kind=='boundary':
                corpus=STATE/(fn+'-boundary.txt');count=0
                with corpus.open('w') as out:
                    for v in boundaries(fn):out.write(f'{v:016x}\n');count+=1
                source=corpus.open('rb')
            else:count=a.count or ((10**9 if kind=='random' else 10**8) if a.full else 1000000)
            name=f'{fn}-{kind}-{count}';start=time.monotonic()
            with (STATE/(name+'.stderr')).open('w') as err:
                producer=subprocess.Popen([str(build/'double_native'),fn,'file' if source else kind,str(count)],stdin=source,stdout=subprocess.PIPE,stderr=err,env=env)
                try:
                    result=subprocess.run([str(build/'double_compare'),str(DLL),fn,str(count)],stdin=producer.stdout,stdout=subprocess.PIPE,stderr=err,env=env)
                    producer.stdout.close();rc=producer.wait()
                finally:
                    if producer.poll() is None:producer.kill();producer.wait()
                    if source:source.close()
            if rc or result.returncode not in (0,1):raise RuntimeError((name,rc,result.returncode))
            data=json.loads(result.stdout);data.update(kind=kind,seconds=time.monotonic()-start,producer_exit=rc,comparator_exit=result.returncode)
            data['sha256']={str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [DLL,build/'double_native',build/'double_compare',ROOT/'ucrtmath/ms/double.c',ROOT/'ucrtmath/ms/double_tables.h']}
            (STATE/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
            print(name,'mismatches',[m['mismatches'] for m in data['modes']],f'{data["seconds"]:.3f}s',flush=True)
            if result.returncode:return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
