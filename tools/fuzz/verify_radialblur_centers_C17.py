#!/usr/bin/env python3
"""Recheck the unpromoted PF16 Rotation center matrix with C11's original inputs."""
import sys
sys.dont_write_bytecode = True
import verify_radialblur_smart_C11 as centers
import verify_radialblur_smart_C06 as verify
centers.ALL_DEPTHS = True

def cases(adapter, matrix=None):
    for case in centers.cases(adapter):
        if case['depth'] == 16 and next(p['value'] for p in case['parameters'] if p['slot']==1) == 2:
            yield case

if __name__ == '__main__':
    verify.independent_cases = cases
    raise SystemExit(verify.main())
