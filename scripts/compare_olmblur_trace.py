#!/usr/bin/env python3
"""Classify returned OLMBlur repeat/writeback runtime trace facts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


CANONICAL_REQUEST_ID = "olmblur_case0006_helper_prestore_witness_20260630"
SECONDARY_REQUEST_IDS = {
    "olmblur_final_word_witness_20260630",
}
LEGACY_REQUEST_IDS = {
    "olmblur_last1px_runtime_trace_20260629",
    "olmblur_repeat_threshold_runtime_trace_20260619",
}
DEFAULT_BASELINE_DIR = Path("refs/reports/olmblur_trace_baseline_20260619_030633_mac")
DEFAULT_CURRENT_WORD_BASELINE_JSON = Path("refs/conformance/olmblur_current_word_baseline_20260629.json")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-summary-json", type=Path, required=True)
    parser.add_argument("--local-baseline-dir", type=Path, default=DEFAULT_BASELINE_DIR)
    parser.add_argument("--current-word-baseline-json", type=Path, default=DEFAULT_CURRENT_WORD_BASELINE_JSON)
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


def find_result(summary: dict[str, Any]) -> dict[str, Any] | None:
    for request_id in [CANONICAL_REQUEST_ID, *sorted(SECONDARY_REQUEST_IDS), *sorted(LEGACY_REQUEST_IDS)]:
        for row in summary.get("results", []):
            if isinstance(row, dict) and row.get("request_id") == request_id:
                return row
    return None


def concrete_trace_value(value: Any) -> bool:
    """Return true only for values that look like measured Windows runtime facts."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, list):
        return any(concrete_trace_value(item) for item in value)
    if isinstance(value, dict):
        return any(concrete_trace_value(item) for item in value.values())
    if isinstance(value, str):
        text = value.strip().lower()
        if not text or text in {
            "0x...",
            "floorf(value + 0.5) | cvt/trunc | other",
            "",
            "none",
            "null",
            "n/a",
            "unknown",
        }:
            return False
        if re.fullmatch(r"[-+]?0x[0-9a-f]+(?:\.[0-9a-f]*)?p[-+]?\d+", text):
            return True
        placeholder_needles = (
            "not isolated",
            "not reached",
            "inferred",
            "likely",
            "expected",
            "runtime",
            "still needs",
            "untraced",
            "unknown",
            "needs live",
            "was not captured",
        )
        if any(needle in text for needle in placeholder_needles):
            return False
        return False
    return False


def read_local_baseline(path: Path) -> dict[str, Any]:
    traces: dict[str, list[dict[str, Any]]] = {}
    pattern = re.compile(
        r"OLMBLUR_TRACE x=(?P<x>-?\d+) y=(?P<y>-?\d+) "
        r"rgb=\((?P<rgb>[^)]*)\) rgb_hex=\((?P<rgb_hex>[^)]*)\) "
        r"floor05=\((?P<floor05>[^)]*)\) nearby=\((?P<nearby>[^)]*)\) "
        r"legacy=(?P<legacy>\d+) repeat=(?P<repeat>\d+)"
    )
    for log_path in sorted(path.glob("case_*_trace.log")):
        rows = []
        for line in log_path.read_text(encoding="utf-8").splitlines():
            match = pattern.search(line)
            if not match:
                continue
            rows.append(
                {
                    "x": int(match.group("x")),
                    "y": int(match.group("y")),
                    "rgb": [part.strip() for part in match.group("rgb").split(",")],
                    "rgb_hex": [part.strip() for part in match.group("rgb_hex").split(",")],
                    "floor05": [part.strip() for part in match.group("floor05").split(",")],
                    "nearby": [part.strip() for part in match.group("nearby").split(",")],
                    "legacy": int(match.group("legacy")),
                    "repeat": int(match.group("repeat")),
                }
            )
        traces[log_path.stem.replace("_trace", "")] = rows
    diff_path = path / "diff.json"
    diff = load_json(diff_path) if diff_path.exists() else None
    return {"baseline_dir": str(path), "traces": traces, "diff": diff}


def read_current_word_baseline(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    if not isinstance(payload, dict):
        return {"baseline_json": str(path), "cases": {}, "samples_by_case": {}}
    cases = payload.get("cases", [])
    if not isinstance(cases, list):
        cases = []
    by_case: dict[str, dict[str, Any]] = {}
    samples_by_case: dict[str, dict[tuple[int, int], dict[str, Any]]] = {}
    for case in cases:
        if not isinstance(case, dict):
            continue
        case_id = str(case.get("case_id"))
        by_case[case_id] = case
        sample_map: dict[tuple[int, int], dict[str, Any]] = {}
        for sample in case.get("samples", []):
            if not isinstance(sample, dict):
                continue
            try:
                key = (int(sample.get("x")), int(sample.get("y")))
            except (TypeError, ValueError):
                continue
            sample_map[key] = sample
        samples_by_case[case_id] = sample_map
    return {
        "baseline_json": str(path),
        "cases": by_case,
        "samples_by_case": samples_by_case,
    }


def summarize_windows(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {"present": False}
    observations = row.get("observations", {})
    if not isinstance(observations, dict):
        observations = {"raw": observations}
    cases = observations.get("cases", [])
    if not isinstance(cases, list):
        cases = []
    if not cases and observations.get("case_id") == "olmblur__case_0006":
        cases = [observations]
    by_case = {case.get("case_id"): case for case in cases if isinstance(case, dict)}
    case_0006 = by_case.get("case_0006") or by_case.get("olmblur__case_0006")
    case_0007 = by_case.get("case_0007") or by_case.get("olmblur__case_0007")
    return {
        "present": True,
        "status": row.get("status"),
        "summary": row.get("summary"),
        "source_file": row.get("source_file"),
        "cases": cases,
        "case_0006": case_0006,
        "case_0007": case_0007,
    }


def maybe_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().lower()
        try:
            return float(value)
        except ValueError:
            if text.startswith(("-0x", "+0x", "0x")) and "p" in text:
                try:
                    return float.fromhex(value)
                except ValueError:
                    return None
            return None
    return None


def maybe_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            f = float(value)
        except ValueError:
            return None
        if f.is_integer():
            return int(f)
    return None


def build_case0006_narrow_analysis(
    windows_case: dict[str, Any] | None,
    current_word_baseline: dict[str, Any],
) -> dict[str, Any] | None:
    if not isinstance(windows_case, dict):
        return None
    witnesses = windows_case.get("witnesses", [])
    if not isinstance(witnesses, list) or not witnesses:
        return None
    sample_map = current_word_baseline.get("samples_by_case", {}).get("olmblur__case_0006", {})
    results: list[dict[str, Any]] = []
    for witness in witnesses:
        if not isinstance(witness, dict):
            continue
        x = maybe_int(witness.get("x"))
        y = maybe_int(witness.get("y"))
        if x is None or y is None:
            continue
        sample = sample_map.get((x, y), {})
        probe = sample.get("probe", {}) if isinstance(sample, dict) else {}
        mac_raw = [maybe_float(v) for v in probe.get("raw", [])] if isinstance(probe, dict) else []
        mac_stored = [maybe_int(v) for v in probe.get("stored", [])] if isinstance(probe, dict) else []
        windows_pre_store = witness.get("windows_pre_store_rgb_float")
        if not isinstance(windows_pre_store, list):
            windows_pre_store = []
        if not windows_pre_store:
            windows_pre_store = witness.get("windows_pre_store_rgb_hex")
            if not isinstance(windows_pre_store, list):
                windows_pre_store = []
        windows_pre_store = [maybe_float(v) for v in windows_pre_store]
        windows_words = witness.get("windows_internal_word_store")
        if not isinstance(windows_words, list):
            windows_words = []
        windows_words = [maybe_int(v) for v in windows_words]

        if windows_pre_store and mac_raw and windows_words and mac_stored:
            if windows_words[0] != mac_stored[0]:
                if windows_pre_store[0] is not None and mac_raw[0] is not None:
                    if windows_pre_store[0] < mac_raw[0]:
                        verdict = "windows-prestore-lower-than-mac"
                    elif windows_pre_store[0] > mac_raw[0]:
                        verdict = "windows-prestore-higher-than-mac"
                    else:
                        verdict = "same-prestore-different-store"
                else:
                    verdict = "different-word-store-with-incomplete-float"
            else:
                verdict = "same-word-store"
        else:
            verdict = "incomplete-case0006-witness"

        results.append(
            {
                "xy": [x, y],
                "mac_probe_raw": mac_raw,
                "mac_probe_stored_word": mac_stored,
                "windows_pre_store_rgb_float": windows_pre_store,
                "windows_internal_word_store": windows_words,
                "sample_reference_rgba": sample.get("reference") if isinstance(sample, dict) else None,
                "sample_candidate_rgba": sample.get("candidate") if isinstance(sample, dict) else None,
                "verdict": verdict,
            }
        )
    if not results:
        return None
    return {
        "case_id": "olmblur__case_0006",
        "results": results,
    }


def has_prewriteback(case: dict[str, Any] | None) -> bool:
    if not isinstance(case, dict):
        return False
    for pixel in case.get("residual_pixels", []):
        if not isinstance(pixel, dict):
            continue
        if concrete_trace_value(pixel.get("aex_pre_writeback_rgb")):
            return True
        if concrete_trace_value(pixel.get("aex_pre_writeback_rgb_hex")):
            return True
        if concrete_trace_value(pixel.get("aex_writeback_operation")):
            return True
        if concrete_trace_value(pixel.get("aex_final_rgba")):
            return True
    return False


def has_case0006_helper_prestore(case: dict[str, Any] | None) -> bool:
    if not isinstance(case, dict):
        return False
    for pixel in case.get("witnesses", []):
        if not isinstance(pixel, dict):
            continue
        if concrete_trace_value(pixel.get("windows_helper_or_last_upstream_rgb_hex")):
            return True
        if concrete_trace_value(pixel.get("windows_pre_store_rgb_hex")):
            return True
        if concrete_trace_value(pixel.get("windows_pre_store_rgb_float")):
            return True
        if concrete_trace_value(pixel.get("windows_internal_word_store")):
            return True
        if concrete_trace_value(pixel.get("windows_final_rgba")):
            return True
    return False


def has_legacy_state(case: dict[str, Any] | None) -> bool:
    if not isinstance(case, dict):
        return False
    for pixel in case.get("residual_pixels", []):
        if not isinstance(pixel, dict):
            continue
        if concrete_trace_value(pixel.get("legacy_all_same_state")):
            return True
        if concrete_trace_value(pixel.get("legacy_border_sample_included")):
            return True
        if concrete_trace_value(pixel.get("aex_pre_writeback_rgb")):
            return True
        if concrete_trace_value(pixel.get("aex_pre_writeback_rgb_hex")):
            return True
        if concrete_trace_value(pixel.get("aex_final_rgba")):
            return True
    return False


def classify_next_focus(windows: dict[str, Any], current_word_baseline: dict[str, Any]) -> str:
    if not windows.get("present"):
        return "await-windows-trace"
    case_0006 = windows.get("case_0006")
    case_0007 = windows.get("case_0007")
    narrow = build_case0006_narrow_analysis(case_0006, current_word_baseline)
    if narrow:
        verdicts = [str(row.get("verdict") or "") for row in narrow.get("results", []) if isinstance(row, dict)]
        if verdicts and all(verdict == "same-word-store" for verdict in verdicts):
            return "case0006-reference-or-export-provenance"
    if has_case0006_helper_prestore(case_0006):
        return "case0006-helper-or-prestore"
    if has_prewriteback(case_0006):
        return "nonlegacy-accumulation-or-writeback"
    if has_legacy_state(case_0007):
        return "legacy-border-or-all-same"
    if case_0006 or case_0007:
        return "trace-structure-present-values-missing"
    return "trace-too-sparse"


def build_comparison(summary: dict[str, Any], baseline_dir: Path, current_word_baseline_json: Path) -> dict[str, Any]:
    row = find_result(summary)
    windows = summarize_windows(row)
    current_word_baseline = read_current_word_baseline(current_word_baseline_json)
    case0006_narrow_analysis = build_case0006_narrow_analysis(windows.get("case_0006"), current_word_baseline)
    return {
        "kind": "olmblur_trace_comparison",
        "schema": 1,
        "request_id": (row or {}).get("request_id", CANONICAL_REQUEST_ID),
        "likely_next_focus": classify_next_focus(windows, current_word_baseline),
        "local_baseline": read_local_baseline(baseline_dir),
        "current_word_baseline": {
            "baseline_json": current_word_baseline.get("baseline_json"),
            "available_cases": sorted(current_word_baseline.get("cases", {}).keys()),
        },
        "windows": windows,
        "case0006_narrow_analysis": case0006_narrow_analysis,
    }


def md_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, ensure_ascii=False, sort_keys=True) + "`"
    return f"`{value}`"


def render_markdown(comparison: dict[str, Any]) -> str:
    windows = comparison["windows"]
    baseline = comparison["local_baseline"]
    current_word_baseline = comparison.get("current_word_baseline") or {}
    case0006_narrow_analysis = comparison.get("case0006_narrow_analysis")
    lines = [
        "# OLMBlur Trace Comparison",
        "",
        f"- Request: `{comparison['request_id']}`",
        f"- Likely next focus: `{comparison['likely_next_focus']}`",
        f"- Windows trace present: `{bool(windows.get('present'))}`",
        f"- Local baseline: `{baseline.get('baseline_dir')}`",
        f"- Current word baseline: `{current_word_baseline.get('baseline_json')}`",
        "",
        "## Local Baseline",
        "",
        f"- Trace cases: {md_value(sorted(baseline.get('traces', {}).keys()))}",
        f"- Diff summary: {md_value((baseline.get('diff') or {}).get('summary'))}",
        "",
        "## Windows Observations",
        "",
        f"- Status: {md_value(windows.get('status'))}",
        f"- Summary: {windows.get('summary') or '-'}",
        f"- Case 0006: {md_value(windows.get('case_0006'))}",
        f"- Case 0007: {md_value(windows.get('case_0007'))}",
        "",
    ]
    if case0006_narrow_analysis:
        lines.extend([
            "## Case 0006 Narrow Analysis",
            "",
            f"- Summary: {md_value(case0006_narrow_analysis)}",
            "",
        ])
    lines.extend([
        "## Interpretation",
        "",
        "- `case0006-reference-or-export-provenance`: Windows and Mac now agree on the traced pre-store float and stored 16bpc word at the active `case_0006` witnesses, so the remaining exported-PNG mismatch should be treated as reference provenance / export-layer evidence, not as a live OLMBlur helper-or-writer bug.",
        "- `case0006-helper-or-prestore`: the new narrow case_0006 witness returned concrete upstream/pre-store values; compare those before changing OLMBlur math.",
        "- `nonlegacy-accumulation-or-writeback`: decide whether case_0006 differs before or only at byte writeback.",
        "- `legacy-border-or-all-same`: settle case_0007 border inclusion and all-same helper state.",
        "- `trace-structure-present-values-missing`: return the requested per-pixel values before changing code.",
        "- `trace-too-sparse`: request missing residual-pixel values instead of PNG tuning.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    summary_path = resolve(root, args.runtime_summary_json)
    baseline_dir = resolve(root, args.local_baseline_dir)
    current_word_baseline_json = resolve(root, args.current_word_baseline_json)
    if not summary_path.exists():
        return fail(f"runtime summary JSON not found: {summary_path}")
    if not baseline_dir.exists():
        return fail(f"local baseline dir not found: {baseline_dir}")
    if not current_word_baseline_json.exists():
        return fail(f"current word baseline JSON not found: {current_word_baseline_json}")
    summary = load_json(summary_path)
    if not isinstance(summary, dict):
        return fail("runtime summary JSON must be an object")
    comparison = build_comparison(summary, baseline_dir, current_word_baseline_json)
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
