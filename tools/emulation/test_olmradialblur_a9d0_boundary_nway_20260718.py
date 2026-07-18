#!/usr/bin/env python3
"""Structural and synthetic tests for the N-way RadialBlur fork runner."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/emulation/run_olmradialblur_a9d0_boundary_nway_20260718.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("radial_boundary_nway_20260718", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    runner = load_runner()
    assert runner.partition_rows(721, 1800, 8) == [
        (721, 856), (856, 991), (991, 1126), (1126, 1261),
        (1261, 1396), (1396, 1531), (1531, 1666), (1666, 1800),
    ]
    for invalid in ((3, 3, 2), (3, 8, 7), (3, 5, 0), (3, 5, 6)):
        try:
            runner.partition_rows(*invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid partition accepted: {invalid}")

    contract = {
        "width": 2,
        "pointers": {"output_rgba": 1000, "output_scalar": 1016},
    }
    assert runner.load_base().owned_ranges(contract, 1, 3) == [
        (1032, 1096), (1024, 1040)
    ]
    base = bytes(range(32))
    changed = bytearray(base)
    changed[8:12] = b"ABCD"
    assert runner.load_base().outside_owned_equal(base, changed, 0, [(8, 12)])
    changed[12] ^= 1
    assert not runner.load_base().outside_owned_equal(base, changed, 0, [(8, 12)])

    command = runner.nway_runner_command(
        runner.load_base(), Path("/tmp/input.aexcp"), Path("/tmp/result.aexcp"),
        Path("/tmp/olmradialblur_a9d0_boundary_nway_20260718"), 7, 12,
    )
    assert command[command.index("--save-checkpoint-at-rip") + 1] == "/tmp/result.aexcp"
    assert command[command.index("--output-json") + 1].endswith("slice_07_runner_20260718.json")
    assert command[command.index("--output-md") + 1].endswith("slice_07_runner_20260718.md")
    assert command[command.index("0x180005c95")] == "0x180005c95"
    old_result = Path("/tmp/olmradialblur_a9d0_boundary_fork_20260718/full_left_result_20260718.aexcp")
    if old_result.exists():
        assert old_result != Path("/tmp/result.aexcp")
    print("PASS_OLMRADIALBLUR_A9D0_BOUNDARY_NWAY_20260718")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
