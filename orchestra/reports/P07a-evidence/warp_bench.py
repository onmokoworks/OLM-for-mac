import os,subprocess
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07a-parallel-helper-kirakira'
env=dict(os.environ,TMPDIR=str(s))
cmd=['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-I'+str(r),str(r/'orchestra/reports/P07a-evidence/warp_bench.cpp'),str(s/'threads/normal/ucrtmath/libucrtmath.a'),'-o',str(s/'warp-bench')]
subprocess.run(cmd,env=env,check=True)
subprocess.run(['lockf','-k',str(Path.home()/'.cache/olm-emu/bench.lock'),str(s/'warp-bench')],env=env,check=True)
