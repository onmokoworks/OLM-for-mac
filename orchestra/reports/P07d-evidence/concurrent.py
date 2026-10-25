from pathlib import Path
import os,subprocess
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07d-distancegradation-blur-colorkey-threading'
e=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s))
cmd=['clang++','-std=c++17','-O2','-ffp-contract=off','-fno-fast-math','-I'+str(r/'core'),str(r/'orchestra/reports/P07d-evidence/blur_concurrent.cpp'),str(r/'core/olmblur_worker_orchestration.cpp'),str(r/'core/olmblur_helper.cpp'),str(s/'threads/normal/ucrtmath/libucrtmath.a'),'-o',str(s/'concurrent')]
subprocess.run(cmd,env=e,check=True)
subprocess.run(['lockf','-k',str(Path.home()/'.cache/olm-emu/bench.lock'),str(s/'concurrent')],env=e,check=True,timeout=600)
