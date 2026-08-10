#!/usr/bin/env python3
"""Pin the PF16 classifier plane for the colored fractional-alpha fixture."""
import ctypes,hashlib,json,struct
from pathlib import Path
from aex_loader import AexLoader
import test_olmsmoother_v1_colored_fractional_alpha_actual_aex_20260811 as colored
import test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810 as base

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'refs/conformance/olmsmoother_v1_classifier16_colored_actual_aex_20260811.json'
ENTRY=0x180006A90

def main():
    temporary,lib=base.build_production(); payload,rowbytes=colored.fixture(16)
    try:
        values=struct.unpack(f'<{len(payload)//2}H',payload)
        source=(ctypes.c_uint16*len(values))(*values)
        fn=lib.olmsmoother_v1_classifier16_matrix
        fn.argtypes=[ctypes.POINTER(ctypes.c_uint16)]+[ctypes.c_int32]*7; fn.restype=ctypes.c_int32
        loader=AexLoader(str(base.AEX),verbose=False,fast=True)
        data=loader.host_alloc(len(payload),align=16); loader.write_bytes(data,payload)
        state=loader.host_alloc(0x80,align=16); loader.write_bytes(state,b'\0'*0x80)
        loader.write_bytes(state+0xC,struct.pack('<i',127))
        calls=0
        for y in range(base.H):
            for x in range(base.W):
                pointers=[]
                for yy,xx in ((y-1,x-1),(y-1,x),(y-1,x+1),(y,x-1),(y,x),(y,x+1),(y+1,x-1),(y+1,x),(y+1,x+1)):
                    pointers.append(0 if xx<0 or xx>=base.W or yy<0 or yy>=base.H else data+yy*rowbytes+xx*8)
                neighbors=loader.host_alloc(80,align=16)
                loader.write_bytes(neighbors,struct.pack('<10Q',*(pointers+[0])))
                for direction in (5,3,1,7):
                    actual=ctypes.c_int32(loader.call_function(ENTRY,[state,x,y,neighbors,direction],max_instructions=100000)['rax']&0xffffffff).value
                    production=fn(source,base.W,base.H,rowbytes,x,y,direction,127)
                    assert actual==production,(x,y,direction,actual,production)
                    calls+=1
    finally: temporary.cleanup()
    report={'schema_version':1,'status':'exact','verdict':'PASS_CLASSIFIER16_COLORED_TOL127_140_CALLS_EXACT',
      'actual_aex_sha256':hashlib.sha256(base.AEX.read_bytes()).hexdigest(),'entry':hex(ENTRY),
      'calls':calls,'domain':'premultiplied colored fractional-alpha 7x5 fixture; tolerance 127; directions 5/3/1/7',
      'closed_stage':'input neighborhood through PF16 classification plane',
      'claims_not_made':['other arbitrary fixtures','kernel accumulator','PF32']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(report['verdict'])

if __name__=='__main__': main()
