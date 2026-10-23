#!/usr/bin/env python3
import os,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[2]
state=root/'orchestra/state/F28-ucrtmath-lib-amd'
src=state/'amd-source';out=state/'survey-build';out.mkdir(exist_ok=True)
assert subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()=='29fd054f383e6c5e2dec2fce781d5220059f1836'
assert not subprocess.check_output(['git','-C',str(src),'status','--porcelain'],text=True).strip()
env=dict(os.environ,TMPDIR=str(out))
for mode,flags in [('off',['-ffp-contract=off']),('fma',['-ffp-contract=fast','-mfma'])]:
 files=['optimized/'+f+'.c' for f in ['log2f','sin','cos','exp','pow','pow_data','sincos_tbl']]+['optimized/data/_log_data.c','alm_special.c']
 subprocess.run(['clang','-arch','x86_64','-O2','-dynamiclib',*flags,'-I'+str(src/'include'),'-I'+str(src/'src/optimized'),*[str(src/'src'/f) for f in files],'-o',str(out/f'amd-{mode}.dylib')],env=env,check=True)
for arch,name in [('arm64','survey_native'),('x86_64','survey_compare')]:
 subprocess.run(['clang','-arch',arch,'-O2','-ffp-contract=off','-Wno-deprecated-declarations',str(root/f'ucrtmath/tests/{name}.c'),'-o',str(out/name)],env=env,check=True)
