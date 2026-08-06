#!/usr/bin/env python3
import hashlib,json,struct,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/emulation'));from aex_loader import AexLoader
AEX=ROOT/'plugins_2025/OLMSmoother.aex';SHA='6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82';SOURCE=ROOT/'refs/win_references/20260604_olm/OLMSmoother/case_0001_before_effects.png';OUT=ROOT/'refs/conformance/olmsmoother_v1_case0001_pf8_subhandler_20260805.json';ENTRY=0x1800033D0
CASES=[(464,170,5),(495,170,3),(459,171,5),(500,171,3)]
def main():
 assert hashlib.sha256(AEX.read_bytes()).hexdigest()==SHA
 im=Image.open(SOURCE).convert('RGBA');w,h=im.size;raw=bytearray()
 for r,g,b,a in im.getdata():raw+=bytes((a,r,g,b))
 l=AexLoader(str(AEX),verbose=False,fast=True);pix=l.host_alloc(len(raw),align=16);l.write_bytes(pix,bytes(raw));world=l.host_alloc(0x40,align=16);l.write_bytes(world,b'\0'*0x40);l.write_bytes(world+4,struct.pack('<iii',w,h,w*4));l.write_bytes(world+0x10,struct.pack('<Q',pix));state=l.host_alloc(0x80,align=16);l.write_bytes(state,b'\0'*0x80);l.write_bytes(state+8,struct.pack('<ii',6,6));l.write_bytes(state+0x10,struct.pack('<Q',world));l.write_bytes(state+0x24,struct.pack('<i',6))
 reports=[]
 for x,y,d in CASES:
  ps=[pix+((y+dy)*w+x+dx)*4 for dy in(-1,0,1) for dx in(-1,0,1)];n=l.host_alloc(72,align=16);l.write_bytes(n,struct.pack('<9Q',*ps));outs=[l.host_alloc(4,align=4) for _ in range(9)];[l.write_bytes(p,b'\xcc'*4) for p in outs]
  res=l.call_function(ENTRY,[state,n,x,y,d,*outs],max_instructions=500000);vals=[struct.unpack('<I',l.read_bytes(p,4))[0] for p in outs]
  reports.append({'center':[x,y],'direction':d,'outputs':{'mode':vals[0],'flag_a':vals[1]&255,'flag_b':vals[2]&255,'p9':vals[3:5],'p11':vals[5:7],'p13':vals[7:9]},'instructions':res['instructions']})
 report={'schema_version':1,'status':'captured','actual_aex_sha256':SHA,'input_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'cases':reports};OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
