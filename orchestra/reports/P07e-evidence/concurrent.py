"""Build concurrency/threshold probe; all timed renders hold the shared lock."""
import os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
s=root/'orchestra/state/P07e-radialblur-rotation-parallel/concurrent'
s.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(root/'tools/emulation'))
import probe_radialblur_topology_20261001 as p
p.ROOT=root.parent.parent
p.HARNESS=root/'orchestra/reports/P07e-evidence/concurrent.cpp'
env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s))
os.environ.update(env)
binary=p.build(s/'build',p.SOURCE.read_text())
subprocess.run(['lockf','-k',str(Path.home()/'.cache/olm-emu/bench.lock'),str(binary)],env=env,check=True)
