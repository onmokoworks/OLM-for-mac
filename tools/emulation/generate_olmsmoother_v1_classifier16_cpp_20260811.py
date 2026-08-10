#!/usr/bin/env python3
"""Generate the direct-threaded PF16 classifier from its pinned CFG."""
from pathlib import Path
import generate_olmsmoother_v1_subhandler8_cpp_20260805 as gen

ROOT=Path(__file__).resolve().parents[2]
gen.SRC=ROOT/'refs/conformance/olmsmoother_v1_classifier16_cfg_20260811.json'
gen.OUT=ROOT/'mac/OLMSmoother/Mac/OLMSmoother_classifier16.generated.inc'
gen.EXPECTED_LINEAR=1724; gen.EXPECTED_UNIQUE=1724
gen.COLOR_COMPARE_TARGET=0x1800021F0
gen.COLOR_COMPARE_EXPR='ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)'
gen.RET_STMT='return (int32_t)R.rax;'

if __name__=='__main__':
    gen.main()
    # Keep the generated subtraction tokenizable by Clang (hex literal
    # immediately followed by '-' is parsed as an invalid pp-number).
    text=gen.OUT.read_text().replace('0x180007d9e-0x7d9eull','0x180007d9e - 0x7d9eull')
    gen.OUT.write_text(text)
