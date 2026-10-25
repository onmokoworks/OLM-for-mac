from pathlib import Path
import os,subprocess
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07d-distancegradation-blur-colorkey-threading';d=s/'dg-threads/normal'
e=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s))
body=(d/'host.cpp').read_text().split('int main(',1)[0]
(d/'concurrent.cpp').write_text(body+(r/'orchestra/reports/P07d-evidence/dg_concurrent.cpp').read_text())
subprocess.run(['clang++','-std=c++17','-O2','-ffp-contract=off','-fno-fast-math','-I'+str(d/'geometry-shim'),str(d/'concurrent.cpp'),str(r/'core/olmdistancegradation_fieldgen.cpp'),str(d/'ucrtmath/libucrtmath.a'),'-o',str(s/'dg-concurrent')],env=e,check=True)
