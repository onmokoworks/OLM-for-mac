#!/usr/bin/env python3
"""Verify migrated compiler arguments against the R03 starting revision."""
import ast,subprocess
from pathlib import Path
BASE='f40209b85623dfeef32b650fa1d004f5c857ef99'
paths=subprocess.check_output(['git','diff',BASE,'--name-only'],text=True).splitlines()
count=0;bad=[]
def commands(t):
 result=[]
 for n in ast.walk(t):
  if not isinstance(n,(ast.List,ast.Tuple)) or not n.elts:continue
  v=n.elts[0]
  if isinstance(v,ast.Name) and v.id=='_UCRT_CXX':result.append(n.elts)
 return result
for name in paths:
 if not name.endswith('.py') or name=='tools/ucrt_cxx.py':continue
 s=Path(name).read_text();t=ast.parse(s);new=commands(t)
 if not new:continue
 old=ast.parse(subprocess.check_output(['git','show',BASE+':'+name],text=True))
 checks=lambda tree:[ast.dump(n) for n in ast.walk(tree) if isinstance(n,ast.Assert) or (isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert'))]
 if checks(t)!=checks(old):bad.append((name,0,'changed assertions'))
 oldlists=[n.elts for n in ast.walk(old) if isinstance(n,(ast.List,ast.Tuple)) and n.elts]
 for vals in new:
  count+=1
  # Original remainder must exist in old AST, with only the compiler prefix changed.
  skip=3 if len(vals)>1 and isinstance(vals[1],ast.Constant) and vals[1].value=='--compiler' else 2 if len(vals)>1 and isinstance(vals[1],ast.Constant) and vals[1].value=='--xcrun' else 1
  tail=[ast.dump(x) for x in vals[skip:]]
  matches=[a for a in oldlists if [ast.dump(x) for x in a[2 if isinstance(a[0],ast.Constant) and a[0].value=='xcrun' else 1:]]==tail]
  if not matches:bad.append((name,vals[0].lineno,'changed compiler arguments'))
  elif skip==3 and not any(ast.dump(a[0])==ast.dump(vals[2]) for a in matches):bad.append((name,vals[0].lineno,'changed selected compiler'))
print('Checked',count,'compiler command tails; problems:',bad)

assert not bad, bad
