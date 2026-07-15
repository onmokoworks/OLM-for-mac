#!/usr/bin/env python3
"""Lightweight DirectionalBlur lane audit for the bounded Front Alpha Fade proof."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

import test_dblur_alpha_fade_witness_row_20260712 as alpha_witness


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_JSON = ROOT / "refs/conformance/olmdirectionalblur_front_alpha_boundary_audit_20260716.json"
OUTPUT_MD = ROOT / "refs/conformance/olmdirectionalblur_front_alpha_boundary_audit_20260716.md"
HOST_BOUNDARY_JSON = ROOT / "refs/conformance/dblur_alpha_host_boundary_20260711.json"
FLOAT_AUDIT_JSON = ROOT / "refs/conformance/olmdirectionalblur_32bpc_float_evidence_audit_20260715.json"
REFERENCE_MANIFEST = ROOT / "refs/win_references/olm_reference_return_windows_20260611/OLMDirectionalBlur/reference_manifest.json"
DECOMP = ROOT / "decomp/OLMDirectionalBlur.aex.c.txt"
CASE_ID = "db_angle0_alpha_fade_hard_edges"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_case_params(case_id: str) -> dict[str, object]:
    manifest = load_json(REFERENCE_MANIFEST)
    for case in manifest["cases"]:
        if case.get("id") != case_id or case.get("render_set_id") != "software":
            continue
        if int(case["comp"]["frame_rate"]) != 24:
            continue
        params: dict[str, object] = {}
        for effect in case.get("effects", []):
            for param in effect.get("params", []):
                index = param.get("property_index")
                if index is None:
                    continue
                params[f"{param.get('name', 'param')}#{index}"] = param.get("value")
        return params
    raise RuntimeError(f"case not found in reference manifest: {case_id}")


def find_line_numbers(needles: list[str]) -> dict[str, list[int]]:
    lines = DECOMP.read_text(encoding="utf-8").splitlines()
    return {
        needle: [index + 1 for index, line in enumerate(lines) if needle in line]
        for needle in needles
    }


def rerun_bounded_alpha_witness() -> dict:
    tables = alpha_witness.table_bytes()
    source = alpha_witness.rotated_witness_row()
    actual_inputs = alpha_witness.initial_inputs(source, alpha_witness.INTERNAL_ROW)
    portable_inputs = alpha_witness.initial_inputs(source, 0)

    with tempfile.TemporaryDirectory(prefix="olm_dblur_front_alpha_audit_") as name:
        actual, rowdriver_instructions = alpha_witness.run_actual(actual_inputs, tables)
        portable = alpha_witness.run_portable(portable_inputs, tables, Path(name))

    comparisons = {
        "destination": alpha_witness.compare(actual["destination"], portable["destination"], 4),
        "denominator": alpha_witness.compare(actual["denominator"], portable["denominator"], 1),
        "alpha": alpha_witness.compare(actual["alpha"], portable["alpha"], 1),
    }

    actual_normalized, normalization_instructions = alpha_witness.run_actual_normalization(
        actual["destination"], actual["denominator"]
    )
    portable_normalized = alpha_witness.portable_normalization(
        portable["destination"], portable["denominator"]
    )
    normalization = alpha_witness.compare(actual_normalized, portable_normalized, 4)

    actual_packed, writer_instructions = alpha_witness.run_actual_writer(actual_normalized)
    windows_packed = alpha_witness.expected_windows_packed()
    writer = alpha_witness.compare(actual_packed, windows_packed, 4)

    return {
        "status": "pass"
        if all(item["exact"] for item in comparisons.values()) and normalization["exact"]
        else "mismatch",
        "aex_sha256": alpha_witness.sha(alpha_witness.AEX.read_bytes()),
        "input_sha256": alpha_witness.sha(alpha_witness.INPUT.read_bytes()),
        "rowdriver_instructions": rowdriver_instructions,
        "normalization_instructions": normalization_instructions,
        "writer_instructions": writer_instructions,
        "comparisons": comparisons,
        "normalization": normalization,
        "writer_vs_windows": writer,
    }


def build_markdown(result: dict) -> str:
    facts = "\n".join(f"- {item}" for item in result["fact"])
    inferences = "\n".join(f"- {item}" for item in result["inference"])
    commands = "\n".join(f"`{item}`" for item in result["commands"])
    witness = result["bounded_witness"]
    return "\n".join(
        [
            "# OLMDirectionalBlur Front Alpha Fade boundary audit",
            "",
            "## Verdict",
            "",
            f"- Selected lane: `{result['selected_lane']}`",
            f"- Status: `{result['status']}`",
            "",
            "## Commands",
            "",
            commands,
            "",
            "## FACT",
            "",
            facts,
            "",
            "## INFERENCE",
            "",
            inferences,
            "",
            "## Witness replay",
            "",
            f"- Rowdriver status: `{witness['status']}`",
            f"- Rowdriver exact: `{all(item['exact'] for item in witness['comparisons'].values())}`",
            f"- Normalization exact: `{witness['normalization']['exact']}`",
            f"- PF writer vs Windows exact: `{witness['writer_vs_windows']['exact']}`",
            f"- PF writer differing values: `{witness['writer_vs_windows']['differing_floats']}`",
            "",
            "This audit is bounded evidence only. It does not change production source or",
            "promote an AE-exact claim for Front Alpha Fade.",
            "",
        ]
    )


def main() -> int:
    host_boundary = load_json(HOST_BOUNDARY_JSON)
    float_audit = load_json(FLOAT_AUDIT_JSON)
    params = find_case_params(CASE_ID)
    decomp_lines = find_line_numbers(
        [
            "FUN_180001000(iVar7,iVar9,lVar2,lVar1,*(longlong *)(param_7 + 0x8088),",
            "param_7 + 0x3ed8,*(int *)(param_7 + 0x4c),",
            "param_7 + 0x7ee8,*(int *)(param_7 + 0x54),param_5,fVar10);",
            "fVar12 = fVar3 - ((float)((uint)((float)param_1 -",
            "*(float *)(param_7 + 0x40)) /",
            "FUN_1800013e0(iVar7,iVar9,'\\x01',lVar2,lVar1,*(longlong *)(param_7 + 0x8080),",
        ]
    )
    witness = rerun_bounded_alpha_witness()

    front_alpha_only_controls = {
        "Size Variation#3": params.get("Size Variation#3"),
        "Alpha Fade#6": params.get("Alpha Fade#6"),
        "Sharp Tail#7": params.get("Sharp Tail#7"),
        "Blur Strength#10": params.get("Blur Strength#10"),
        "Alpha Fade#11": params.get("Alpha Fade#11"),
        "Sharp Tail#12": params.get("Sharp Tail#12"),
        "Noise Variation#15": params.get("Noise Variation#15"),
    }

    rowdriver_exact = all(item["exact"] for item in witness["comparisons"].values())
    normalization_exact = witness["normalization"]["exact"]
    host_formula_exact = (
        host_boundary["host_boundary"]["input_formula_max_diff"] == 0
        and host_boundary["host_boundary"]["output_formula_max_diff"] == 0
    )

    status = "pass" if rowdriver_exact and normalization_exact and host_formula_exact else "fail"

    result = {
        "schema": 1,
        "kind": "olmdirectionalblur_front_alpha_boundary_audit",
        "selected_lane": "Front Alpha Fade",
        "status": status,
        "commands": [
            "python3 tools/emulation/test_dblur_front_alpha_boundary_audit_20260716.py",
        ],
        "same_run_case": {
            "case_id": CASE_ID,
            "request_id": host_boundary["request_id"],
            "loaded_aex_sha256": host_boundary["windows_run"]["loaded_aex_sha256"],
            "input_alpha_mode": "PREMULTIPLIED",
            "host_boundary_input_formula_max_diff": host_boundary["host_boundary"]["input_formula_max_diff"],
            "host_boundary_output_formula_max_diff": host_boundary["host_boundary"]["output_formula_max_diff"],
        },
        "case_controls": front_alpha_only_controls,
        "decomp_evidence": {
            "file": str(DECOMP.relative_to(ROOT)),
            "line_hits": decomp_lines,
            "summary": {
                "front_alpha_fade_gather_count": "+0x4c feeds FUN_180001000 prepass/gather table",
                "back_alpha_fade_gather_count": "+0x54 feeds FUN_180001000 back gather table",
                "front_sharp_tail_taper": "+0x40 participates in the scatter taper path, not the gather-count path",
            },
        },
        "bounded_witness": witness,
        "mixed_family_evidence": {
            "32bpc_case_count": float_audit["evidence"]["32bpc_windows"]["case_count"],
            "32bpc_family_counts": float_audit["evidence"]["32bpc_family_counts"],
        },
        "fact": [
            "The same-run Windows host-boundary proof for db_angle0_alpha_fade_hard_edges loaded the pinned 2025 AEX and both host formulas are exact (max_diff=0 in and out).",
            "The bounded actual-AEX Front Alpha Fade witness rerun is byte-exact for rowdriver destination, denominator, alpha, and normalization against the portable harness.",
            "The decomp rowdriver calls FUN_180001000 with +0x3ed8/+0x4c and +0x7ee8/+0x54, while the scatter taper path uses +0x40 before FUN_1800013e0.",
            "The current software 24fps reference case keeps front Sharp Tail, all Back controls, and Noise Variation at zero while Front Alpha Fade is 96.",
            "The imported 32bpc Windows family remains fully mixed across variation/fade/tail/back/noise (10/10 for each family), so those broader lanes are not isolated by the current float return set.",
        ],
        "inference": [
            "Front Alpha Fade is the smallest remaining DirectionalBlur lane that can be closed today with existing AEX, decomp, and harness evidence because it already has an exact bounded AEX replay and a pinned same-run host boundary.",
            "Size Variation, Sharp Tail, Back, and Noise still require either a narrower typed witness or a less entangled return set before the same style of closure is justified.",
            "The remaining Front Alpha Fade gap is downstream of the bounded rowdriver/normalization witness; this audit does not convert that lane into an AE-exact claim.",
        ],
        "production_changed": False,
    }

    OUTPUT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(build_markdown(result), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
