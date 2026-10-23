#!/usr/bin/env python3
"""Capture original Smoother's PF16 suite acquisition and legacy allocator flags."""
import json,os,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/F32-smoother-oracle-deep-pixels/deep-probe'
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools/emulation'))
import test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810 as owner
Original=owner.AexLoader
calls=[]
class Traced(Original):
 def install_callback(self,label,handler):
  def wrapped(ld,args):
   if label=='acquire':
    calls.append(dict(callback=label,suite=ld.read_bytes(args[0],64).split(b'\0')[0].decode(),version=args[1]))
   elif label=='new_world':
    calls.append(dict(callback=label,width=args[1],height=args[2],flags=args[3]))
   return handler(ld,args)
  return super().install_callback(label,wrapped)
def main():
 S.mkdir(parents=True,exist_ok=True)
 os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
 owner.AexLoader=Traced;owner.AEX=ROOT.parent.parent/'plugins_2025/OLMSmoother.aex';owner.W=owner.H=3
 raw,_=owner.actual(16,struct.pack('<4H',32768,1234,5678,9012)*9,24,1,6,owner.guest_code(S,8))
 result=dict(selector=11,selector_name='PF_Cmd_RENDER',calls=calls,output_bytes=len(raw))
 (S.parent/'deep-callbacks.json').write_text(json.dumps(result,indent=2)+'\n')
 print(result)
 assert any(c.get('flags',0)&2 for c in calls)
if __name__=='__main__':main()
