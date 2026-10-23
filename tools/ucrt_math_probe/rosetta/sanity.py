#!/usr/bin/env python3
"""MPFR 200-bit sanity of a shared corpus; this is not exhaustive proof."""
import argparse,json,pathlib,struct,subprocess,time
import gmpy2 as g

def value(b):return g.mpfr(struct.unpack('<f',struct.pack('<I',b))[0])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--oracle',required=True);ap.add_argument('--corpus',required=True,type=pathlib.Path);args=ap.parse_args()
 g.get_context().precision=200
 dll=pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll';summary=[]
 for fn,bound in [('expf','0.501'),('atan2f','0.584'),('sinf','0.530'),('cosf','0.530'),('powf','1.00')]:
  start=time.monotonic();out=args.corpus/(fn+'.fma');err=args.corpus/(fn+'.fma.stderr')
  with (args.corpus/(fn+'.in')).open() as inp,out.open('w') as f,err.open('w') as e:rc=subprocess.run([args.oracle,str(dll),'1',fn],stdin=inp,stdout=f,stderr=e).returncode
  row=dict(function=fn,exit=rc,bound=bound);worst=g.mpfr(0);fail=0;count=0;first=None;witness=None
  if not rc:
   with (args.corpus/(fn+'.in')).open() as inp,out.open() as f:
    for line,result in zip(inp,f,strict=True):
     a,b=map(lambda x:int(x,16),line.split());r=int(result,16);x,y=value(a),value(b)
     exact={'expf':g.exp,'atan2f':g.atan2,'sinf':g.sin,'cosf':g.cos,'powf':lambda x,y:x**y}[fn](*((x,y) if fn in ('powf','atan2f') else (x,)))
     # ULP at the exact result, bounded below by the subnormal spacing.
     exponent=int(g.get_exp(abs(exact))) if exact else -125
     ulp=g.exp2(max(-149,exponent-24));error=abs(value(r)-exact)/ulp;count+=1
     sample=dict(a=f'{a:08x}',b=f'{b:08x}',result=f'{r:08x}',error_ulp=str(error))
     if error>worst:worst=error;witness=sample
     if error>g.mpfr(bound):
      fail+=1
      if first is None:first=sample
   row.update(count=count,violations=fail,max_error_ulp=str(worst),worst=witness,first_violation=first)
  else:row['failure']=err.read_text()
  row['seconds']=time.monotonic()-start;summary.append(row);print(json.dumps(row),flush=True)
 (args.corpus/'sanity.json').write_text(json.dumps(dict(gmpy2=g.version(),mpfr=g.mpfr_version(),precision=200,results=summary),indent=2)+'\n')
 return 0 if all(r.get('violations')==0 for r in summary) else 1
if __name__=='__main__':raise SystemExit(main())
