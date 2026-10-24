"""Compare free-function tests with pre-ticket and final Blur worker sources."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
files=[ROOT/'core'/name for name in ('olmblur_worker_orchestration.cpp','olmblur_worker16_nonlegacy.cpp','olmblur_worker32_nonlegacy.cpp')]
original={p:p.read_bytes() for p in files}
try:
 for p in files:p.write_bytes(subprocess.check_output(['git','show','00b91897d2fee8ba1b100af4f83dff6adeacbad2:'+str(p.relative_to(ROOT))],cwd=ROOT))
 subprocess.run([sys.executable,str(ROOT/'orchestra/reports/P05c-evidence/functions.py'),'olmblur','blur-functions-before'],cwd=ROOT,check=True)
finally:
 for p,content in original.items():p.write_bytes(content)
subprocess.run([sys.executable,str(ROOT/'orchestra/reports/P05c-evidence/functions.py'),'olmblur','blur-functions-after'],cwd=ROOT,check=True)
