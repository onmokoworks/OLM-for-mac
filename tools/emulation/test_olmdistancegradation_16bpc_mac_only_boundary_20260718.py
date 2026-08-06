#!/usr/bin/env python3
"""Fail-closed conformance test for the DG 16bpc Mac-only boundary.

This is intentionally a witness test, not an AE exactness test. It prevents
the retained evidence from being turned into a global PF16 rounding patch or
an invented field-word replay for the unresolved max=1 family.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import audit_olmdistancegradation_16bpc_nearmiss_boundary_20260718 as near_miss  # noqa: E402
import audit_olmdistancegradation_pf16_store_boundary_20260718 as store_audit  # noqa: E402


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    source = (ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp").read_text(encoding="utf-8")
    fieldgen = (ROOT / "core/olmdistancegradation_fieldgen.cpp").read_text(encoding="utf-8")

    # Local implementation facts: final PF16 stores truncate, while the
    # separately modeled OpenCV field pack uses nearest-even.
    assert "static inline u_short clamp16" in source
    assert "return (v < 0) ? 0 : (v > 32768.f ? 32768 : (u_short)v);" in source
    assert "if (fraction > 0.5f || (fraction == 0.5f && (word & 1U) != 0U))" in fieldgen

    local_store = store_audit.run()
    assert local_store["facts"]["actual_aex_matches_all"] == {
        "half_up": False,
        "nearest_even": False,
        "trunc": True,
    }

    unresolved = near_miss.classify()
    assert unresolved["status"] == "classified_not_separable_locally"
    assert unresolved["production_source_changed"] is False
    assert unresolved["inference"]["final_pf16_store_only_explanation"] == "not proven"
    assert unresolved["inference"]["final_writer_global_rounding_fix"].startswith("not authorized")

    family_module = load_module(ROOT / "scripts/audit_distancegradation_16bpc_family_boundary_20260715.py")
    family = family_module.build_report()
    checks = family["FACT"]["case_0026_store_checks"]
    assert checks and all(row["store_matches"] for row in checks)
    assert all(row["field_raw_words_present"] is False for row in checks)
    assert "field-word capture or field generation" in family["INFERENCE"]["case_0024_0025_0026_0027"]

    result = {
        "schema": "olmdistancegradation.16bpc-mac-only-boundary-conformance/1",
        "status": "PASS_FAIL_CLOSED",
        "scope": ["case_0012", "case_0014", "case_0024", "case_0025", "case_0026", "case_0027"],
        "claims": {
            "mac_only": True,
            "ae_exact": False,
            "windows_claim": False,
            "production_source_changed": False,
            "ledger_changed": False,
        },
        "decision": {
            "case_0012_0014": "retain unresolved pre-store/store/export boundary; no global PF16 rounding change",
            "case_0024_0027": "retain unresolved field-word/field-generation boundary; do not invent field words",
        },
        "checks": {
            "actual_aex_store_rule": "truncation",
            "mac_clamp16_rule": "float32(value * 32768) then truncating uint16 conversion with saturation",
            "field_pack_rule": "nearest-even PF16 round-trip model",
            "case0026_store_points": len(checks),
            "case0026_store_matches": True,
            "case0026_field_words_present": False,
            "case0012_0014_windows_boundary_complete": False,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    print("PASS_OLMDISTANCEGRADATION_16BPC_MAC_ONLY_BOUNDARY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
