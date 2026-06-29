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


def find_request(requests: list[dict], request_id: str) -> dict:
    for row in requests:
        if row.get("request_id") == request_id:
            return row
    raise KeyError(f"request not found: {request_id}")


def find_first_request(requests: list[dict], request_ids: list[str]) -> dict:
    last_error: KeyError | None = None
    for request_id in request_ids:
        try:
            return find_request(requests, request_id)
        except KeyError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


def build_summary(
    decision: dict,
    contract: dict,
    plan: dict,
    scatter: dict,
    pending: dict,
) -> dict:
    angle0 = next(row for row in plan["plans"] if row["family"] == "angle0-rowdriver-valid-alpha")
    diagonal = next(row for row in plan["plans"] if row["family"] == "diagonal-rotate-validity")
    pending_row = find_first_request(
        pending["requests"],
        [
            "olmdirectionalblur_helper_coverage_witness_20260630",
            "olmdirectionalblur_angle0_diagonal_residual_witness_20260622",
        ],
    )
    case0001_scatter = scatter["cases"]["case_0001"]
    case0005_scatter = scatter["cases"]["case_0005"]

    return {
        "kind": "olmdirectionalblur_pending_witness_proof",
        "date": "2026-06-29",
        "runtime_package": pending_row["package"],
        "decision_boundary": (
            "Keep OLMDirectionalBlur blocked on typed witness proof only: the angle-0 strip still "
            "needs helper-local destination coverage or valid-alpha evidence, and the diagonal family "
            "still needs rotate/validity evidence. Broad PNG tuning and candidate promotion remain forbidden."
        ),
        "why_global_tuning_is_forbidden_now": [
            "The best numeric candidates are still measurement scaffolds, not AEX-shaped implementations.",
            "The current runtime return is answered_partial but not actionable because it never captured typed per-pixel values after the module actually loaded.",
            "Local scatter-ownership audit shows the dominant angle-0 strip mask is unchanged by source-driven scatter, so broad scatter toggles are no longer the leading explanation.",
        ],
        "angle0_lane": {
            "classification": decision["residuals"]["cases"][0]["residual_kind"],
            "primary_witness": angle0["primary_witness"],
            "scan_order_max_witness": angle0["scan_order_max_witness"],
            "required_values": angle0["required_values"],
            "helper_local_static_facts": [
                "front helper call uses param_3 = 1",
                "effective span is int(param_9 * param_11) with left-edge clipping",
                "writes start at offset = 1",
                "loop continues while offset < param_9",
                "front helper writes only to destination columns strictly left of the current source x",
            ],
            "current_local_readback": {
                "witness_row_y": case0001_scatter["witness_row"]["y"],
                "full_segments": case0001_scatter["witness_row"]["full_segments"],
                "scatter_segments": case0001_scatter["witness_row"]["scatter_segments"],
                "identical_mask": case0001_scatter["witness_row"]["identical_mask"],
            },
            "required_next_proof": (
                "A helper-local source-to-destination range witness on the strip row, especially the right endpoint "
                "(579,169) plus companion witness (494,169), including actual touched destination x range, "
                "rowdriver/group membership, validity side-channel, accumulation, pre-writeback RGBA, and final bytes."
            ),
        },
        "diagonal_lane": {
            "classification": decision["residuals"]["cases"][1]["residual_kind"],
            "primary_witness": diagonal["primary_witness"],
            "companion_witnesses": diagonal["companion_witnesses"][:3],
            "required_values": diagonal["required_values"],
            "current_local_readback": {
                "scatter_vs_full_bbox": case0005_scatter["scatter_vs_full_bbox"],
                "scatter_vs_full_max_abs": case0005_scatter["scatter_vs_full"]["max_abs"],
            },
            "required_next_proof": (
                "Typed rotate sampler source coordinates/order, border or validity decision, group-size or opacity gate, "
                "accumulation denominator, pre-writeback RGBA, and final bytes at the diagonal witnesses."
            ),
        },
        "actionable_return_if": [
            "The angle-0 return includes helper-local source x/y, param_1/param_3/param_9/param_11, clipped effective span, actual touched destination x range on row y=169, plus accumulation and final bytes.",
            "The diagonal return includes typed rotate/sampler/validity values at a real residual witness, not only final PNG bytes.",
            "The return keeps angle-0 and diagonal families separate instead of collapsing them into one generic rowdriver answer.",
        ],
        "not_actionable_if": [
            "It only repeats Software PNGs or broad candidate means without helper-local or per-pixel typed values.",
            "It promotes direct or rotated-front-strength because they score better numerically despite violating AEX-shaped facts.",
            "It treats source-driven scatter ownership as the main angle-0 fix even though the dominant strip mask is unchanged locally.",
        ],
        "recommended_next_windows_probe": [
            pending_row["command"],
            "If the full package is resent, force the angle-0 answer to include the right strip endpoint (579,169) in addition to (494,169), so row coverage and leftward-exclusive helper behavior can be checked directly.",
            "If the diagonal witness cannot be traced at the exact pixel first, return the nearest high-residual hit only if it still includes typed rotate/validity/pre-writeback values.",
        ],
    }


def write_markdown(summary: dict, out: Path) -> None:
    lines = [
        "# OLMDirectionalBlur Pending Witness Proof",
        "",
        f"- Runtime package: `{summary['runtime_package']}`",
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
    lines.extend(["", "## Angle-0 Lane", ""])
    lines.append(f"- Classification: `{summary['angle0_lane']['classification']}`")
    lines.append(f"- Primary witness: `{summary['angle0_lane']['primary_witness']}`")
    lines.append(f"- Scan-order max witness: `{summary['angle0_lane']['scan_order_max_witness']}`")
    lines.append(f"- Current local readback: `{summary['angle0_lane']['current_local_readback']}`")
    lines.append("- Helper-local static facts:")
    for item in summary["angle0_lane"]["helper_local_static_facts"]:
        lines.append(f"  - {item}")
    lines.append(f"- Required next proof: {summary['angle0_lane']['required_next_proof']}")
    lines.extend(["", "## Diagonal Lane", ""])
    lines.append(f"- Classification: `{summary['diagonal_lane']['classification']}`")
    lines.append(f"- Primary witness: `{summary['diagonal_lane']['primary_witness']}`")
    lines.append(f"- Companion witnesses: `{summary['diagonal_lane']['companion_witnesses']}`")
    lines.append(f"- Current local readback: `{summary['diagonal_lane']['current_local_readback']}`")
    lines.append(f"- Required next proof: {summary['diagonal_lane']['required_next_proof']}")
    lines.extend(["", "## Actionable Return Criteria", ""])
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
        "--decision-json",
        type=Path,
        default=repo_root() / "refs" / "reports" / "olmdirectionalblur_decision_matrix_20260624" / "decision_matrix.json",
    )
    parser.add_argument(
        "--contract-json",
        type=Path,
        default=repo_root() / "refs" / "reports" / "olmdirectionalblur_witness_contract_20260624" / "witness_contract.json",
    )
    parser.add_argument(
        "--plan-json",
        type=Path,
        default=repo_root() / "refs" / "reports" / "olmdirectionalblur_witness_plan_20260625" / "witness_plan.json",
    )
    parser.add_argument(
        "--scatter-json",
        type=Path,
        default=repo_root() / "refs" / "reports" / "olmdirectionalblur_scatter_ownership_20260629.json",
    )
    parser.add_argument(
        "--pending-json",
        type=Path,
        default=repo_root() / "refs" / "reports" / "pending_runtime_trace_packages.json",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=repo_root() / "refs" / "conformance" / "olmdirectionalblur_pending_witness_proof_20260629.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=repo_root() / "refs" / "conformance" / "olmdirectionalblur_pending_witness_proof_20260629.md",
    )
    args = parser.parse_args()

    summary = build_summary(
        load_json(args.decision_json),
        load_json(args.contract_json),
        load_json(args.plan_json),
        load_json(args.scatter_json),
        load_json(args.pending_json),
    )
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(summary, args.output_md)
    print(args.output_json)
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
