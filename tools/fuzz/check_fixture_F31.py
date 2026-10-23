#!/usr/bin/env python3
"""Recapture the first failing historical DirectionalBlur fixture under F30."""
import hashlib,json,os,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/F31-port-ucrtmath-switch-oracle/fixture137'
S.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_directionalblur_general_features_20261001 as probe
import probe_directionalblur_fixed_getter_20261001 as fixed
case=json.loads((ROOT/'reports/directionalblur_general_features_candidate_20261001.json').read_text())['cases'][137]
w,h=case['geometry'];data=probe.owner.typed(probe.owner.pixels(w,h,True),case['depth'])
sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha(data)==case['input_sha256']
(S/'input.raw').write_bytes(data)
worker=Path.home()/'.cache/olm-emu/worker-F30-ucrtmath/aex-guest-worker'
aex=Path('/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/OLMDirectionalBlur.aex')
request=json.dumps({'v':4,'type':'render_frame','frame_index':0,'current_time':{'value':0,'scale':24,'step':1,'total':1},'parameters':case['parameter_payload']}).encode()
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_UCRT_FMA='1')
for pattern in ('output.raw*','fixture-*.bin'):
    for old in S.glob(pattern):old.unlink()
run=subprocess.run([str(worker),'session',str(aex),str(S/'input.raw'),str(S/'output.raw'),str(w),str(h),'24','--pixel-format','argb32f','--fixture-render-path','smart'],input=struct.pack('<I',len(request))+request,capture_output=True,env=env,timeout=30)
(S/'worker.log').write_bytes(run.stderr)
assert run.returncode==0
raw=(S/'output.raw').read_bytes()
messages=[];pos=0
while pos<len(run.stdout):
    n=struct.unpack_from('<I',run.stdout,pos)[0];pos+=4
    messages.append(json.loads(run.stdout[pos:pos+n]));pos+=n
frame=next(m for m in messages if m['type']=='frame_done')
assert frame['status']=='ok' and frame['render_error']==0 and frame['output']['guards_intact']
assert frame['output']['checksum']==sha(raw)
(S/'bin').mkdir(exist_ok=True)
link=S/'bin/clang++'
if not link.exists():link.symlink_to(ROOT/'tools/ucrt_cxx.py')
os.environ.update(env)
os.environ['PATH']=str(S/'bin')+os.pathsep+os.environ['PATH']
fixed.HARNESS=probe.HARNESS
fixed.compile_harness(S/'mac')
params=','.join(f'{slot}={value}' for slot,value in case['parameters'].items())
measured=subprocess.run([str(S/'mac'),str(w),str(h),str(case['depth']),params],input=data,capture_output=True,check=True)
lines=dict(line.split(' ',1) for line in measured.stdout.decode().splitlines())
assert int(lines['PUBLIC_ERROR'])==0 and int(lines['ERROR'])==0
candidate=bytes.fromhex(lines['RAW'])
result={'fixture_index':137,'input_sha256':sha(data),'worker_sha256':sha(worker.read_bytes()),'aex_sha256':sha(aex.read_bytes()),'historical_reference_sha256':case['native_raw_sha256'],'f30_reference_sha256':sha(raw),'measured_f31_candidate_sha256':sha(candidate),'parameters':case['parameters']}
result['f31_exact_f30']=result['f30_reference_sha256']==result['measured_f31_candidate_sha256']
(ROOT/'orchestra/reports/F31-evidence/fixture137.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
assert result['f31_exact_f30'], "Current candidate differs from the original AEX under F30"
