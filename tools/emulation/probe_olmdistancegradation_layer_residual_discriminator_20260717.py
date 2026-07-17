#!/usr/bin/env python3
"""Build the narrow Mac-only discriminator for the DG 16bpc Layer residual.

This harness does not alter production source or run a new AE project.  It
binds the current residual, source/decomp anchors, and the exact debug points
needed for one fresh Mac AE run.  It deliberately fails closed: PNG bytes
alone cannot select a source patch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESIDUAL = ROOT / "refs/conformance/olmdistancegradation_16bpc_layer_residual_mac_ae_20260717.json"
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
DECOMP = ROOT / "decomp/DistanceGradation.aex.c.txt"
FIELD_PROOF = ROOT / "refs/conformance/olmdistancegradation_pf16_field_staging_exact_20260717.json"
REQUEST = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
CASES = {
    "olmdistancegradation_extended__case_0012": {"failing": [165, 10], "control": [164, 10]},
    "olmdistancegradation_extended__case_0014": {"failing": [1035, 1], "control": [1034, 1]},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def line_of(path: Path, needle: str) -> int:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if needle in line:
            return number
    raise ValueError(f"missing anchor {needle!r} in {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/olmdistancegradation_layer_residual_discriminator_20260717.json")
    args = parser.parse_args()

    residual = json.loads(RESIDUAL.read_text(encoding="utf-8"))
    by_case = {row["case_id"]: row for row in residual["cases"]}
    assert set(by_case) == set(CASES)
    assert all(row["max_diff"] == 1 for row in by_case.values())
    assert all(row["nonzero_samples_by_channel"]["A"] == 0 for row in by_case.values())
    assert all(row["signed_delta_histogram"] == {"-1": row["nonzero_samples"]} for row in by_case.values())

    source_text = SOURCE.read_text(encoding="utf-8")
    decomp_text = DECOMP.read_text(encoding="utf-8")
    field_proof = json.loads(FIELD_PROOF.read_text(encoding="utf-8"))
    assert "static inline u_short clamp16" in source_text
    assert "param_5[1] = (short)(int)(fVar13 * DAT_181504ac4);" in decomp_text
    assert field_proof["claims"]["bounded_actual_aex_source_exact"] is True

    points = []
    for case_id, pair in CASES.items():
        row = by_case[case_id]
        points.extend([pair["failing"], pair["control"]])
        row["probe_points"] = pair

    point_arg = ";".join(f"{x},{y}" for x, y in points)
    output_root = "$TMP/olmdg_layer_residual_discriminator_20260717"
    commands = {
        case_id: (
            "python3 scripts/run_ae_single_case.py "
            f"--request-dir {REQUEST} --case-id {case_id} "
            f"--output-dir {output_root}/{case_id} --app-name 'Adobe After Effects 2026' "
            "--timeout 1200 --ae-env OLM_AE_FORCE_NEW_PROJECT=1 "
            "--ae-env OLM_AE_FORCE_SOFTWARE=1 "
            "--ae-env OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT=1 "
            f"--ae-env OLM_DG_DEBUG_POINTS={point_arg} "
            f"--ae-env OLM_DG_DEBUG_DUMP_PATH={output_root}/{case_id}/field_debug.txt "
            f"--ae-env OLM_DG_SHADE_DEBUG_PATH={output_root}/{case_id}/shade_debug.txt"
        )
        for case_id in CASES
    }
    report = {
        "schema": "olmdistancegradation.layer-residual-discriminator/1",
        "date": "2026-07-17",
        "status": "probe_required",
        "classification": "Mac_AE_pre_store_store_export_boundary",
        "production_source_edited": False,
        "residual_sha256": sha256(RESIDUAL),
        "source_sha256": sha256(SOURCE),
        "decomp_sha256": sha256(DECOMP),
        "anchors": {
            "mac_clamp16": line_of(SOURCE, "static inline u_short clamp16"),
            "mac_layer_no_bg": line_of(SOURCE, "p.render_mode == RENDER_MODE_LAYER && !p.use_bg"),
            "mac_debug_store": line_of(SOURCE, "debug_dump_shade_point(shade_debug_path"),
            "aex_pf16_store": line_of(DECOMP, "param_5[1] = (short)(int)(fVar13 * DAT_181504ac4);")
        },
        "observed_residual": {
            case_id: {
                "max_diff": by_case[case_id]["max_diff"],
                "nonzero_pixels": by_case[case_id]["nonzero_pixels"],
                "nonzero_samples": by_case[case_id]["nonzero_samples"],
                "nonzero_samples_by_channel": by_case[case_id]["nonzero_samples_by_channel"],
                "signed_delta_histogram": by_case[case_id]["signed_delta_histogram"],
                "failing_point": CASES[case_id]["failing"],
                "exact_control": CASES[case_id]["control"],
            }
            for case_id in CASES
        },
        "rejected_patch_hypotheses": [
            "global PF16 rounding change: current Mac source and bounded actual-AEX PF16 fixture both use truncating float-to-int stores",
            "neighbor inheritance change at selected witnesses: both failing source pixels are nonzero RGB, so the extra black-pixel inheritance branch is not entered",
            "distance-field retune: alpha is exact and the residual is sparse RGB-only with a single sign",
        ],
        "required_capture_per_point": [
            "input PF_Pixel16 ARGB words and normalized source RGBA",
            "field X and d_alpha",
            "compose RGBA float immediately before PF16 conversion",
            "PF_Pixel16 words immediately after store",
            "same-run exported true16 value",
        ],
        "decision_rule": {
            "source_or_field": "change only if source/field/compose differs at the failing point while the exact control remains aligned",
            "mac_store": "change only if Mac pre-store matches the Windows target but Mac PF16 store does not",
            "host_export": "make no production change if Mac PF16 store matches the Windows target and only exported true16 differs",
        },
        "commands": commands,
        "claims": {
            "ae_exact_claim": False,
            "windows_claim": False,
            "safe_patch_identified": False,
            "next_action": "run the two commands with a fresh AE project and return the six-stage chain for both failing points and controls",
        },
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(args.output_json), "points": points}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
