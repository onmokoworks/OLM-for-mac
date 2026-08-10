#!/usr/bin/env python3
"""Compare colored PF16 ColorCompare calls against the actual Windows AEX."""
import ctypes, hashlib, json, random
from pathlib import Path
from aex_loader import AexLoader
import test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810 as base

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'refs/conformance/olmsmoother_v1_colorcompare16_colored_actual_aex_20260811.json'
CALLS=20000

def main():
    temporary,lib=base.build_production()
    try:
        fn=lib.olmsmoother_v1_color_compare16
        fn.argtypes=[ctypes.POINTER(ctypes.c_uint16),ctypes.POINTER(ctypes.c_uint16)]
        fn.restype=ctypes.c_int32
        loader=AexLoader(str(base.AEX),verbose=False,fast=True)
        left=loader.host_alloc(8); right=loader.host_alloc(8)
        rng=random.Random(0x51A001)
        for index in range(CALLS):
            a=tuple(rng.randrange(0x8001) for _ in range(4))
            b=tuple(rng.randrange(0x8001) for _ in range(4))
            aa=(ctypes.c_uint16*4)(*a); bb=(ctypes.c_uint16*4)(*b)
            loader.write_bytes(left,bytes(aa)); loader.write_bytes(right,bytes(bb))
            actual=loader.call_function(0x1800021f0,[left,right],max_instructions=10000)['rax']&0xffffffff
            if actual&0x80000000: actual-=0x100000000
            production=fn(aa,bb)
            assert actual==production,(index,a,b,actual,production)
    finally: temporary.cleanup()
    report={'schema_version':1,'status':'exact','verdict':'PASS_COLORCOMPARE16_COLORED_20000_CALLS_EXACT',
      'actual_aex_sha256':hashlib.sha256(base.AEX.read_bytes()).hexdigest(),'calls':CALLS,
      'domain':'deterministic colored ARGB16 ordered pairs; each component uniform in 0..32768',
      'seed':'0x51a001','closed_rule':'scalar-SSE binary32 boundaries and signed luma conversion toward zero',
      'claims_not_made':['exhaustive 32769^8 tuples','full PF16 render exactness','PF32']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(report['verdict'])

if __name__=='__main__': main()
