"""Remove only this ticket's regenerable build trees after all runs have joined."""
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[3]
s=root/'orchestra/state/P07e-radialblur-rotation-parallel'
relative=['bundle/xcode','small/radialblur/fast','small/radialblur/reference',
          'threads/fast/build','threads/reference/build','threads/tsan/build',
          'concurrent/build','native/radialblur/fast','native/radialblur/reference']
for name in relative:
 p=s/name
 assert p.resolve().is_relative_to(s.resolve()) and not p.is_symlink()
 if p.is_dir():shutil.rmtree(p)
for kind in ('fast','reference','tsan'):
 for name in ('input.raw','output.raw','stdout','geometry-input.raw','geometry-output.raw'):
  (s/'threads'/kind/name).unlink(missing_ok=True)
print('Removed generated build trees and scratch raw frames; logs/reports retained')
