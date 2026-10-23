#!/usr/bin/env python3
"""Retain successful F42 evidence and bind the current build to source hashes."""
import hashlib,json,pathlib,platform,subprocess
root=pathlib.Path(__file__).resolve().parents[2]
state=root/'orchestra/state/F42-ucrtmath-ms-float'
out=root/'ucrtmath/ms/results';out.mkdir(exist_ok=True)
for kind,count in [('targeted',106167),('full',2**32)]:
 for fn in ['sinf','cosf','log2f']:
  name=f'{kind}-{fn}.json';data=json.loads((state/name).read_text())
  assert data['function']==fn and data['count']==count
  assert len(data['modes'])==2
  for mode,row in enumerate(data['modes']):
   assert row['mode']==mode and row['mismatches']==0
   assert row['first_a_b_oracle_native']==['00000000']*4
  (out/name).write_text(json.dumps(data,indent=2)+'\n')
for fn,count in [('expf',8128),('atan2f',13779),('powf',79201)]:
 name=f'regression-{fn}.json'; data=json.loads((state/name).read_text())
 assert data['function']==fn and data['count']==count
 assert all(row['mismatches']==0 for row in data['modes'])
 (out/name).write_text(json.dumps(data,indent=2)+'\n')
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
paths=[root/'ucrtmath/build.sh',root/'ucrtmath/tests/build.sh',root/'ucrtmath/tests/targeted.py',root/'ucrtmath/tests/native.c',root/'ucrtmath/tests/compare.c',root/'ucrtmath/include/ucrtmath.h',root/'tools/ucrt_math_probe/rosetta/oracle.c']
paths+=sorted((root/'ucrtmath/src').glob('*'))
paths+=sorted(p for p in (root/'ucrtmath/ms').glob('*') if p.suffix in ['.c','.h','.py'])
identity={'platform':platform.platform(),'compiler':subprocess.check_output(['clang','--version'],text=True).splitlines(),
 'source_sha256':{str(p.relative_to(root)):sha(p) for p in paths if p.is_file()},
 'build_sha256':{name:sha(state/'build'/name) for name in ['native','compare','libucrtmath.a']},
 'dll_sha256':sha(pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'),
 'targets_sha256':sha(state/'targets.txt'),
 'full_input_order':'unsigned words 0 through 4294967295, each compared in modes 0 and 1',
 'contract':'raw binary32 return bits; RN; gradual underflow; no errno/exception-flags claim'}
(out/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
print('Retained six F42 campaigns, three F28 regressions, and build/source identity.')
