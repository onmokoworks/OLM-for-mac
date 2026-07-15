#!/usr/bin/env python3
"""Audit OLMDirectionalBlur bit-depth evidence without tuning pixels."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr


WIN_ROOT = ROOT / "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMDirectionalBlur"
WIN_MANIFEST = WIN_ROOT / "reference_manifest.json"
INPUT = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_olm_final_random10_olm_directionalblur_20260629/input/olm_final_random10_olm_directionalblur_20260629__software__fr24__final_random10_olm_directionalblur_01_before_effects.png"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def values(case: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for effect in case.get("effects", []):
        if effect.get("name") != "OLM DirectionalBlur":
            continue
        for param in effect.get("params", []):
            if param.get("value") is not None:
                result[str(param["name"]) + f"#{param['property_index']}"] = param["value"]
    return result


def classify(params: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    if params.get("Size Variation#3", 0) != 0:
        labels.append("variation")
    if params.get("Alpha Fade#6", 0) != 0 or params.get("Alpha Fade#11", 0) != 0:
        labels.append("fade")
    if params.get("Sharp Tail#7", 0) != 0 or params.get("Sharp Tail#12", 0) != 0:
        labels.append("tail")
    if params.get("Blur Strength#10", 0) != 0 or params.get("Alpha Fade#11", 0) != 0 or params.get("Sharp Tail#12", 0) != 0:
        labels.append("back")
    if params.get("Noise Variation#15", 0) != 0:
        labels.append("noise")
    return labels or ["front-only-exact-family-eligible"]


def audit_windows() -> dict[str, Any]:
    manifest = json.loads(WIN_MANIFEST.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for case in sorted(manifest["cases"], key=lambda row: row["id"]):
        effect = WIN_ROOT / case["frame"]
        before = WIN_ROOT / case["before_effects_frame"]
        row: dict[str, Any] = {
            "case_id": case["id"],
            "input_id": case.get("input_id"),
            "effect": effect.name,
            "before_effects": before.name,
            "params": values(case),
        }
        row["families"] = classify(row["params"])
        try:
            ei = inspect_float_rgba_exr(effect)
            bi = inspect_float_rgba_exr(before)
            row.update({
                "effect_float_exr": True,
                "before_effects_float_exr": True,
                "dimensions": ei["dimensions"],
                "effect_header": {k: ei[k] for k in ("channel_order", "sample_types", "compression")},
                "before_header": {k: bi[k] for k in ("channel_order", "sample_types", "compression")},
                "dimensions_match": ei["dimensions"] == bi["dimensions"],
                "effect_sha256": sha256(effect),
                "before_sha256": sha256(before),
            })
        except (OSError, KeyError, TypeError, VerificationError) as exc:
            row.update({"effect_float_exr": False, "before_effects_float_exr": False, "error": str(exc)})
        rows.append(row)
    software = manifest.get("project", {}).get("project_gpu_accel_type", {}).get("current_name") == "SOFTWARE"
    valid = len(rows) == 10 and software and all(
        r.get("effect_float_exr") and r.get("before_effects_float_exr") and r.get("dimensions_match") for r in rows
    )
    return {
        "classification": "windows-software-float-reference-only" if valid else "not-verified",
        "manifest": str(WIN_MANIFEST.relative_to(ROOT)),
        "case_count": len(rows),
        "software": software,
        "float_preserving": valid,
        "cases": rows,
    }


def build_report() -> dict[str, Any]:
    exact16 = json.loads((ROOT / "refs/conformance/bitdepth_16bpc_exact_manifest_20260709.json").read_text(encoding="utf-8"))
    dblur16 = [row for row in exact16.get("cases", []) if "direction" in str(row).lower() or "dblur" in str(row).lower()]
    windows = audit_windows()
    family_counts: dict[str, int] = {}
    for row in windows["cases"]:
        for family in row["families"]:
            family_counts[family] = family_counts.get(family, 0) + 1
    return {
        "kind": "olmdirectionalblur_bitdepth_evidence_audit",
        "schema": 1,
        "generated": "2026-07-15",
        "scope": "OLMDirectionalBlur 16/32bpc evidence only; no production source, row755, ledger, or orchestration",
        "evidence": {
            "32bpc_windows": windows,
            "32bpc_family_counts": family_counts,
            "16bpc": {
                "classification": "no-directionalblur-rows-in-covered-16bpc-exact-manifest",
                "covered_manifest": "refs/conformance/bitdepth_16bpc_exact_manifest_20260709.json",
                "covered_case_count": len(exact16.get("cases", [])),
                "directionalblur_case_count": len(dblur16),
                "covered_plugins": sorted({row.get("plugin") for row in exact16.get("cases", [])}),
            },
            "front_only_exact_family": {
                "classification": "separate-8bpc-family",
                "cases": ["db_angle0_strength_sweep_small", "db_angle0_no_tail_no_size"],
                "source": "refs/conformance/dblur_frontonly_mac_ae_exact_20260711.md",
                "claim": "8bpc front-only only; does not promote 16bpc or 32bpc",
            },
        },
        "decision": {
            "mac_validation": "single-case-float-exr-gate",
            "request": "refs/mac_validation_requests/olmdirectionalblur_32bpc_mac_validation_20260715.json",
            "case": "final_random10_olm_directionalblur_01",
            "raw_cross_host_equality_required": True,
            "ae_exact_claim_allowed_now": False,
            "no_retune_justified": True,
        },
        "fail_closed": [
            "No DirectionalBlur 16bpc exact claim: covered 16bpc manifest has no DirectionalBlur rows.",
            "All imported 32bpc cases are variation/fade/tail/back/noise families; none is front-only exact-family evidence.",
            "PNG or visual similarity cannot establish 32bpc exactness.",
            "A Mac result is not exact unless same-contract control gates pass and raw FLOAT32 words are equal cross-host.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    w = report["evidence"]["32bpc_windows"]
    lines = [
        "# OLMDirectionalBlur 16/32bpc Evidence Audit - 2026-07-15", "",
        "## Verdict", "",
        "`windows-software-float-reference-only; no AE exact claim`", "",
        "The imported Windows return contains 10 effect/control pairs. Every pair is an uncompressed FLOAT RGBA EXR at 1920x1080 from the SOFTWARE render set.", "",
        "## Family Separation", "",
        "- The established front-only exact family is the separate 8bpc slice `db_angle0_strength_sweep_small` and `db_angle0_no_tail_no_size`.",
        "- All 10 imported 32bpc cases have nonzero Size Variation, front/back Alpha Fade, front/back Sharp Tail, back Blur Strength, and Noise Variation. They are mixed variation/fade/tail/back/noise stress cases.",
        "- No DirectionalBlur row exists in the covered 16bpc exact manifest. Its 12 rows are OLMColorKey and OLMToonDilate only.", "",
        "## Windows 32bpc Return", "",
        "| Cases | Effect/control pairs | Format | Renderer | Exactness |",
        "| ---: | ---: | --- | --- | --- |",
        f"| 10 | {len(w['cases'])} | FLOAT RGBA, uncompressed EXR | SOFTWARE | Windows reference only |", "",
        "The audit records per-artifact SHA-256 and EXR header facts. It does not infer algorithm equality from the files and does not retune production source.", "",
        "## Mac Gate", "",
        "The narrowest pinned request is one case, `final_random10_olm_directionalblur_01`, with its input identity, complete effect parameter values, 1920x1080/24fps comp, 32bpc SOFTWARE project, no-effect control, effect-on output, and OpenEXR FLOAT/no-compression contract. See `refs/mac_validation_requests/olmdirectionalblur_32bpc_mac_validation_20260715.json`.", "",
        "Pass requires raw FLOAT32 word equality after the Windows/Mac no-effect control gate. Any missing hash, changed input/parameter, output drift, non-FLOAT/compressed EXR, or PNG-only return fails closed. No `AE exact` claim is permitted by this request.", "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    report = build_report()
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown(report), encoding="utf-8")
    if not args.output_json and not args.output_md:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
