"""Rebuild the original warp header in a private source snapshot; compare 50 hashes."""
import hashlib,json,os,shutil,subprocess,sys,time,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/fuzz'))
sys.dont_write_bytecode=True
from adapters.olmkirakira import Adapter,SOURCE
S=ROOT/'orchestra/state/P07a-parallel-helper-kirakira/original';S.mkdir(parents=True,exist_ok=True)
snapshot=S/'source';snapshot.mkdir(exist_ok=True)
shutil.copytree(ROOT/'core',snapshot/'core',dirs_exist_ok=True)
shutil.copytree(ROOT/'mac/OLMKiraKira',snapshot/'mac/OLMKiraKira',dirs_exist_ok=True)
if not (snapshot/'ucrtmath').exists():(snapshot/'ucrtmath').symlink_to(ROOT/'ucrtmath')
(snapshot/'core/kirakira_warp.h').write_bytes(subprocess.check_output(['git','show','c101e2880a4b423e5e285c36baf120cbedd609b3:core/kirakira_warp.h'],cwd=ROOT))
o=types.SimpleNamespace(max_size=256,case_timeout=60,main=(ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT),worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker')
a=Adapter(o);a.env.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
original_compile=a.compile_sdk
original_source=snapshot/'mac/OLMKiraKira/OLMKiraKira.cpp'
def compile_sdk(scratch,body,source,deadline,cores=()):
 return original_compile(scratch,body.replace(str(SOURCE),str(original_source)),original_source,deadline,cores)
a.compile_sdk=compile_sdk
a.binary,_=a.build(S,time.monotonic()+180)
expected=json.loads((S.parent/'threads/results.json').read_text())
results=[]
for index in range(50):
 case=a.generate(20261025,index)
 if index%2==0:
  w,h=case['geometry'];pixels=case['pixels'];n=257*259*case['depth']//8*4
  case['geometry']=[257,259];case['pixels']=(pixels*((n+len(pixels)-1)//len(pixels)))[:n];a.resize(case,[w,h])
 d=S/f'case-{index}';d.mkdir(exist_ok=True)
 result,raw,*_=a.candidate(case,d,'smart',time.monotonic()+90)
 sha=hashlib.sha256(raw).hexdigest()
 assert result['status']=='ok' and sha==expected[index]['runs'][0]['sha256'],(index,result,sha)
 results.append(dict(index=index,sha256=sha))
(S/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print('Original header: 50/50 exact against candidate task caps 1/2/8 and TSan')
