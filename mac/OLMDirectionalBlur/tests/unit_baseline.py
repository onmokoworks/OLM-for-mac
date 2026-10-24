#!/usr/bin/env python3
"""Diagnose existing unit failures against the ticket base, without changing source."""
import itertools, re, subprocess, sys, types, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P01b-directionalblur-downsample/unit-baseline';S.mkdir(parents=True,exist_ok=True)
BASE='22f8f8023645f6299abe6a19f2f596eae7157148'
paths=[ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp',ROOT/'core/dblur_generic_budget.h']
original={p:subprocess.check_output(['git','show',f'{BASE}:{p.relative_to(ROOT)}'],cwd=ROOT) for p in paths}
overlay={p:S/p.name for p in paths}
def rewrite(text,parent):
    def include(m):
        target=(parent/m[1]).resolve()
        if not target.exists() and (ROOT/m[1]).exists():target=(ROOT/m[1]).resolve()
        return '#include "'+str(overlay.get(target,target))+'"'
    return re.sub(r'#include "([^"]+)"',include,text)
for p in paths:overlay[p].write_text(rewrite(original[p].decode(),p.parent))
real_run=subprocess.run;real_read=Path.read_bytes;counter=itertools.count()
def run(command,*a,**kw):
    if isinstance(command,(tuple,list)):
        command=list(command)
        for i,v in enumerate(command):
            p=Path(str(v))
            if p.suffix=='.cpp' and p.is_file():
                text=p.read_text()
                if 'OLMDirectionalBlur.cpp' in text:
                    dest=S/f'host{next(counter)}.cpp';dest.write_text(rewrite(text,p.parent));command[i]=str(dest)
    return real_run(command,*a,**kw)
subprocess.run=run
Path.read_bytes=lambda p:original[p] if p in original else real_read(p)
sys.path.insert(0,str(ROOT))
# Load the base revision's assertions too, so future edits cannot change this
# diagnostic. Keep __file__ at the real test location for its resource paths.
pattern=sys.argv[1] if len(sys.argv)>1 else 'test_directionalblur_*.py'
suite=unittest.TestSuite()
for path in sorted((ROOT/'tests').glob(pattern)):
    if 'general_feature_budget' in path.name:continue
    code=subprocess.check_output(['git','show',f'{BASE}:{path.relative_to(ROOT)}'],cwd=ROOT,text=True)
    module=types.ModuleType(path.stem);module.__file__=str(path)
    sys.modules[path.stem]=module
    exec(compile(code,str(path),'exec'),module.__dict__)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
result=unittest.TextTestRunner(verbosity=1).run(suite)
sys.exit(not result.wasSuccessful())
