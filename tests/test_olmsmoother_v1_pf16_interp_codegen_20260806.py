#!/usr/bin/env python3
"""Static fail-closed checks for PF16 interpolation extraction/codegen."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"


def check(name, count, generated):
    cfg = json.loads((ROOT / f"refs/conformance/olmsmoother_v1_{name}_cfg_20260806.json").read_text())
    assert cfg["aex_sha256"] == SHA
    unique = {ins["address"] for block in cfg["blocks"] for ins in block["instructions"]}
    assert len(unique) == cfg["instruction_count"] == count
    text = (ROOT / "mac/OLMSmoother/Mac" / generated).read_text()
    assert text.count("OLM_PF16_") == count + 1  # one header comment
    return cfg, text


def main():
    assert hashlib.sha256((ROOT / "plugins_2025/OLMSmoother.aex").read_bytes()).hexdigest() == SHA
    main_cfg, main_cpp = check("mainkernel16", 617, "OLMSmoother_mainkernel16.generated.inc")
    exec_cfg, exec_cpp = check("executor16", 188, "OLMSmoother_executor16.generated.inc")
    assert main_cfg["range"] == ["0x180004b80", "0x18000556f"]
    assert exec_cfg["range"] == ["0x180005f60", "0x180006263"]
    assert main_cpp.count(", ColorCompare16)") == 8
    assert main_cpp.count(", InterpExecutor16Exact)") == 5
    assert main_cpp.count(", ColorBlend16)") == 2
    assert main_cpp.count(", NeighborExtract16)") == 1
    assert exec_cpp.count(", AlphaBlend16)") == 2
    assert exec_cpp.count("OLM_PF16_CALL_INDIRECT") == 1
    assert re.search(r"OLM_PF16_INSN\([^\n]+movzx, \"eax, word ptr \[r10\]\"", exec_cpp)
    assert "OLM_PF16_INSN(0x180006089, nop" in exec_cpp
    syntax = """
#define OLM_PF16_INSN(...)
#define OLM_PF16_BRANCH(...)
#define OLM_PF16_CALL(...)
#define OLM_PF16_CALL_INDIRECT(...)
#define OLM_PF16_RET(...)
#include \"mac/OLMSmoother/Mac/OLMSmoother_mainkernel16.generated.inc\"
#include \"mac/OLMSmoother/Mac/OLMSmoother_executor16.generated.inc\"
int main() { return 0; }
"""
    subprocess.run(["clang++", "-std=c++17", "-fsyntax-only", "-x", "c++", "-"],
                   cwd=ROOT, input=syntax, text=True, check=True)
    print("PASS PF16 interpolation CFG/codegen: 805 instructions, helper mapping exact")


if __name__ == "__main__":
    main()
