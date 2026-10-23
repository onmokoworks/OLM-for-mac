#!/usr/bin/env python3
"""Record inputs, source and executable identities alongside completed runs."""
import hashlib,json,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[2]
state=root/'orchestra/state/F28-ucrtmath-lib-amd'
paths=list((root/'ucrtmath').rglob('*.c'))+list((root/'ucrtmath').rglob('*.h'))+list((root/'ucrtmath/tests').glob('*.py'))+list((root/'ucrtmath').rglob('*.sh'))
paths += [root/'tools/ucrt_math_probe/rosetta/oracle.c']
paths += [p for d in ['build','survey-build'] for p in (state/d).iterdir() if p.is_file() and p.suffix not in ['.o']]
paths += [pathlib.Path('/Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll')]
paths += list((state/'targeted').glob('*.txt'))
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest()
print(json.dumps({'clang':subprocess.check_output(['clang','--version'],text=True),'sha256':{str(p.relative_to(root)) if p.is_relative_to(root) else str(p):digest(p) for p in sorted(paths)}},indent=2))
