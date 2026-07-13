#!/usr/bin/env python3
"""Static smoke for the A850 downstream actual-AEX probe."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/probe_radialblur_a850_downstream_actual_aex_20260713.py"
EVIDENCE = ROOT / "refs/conformance/olmradialblur_a850_downstream_actual_aex_20260713.json"


def main() -> int:
    ast.parse(PROBE.read_text(encoding="utf-8"))
    text = PROBE.read_text(encoding="utf-8")
    for token in ("FUN_18000A850", "FUN_180009D80", "actual_vs_mirror", "prefill_scope"):
        assert token in text, token
    if EVIDENCE.exists():
        data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        assert data["kind"] == "olmradialblur_a850_downstream_actual_aex_probe"
        assert data["prefill_scope"].startswith("opaque actual-AEX")
        for point in data["points"]:
            assert point["a850"] is not None
            assert point["downstream_indices"] is not None
    print("smoke_radialblur_a850_downstream_actual_aex_20260713=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
