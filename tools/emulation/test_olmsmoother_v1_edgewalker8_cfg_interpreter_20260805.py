#!/usr/bin/env python3
"""Independent CFG interpreter gate for FUN_180009e30 (EdgeWalker8)."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/emulation'))
from aex_loader import AexLoader
import test_olmsmoother_v1_subhandler8_cfg_interpreter_20260805 as core
AEX=ROOT/'plugins_2025/OLMSmoother.aex';SHA='6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82';CFG=ROOT/'refs/conformance/olmsmoother_v1_edgewalker8_cfg_20260805.json';ENTRY=0x180009e30;DIRS=(5,3,1,7);OPPOSITE=(8,7,6,5,4,3,2,1,0)
def fixture(l,mask):
 w=h=7;raw=bytearray()
 for y in range(h):
  for x in range(w):
   i=(y%3)*3+(x%3);raw+=bytes((255,255 if mask>>i&1 else 0,0,0))
 pix=l.host_alloc(len(raw),align=16);l.write_bytes(pix,bytes(raw));world=l.host_alloc(0x40,align=16);l.write_bytes(world,b'\0'*0x40);l.write_bytes(world+4,struct.pack('<iii',w,h,w*4));l.write_bytes(world+0x10,struct.pack('<Q',pix));l.write_bytes(world+0x18,struct.pack('<Qiii',pix,w*4,w,h));state=l.host_alloc(0x80,align=16);l.write_bytes(state,b'\0'*0x80);l.write_bytes(state+0x10,struct.pack('<Q',world));ox=l.host_alloc(4,align=4);oy=l.host_alloc(4,align=4);return state,ox,oy
def main():
 assert hashlib.sha256(AEX.read_bytes()).hexdigest()==SHA;D=json.loads(CFG.read_text());I={int(i['address'],0):i for b in D['blocks'] for i in b['instructions']};l=AexLoader(str(AEX),verbose=False,fast=True);core.ENTRY=ENTRY;mis=[]
 for mask in range(512):
  for d in DIRS:
   state,ox,oy=fixture(l,mask);args=[state,3,3,d,OPPOSITE[d],ox,oy,6];l.write_bytes(ox,b'\xcc'*4);l.write_bytes(oy,b'\xcc'*4);a=l.call_function(ENTRY,args,max_instructions=500000);actual=[a['rax'],l.read_bytes(ox,4),l.read_bytes(oy,4)];l.write_bytes(ox,b'\xcc'*4);l.write_bytes(oy,b'\xcc'*4);m=core.M(l,I,args);m.run();got=[m.r['rax'],l.read_bytes(ox,4),l.read_bytes(oy,4)]
   if actual!=got:mis.append((mask,d,[actual[0],actual[1].hex(),actual[2].hex()],[got[0],got[1].hex(),got[2].hex()]))
 print(json.dumps({'status':'exact' if not mis else 'fail','calls':2048,'mismatch_count':len(mis),'first':mis[:3]},indent=2));assert not mis
if __name__=='__main__':main()
