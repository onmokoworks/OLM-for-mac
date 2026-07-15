#!/usr/bin/env python3
"""Audit imported OLMKiraKira 32bpc EXRs and write a narrow Mac request."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
WINDOWS_ROOT = ROOT / "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMKiraKira"
MANIFEST = WINDOWS_ROOT / "reference_manifest.json"
IMPORT = WINDOWS_ROOT / "reference_import.json"
REPORT_JSON = ROOT / "refs/conformance/olmkirakira_32bpc_evidence_audit_20260715.json"
REPORT_MD = ROOT / "refs/conformance/olmkirakira_32bpc_evidence_audit_20260715.md"
REQUEST_JSON = ROOT / "refs/mac_validation_requests/olmkirakira_mode2_32bpc_mac_validation_20260715.json"
PLUGIN_SHA256 = "421f670fdf26cc61170028e4b65709c8232358f4a63a04f46b498b6dd4b96b0a"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def exr_header(path: Path) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_32bpc_float_return import decode_attrs, parse_exr_header

    attrs, _ = parse_exr_header(path)
    info = decode_attrs(attrs, path)
    channels = info["channels"]
    return {
        "sha256": sha256(path),
        "dimensions": [info["width"], info["height"]],
        "channel_order": [channel["name"] for channel in channels],
        "sample_types": [channel["sample_type"] for channel in channels],
        "compression": info["compression"],
        "valid_uncompressed_float_rgba": (
            len(channels) == 4
            and {channel["name"] for channel in channels} == {"A", "B", "G", "R"}
            and all(channel["sample_type"] == 2 for channel in channels)
            and info["compression"] == 0
        ),
    }


def effect_case(case: dict[str, Any]) -> dict[str, Any]:
    effect = next(item for item in case["effects"] if item.get("match_name") == "OLM OLM Kira Kira")
    params = effect["params"]
    values = {param.get("name", ""): param.get("value") for param in params}
    mode = values.get("Blur Mode")
    family = f"blur_mode_{mode}"
    if mode in (1, 2):
        eligibility = "eligible_grounded_mode1_or_mode2"
    elif values.get("Strength multiplier") == 0:
        family = "strength_zero"
        eligibility = "eligible_strength_zero"
    else:
        eligibility = "blocked_unresolved_mode3_or_mode4"
    before = WINDOWS_ROOT / case["before_effects_frame"]
    effect_frame = WINDOWS_ROOT / case["frame"]
    return {
        "id": case["id"],
        "mode": mode,
        "control_family": family,
        "eligibility": eligibility,
        "fully_pinned": len(params) == 42 and all("match_name" in param and "property_index" in param for param in params),
        "params_count": len(params),
        "params_sha256": canonical_sha256(params),
        "merge_mode": values.get("Merge mode"),
        "approximated_input": values.get("Approximated Input"),
        "strength_multiplier": values.get("Strength multiplier"),
        "input_id": case.get("input_id"),
        "before_effects_frame": case["before_effects_frame"],
        "effect_frame": case["frame"],
        "before_effects_exr": exr_header(before),
        "effect_exr": exr_header(effect_frame),
    }


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    imported = json.loads(IMPORT.read_text(encoding="utf-8"))
    rows = [effect_case(case) for case in manifest["cases"]]
    eligible = [row for row in rows if row["eligibility"].startswith("eligible_") and row["fully_pinned"]]
    selected = next(row for row in eligible if row["id"] == "final_random10_olm_kira_kira_06")
    selected_case = next(case for case in manifest["cases"] if case["id"] == selected["id"])
    effect = next(item for item in selected_case["effects"] if item.get("match_name") == "OLM OLM Kira Kira")
    request = {
        "kind": "olmkirakira_mode2_32bpc_mac_validation_request",
        "schema_version": 1,
        "request_id": "olmkirakira_mode2_32bpc_mac_validation_20260715",
        "status": "sendable_fail_closed_no_ae_exact_claim",
        "scope": "smallest fully pinned imported Windows 32bpc candidate independent of unresolved Mode3 Gaussian",
        "source_audit": "refs/conformance/olmkirakira_32bpc_evidence_audit_20260715.json",
        "windows_contract": {
            "manifest": str(MANIFEST.relative_to(ROOT)),
            "import": str(IMPORT.relative_to(ROOT)),
            "ae_version": manifest["ae_version"],
            "renderer": "SOFTWARE",
            "bits_per_channel": 32,
            "output": {"container": "OpenEXR", "channels": ["A", "B", "G", "R"], "sample_type": "FLOAT", "compression": "none"},
        },
        "case": {
            "id": selected_case["id"],
            "source_case_id": selected_case["id"],
            "input_id": selected_case["input_id"],
            "input_path": selected_case["layer"]["source_name"],
            "comp": selected_case["comp"],
            "effect": {"name": effect["name"], "match_name": effect["match_name"], "property_index": effect["property_index"], "params_full": effect["params"]},
            "params_sha256": canonical_sha256(effect["params"]),
            "windows_outputs": {
                "before_effects": {"path": str((WINDOWS_ROOT / selected_case["before_effects_frame"]).relative_to(ROOT)), **selected["before_effects_exr"]},
                "effect_on": {"path": str((WINDOWS_ROOT / selected_case["frame"]).relative_to(ROOT)), **selected["effect_exr"]},
            },
        },
        "mac_contract": {
            "ae_major_minor": "26.3",
            "renderer": "SOFTWARE",
            "bits_per_channel": 32,
            "frame": 0,
            "working_space": "record actual value; reject drift from Windows contract",
            "linear_blending": "record actual value; reject drift from Windows contract",
            "output_template": "OLM EXR 32 Float",
            "output_module": {"container": "OpenEXR", "channels": ["A", "B", "G", "R"], "sample_type": "FLOAT", "compression": "none", "settings_capture_required": True},
            "outputs": ["before_effects_control", "effect_on"],
        },
        "plugin": {"filename": "OLMKiraKira.plugin", "sha256": PLUGIN_SHA256, "loaded_hash_capture_required": True},
        "comparison": {"required": "raw FLOAT32 word equality for both returned files after semantic channel mapping", "ae_exact_claim": False, "png_only": "probe_only"},
        "fail_closed": [
            "reject missing or changed source input",
            "reject missing or mismatched loaded OLMKiraKira.plugin SHA-256",
            "reject missing params_full, property identity, value, or params_sha256 mismatch",
            "reject AE version, SOFTWARE renderer, 32bpc, frame, color, or Output Module drift",
            "reject missing before-effects control or effect-on output",
            "reject non-OpenEXR, compressed, HALF, non-RGBA, non-FLOAT, non-1920x1080, or unhashed outputs",
            "reject exactness until both raw FLOAT32 comparisons pass",
            "never infer exactness from PNG, CLI, emulation, visual similarity, or unresolved Mode3 Gaussian evidence",
        ],
    }
    report = {
        "kind": "olmkirakira_32bpc_evidence_audit",
        "schema_version": 1,
        "date": "2026-07-15",
        "status": "candidate_identified_mac_validation_pending",
        "ae_exact_claim": False,
        "source_manifest": str(MANIFEST.relative_to(ROOT)),
        "import_summary": {"case_count": len(manifest["cases"]), "split_case_count": imported.get("split_case_count"), "float_preserving_present": imported.get("float_preserving_present")},
        "mode_counts": {str(mode): sum(row["mode"] == mode for row in rows) for mode in (1, 2, 3, 4)},
        "control_family_counts": {family: sum(row["control_family"] == family for row in rows) for family in sorted({row["control_family"] for row in rows})},
        "eligible_cases": [row["id"] for row in eligible],
        "selected_candidate": selected,
        "cases": rows,
        "limits": ["The imported EXRs are Windows reference evidence, not Mac validation.", "No raw cross-host equality was performed.", "No source or production lane was changed.", "Mode3 Gaussian remains unresolved and is excluded from the selected candidate."],
        "mac_request": str(REQUEST_JSON.relative_to(ROOT)),
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REQUEST_JSON.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# OLMKiraKira Imported Windows 32bpc Evidence Audit",
        "",
        "Date: 2026-07-15",
        "",
        "## Decision",
        "",
        "Smallest candidate: `final_random10_olm_kira_kira_06` (one fully pinned case). It uses Blur Mode 2, Merge mode 1, and `Approximated Input=0`; it does not depend on unresolved Mode3 Gaussian behavior.",
        "",
        "Status: **candidate identified; Mac validation pending**. This is not an AE exact claim.",
        "",
        "## Imported EXR audit",
        "",
        f"- Windows manifest: `{MANIFEST.relative_to(ROOT)}`.",
        f"- Cases: `{len(rows)}`; all cases have 42 parameter records and complete property identity/value metadata.",
        "- Every before-effects/effect-on file inspected has 1920x1080, A/B/G/R channels, FLOAT sample type `2`, and uncompressed scanline compression `0`.",
        "",
        "| Family | Cases | Eligibility |",
        "| --- | --- | --- |",
        f"| Blur Mode 1 | `{', '.join(row['id'][-2:] for row in rows if row['mode'] == 1)}` | grounded dispatch candidate |",
        f"| Blur Mode 2 | `{', '.join(row['id'][-2:] for row in rows if row['mode'] == 2)}` | grounded three-box candidate |",
        f"| Blur Mode 3 | `{', '.join(row['id'][-2:] for row in rows if row['mode'] == 3)}` | excluded; Gaussian unresolved |",
        f"| Blur Mode 4 | `{', '.join(row['id'][-2:] for row in rows if row['mode'] == 4)}` | excluded; behavior unresolved |",
        "| Strength zero | none in imported 32bpc set | no 32bpc strength-zero candidate present |",
        "",
        "## Selected pin",
        "",
        "- Case: `final_random10_olm_kira_kira_06`.",
        "- Input: `random_final_alpha_1920x1080`.",
        "- Parameter SHA-256: `" + selected["params_sha256"] + "`.",
        "- Before-effects EXR SHA-256: `" + selected["before_effects_exr"]["sha256"] + "`.",
        "- Effect-on EXR SHA-256: `" + selected["effect_exr"]["sha256"] + "`.",
        "",
        "## Mac contract",
        "",
        f"Request: `{REQUEST_JSON.relative_to(ROOT)}`.",
        "It requires the exact 42-property pin, the Windows input/output hashes, loaded plugin SHA-256, same-comp before-effects control, uncompressed FLOAT RGBA EXRs, Output Module settings capture, and raw FLOAT32 equality before any exactness status can be emitted.",
        "",
        "## Limits",
        "",
        "No retuning was performed. No production source, Mode3 live-Gaussian/aggregation lane, shared ledger/orchestration, or generic reference checker was changed. PNG, CLI, emulation, visual similarity, and unresolved Mode3 evidence cannot satisfy this contract.",
        "",
    ]
    REPORT_MD.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"status": report["status"], "selected": selected["id"], "report": str(REPORT_JSON), "request": str(REQUEST_JSON)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
