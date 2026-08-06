#!/usr/bin/env python3
"""Generate portable direct-threaded EdgeWalker8 from its validated CFG."""
from pathlib import Path
import generate_olmsmoother_v1_subhandler8_cpp_20260805 as gen
ROOT=Path(__file__).resolve().parents[2]
gen.SRC=ROOT/'refs/conformance/olmsmoother_v1_edgewalker8_cfg_20260805.json'
gen.OUT=ROOT/'mac/OLMSmoother/Mac/OLMSmoother_edgewalker8.generated.inc'
gen.EXPECTED_LINEAR=379
gen.EXPECTED_UNIQUE=379
gen.RET_STMT='return (uint8_t*)(uintptr_t)R.rax;'
if __name__=='__main__':gen.main()
