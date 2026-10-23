#!/usr/bin/env python3
"""Build pinned, unmodified AOCL scalar C only; never run its ISA dispatcher."""
import argparse,os,pathlib,subprocess
PIN='29fd054f383e6c5e2dec2fce781d5220059f1836'
SOURCES=['optimized/'+f+'.c' for f in ('expf','sinf','cosf','powf')]+['ref/atan2f.c','alm_special.c','optimized/data/_exp_j_by_64.c','optimized/log_tables.c']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True,type=pathlib.Path);ap.add_argument('--out',required=True,type=pathlib.Path);args=ap.parse_args()
 assert subprocess.check_output(['git','-C',str(args.source),'rev-parse','HEAD'],text=True).strip()==PIN
 assert not subprocess.check_output(['git','-C',str(args.source),'status','--porcelain'],text=True).strip(),'AOCL source must be unmodified'
 args.out.mkdir(parents=True,exist_ok=True);env=dict(os.environ,TMPDIR=str(args.out.resolve()))
 for mode,flags in [('off',['-ffp-contract=off']),('fma',['-ffp-contract=fast','-mfma'])]:
  cmd=['clang','-arch','x86_64','-O2','-dynamiclib',*flags,'-I'+str(args.source/'include'),'-I'+str(args.source/'src/optimized'),*[str(args.source/'src'/s) for s in SOURCES],'-o',str(args.out/('amd-'+mode+'.dylib'))]
  print(cmd,flush=True);subprocess.run(cmd,env=env,check=True)
if __name__=='__main__':main()
