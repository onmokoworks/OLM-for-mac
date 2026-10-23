#!/usr/bin/env python3
"""Independent PF32 center matrix for C26; original AEX and sanitized layouts."""
import sys
sys.dont_write_bytecode = True
import verify_radialblur_smart_C11 as centers
import verify_radialblur_smart_C06 as verify


def cases(adapter, matrix=None):
    centers.ALL_DEPTHS = True
    for case in centers.cases(adapter):
        if case['depth'] == 32:
            yield case


if __name__ == '__main__':
    verify.independent_cases = cases
    raise SystemExit(verify.main())
