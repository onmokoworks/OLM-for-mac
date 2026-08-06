#!/usr/bin/env python3
"""Compare generated portable SubHandler8 against the original AEX."""
import ctypes, hashlib, json, struct, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/emulation'))
from aex_loader import AexLoader

AEX=ROOT/'plugins_2025/OLMSmoother.aex'
SHA='6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82'
ENTRY=0x1800033d0
DIRS=(5,3,1,7)
LIB=Path('/tmp/olmsmoother_subhandler8_generated.dylib')

def build():
 subprocess.run(['clang++','-std=c++17','-fPIC','-shared','-I'+str(ROOT/'cli/OLMSmoother/shim'),
  str(ROOT/'tools/emulation/olmsmoother_v1_classifier8_ctypes_harness_20260805.cpp'),'-o',str(LIB)],check=True)

def oracle_fixture(loader,raw):
 w=h=7;pix=loader.host_alloc(len(raw),align=16);loader.write_bytes(pix,raw)
 world=loader.host_alloc(0x40,align=16);loader.write_bytes(world,b'\0'*0x40)
 loader.write_bytes(world+4,struct.pack('<iii',w,h,w*4));loader.write_bytes(world+0x10,struct.pack('<Q',pix))
 loader.write_bytes(world+0x18,struct.pack('<Qiii',pix,w*4,w,h))
 state=loader.host_alloc(0x80,align=16);loader.write_bytes(state,b'\0'*0x80)
 loader.write_bytes(state+8,struct.pack('<ii',6,6));loader.write_bytes(state+0x10,struct.pack('<Q',world));loader.write_bytes(state+0x24,struct.pack('<i',6))
 x=y=3;ps=[pix+((y+dy)*w+x+dx)*4 for dy in(-1,0,1) for dx in(-1,0,1)]
 neigh=loader.host_alloc(72,align=16);loader.write_bytes(neigh,struct.pack('<9Q',*ps))
 outs=[loader.host_alloc(4,align=4) for _ in range(9)]
 return state,neigh,x,y,outs

def main():
 assert hashlib.sha256(AEX.read_bytes()).hexdigest()==SHA
 build();dll=ctypes.CDLL(str(LIB));fn=dll.olmsmoother_subhandler8
 fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_uint32,ctypes.c_int32,ctypes.POINTER(ctypes.c_uint32)]
 loader=AexLoader(str(AEX),verbose=False,fast=True);mismatches=[]
 for mask in range(512):
  raw=bytes(sum(([255,255 if mask>>((y%3)*3+x%3)&1 else 0,0,0] for y in range(7) for x in range(7)),[]))
  for direction in DIRS:
   state,neigh,x,y,outs=oracle_fixture(loader,raw)
   loader.call_function(ENTRY,[state,neigh,x,y,direction,*outs],max_instructions=500000)
   actual=[struct.unpack('<I',loader.read_bytes(p,4))[0] for p in outs]
   buf=(ctypes.c_uint8*len(raw)).from_buffer_copy(raw);got=(ctypes.c_uint32*9)()
   fn(buf,7,7,3,3,direction,6,got);portable=list(got)
   if actual!=portable:mismatches.append((mask,direction,actual,portable))
 result={'status':'exact' if not mismatches else 'fail','calls':2048,'mismatch_count':len(mismatches),'first':mismatches[:3]}
 print(json.dumps(result,indent=2));assert not mismatches

if __name__=='__main__':main()
