#!/usr/bin/env python3
"""Generate direct-threaded PF16 walker/sub-handler from pinned CFGs."""
from pathlib import Path
import generate_olmsmoother_v1_subhandler8_cpp_20260805 as gen

ROOT = Path(__file__).resolve().parents[2]


def configure_common() -> None:
    gen.COLOR_COMPARE_TARGET = 0x1800021F0
    gen.COLOR_COMPARE_EXPR = "ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)"
    gen.EDGE_WALKER_TARGET = 0x180009960
    gen.EDGE_WALKER_EXPR = (
        "EdgeWalker16Exact((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,"
        "(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),"
        "(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38))"
    )


def main() -> None:
    configure_common()
    gen.SRC = ROOT / "refs/conformance/olmsmoother_v1_edgewalker16_cfg_20260806.json"
    gen.OUT = ROOT / "mac/OLMSmoother/Mac/OLMSmoother_edgewalker16.generated.inc"
    gen.EXPECTED_LINEAR = 392; gen.EXPECTED_UNIQUE = 392
    gen.RET_STMT = "return (uint16_t*)(uintptr_t)R.rax;"
    gen.main()

    gen.SRC = ROOT / "refs/conformance/olmsmoother_v1_subhandler16_cfg_20260806.json"
    gen.OUT = ROOT / "mac/OLMSmoother/Mac/OLMSmoother_subhandler16.generated.inc"
    gen.EXPECTED_LINEAR = 963; gen.EXPECTED_UNIQUE = 963
    gen.RET_STMT = "return;"
    gen.main()


if __name__ == "__main__": main()
