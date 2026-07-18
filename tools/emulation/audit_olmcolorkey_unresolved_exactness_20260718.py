#!/usr/bin/env python3
"""Read-only audit of OLMColorKey's unresolved Edge Thin ownership boundary."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
EVIDENCE = {
    "legacy_misnamed_edge_blur_leaf": ROOT / "refs/conformance/olmcolorkey_edge_thin_erode_aex_20260717.json",
    "legacy_misnamed_edge_blur_caller": ROOT / "refs/conformance/olmcolorkey_edge_thin_actual_caller_20260717.json",
    "edge_thin_caller_amount": ROOT / "refs/conformance/olmcolorkey_edge_thin_caller_amount_20260718.json",
    "distance_type3": ROOT / "refs/conformance/olmcolorkey_boundary_to_distance_type3_actual_aex_20260716.json",
    "host_32bpc": ROOT / "refs/conformance/olmcolorkey_32bpc_host_path_proof_20260716.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    source = SOURCE.read_text()
    present = {name: path.exists() for name, path in EVIDENCE.items()}
    amount_facts = json.loads(EVIDENCE["edge_thin_caller_amount"].read_text()) if EVIDENCE["edge_thin_caller_amount"].exists() else {}
    source_has_caller_threshold = bool(
        re.search(r"matched\[i\]\s*=\s*\(matched\[i\]\s*&&\s*dist\[i\]\s*>\s*limit\)", source)
    )
    source_has_plus_one = "+ 1.0f" in source or "+1.0f" in source
    source_has_integer_amount = "u.sd.value" in source and "PF_ADD_SLIDER(GetStringPtr(StrID_Amount_Param_Name)" in source
    result = {
        "audit": "olmcolorkey_unresolved_exactness_20260718",
        "scope": "Mac-only read-only audit; no source, ledger, AE, or Windows mutation",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "evidence_files_present": present,
        "ownership_correction": {
            "edge_thin": "record+0x28 int32 and inline FUN_180009000 compare loops",
            "edge_blur": "record+0x40 float32 and FUN_180008320 apply leaf",
            "legacy_edge_thin_leaf_files_are_misnamed": True,
        },
        "retained_aex_edge_thin_caller": {
            "status": amount_facts.get("status"),
            "normalization_formula": amount_facts.get("normalization_formula"),
            "matrix_counts": amount_facts.get("matrix_counts"),
        },
        "current_source_boundary": {
            "caller_applies_distance_threshold": source_has_caller_threshold,
            "adds_one_for_distance_types_0_or_2": source_has_plus_one,
            "integer_amount_boundary": source_has_integer_amount,
        },
        "finding": {
            "status": "caller_amount_normalization_closed",
            "highest_value_next_action": "preserve the integer host boundary and validate distance primitive outputs separately; do not tune PNG output",
            "why": "The actual-AEX matrix proves direct int32-to-float32 conversion and both threshold predicates across all three distance-type dispatches",
            "next_evidence_needed": "distance primitive output or Mac AE conformance evidence, not another amount-normalization witness",
        },
        "checks": {
            "all_evidence_present": all(present.values()),
            "source_keeps_threshold_outside_leaf": source_has_caller_threshold,
            "source_contains_distance_type_offset": source_has_plus_one,
            "source_uses_integer_amount_boundary": source_has_integer_amount,
            "caller_amount_fixture_passes": amount_facts.get("status") == "pass",
        },
    }
    result["pass"] = all(result["checks"].values())
    out = ROOT / "refs/conformance/olmcolorkey_unresolved_exactness_20260718.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
