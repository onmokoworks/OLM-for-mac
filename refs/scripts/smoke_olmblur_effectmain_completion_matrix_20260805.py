#!/usr/bin/env python3
"""Audit the OLMBlur command/dispatch/parameter completion matrix."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "refs/conformance/olmblur_effectmain_completion_matrix_20260805.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    assert [row["command"] for row in matrix["public_commands"]] == [
        "PF_Cmd_ABOUT", "PF_Cmd_GLOBAL_SETUP", "PF_Cmd_PARAMS_SETUP",
        "PF_Cmd_RENDER", "PF_Cmd_SMART_PRE_RENDER", "PF_Cmd_SMART_RENDER"]
    cells = {(row["bit_depth"], row["legacy"]): row
             for row in matrix["render_cells"]}
    assert set(cells) == {(depth, legacy) for depth in (8, 16, 32)
                          for legacy in (0, 1)}
    assert all(row["actual_worker_exact"] for row in cells.values())
    assert {key for key, row in cells.items()
            if row["production_blur_render_dispatch_exact"]} == {
                (8, 0), (8, 1), (16, 0), (16, 1), (32, 0), (32, 1)}
    closed = matrix["newly_closed"]
    assert sha256(ROOT / closed["actual_fixture_manifest"]) == closed["manifest_sha256"]
    assert sha256(ROOT / closed["production_source"]) == closed["production_source_sha256"]
    assert sha256(ROOT / closed["regression"]) == closed["regression_sha256"]
    subprocess.run([sys.executable, closed["regression"]], cwd=ROOT, check=True)
    subsequent = matrix["subsequently_closed"]
    assert sha256(ROOT / subsequent["actual_fixture_manifest"]) == subsequent["manifest_sha256"]
    assert sha256(ROOT / subsequent["production_source"]) == subsequent["production_source_sha256"]
    assert sha256(ROOT / subsequent["regression"]) == subsequent["regression_sha256"]
    subprocess.run([sys.executable, subsequent["regression"]], cwd=ROOT, check=True)
    latest = matrix["latest_closed"]
    assert sha256(ROOT / latest["actual_fixture_manifest"]) == latest["manifest_sha256"]
    assert sha256(ROOT / latest["production_source"]) == latest["production_source_sha256"]
    assert sha256(ROOT / latest["regression"]) == latest["regression_sha256"]
    subprocess.run([sys.executable, latest["regression"]], cwd=ROOT, check=True)
    final = matrix["final_typed_dispatch_closed"]
    assert sha256(ROOT / final["actual_fixture_manifest"]) == final["manifest_sha256"]
    assert sha256(ROOT / final["production_source"]) == final["production_source_sha256"]
    assert sha256(ROOT / final["regression"]) == final["regression_sha256"]
    subprocess.run([sys.executable, final["regression"]], cwd=ROOT, check=True)
    smart = matrix["production_effectmain_smart_chain"]
    assert sha256(ROOT / smart["regression"]) == smart["regression_sha256"]
    assert sha256(ROOT / smart["fixture"] / "source_argb.bin") == smart["source_sha256"]
    assert sha256(ROOT / smart["fixture"] / "expected_argb.bin") == smart["expected_sha256"]
    subprocess.run([sys.executable, smart["regression"]], cwd=ROOT, check=True)
    subprocess.run([sys.executable,
                    "tools/emulation/test_olmblur_32bpc_source_aex_adapter_20260717.py"],
                   cwd=ROOT, check=True)
    print("[OK] OLMBlur completion matrix: all PF8/PF16/PF32 Legacy and NonLegacy worker and BlurRender dispatch cells exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
