#!/usr/bin/env python3
"""Exhaust the PF8 grayscale/key ColorCompare caller domain."""
import ctypes, hashlib, json
from pathlib import Path
from aex_loader import AexLoader
import test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810 as base

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'refs/conformance/olmsmoother_v1_colorcompare8_grayscale_actual_aex_20260810.json'

def main():
    temporary,lib=base.build_production()
    try:
        fn=lib.olmsmoother_v1_color_compare8
        fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.POINTER(ctypes.c_uint8)]
        fn.restype=ctypes.c_int32
        loader=AexLoader(str(base.AEX),verbose=False,fast=True)
        left=loader.host_alloc(4); right=loader.host_alloc(4)
        colors=[(255,v,v,v) for v in range(256)]+[(255,*base.KEY)]
        calls=0
        for a in colors:
            aa=(ctypes.c_uint8*4)(*a); loader.write_bytes(left,bytes(a))
            for b in colors:
                loader.write_bytes(right,bytes(b)); bb=(ctypes.c_uint8*4)(*b)
                actual=loader.call_function(0x180002430,[left,right],max_instructions=10000)['rax']&0xffffffff
                if actual&0x80000000: actual-=0x100000000
                assert actual==fn(aa,bb),(a,b,actual,fn(aa,bb))
                calls+=1
    finally: temporary.cleanup()
    report={'schema_version':1,'status':'exact','verdict':'PASS_COLORCOMPARE8_GRAYSCALE_KEY_66049_CALLS_EXACT',
      'actual_aex_sha256':hashlib.sha256(base.AEX.read_bytes()).hexdigest(),'calls':calls,
      'domain':'ordered pairs of all opaque grayscale RGB 0..255 plus key RGB (202,187,230)',
      'closed_rule':'scalar-SSE binary32 boundaries and signed luma conversion toward zero',
      'claims_not_made':['arbitrary RGB/alpha tuples']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(report['verdict'])
if __name__=='__main__':main()
