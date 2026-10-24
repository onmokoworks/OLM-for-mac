"""Compare old and new kernels including arbitrary IEEE inputs and row parallelism."""
import os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/P05a-directionalblur-performance/kernels';S.mkdir(parents=True,exist_ok=True)
E=R/'orchestra/reports/P05a-evidence';env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S))
base='9123f22a0cee8a7592ca7a89ec4f0a962d02b9a8'
flags=['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-I'+str(R),'-I'+str(R/'core')]
with (S/'build.log').open('w') as log:
 subprocess.run(['sh',str(R/'ucrtmath/build.sh'),str(S/'ucrt')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 for version in ('old','new'):
  inputs=[]
  for file in ('dblur_rowdriver.cpp','dblur_rotate.cpp'):
   if version=='old':
    p=S/file;s=subprocess.check_output(['git','show',base+':core/'+file],cwd=R,text=True);s=s.replace('../ucrtmath/include/ucrtmath.h',str(R/'ucrtmath/include/ucrtmath.h'));p.write_text(s)
   else:p=R/'core'/file
   inputs.append(str(p))
  objects=[]
  for source in inputs:
   obj=S/(version+'-'+Path(source).stem+'.o')
   opt=['-O0'] if version=='old' and 'rotate' in source else []
   subprocess.run(flags+opt+['-c',source,'-o',str(obj)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
   objects.append(str(obj))
  subprocess.run(flags+['-dynamiclib',*objects,str(S/'ucrt/libucrtmath.a'),'-o',str(S/(version+'.dylib'))],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 subprocess.run(flags+[str(E/'kernel_witness.cpp'),'-o',str(S/'witness')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
with (E/'kernel-witness.txt').open('w') as log:subprocess.run([str(S/'witness'),str(S/'old.dylib'),str(S/'new.dylib')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
print((E/'kernel-witness.txt').read_text())
