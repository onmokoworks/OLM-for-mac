#!/usr/bin/env python3
"""Focused smoke for the bounded second-leaf diagnostic contract."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/probe_smoother2_case0012_second_leaf_20260716.py"
ADAPTER_SOURCE = ROOT / "tools/emulation/smoother2_case0012_second_leaf_adapter_20260716.cpp"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_second_leaf_") as temp:
        adapter = Path(temp) / "second_leaf_adapter"
        output = Path(temp) / "second_leaf.json"
        build = subprocess.run(
            ["clang++", "-std=c++17", "-O2", "-I", "cli/OLMSmoother2/shim", "-I", "mac/OLMSmoother2", str(ADAPTER_SOURCE), "-o", str(adapter)],
            cwd=ROOT, text=True, capture_output=True,
        )
        if build.returncode != 0:
            print(build.stdout, end="")
            print(build.stderr, end="", file=sys.stderr)
            return build.returncode
        result = subprocess.run(
            [sys.executable, str(PROBE), "--adapter", str(adapter), "--output", str(output)],
            cwd=ROOT, text=True, capture_output=True,
        )
        if result.returncode != 0:
            print(result.stdout, end="")
            print(result.stderr, end="", file=sys.stderr)
            return result.returncode
        data = json.loads(output.read_text(encoding="utf-8"))
    assert data["verdict"] == "PASS_MAC_CASE0012_SECOND_LEAF_BOUNDARY"
    assert data["binding"]["descriptor"] == [92, 841, 1, 92, 842, 2]
    assert data["binding"]["accepted_e170"] == 7
    assert data["binding"]["accepted_first_count"] == 1
    assert data["comparison"]["accepted_case_id"] is True
    assert data["comparison"]["accepted_descriptor"] is True
    assert data["comparison"]["accepted_e170"] is True
    assert data["comparison"]["accepted_first_count"] is True
    assert data["aex"]["trace"]["first_leaf"]["count_after"] == 1
    assert data["aex"]["trace"]["second_leaf"]["count_before"] == 1
    assert data["aex"]["trace"]["second_leaf"]["count_after"] == 2
    assert data["aex"]["trace"]["second_leaf"]["append"] is True
    assert data["aex"]["trace"]["second_leaf"]["returned_vertex"]["source_xy"] == [92, 843]
    assert data["aex"]["trace"]["second_leaf"]["returned_vertex"]["rgba"] == [0.125, 0.25, 0.75, 0.625]
    assert data["comparison"]["aex_df30_f130_e290_path"] is True
    assert data["comparison"]["aex_portable_rgba_equal"] is True
    assert data["comparison"]["aex_portable_weight_equal"] is True
    assert data["comparison"]["second_append_count_one_to_two"] is True
    assert data["aex"]["trace"]["dispatcher"] == {"name": "fef0", "key": 0x14, "count_after": 2}
    assert data["portable"]["dispatcher"] == {"name": "fef0", "key": 0x14, "count_after": 2}
    print("PASS: case0012 second-leaf binding, path, payload, weight, and count contract")
    print("accepted descriptor selects fef0 key 0x14; AEX/portable df30->f130->e290 payload and count=2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
