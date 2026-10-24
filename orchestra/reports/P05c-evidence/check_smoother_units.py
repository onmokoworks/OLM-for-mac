"""Repeat Smoother units with all helper globals redirected to ticket scratch.
Run only when no other source-consuming Smoother build/campaign is active.
"""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[3];p=ROOT/'mac/OLMSmoother/Mac/OLMSmoother_port.cpp';candidate=p.read_bytes()
try:
 p.write_bytes(subprocess.check_output(['git','show','00b91897d2fee8ba1b100af4f83dff6adeacbad2:mac/OLMSmoother/Mac/OLMSmoother_port.cpp'],cwd=ROOT))
 for kind in ['units','functions']:
  subprocess.run([sys.executable,str(ROOT/f'orchestra/reports/P05c-evidence/{kind}.py'),'olmsmoother',f'smooth-{kind}-before'],cwd=ROOT,check=True)
finally:p.write_bytes(candidate)
for kind in ['units','functions']:
 subprocess.run([sys.executable,str(ROOT/f'orchestra/reports/P05c-evidence/{kind}.py'),'olmsmoother',f'smooth-{kind}-after'],cwd=ROOT,check=True)
