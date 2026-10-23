#!/usr/bin/env python3
"""Run the current harness against pre-F44 core/Mac sources, without editing the worktree."""
import importlib
from pathlib import Path
import subprocess
import sys
import run
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/F44-integrate-ms-float/before-source'
# Fixed parent ensures this remains reproducible after F44 is committed.
REV='f23b5a664f13a42663fbac9a8d39b37600995ad0'
S.mkdir(parents=True,exist_ok=True)
if not (S/'mac').exists():
    archive=subprocess.Popen(['git','archive',REV,'core','mac'],cwd=ROOT,stdout=subprocess.PIPE)
    subprocess.run(['tar','-x','-C',str(S)],stdin=archive.stdout,check=True)
    archive.stdout.close()
    if archive.wait():raise RuntimeError('git archive failed')
for name in ['tools','tests','refs','ucrtmath']:
    if not (S/name).exists():(S/name).symlink_to(ROOT/name,target_is_directory=True)
plugin=sys.argv[sys.argv.index('--plugin')+1]
module=importlib.import_module('adapters.'+plugin)
def remap(v):
    if isinstance(v,Path) and v.is_relative_to(ROOT):
        parts=v.relative_to(ROOT).parts
        if not parts:return S
        if parts[0] in ('mac','core'):return S/v.relative_to(ROOT)
    if isinstance(v,list):return [remap(x) for x in v]
    if isinstance(v,tuple):return tuple(remap(x) for x in v)
    return v
for name,value in list(vars(module).items()):
    setattr(module,name,remap(value))
if plugin == 'radialblur':
    module.public.SOURCE = remap(module.public.SOURCE)
    module.public.initial.SOURCE = remap(module.public.initial.SOURCE)
sys.exit(run.main())
