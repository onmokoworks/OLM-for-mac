"""Labelled heavy-preset witnesses, including finite float boundary inputs."""
import importlib,json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from core import evaluate,save_corpus
from run import main_checkout
from ae_realism_audit import samples
S=ROOT/'orchestra/state/P05a-directionalblur-performance/witness';S.mkdir(parents=True,exist_ok=True)
E=ROOT/'orchestra/reports/P05a-evidence'
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1')
ad=importlib.import_module('adapters.olmdirectionalblur').Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker',max_size=256,case_timeout=10))
deadline=time.monotonic()+1800
p=ad.prepare(S,deadline);rows=[]
import struct
for i,depth in enumerate([8,16,32,8,16,32]):
 c=ad.generate(2053,i);w,h=(17,11) if i<3 else (32,24)
 c.update(geometry=[w,h],depth=depth,parameters=samples('olmdirectionalblur')[0][9][1]['case']['parameters'],input_padding=0,output_padding=0)
 if depth==8:c['pixels']=bytes((j*31+17)%256 for j in range(w*h*4))
 elif depth==16:c['pixels']=struct.pack('<'+'H'*(w*h*4),*((j*997)%65536 for j in range(w*h*4)))
 else:
  # Public admission accepts finite inputs. Include signed zero/subnormals and
  # moderate HDR; arithmetic nonfinite payloads are covered in float_witness.cpp.
  bits=[0,0x80000000,1,0x80000001,0x00800000,0x3f800000,0xbf800000,0x40000000]
  c['pixels']=b''.join(struct.pack('<I',0x3f800000 if j%4==0 else bits[(j+i)%len(bits)]) for j in range(w*h*4))
 r=evaluate(ad,c,S,deadline,{})
 dst=ROOT/'tests/fuzz_corpus/olmdirectionalblur/P05a-performance';dst.mkdir(parents=True,exist_ok=True)
 save_corpus(dst/f'witness-{i}.json',ad,c,c,r,dict(accepted=[],attempts=0),p)
 rows.append(r);print(i,{k:v['status'] for k,v in r['routes'].items()},flush=True)
(E/'witness.json').write_text(json.dumps(rows,indent=2)+'\n')
