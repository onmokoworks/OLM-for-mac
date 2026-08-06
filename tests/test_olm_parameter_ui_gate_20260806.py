#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_olm_parameter_ui_gate_20260806.py"
spec = importlib.util.spec_from_file_location("parameter_ui_gate", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> int:
    manifest = json.loads(module.MANIFEST.read_text(encoding="utf-8"))
    assert module.validate_manifest(manifest) == []
    audit = module.run_gate(manifest, run_runners=False)
    assert audit["passed"] is False
    assert audit["counts"] == {"proven": 0, "pending": 10, "invalid": 0}

    bad = copy.deepcopy(manifest)
    bad["plugins"][0]["classification"] = "exact"
    assert module.validate_manifest(bad)
    missing_boundary = copy.deepcopy(manifest)
    bounded = next(row for row in missing_boundary["plugins"] if row["classification"] == "bounded_public_registration")
    bounded["boundary"] = "unknown"
    assert module.validate_manifest(missing_boundary)

    result = module.run_gate(manifest, run_runners=True)
    assert result["passed"] is True, result
    assert result["counts"] == {"proven": 10, "pending": 0, "invalid": 0}
    assert result["bounded_count"] == 3
    print("PASS_OLM_PARAMETER_UI_GATE proven=10 bounded=3 invalid=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
