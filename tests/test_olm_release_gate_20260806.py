#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_olm_release_gate_20260806.py"
spec = importlib.util.spec_from_file_location("release_gate", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> int:
    manifest = json.loads(module.MANIFEST.read_text(encoding="utf-8"))
    rows = module.validate_host_rows(manifest)
    assert len(rows) == 10
    assert {row["plugin"] for row in rows} == {
        "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
        "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
        "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
    }
    assert not [row for row in rows if row["state"] == "invalid"]
    assert not [row for row in rows if row["state"] == "pending"]
    install = module.installed_gate()
    assert install["state"] == "proven", install
    parameter_ui = module.parameter_ui_gate()
    assert parameter_ui["state"] == "proven", parameter_ui
    assert parameter_ui["counts"] == {"proven": 10, "pending": 0, "invalid": 0}
    print("PASS_OLM_RELEASE_GATE_AUDIT proven=10 pending=0 invalid=0 universal=10 parameter_ui=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
