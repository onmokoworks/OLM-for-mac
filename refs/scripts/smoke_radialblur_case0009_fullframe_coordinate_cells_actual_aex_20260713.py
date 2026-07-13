#!/usr/bin/env python3
"""Static smoke for the RadialBlur coordinate/cell actual-AEX probe."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/probe_radialblur_case0009_fullframe_coordinate_cells_actual_aex_20260713.py"
EVIDENCE = ROOT / "refs/conformance/olmradialblur_case0009_fullframe_coordinate_cells_actual_aex_20260713.json"


def main() -> int:
    source = PROBE.read_text(encoding="utf-8")
    ast.parse(source)
    for token in ("FUN_18000A850", "FUN_180009D80", "cell_selection", "prefill_scope"):
        assert token in source, token
    if EVIDENCE.exists():
        data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        assert data["kind"] == "olmradialblur_case0009_fullframe_coordinate_cells_actual_aex_probe"
        assert data["prefill_scope"].startswith("opaque actual-AEX")
        assert data["target_windows_alpha_254_x"] == [6, 7, 12]
        assert data["direct_d80_subunit_alpha_x"] == [6, 10, 13]
        assert data["target_x_direct_d80_alpha_one"] == [7, 12]
        assert data["audit_verdict"] == "not_proven_coordinate_or_cell_selection_residual_source"
        assert "probe does not provide same-point Mac coordinate/cell evidence" in data["audit_basis"]
        assert len(data["points"]) == 32
        assert all(point["entry_reached"] for point in data["points"])
        assert all(point["cell_selection"]["cells"] for point in data["points"])
    print("smoke_radialblur_case0009_fullframe_coordinate_cells_actual_aex_20260713=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
