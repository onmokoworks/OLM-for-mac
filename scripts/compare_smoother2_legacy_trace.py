#!/usr/bin/env python3
"""Classify returned OLMSmoother2 legacy current-AEX runtime trace facts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


WRITER_FRAME_REQUEST_ID = "olmsmoother2_current_aex_writer_frame_followup_trace_20260625"
PRODUCER_DIFF_REQUEST_ID = "olmsmoother2_current_aex_producer_path_diff_20260702"
WRITER_GATE_REQUEST_ID = "olmsmoother2_current_aex_0004_writer_gate_retry_20260702"
LOAD_PREWARM_REQUEST_ID = "olmsmoother2_current_aex_0004_load_prewarm_retry_20260703"
PRODUCER_BYTES_20260708_REQUEST_ID = "olmsmoother2_current_aex_producer_bytes_20260708"
BIND_THEN_READ_20260708_REQUEST_ID = "olmsmoother2_current_aex_0012_bind_then_read_20260708"
LEGACY_KEY_GAMMA_REQUEST_ID = "olmsmoother2_legacy_key_gamma_runtime_trace_20260620"

REQUEST_ORDER = [
    BIND_THEN_READ_20260708_REQUEST_ID,
    PRODUCER_BYTES_20260708_REQUEST_ID,
    WRITER_GATE_REQUEST_ID,
    PRODUCER_DIFF_REQUEST_ID,
    LOAD_PREWARM_REQUEST_ID,
    WRITER_FRAME_REQUEST_ID,
    LEGACY_KEY_GAMMA_REQUEST_ID,
]

LANE_STATE_JSON = (
    Path(__file__).resolve().parents[1]
    / "refs"
    / "conformance"
    / "olmsmoother2_legacy_lane_state_20260707.json"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-summary-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_result(summary: dict[str, Any], request_id: str) -> dict[str, Any] | None:
    for row in summary.get("results", []):
        if isinstance(row, dict) and row.get("request_id") == request_id:
            return row
    return None


def find_first_result(summary: dict[str, Any], request_ids: list[str]) -> tuple[str, dict[str, Any] | None]:
    for request_id in request_ids:
        row = find_result(summary, request_id)
        if row is not None:
            return request_id, row
    return request_ids[0], None


def observations_for(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {}
    observations = row.get("observations", {})
    return observations if isinstance(observations, dict) else {"raw": observations}


def case_rows(observations: dict[str, Any]) -> list[dict[str, Any]]:
    rows = observations.get("cases", [])
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def requested_values(observations: dict[str, Any]) -> dict[str, Any]:
    for key in ("requested_for_each_case", "requested_for_each_pixel", "requested_fields"):
        value = observations.get(key)
        if isinstance(value, dict):
            return value
    return {}


def witness_pixels(case: dict[str, Any]) -> list[dict[str, Any]]:
    pixels = case.get("witness_pixels", [])
    return [row for row in pixels if isinstance(row, dict)] if isinstance(pixels, list) else []


def observed_or_local_values(case: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for pixel in witness_pixels(case):
        intermediate = pixel.get("intermediate_values")
        if isinstance(intermediate, dict):
            values.update(intermediate)
    return values


def missing_field_matrix(request_id: str, observations: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in case_rows(observations):
        case_id = str(case.get("case_id") or "")
        if request_id == BIND_THEN_READ_20260708_REQUEST_ID:
            missing = [
                "Windows Stage A module base",
                "Windows Stage A exact hook/breakpoint site",
                "Windows Stage A exact xy binding",
                "Windows Stage A pointer recovery route",
                "Windows Stage B center_b0",
                "Windows Stage B prev_b0",
                "Windows Stage B left_b1",
                "Windows Stage B observed e170 c",
            ]
        elif request_id == PRODUCER_BYTES_20260708_REQUEST_ID and "0012" in case_id:
            missing = [
                "Windows same-run 0012 center_b0",
                "Windows same-run 0012 prev_b0",
                "Windows same-run 0012 left_b1",
                "Windows same-run 0012 observed e170 c",
                "Windows f270 append/no-append",
                "Windows e3a0 append/no-append",
            ]
        elif request_id == PRODUCER_BYTES_20260708_REQUEST_ID and "0004" in case_id:
            missing = [
                "Windows same-run 0004 iVar6",
                "Windows same-run 0004 iVar5",
                "Windows same-run 0004 class_prev_b3",
                "Windows emit/no-emit guard",
                "Windows polygon count",
                "Windows cce0 output floats",
            ]
        else:
            required = case.get("required_windows_fields", [])
            missing = [str(item) for item in required] if isinstance(required, list) else []
        rows.append(
            {
                "case_id": case_id or "-",
                "witness_pixels": [{"x": pixel.get("x"), "y": pixel.get("y")} for pixel in witness_pixels(case)],
                "local_or_package_values": observed_or_local_values(case),
                "missing_windows_fields": missing,
            }
        )
    return rows


def meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, list):
        return any(meaningful(item) for item in value)
    if isinstance(value, dict):
        return any(meaningful(item) for item in value.values())
    if isinstance(value, str):
        text = value.strip().lower()
        if not text or text in {"0x...", "none", "null", "n/a", "unknown"}:
            return False
        placeholder_needles = (
            "not isolated",
            "not reached",
            "inferred",
            "likely",
            "expected",
            "still needs",
            "untraced",
            "was not captured",
            "broad hit storm",
            "stalled before",
        )
        if any(needle in text for needle in placeholder_needles):
            return False
        return True
    return False


def classify_legacy_key_gamma(observations: dict[str, Any]) -> str:
    if not observations:
        return "await-windows-trace"
    req = requested_values(observations)
    setup = req.get("setup_and_keying", {}) if isinstance(req.get("setup_and_keying"), dict) else {}
    writeback = req.get("smoothing_and_writeback", {}) if isinstance(req.get("smoothing_and_writeback"), dict) else {}
    params = req.get("parameter_struct", {}) if isinstance(req.get("parameter_struct"), dict) else {}
    if meaningful(setup.get("active_palette_filter_value")) or meaningful(setup.get("scalar_key_filter_value")):
        return "legacy-key-mask-polarity-or-class-plane"
    if meaningful(setup.get("class_plane_byte_before_smoothing")) or meaningful(setup.get("class_plane_neighbors")):
        return "legacy-class-plane-generation"
    if meaningful(writeback.get("before_FUN_1800036e0_rgba_float_hex")):
        return "legacy-premultiply-gamma-or-writeback"
    if meaningful(writeback.get("final_rgba_8bit")):
        return "legacy-final-byte-writeback"
    if meaningful(params):
        return "legacy-parameter-struct-only"
    if case_rows(observations):
        return "trace-structure-present-values-missing"
    return "trace-too-sparse"


def classify_current_aex(request_id: str, row: dict[str, Any] | None, observations: dict[str, Any]) -> str:
    if row is None:
        return "await-windows-trace"
    summary = str(row.get("summary") or "").lower()
    if request_id == BIND_THEN_READ_20260708_REQUEST_ID:
        if "no fresh same-run windows stage a bind" in summary or "no fresh windows witness-local stop" in summary:
            return "0012-stage-a-bind-missing"
        return "0012-bind-then-read-unclassified"
    if request_id == PRODUCER_BYTES_20260708_REQUEST_ID:
        if "does not contain the requested same-run windows producer-byte" in summary:
            return "producer-byte-class-plane-windows-bind-missing"
        return "producer-byte-class-plane-unclassified"
    if request_id == WRITER_FRAME_REQUEST_ID:
        return "writer-frame-confirmed-producer-unresolved"
    if request_id == PRODUCER_DIFF_REQUEST_ID:
        if "loaded and broad breakpoints" in summary or "producer/writeback path is reachable" in summary:
            return "producer-path-diff-writer-anchor-reached"
        return "producer-path-diff-not-isolated"
    if request_id == WRITER_GATE_REQUEST_ID:
        if "stalled before olmsmoother2 loaded" in summary:
            return "writer-gate-preload-stall"
        return "writer-gate-not-isolated"
    if request_id == LOAD_PREWARM_REQUEST_ID:
        return "module-load-prewarm"
    return classify_legacy_key_gamma(observations)


def recommended_next_evidence(focus: str) -> str:
    if focus == "await-windows-trace":
        return "Import the focused Smoother2 current-AEX runtime trace return before changing legacy producer behavior."
    if focus == "0012-stage-a-bind-missing":
        return "Retry only the `0012 (91,841)` bind-then-read lane: first bind the Windows witness-local producer/class buffer address, then read center_b0, prev_b0, left_b1, and observed e170 c in the same run."
    if focus == "producer-byte-class-plane-windows-bind-missing":
        return "Do not repeat final writer bytes. Bind the first Windows producer divergence: 0012 e170 byte/c facts and 0004 scanner/class-plane facts."
    if focus == "writer-frame-confirmed-producer-unresolved":
        return "Keep the writer frame as the anchor and capture only the first c280/cce0 producer divergence for `legacy_case_0004_current_aex` and `legacy_case_0012_gamma5_red_blue_current_aex`."
    if focus == "producer-path-diff-writer-anchor-reached":
        return "The writer/proof path is reachable; next useful witness is the first diverging producer field, not another final writer replay."
    if focus == "producer-path-diff-not-isolated":
        return "Retry from the writer anchor and retain the first c280/cce0 divergence fields instead of broad breakpoint coverage alone."
    if focus == "writer-gate-preload-stall":
        return "Stabilize module load for the exact `0004` gate before asking for producer fields; this return does not yet reach the gate."
    if focus == "writer-gate-not-isolated":
        return "Hold the exact writer gate at `legacy_case_0004_current_aex (1903,519)` and capture switch index, polygon count, append inputs, and cce0 output floats."
    if focus == "module-load-prewarm":
        return "Treat this as startup/load stabilization only; once load is stable, go back to writer-gated or producer-diff witness collection."
    if focus == "legacy-key-mask-polarity-or-class-plane":
        return "Compare Color Key keep/drop decisions before smoothing."
    if focus == "legacy-class-plane-generation":
        return "Patch mask/class-plane creation before touching polygon weights."
    if focus == "legacy-premultiply-gamma-or-writeback":
        return "Inspect legacy gamma/premultiply/writeback only after current-AEX producer lanes are settled."
    if focus == "legacy-parameter-struct-only":
        return "The trace found params but not per-pixel state; request witness values next."
    if focus in {"trace-structure-present-values-missing", "trace-too-sparse"}:
        return "Do not tune from this return; repeat with the exact requested witness fields."
    return "Record the first producer-side divergence before changing OLMSmoother2 legacy behavior."


def summarize_windows(request_id: str, row: dict[str, Any] | None) -> dict[str, Any]:
    observations = observations_for(row)
    return {
        "present": row is not None,
        "request_id": request_id,
        "status": row.get("status") if row else None,
        "summary": row.get("summary") if row else None,
        "source_file": row.get("source_file") if row else None,
        "cases": case_rows(observations),
        "requested_values": requested_values(observations),
        "directly_observed_vs_inferred": observations.get("directly_observed_vs_inferred") if observations else None,
        "ae_context": observations.get("ae_context") if observations else None,
        "missing_field_matrix": missing_field_matrix(request_id, observations),
    }


def load_lane_state() -> dict[str, Any] | None:
    if not LANE_STATE_JSON.exists():
        return None
    data = load_json(LANE_STATE_JSON)
    if not isinstance(data, dict):
        return None
    return {
        "status": data.get("status"),
        "decision": data.get("decision"),
        "recommended_action": data.get("recommended_action"),
        "safe_claim": data.get("safe_claim"),
        "latest_windows_return": data.get("latest_windows_return"),
        "cases": data.get("cases"),
        "global_rejections": data.get("global_rejections"),
    }


def build_comparison(summary: dict[str, Any]) -> dict[str, Any]:
    request_id, row = find_first_result(summary, REQUEST_ORDER)
    observations = observations_for(row)
    comparison = {
        "kind": "olmsmoother2_legacy_trace_comparison",
        "schema": 2,
        "request_id": request_id,
        "likely_next_focus": classify_current_aex(request_id, row, observations),
        "recommended_next_evidence": recommended_next_evidence(classify_current_aex(request_id, row, observations)),
        "windows": summarize_windows(request_id, row),
    }
    lane_state = load_lane_state()
    if lane_state:
        comparison["local_legacy_lane_state"] = lane_state
    return comparison


def md_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, ensure_ascii=False, sort_keys=True) + "`"
    return f"`{value}`"


def render_markdown(comparison: dict[str, Any]) -> str:
    windows = comparison["windows"]
    lane_state = comparison.get("local_legacy_lane_state")
    lines = [
        "# OLMSmoother2 Legacy Trace Comparison",
        "",
        f"- Request: `{comparison['request_id']}`",
        f"- Likely next focus: `{comparison['likely_next_focus']}`",
        f"- Recommended next evidence: {comparison['recommended_next_evidence']}",
        f"- Windows trace present: `{bool(windows.get('present'))}`",
        "",
        "## Windows Observations",
        "",
        f"- Status: {md_value(windows.get('status'))}",
        f"- Summary: {windows.get('summary') or '-'}",
        f"- AE context: {md_value(windows.get('ae_context'))}",
        f"- Cases: {md_value(windows.get('cases'))}",
        f"- Requested values: {md_value(windows.get('requested_values'))}",
        f"- Observed/inferred split: {md_value(windows.get('directly_observed_vs_inferred'))}",
        "",
    ]
    if windows.get("missing_field_matrix"):
        lines.extend(["## Missing Field Matrix", ""])
        for row in windows["missing_field_matrix"]:
            lines.extend(
                [
                    f"### {row.get('case_id')}",
                    "",
                    f"- Witness pixels: {md_value(row.get('witness_pixels'))}",
                    f"- Local/package values: {md_value(row.get('local_or_package_values'))}",
                    f"- Missing Windows fields: {md_value(row.get('missing_windows_fields'))}",
                    "",
                ]
            )
    if lane_state:
        lines.extend(
            [
                "## Local Legacy Lane State",
                "",
                f"- Status: {md_value(lane_state.get('status'))}",
                f"- Decision: {md_value(lane_state.get('decision'))}",
                f"- Recommended action: {lane_state.get('recommended_action') or '-'}",
                f"- Safe claim: {lane_state.get('safe_claim') or '-'}",
                f"- Latest Windows return: {md_value(lane_state.get('latest_windows_return'))}",
                f"- Cases: {md_value(lane_state.get('cases'))}",
                f"- Global rejections: {md_value(lane_state.get('global_rejections'))}",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "- `writer-frame-confirmed-producer-unresolved`: final writer bytes/floats are already grounded; keep the next trace at the first producer divergence.",
            "- `producer-path-diff-writer-anchor-reached`: the writer/proof path is reachable, but the first differing producer field is still missing.",
            "- `producer-path-diff-not-isolated`: broad breakpoints are not enough; preserve c280/cce0 divergence fields only.",
            "- `writer-gate-preload-stall`: stabilize module load before requesting exact gated producer facts.",
            "- `writer-gate-not-isolated`: exact gate reached, but the requested c280/polygon/cce0 fields are still missing.",
            "- `module-load-prewarm`: startup/load-only evidence; not yet an implementation proof lane.",
            "- `0012-stage-a-bind-missing`: July 8 narrowed the request, but Windows Stage A bind and Stage B producer-byte reads are still missing.",
            "- `producer-byte-class-plane-windows-bind-missing`: local producer facts exist, but they are not Windows same-run typed facts.",
            "- `trace-too-sparse`: do not tune from PNGs or broad summaries.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    summary_path = resolve(root, args.runtime_summary_json)
    if not summary_path.exists():
        return fail(f"runtime summary JSON not found: {summary_path}")
    summary = load_json(summary_path)
    if not isinstance(summary, dict):
        return fail("runtime summary JSON must be an object")
    comparison = build_comparison(summary)
    if args.output_json:
        output = resolve(root, args.output_json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(comparison, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        print(f"comparison_json={output}")
    if args.output_md:
        output = resolve(root, args.output_md)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_markdown(comparison), encoding="utf-8")
        print(f"comparison_md={output}")
    if not args.output_json and not args.output_md:
        print(render_markdown(comparison))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
