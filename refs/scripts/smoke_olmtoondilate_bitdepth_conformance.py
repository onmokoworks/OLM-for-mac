#!/usr/bin/env python3
"""Audit the ToonDilate-only 8/16/32bpc conformance boundary."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGED_8 = ROOT / "refs/conformance/packaged_8bpc_manifest.json"
EXACT_16 = ROOT / "refs/conformance/bitdepth_16bpc_exact_manifest_20260703.md"
WITNESS = ROOT / "refs/runtime_trace_packages/windows_witness_olmtoondilate_32bpc_typed_procedural_samecomp_20260713"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def audit_8bpc() -> dict[str, int]:
    manifest = json.loads(PACKAGED_8.read_text(encoding="utf-8"))
    cases = [
        row
        for row in manifest["cases"]
        if row.get("plugin") == "OLMToonDilate" and row.get("bit_depth") == "8bpc"
    ]
    require([row["case_id"] for row in cases] == ["case_0001", "case_0002", "case_0003"], "8bpc case set drifted")
    require(all(row["result_status"] == "AE exact" for row in cases), "8bpc ToonDilate is not all exact")
    require(all(row["max_diff"] == 0 and row["mean_diff"] == 0.0 for row in cases), "8bpc diff gate drifted")
    return {"cases": len(cases), "exact": sum(row["result_status"] == "AE exact" for row in cases)}


def audit_16bpc() -> dict[str, int]:
    text = EXACT_16.read_text(encoding="utf-8")
    marker = "### OLMToonDilate"
    section = text[text.index(marker) : text.index("## Interpretation")]
    require("Counts: `{'AE exact': 3}`" in section, "16bpc ToonDilate exact count drifted")
    require("passes 3/3 with max_diff=0" in section, "16bpc ToonDilate zero-diff gate drifted")
    return {"cases": 3, "exact": 3}


def audit_32bpc_typed_witness() -> dict[str, object]:
    request = json.loads((WITNESS / "request/request_manifest.json").read_text(encoding="utf-8"))
    contract = json.loads((WITNESS / "witness-contract.json").read_text(encoding="utf-8"))
    fixture = request["fixture_contract"]
    case = request["cases"][0]
    witness_case = contract["cases"][0]

    require(request["generator_supports"] == ["toondilate"], "32bpc witness is not ToonDilate-only")
    require(request["output_template"] == "OLM EXR 32 Float", "32bpc witness is not float EXR scoped")
    require(fixture["project_bits_per_channel"] == 32, "fixture is not 32bpc")
    require(fixture["render_policy"] == "same comp, only branch enabled state changes", "A/B render is not same-comp")
    require(fixture["source_policy"] == "AE-generated solids only; no footage imported", "fixture is not typed procedural")
    require(contract["project"] == {
        "bits_per_channel": 32,
        "environment": {"OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT": "1"},
        "renderer": "Software",
    }, "witness project contract drifted")
    require(case["effect_name"] == "OLM Toon Dilate", "wrong effect in typed witness request")
    require(case["live_hook"]["semantic"] == "32bpc PF_PixelFloat ToonDilate render core", "typed hook semantic drifted")
    require(case["parameters"][0]["name"] == "Search Radius", "typed witness parameter drifted")
    require(witness_case["exports"][0]["archive_path"].endswith("effect_no_effect_00000.exr"), "no-effect output is not EXR")
    require(witness_case["exports"][1]["archive_path"].endswith("effect_effect_on_00000.exr"), "effect output is not EXR")
    require(not list(WITNESS.rglob("*.png")), "PNG artifact entered the typed witness package")
    return {"cases": 1, "status": "typed-procedural-contract-ready", "ae_exact": False}


def main() -> int:
    result = {"8bpc": audit_8bpc(), "16bpc": audit_16bpc(), "32bpc": audit_32bpc_typed_witness()}
    print(json.dumps(result, sort_keys=True))
    print("[OK] ToonDilate 8/16bpc exact slices and 32bpc typed witness contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
