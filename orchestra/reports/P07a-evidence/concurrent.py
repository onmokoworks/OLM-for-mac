import os,subprocess
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07a-parallel-helper-kirakira';d=s/'threads/normal'
body=(d/'host.cpp').read_text().split('int main(int argc,char **argv)',1)[0]
(d/'concurrent.cpp').write_text(body+(r/'orchestra/reports/P07a-evidence/concurrent.cpp').read_text())
env=dict(os.environ,TMPDIR=str(s))
main=r.parent.parent
cmd=['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-Wno-pragma-pack','-Wno-deprecated-declarations',*[a for p in ('Headers','Headers/SP','Util','Resources') for a in ('-I',str(main/p))],'-I'+str(r/'core'),str(d/'concurrent.cpp'),str(r/'mac/OLMKiraKira/OLMKiraKira_Strings.cpp'),str(main/'Util/AEGP_SuiteHandler.cpp'),str(main/'Util/MissingSuiteError.cpp'),str(d/'ucrtmath/libucrtmath.a'),'-framework','Cocoa','-o',str(s/'concurrent')]
subprocess.run(cmd,env=env,check=True)
subprocess.run(['lockf','-k',str(Path.home()/'.cache/olm-emu/bench.lock'),str(s/'concurrent')],env=env,check=True)
