"""Run with no concurrent source builds; restore the candidate even on failure."""
import subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07b-smoother2-threading'
p=r/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';candidate=p.read_bytes()
try:
 p.write_bytes(subprocess.check_output(['git','show','3d270436baa65a980f542461c975344cb55063c9:mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'],cwd=r))
 subprocess.run([sys.executable,str(r/'orchestra/reports/P07b-evidence/units.py'),'units-before-sdk'],check=True)
finally:p.write_bytes(candidate)
subprocess.run([sys.executable,str(r/'orchestra/reports/P07b-evidence/units.py'),'units-after'],check=True)
