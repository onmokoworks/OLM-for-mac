#!/usr/bin/env python3
"""Audit the imported Windows 32bpc DistanceGradation FLOAT EXR evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WINDOWS_DIR = ROOT / "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"
WINDOWS_MANIFEST = WINDOWS_DIR / "reference_manifest.json"
OUT_JSON = ROOT / "refs/conformance/olmdistancegradation_32bpc_float_evidence_audit_20260715.json"
OUT_MD = ROOT / "refs/conformance/olmdistancegradation_32bpc_float_evidence_audit_20260715.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compact_case(case: dict) -> dict:
    effect = case["effects"][0]
    params = [
        {"name": p["name"], "match_name": p["match_name"], "value": p.get("value")}
        for p in effect.get("params", [])
        if p.get("value") is not None and p["name"] not in {"Effect Opacity", "GPU Rendering"}
    ]
    before = WINDOWS_DIR / case["before_effects_frame"]
    output = WINDOWS_DIR / case["frame"]
    return {
        "id": case["id"],
        "group": case["id"].split("__", 1)[0],
        "input_id": case["input_id"],
        "render_set_id": case["render_set_id"],
        "input": case["before_effects_frame"],
        "output": case["frame"],
        "input_sha256": sha256(before) if before.is_file() else None,
        "output_sha256": sha256(output) if output.is_file() else None,
        "input_bytes": before.stat().st_size if before.is_file() else None,
        "output_bytes": output.stat().st_size if output.is_file() else None,
        "comp": case.get("comp"),
        "effect": {
            "name": effect.get("name"),
            "match_name": effect.get("match_name"),
            "property_index": effect.get("property_index"),
            "params": params,
        },
    }


def audit() -> dict:
    manifest = json.loads(WINDOWS_MANIFEST.read_text(encoding="utf-8"))
    project = manifest.get("project", {})
    renderer = project.get("project_gpu_accel_type", {})
    capabilities = manifest.get("output_capabilities", {})
    if manifest.get("platform") != "windows" or manifest.get("ae_version") != "26.3x87":
        raise ValueError("Windows AE provenance drifted")
    if project.get("bits_per_channel") != 32 or renderer.get("current_name") != "SOFTWARE" or renderer.get("raw") != 1816:
        raise ValueError("Windows 32bpc Software renderer binding drifted")
    if capabilities.get("output_format") != "exr" or capabilities.get("float_preserving") is not True or capabilities.get("output_template") != "OLM EXR 32 Float":
        raise ValueError("Windows FLOAT EXR output contract drifted")
    cases = [c for c in manifest["cases"] if c["id"].startswith("olmdistancegradation_")]
    records = [compact_case(case) for case in cases]
    complete = [
        r for r in records
        if r["render_set_id"] == "software_32bpc"
        and r["input_sha256"]
        and r["output_sha256"]
        and r["effect"]["match_name"] == "OLM Distance Gradation"
        and len(r["effect"]["params"]) == 12
        and r["input"].lower().endswith(".exr")
        and r["output"].lower().endswith(".exr")
    ]
    groups = {group: sum(r["group"] == group for r in complete) for group in sorted({r["group"] for r in complete})}
    return {
        "schema": 1,
        "kind": "olmdistancegradation_32bpc_float_evidence_audit",
        "audited_at": "2026-07-15",
        "windows_source": str(WINDOWS_MANIFEST.relative_to(ROOT)),
        "windows_provenance": {
            "platform": manifest.get("platform"),
            "ae_version": manifest.get("ae_version"),
            "bits_per_channel": manifest.get("project", {}).get("bits_per_channel"),
            "renderer": manifest.get("project", {}).get("project_gpu_accel_type"),
            "output_capabilities": manifest.get("output_capabilities"),
        },
        "candidate_subset": {
            "selection": "all DistanceGradation cases with complete before/effect FLOAT EXR pairs and 12 effect parameter values",
            "case_count": len(complete),
            "groups": groups,
            "case_ids": [r["id"] for r in complete],
        },
        "rejected_or_pending": {
            "missing_windows_pair_or_binding": [r["id"] for r in records if r not in complete],
            "mac_exact_case_count": 0,
            "current_mac_evidence": [
                {
                    "path": "refs/conformance/olmdistancegradation_fieldgen_bitdepth_boundary_20260715.json",
                    "finding": "32bpc rendered references are present, but typed field callback artifacts are zero",
                    "eligibility": "not a Mac 32bpc output comparison",
                },
                {
                    "path": "refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.json",
                    "finding": "16bpc livefield/source evidence only",
                    "eligibility": "wrong bit depth and no 32bpc raw EXR pair",
                },
                {
                    "path": "refs/conformance/olmdistancegradation_true16_residual_family_audit_20260709.json",
                    "finding": "true16 residual-family analysis",
                    "eligibility": "diagnostic evidence, not 32bpc cross-host equality",
                },
            ],
            "mac_missing_binding": [
                "fresh Mac 32bpc Software render result",
                "same-run raw-float Mac output corresponding to each Windows effect EXR",
                "Mac input hash proving the imported before-effects frame is the selected Windows input",
                "Mac parameter snapshot for the same case IDs",
                "Mac plugin SHA-256 and AE/project/output-module provenance",
            ],
        },
        "guardrails": [
            "Windows FLOAT EXR presence is reference evidence, not Mac validation.",
            "16bpc PNG or diagnostic float samples cannot bind a 32bpc exact result.",
            "PNG-only Mac output is probe evidence and cannot satisfy this contract.",
            "No production retune and no AE-exact claim without raw cross-host equality.",
        ],
        "cases": complete,
    }


def render_markdown(data: dict) -> str:
    lines = [
        "# OLMDistanceGradation 32bpc FLOAT Evidence Audit",
        "",
        "Status: Windows reference evidence is complete for the selected subset; Mac exact validation is pending and fail-closed.",
        "",
        "## Windows evidence",
        f"- Source: `{data['windows_source']}`",
        f"- Provenance: Windows AE {data['windows_provenance']['ae_version']}, {data['windows_provenance']['bits_per_channel']}bpc, `{data['windows_provenance']['renderer']['current_name']}`, float-preserving EXR.",
        f"- Strongest valid candidate subset: {data['candidate_subset']['case_count']} cases ({', '.join(f'{k}: {v}' for k, v in data['candidate_subset']['groups'].items())}).",
        "- Every selected case has a SHA-256-bound before-effects EXR, effect EXR, and 12 DistanceGradation parameter values.",
        "",
        "## Mac status",
        "- Eligible exact Mac cases: 0.",
        "- Existing Mac evidence is 16bpc/diagnostic or field-boundary evidence. It does not provide a same-run 32bpc raw-float output for any selected EXR pair.",
        "- Audited Mac artifacts: `refs/conformance/olmdistancegradation_fieldgen_bitdepth_boundary_20260715.json`, `refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.json`, and `refs/conformance/olmdistancegradation_true16_residual_family_audit_20260709.json`.",
        "- The missing binding is listed in the JSON and enforced by the Mac request contract.",
        "",
        "## Contract",
        "- Request: `refs/mac_validation_requests/olmdistancegradation_32bpc_mac_validation_20260715.json`.",
        "- A Mac result is accepted only when input identity, exact parameters, AE/project/renderer settings, plugin SHA-256, output module, and raw float output are all present and bound to the case ID.",
        "- No PNG-only result, 16bpc result, inferred parameter match, retune, or AE-exact claim is permitted.",
        "",
        "## Case IDs",
        "- " + ", ".join(data["candidate_subset"]["case_ids"]),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="audit without writing output files")
    args = parser.parse_args()
    data = audit()
    if data["candidate_subset"]["case_count"] != 29:
        raise SystemExit(f"FAIL_CLOSED: expected 29 complete DistanceGradation cases, found {data['candidate_subset']['case_count']}")
    if not args.check:
        OUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        OUT_MD.write_text(render_markdown(data), encoding="utf-8")
    print(json.dumps({"ok": True, "candidate_case_count": data["candidate_subset"]["case_count"], "mac_exact_case_count": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
