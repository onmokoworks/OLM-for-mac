#!/usr/bin/env python3
"""Fail closed on the bounded corrected host-transform classification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "refs/conformance/olm_crosshost_corrected_return_audit_20260806.json"
FILES = {
    "package_sha256": ROOT / "refs/reference_requests/olm_crosshost_linear_input_20260806.zip",
    "windows_return_sha256": ROOT / "refs/returns/windows/RETURN_OLM_CROSSHOST_LINEAR_INPUT_CORRECTED_20260806.zip",
    "mac_return_sha256": ROOT / "refs/returns/mac/RETURN_OLM_CROSSHOST_LINEAR_INPUT_MAC_CORRECTED_20260806.zip",
    "normalized_kira_report_sha256": ROOT / "refs/conformance/olmkirakira_crosshost_normalized_mac_ae_20260806.json",
}


def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def fail(message: str): raise ValueError(message)


def verify() -> dict:
    data = json.loads(AUDIT.read_text(encoding="utf-8"))
    if data.get("status") != "host_transform_classified_kira_exact_pending": fail("status")
    for field, path in FILES.items():
        if not path.is_file() or data["artifacts"].get(field) != sha(path): fail(field)
    rows = data.get("rows", [])
    if len(rows) != 6 or {(r["plugin"], r["depth"]) for r in rows} != {(p, d) for p in ("ColorKeep", "OLMKiraKira") for d in (8, 16, 32)}: fail("row surface")
    for row in rows:
        if not row.get("channel_binding_correct") or not row.get("source_interpretation_equal"): fail("binding/interpretation")
        if row["cross_host"]["no_effect"] != {"total": 6220800, "by_channel": {"R": 2073600, "G": 2073600, "B": 2073600, "A": 0}}: fail("no-effect difference")
        transfer = row["no_effect_host_transfer"]
        if transfer["conflicting_input_words"] != 0 or not (2.3999 < transfer["effective_power_median"] < 2.4001): fail("host transfer")
        if row["plugin"] == "ColorKeep":
            relation = row["effect_relation"]
            if not relation["plugin_relation_exact"] or relation["retained_pixels"] != 307500 or relation["rejected_pixels"] != 1766100: fail("ColorKeep relation")
            if row["cross_host"]["effect_on"] != {"total": 922500, "by_channel": {"R": 307500, "G": 307500, "B": 307500, "A": 0}}: fail("ColorKeep effect difference")
        else:
            if row["cross_host"]["effect_on"] != {"total": 6220800, "by_channel": {"R": 2073600, "G": 2073600, "B": 2073600, "A": 0}}: fail("Kira effect difference")
            if row["effect_host_transfer"]["conflicting_input_words"] <= 0: fail("Kira scalar-transfer rejection")
            normalized = row["normalized_mac_replay"]
            if normalized["branches"]["effect_on"]["mismatched_values"] != 6220800: fail("Kira normalized effect")
            if row["depth"] == 32 and normalized["branches"]["no_effect"]["mismatched_values"] != 0: fail("Kira PF32 normalized control")
    verdict = data["verdict"]
    if verdict["raw_cross_host_exact_rows"] or verdict["kira_operation_exact_depths"] or verdict["color_keep_relation_exact_depths"] != [8, 16, 32]: fail("claim boundary")
    return {"status": "accepted_bounded_relation", "color_keep_relation_exact_depths": [8, 16, 32], "kira_operation_exact_depths": [], "raw_cross_host_exact_rows": [], "claim_boundary": data["claim_boundary"]}


def main() -> int:
    try: print(json.dumps(verify(), indent=2)); return 0
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc: print(f"[FAIL] {exc}"); return 1


if __name__ == "__main__": raise SystemExit(main())
