#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def find_result(results: list[dict], request_id: str) -> dict:
    for row in results:
        if row.get("request_id") == request_id and row.get("source_file", "").endswith("RESULT.json"):
            return row
    raise KeyError(f"result not found: {request_id}")


def find_first_result(results: list[dict], request_ids: list[str]) -> dict:
    last_error: KeyError | None = None
    for request_id in request_ids:
        try:
            return find_result(results, request_id)
        except KeyError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


def build_summary(residual: dict, inner: dict, residual_pkg: Path, inner_pkg: Path) -> dict:
    residual_result = find_first_result(
        residual["results"],
        [
            "olmradialblur_caller_collapse_witness_20260630",
            "olmradialblur_zoom_tiny_rotation_residual_witness_20260622",
        ],
    )
    zoom_case = next(case for case in residual_result["observations"]["cases"] if case["case_id"] == "case_0009")
    tiny_rotation_case = next(case for case in residual_result["observations"]["cases"] if case["case_id"] == "case_0010")
    inner_result = find_result(inner["results"], "olmradialblur_inner_cell_witness_trace_20260625")
    inner_observations = inner_result["observations"]["observations"]
    inner_cases = inner_observations["cases"]

    return {
        "kind": "olmradialblur_pending_narrow_proof",
        "date": "2026-06-29",
        "runtime_packages": [str(residual_pkg), str(inner_pkg)],
        "decision_boundary": (
            "Keep OLMRadialBlur blocked on narrow binary proof only: Zoom still needs upstream "
            "alpha-normalization evidence, tiny Rotation still needs exact inverse-sampler/validity "
            "evidence, and Inner still needs one typed helper-to-output witness that survives past "
            "effective span into real accumulation/writeback."
        ),
        "why_global_tuning_is_forbidden_now": [
            "Zoom already has Windows sampler/pre-output floats that truncate to the exact Windows bytes, so final byte packing is not the live issue.",
            "tiny Rotation already rejects the closest traced inverse-sampler sample as the final explanation because it truncates to black while the exact Windows output is white.",
            "Inner already has binary-grounded helper facts and candidate matrices, but no global loop/wrap/table toggle is exact and the best candidates split by family.",
        ],
        "narrow_lanes": [
            {
                "lane": "zoom",
                "classification": zoom_case["classification"],
                "case_id": zoom_case["case_id"],
                "witness": zoom_case["witness"],
                "windows_pre_writeback_rgba_float": zoom_case["aex_pre_writeback_rgba_float_or_hex"],
                "windows_final_rgba_u8": zoom_case["aex_final_rgba_u8"],
                "caller_collapse_boundary": {
                    "sampler_helpers": {
                        "nonrepeat_rgba": "FUN_180001270",
                        "repeat_rgba": "FUN_180001520",
                    },
                    "preserved_validity_plane": "+0xf252",
                    "normalized_accum_rgba_plane": "+0xf250",
                    "final_polar_rgba_plane": "+0xe",
                },
                "required_next_proof": (
                    "Polar alpha/sample accumulation before sampler return, including the denominator "
                    "or substitute alpha state that explains Windows alpha 0.99999994 versus local 1.0, "
                    "plus the caller-side collapse from preserved validity/+0xf252 into final +0xe alpha."
                ),
            },
            {
                "lane": "tiny_rotation",
                "classification": tiny_rotation_case["classification"],
                "case_id": tiny_rotation_case["case_id"],
                "witness": tiny_rotation_case["witness"],
                "closest_traced_sampler_rgba_float": tiny_rotation_case["aex_source_or_polar_rgba_float"],
                "windows_final_rgba_u8": tiny_rotation_case["aex_final_rgba_u8"],
                "caller_collapse_boundary": {
                    "preserved_validity_plane": "+0xf252",
                    "normalized_accum_rgba_plane": "+0xf250",
                    "final_polar_rgba_plane": "+0xe",
                    "final_inverse_sampler": "FUN_180009d80",
                },
                "required_next_proof": (
                    "Exact inverse-sampler validity/border or substitute late path for the top-border "
                    "high-max witness, plus the caller-side collapse values: preserved validity/+0xf252, "
                    "accumulated +0xf250 RGBA, normalized +0xe RGBA, and then the final output if the "
                    "sampler sample is bypassed."
                ),
            },
            {
                "lane": "inner",
                "classification": inner_observations["failure_if_any"]["classification"],
                "request_summary": inner_result["summary"],
                "typed_effective_spans": [
                    {
                        "case_id": row["case_id"],
                        "family": row["family"],
                        "effective_span": row["witness_pixels"][0]["intermediate_values"]["effective_span_r14d_after_1d18"],
                        "span_gate_float": row["witness_pixels"][0]["span_gate_float"],
                        "fault_site": row["witness_pixels"][0]["fault_after_effective_span"]["site"],
                    }
                    for row in inner_cases
                ],
                "required_next_proof": (
                    "One typed helper-to-output witness that stays on the same helper instance beyond "
                    "effective span: resolved span, table step/index, source and destination polar cell, "
                    "accumulated RGBA numerator/denominator, and pre-writeback RGBA."
                ),
            },
        ],
        "actionable_return_if": [
            "Zoom returns the actual polar alpha/sample accumulation state at case_0009 witness (6,0), including any preserved validity/+0xf252 to +0xe alpha collapse, not just the already-known final bytes or sampler return.",
            "tiny Rotation returns the exact validity/border branch or substitute path for witness (1614,6), plus +0xf252, +0xf250 RGBA, normalized +0xe RGBA, and the final output that becomes the white pixel.",
            "Inner binds one representative output witness to one helper instance and records values after +0x1d18 all the way through accumulation/denominator/writeback.",
        ],
        "not_actionable_if": [
            "It only repeats final PNG bytes or the already-grounded closest sampler return for Zoom/tiny Rotation without the caller-side +0xf252/+0xf250/+0xe collapse state.",
            "It proposes broad loop-minus-one, circular-wrap, table-span-minus-one, or final-byte tweaks without witness values that survive to writeback.",
            "Inner tracing stops again immediately after effective span without isolating the actual destination cell and accumulated numerator/denominator.",
        ],
        "recommended_next_windows_probe": [
            "Zoom case_0009 at (6,0): capture polar/sample accumulation alpha, normalization denominator or equivalent, sampler return RGBA, preserved validity/+0xf252, accumulated +0xf250 RGBA, normalized +0xe RGBA, pre-writeback RGBA, and final bytes in one chain.",
            "tiny Rotation case_0010 at (1614,6): capture inverse-sampler input XY, validity/border branch decision, any fallback/substitute path, preserved validity/+0xf252, accumulated +0xf250 RGBA, normalized +0xe RGBA, pre-writeback RGBA, and final bytes in one chain.",
            "Inner: choose one low-span witness and one quality-strong witness, but bind each to a concrete output pixel so the trace can follow the same helper instance into destination accumulation and writeback.",
        ],
    }


def write_markdown(summary: dict, out: Path) -> None:
    lines = [
        "# OLMRadialBlur Pending Narrow Proof",
        "",
        "## Decision Boundary",
        "",
        summary["decision_boundary"],
        "",
        "## Why Global Tuning Is Still Forbidden",
        "",
    ]
    for item in summary["why_global_tuning_is_forbidden_now"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Narrow Lanes", ""])
    for lane in summary["narrow_lanes"]:
        lines.append(f"### {lane['lane']}")
        lines.append("")
        lines.append(f"- Classification: `{lane['classification']}`")
        if "case_id" in lane:
            lines.append(f"- Case: `{lane['case_id']}`")
        if "witness" in lane:
            lines.append(f"- Witness: `{lane['witness']}`")
        if "windows_pre_writeback_rgba_float" in lane:
            lines.append(f"- Windows pre-writeback RGBA float: `{lane['windows_pre_writeback_rgba_float']}`")
        if "closest_traced_sampler_rgba_float" in lane:
            lines.append(f"- Closest traced sampler RGBA float: `{lane['closest_traced_sampler_rgba_float']}`")
        if "windows_final_rgba_u8" in lane:
            lines.append(f"- Windows final RGBA u8: `{lane['windows_final_rgba_u8']}`")
        if "caller_collapse_boundary" in lane:
            lines.append(f"- Caller collapse boundary: `{lane['caller_collapse_boundary']}`")
        if "typed_effective_spans" in lane:
            lines.append(f"- Typed effective spans: `{lane['typed_effective_spans']}`")
        lines.append(f"- Required next proof: {lane['required_next_proof']}")
        lines.append("")
    lines.extend(["## Actionable Return Criteria", ""])
    for item in summary["actionable_return_if"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Not Actionable", ""])
    for item in summary["not_actionable_if"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Recommended Next Windows Probe", ""])
    for item in summary["recommended_next_windows_probe"]:
        lines.append(f"- {item}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--residual-summary-json",
        type=Path,
        default=repo_root() / "refs" / "reports" / "runtime_trace_summary_radialblur_20260624.json",
    )
    parser.add_argument(
        "--inner-summary-json",
        type=Path,
        default=repo_root() / "refs" / "reports" / "radialblur_inner_cell_witness_20260625" / "runtime_trace_summary_radialblur_inner_cell_witness_20260625_214017.json",
    )
    parser.add_argument(
        "--residual-runtime-package",
        type=Path,
        default=repo_root() / "refs" / "runtime_trace_packages" / "olm_runtime_trace_radialblur_residual_witness_20260622_012712.zip",
    )
    parser.add_argument(
        "--inner-runtime-package",
        type=Path,
        default=repo_root() / "refs" / "runtime_trace_packages" / "olm_runtime_trace_radialblur_inner_cell_witness_20260625_2130.zip",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=repo_root() / "refs" / "conformance" / "olmradialblur_pending_narrow_proof_20260629.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=repo_root() / "refs" / "conformance" / "olmradialblur_pending_narrow_proof_20260629.md",
    )
    args = parser.parse_args()

    summary = build_summary(
        load_json(args.residual_summary_json),
        load_json(args.inner_summary_json),
        args.residual_runtime_package,
        args.inner_runtime_package,
    )
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(summary, args.output_md)
    print(args.output_json)
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
