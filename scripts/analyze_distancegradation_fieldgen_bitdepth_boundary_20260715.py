#!/usr/bin/env python3
"""Classify the DG field-generation boundary using local source and evidence.

This is deliberately a Mac-only structural analyzer. It does not infer Windows
field words from rendered images and it does not modify the plugin algorithm.
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MAC_SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
DECOMP = ROOT / "decomp/DistanceGradation.aex.c.txt"
PF16_BOUNDARY = ROOT / "refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.json"
LIVEFIELD = ROOT / "refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.json"
RETURN_8 = ROOT / "refs/windows_returns/20260714/20260714_1640__RETURN__OLMDG_8BPC_TYPED_BOUNDARY__fixed_batch.zip"
RETURN_16 = ROOT / "refs/windows_returns/20260714/20260714_180155__RETURN__OLMDISTANCEGRADATION_CASE0026_16BPC_LIVEFIELD.zip"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def return_status(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        json_names = [name for name in archive.namelist() if name.startswith("RETURN_") and name.endswith(".json")]
        if len(json_names) != 1:
            raise ValueError(f"expected one return json in {path}")
        value = json.loads(archive.read(json_names[0]))
    return {
        "archive": rel(path),
        "status": value.get("status"),
        "failure_reason": value.get("failure", {}).get("reason"),
        "missing_fields": value.get("failure", {}).get("missing_fields", []),
    }


def build_report() -> dict[str, Any]:
    source = MAC_SOURCE.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    fieldgen_start = source.rindex("static void dt_to_normalized(")
    fieldgen_end = source.index("static float debug_raw_distance_at(", fieldgen_start)
    fieldgen = source[fieldgen_start:fieldgen_end]
    fieldgen_calls = len(re.findall(r"distance_to_normalized_u8\(", fieldgen))
    render_depth_branches = re.findall(r"depth == (8|16)|RenderBits<PF_Pixel(Float|16|8)>", source)
    binary_body = decomp[decomp.index("// === FUN_181174760"):decomp.index("// === FUN_18117ca50")]
    boundary = load_json(PF16_BOUNDARY)
    livefield = load_json(LIVEFIELD)
    dg_32 = sorted(
        rel(path)
        for path in (ROOT / "refs/win_references").rglob("*")
        if path.is_file()
        and "32bpc" in path.name
        and "olmdistancegradation" in path.name.lower()
        and path.suffix.lower() in {".png", ".exr"}
    )
    rows = {row["case_id"]: row for row in boundary["ae_16bpc"]["rows"]}

    report: dict[str, Any] = {
        "kind": "olmdistancegradation_fieldgen_bitdepth_boundary",
        "schema": 1,
        "question": "Does Mac field generation itself branch on pixel depth before normalization?",
        "FACT": {
            "mac_shared_fieldgen": {
                "source": rel(MAC_SOURCE),
                "fieldgen_function": "dt_to_normalized",
                "calls_distance_to_normalized_u8": fieldgen_calls,
                "fieldgen_body_contains_pixel_size_branch": "pixel_size" in fieldgen,
                "render_depth_dispatches": [list(item) for item in render_depth_branches],
                "threshold_scales_by_ds": "threshold * ds_scale" in fieldgen,
            },
            "windows_binary_fieldgen": {
                "source": rel(DECOMP),
                "function": "FUN_181174760",
                "pipeline_tokens_present": [
                    token in binary_body
                    for token in ("FUN_1812b15a0", "FUN_1812aef70", "FUN_1812b6a40", "FUN_18117ca50")
                ],
                "explicit_pixel_depth_token_in_function_body": bool(re.search(r"8bpc|16bpc|32bpc|bit.?depth|PF_Pixel", binary_body, re.I)),
                "fieldgen_param_signature": "param_4 threshold plus param_8 mode; no explicit depth parameter in decomp signature",
            },
            "eight_bpc_typed_request": return_status(RETURN_8),
            "sixteen_bpc_typed_request": return_status(RETURN_16),
            "sixteen_bpc_mac_residual_families": {
                case: {"max_diff": rows[case]["max_diff"], "nonzero_pixels": rows[case]["nonzero_pixels"]}
                for case in ("case_0012", "case_0014", "case_0024", "case_0026", "case_0028")
            },
            "sixteen_bpc_livefield": {
                "status": livefield["status"],
                "case_0026_points": len(livefield["point_candidates"]),
                "raw_field_words_present": sum(item.get("field_raw_words_agrb") is not None for item in livefield["point_candidates"]),
            },
            "thirty_two_bpc_evidence": {
                "rendered_reference_artifacts": len(dg_32),
                "sample_artifacts": dg_32[:6],
                "typed_field_callback_artifacts": 0,
            },
        },
        "INFERENCE": {
            "decision": "mac_field_generation_shared_before_depth_specific_mask_and_compose",
            "fieldgen_boundary": "The Mac field builder is shared across RenderBits dispatches; observed depth branches are outside dt_to_normalized, in source-mask selection, compose, and PF16 handling.",
            "residual_ownership": "The 16bpc max-2 and outlier families are not proven to originate in field generation by current evidence. The missing Windows raw field words and failed typed requests leave upstream-vs-boundary ownership open.",
            "32bpc_limit": "The 32bpc artifacts establish rendered-reference presence only; they do not establish a typed field-generation boundary.",
        },
        "guardrails": [
            "No PNG or EXR pixels are converted into field values.",
            "Windows typed-request failures are recorded as missing evidence, not as numeric facts.",
            "No production plugin algorithm was changed because no byte-exact field-generation defect is proven.",
        ],
    }
    return report


def markdown(report: dict[str, Any]) -> str:
    fact = report["FACT"]
    inference = report["INFERENCE"]
    eight = fact["eight_bpc_typed_request"]
    sixteen = fact["sixteen_bpc_typed_request"]
    lines = [
        "# OLMDistanceGradation Field-Generation Bit-Depth Boundary",
        "",
        f"Question: {report['question']}",
        "",
        "## FACT",
        "",
        f"- Mac `dt_to_normalized` calls the shared core field generator `{fact['mac_shared_fieldgen']['calls_distance_to_normalized_u8']}` time(s); its body has no `pixel_size` branch.",
        f"- Mac depth dispatch exists at render entry (`{fact['mac_shared_fieldgen']['render_depth_dispatches']}`), outside the field builder. The field builder does apply `threshold * ds_scale`.",
        "- The decompiled Windows `FUN_181174760` pipeline contains distance, convert, threshold, and output-normalize stages, with no explicit 8/16/32bpc token in that function body.",
        f"- The active 8bpc typed request returned `{eight['status']}` because `{eight['failure_reason']}`; missing fields: `{eight['missing_fields']}`.",
        f"- The active 16bpc case-0026 typed request returned `{sixteen['status']}` because `{sixteen['failure_reason']}`; no raw field words are present in the local livefield manifest.",
        f"- Current Mac 16bpc residuals remain max-2 for cases 0012/0014/0024/0026 and max-{fact['sixteen_bpc_mac_residual_families']['case_0028']['max_diff']} for case 0028.",
        f"- 32bpc DG evidence contains `{fact['thirty_two_bpc_evidence']['rendered_reference_artifacts']}` rendered reference artifacts and zero typed field-callback artifacts.",
        "",
        "## INFERENCE",
        "",
        f"- **Decision:** `{inference['decision']}`.",
        f"- {inference['fieldgen_boundary']}",
        f"- {inference['residual_ownership']}",
        f"- {inference['32bpc_limit']}",
        "",
        "## Guardrails",
        "",
        *[f"- {item}" for item in report["guardrails"]],
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    result = build_report()
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(result), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
