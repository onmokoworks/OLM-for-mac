#!/usr/bin/env python3
"""Bounded static contract test for the Radial natural progress runner."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/emulation/run_radialblur_natural_progress_hook_20260718.py"
AUDIT = ROOT / "tools/emulation/audit_radialblur_natural_sampler_strategy_20260718.py"
DISASM = ROOT / "disasm/OLMRadialBlur.aex.asm.txt"


def constants(path: Path) -> dict[str, int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, int):
                    result[target.id] = node.value.value
    return result


def main() -> int:
    runner_text = RUNNER.read_text(encoding="utf-8")
    audit_text = AUDIT.read_text(encoding="utf-8")
    disasm_text = DISASM.read_text(encoding="utf-8")
    runner = constants(RUNNER)
    audit = constants(AUDIT)

    expected = {
        "WORKER_CELL_COMPLETION_BEFORE_INCREMENT": 0x18000B0B4,
        "WORKER_CELL_PROGRESS_AFTER_INCREMENT": 0x18000B0B7,
        "WORKER_ROW_STORE": 0x18000B0F1,
        "WORKER_ROW_PROGRESS_AFTER_STORE": 0x18000B0F9,
    }
    assert all(runner.get(name) == value for name, value in expected.items())
    assert audit["CELL_COMPLETION_BEFORE_INCREMENT"] == expected["WORKER_CELL_COMPLETION_BEFORE_INCREMENT"]
    assert audit["CELL_PROGRESS_AFTER_INCREMENT"] == expected["WORKER_CELL_PROGRESS_AFTER_INCREMENT"]
    assert audit["ROW_STORE"] == expected["WORKER_ROW_STORE"]
    assert audit["ROW_PROGRESS_AFTER_STORE"] == expected["WORKER_ROW_PROGRESS_AFTER_STORE"]

    assert "choices=(\"cell\", \"row\")" in runner_text
    assert "WORKER_CELL_PROGRESS_AFTER_INCREMENT" in runner_text
    assert "WORKER_ROW_PROGRESS_AFTER_STORE" in runner_text
    assert "original_add_code_hook(loader, hook_address, capture_worker_boundary)" in runner_text
    assert "18000b0b4  INC R14D" in disasm_text
    assert "18000b0b7  DEC R15D" in disasm_text
    assert "18000b0f1  MOV dword ptr [RSP + 0xc8],R11D" in disasm_text
    assert "18000b0f9  MOV dword ptr [RSP + 0x98],R10D" in disasm_text
    assert "0x180005e68" in audit_text

    print("PASS RadialBlur natural progress hook static contract")
    print("cell_hook=0x18000b0b7")
    print("row_hook=0x18000b0f9")
    print("parallel_worker_detour=forbidden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
