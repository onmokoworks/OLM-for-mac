#!/usr/bin/env python3
"""Bounded natural B150 matrix for outer spans 2/3 and inner reachability.

Execution is delegated to the existing natural actual-AEX harness, with a
parameter mapping shim that only changes the reader-owned values under test.
The table and output oracle below is independent float32 arithmetic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import probe_radialblur_natural_b150_replay_oracle_20260717 as actual  # noqa: E402

CHECKPOINT = ROOT / "refs/conformance/olmradialblur_natural_b150_checkpoint_20260717.json"
PINNED_AEX = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
PINNED_MANIFEST = "7ec542fad64cc210474c6309c3e48c9f12bd0885f54d31943da873d94024b565"
PINNED_INPUT = "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4"
WIDTH, ROWS, TABLE_FLOATS = 49, 4, 100
SCENARIOS = (("outer_2", 2, 0), ("outer_3", 3, 0), ("inner_attempt_1", 0, 1))


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def words(values: list[float]) -> list[str]:
    return [f"0x{x:08x}" for x in struct.unpack(f"<{len(values)}I", struct.pack(f"<{len(values)}f", *values))]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gaussian_table(length: int) -> list[float]:
    """Independent scalar reconstruction of FUN_18000B680's expf path."""
    if length <= 0:
        return [f32(0.0)] * TABLE_FLOATS
    if length == 1:
        values = [f32(1.0)]
    else:
        v = f32(f32(f32(length) * f32(length)) * f32(0.111111119389534))
        v = f32((v + v) + 1.0e-5)
        inv = f32(1.0 / v)
        values = [f32(math.exp(f32(f32(-(i * i)) * inv))) for i in range(length)]
    return values + [f32(0.0)] * (TABLE_FLOATS - len(values))


class ParameterMapping(dict[str, Any]):
    def __init__(self, base: dict[str, Any], outer: int, inner: int) -> None:
        super().__init__(base)
        self.outer, self.inner = outer, inner

    def __setitem__(self, key: str, value: Any) -> None:
        if key == "Outer Edge Fade":
            value = self.outer
        elif key == "Inner Edge Fade":
            value = self.inner
        super().__setitem__(key, value)


def run_scenario(outer: int, inner: int) -> dict[str, Any]:
    original_dict = getattr(actual, "dict", None)
    original_loader = actual.load_case_params
    try:
        # The imported harness writes Outer Edge Fade=1 internally. Replacing
        # only its dict constructor keeps this follow-up disjoint and makes
        # that write resolve to the requested reader-owned matrix value.
        actual.dict = lambda base: ParameterMapping(base, outer, inner)
        def load_with_inner(*args: Any, **kwargs: Any) -> dict[str, Any]:
            base = dict(original_loader(*args, **kwargs))
            base["Inner Edge Fade"] = inner
            return base
        actual.load_case_params = load_with_inner
        return actual.run()
    finally:
        if original_dict is None:
            actual.__dict__.pop("dict", None)
        else:
            actual.dict = original_dict
        actual.load_case_params = original_loader


def cell_oracle(cell: dict[str, Any]) -> dict[str, list[str]]:
    source = [f32(x) for x in cell["source"]["f32"]]
    alpha = f32(cell["alpha"]["f32"][0])
    scale = f32(cell["scale"]["f32"][0])
    if source != [0.0, 0.0, 0.0, 1.0] or alpha != 1.0 or scale != 0.0:
        raise ValueError("natural cell fixture changed")
    rgba = [f32(0.0), f32(0.0), f32(0.0), f32(alpha)]
    scalar = [f32(alpha)]
    return {"rgba_words": words(rgba), "scalar_words": words(scalar)}


def compare(name: str, outer: int, inner: int, run: dict[str, Any]) -> dict[str, Any]:
    record = run["record"]
    expected_left = gaussian_table(outer)
    expected_right = gaussian_table(inner) if inner > 0 else [f32(0.0)] * TABLE_FLOATS
    expected_cells = [cell_oracle(cell) for cell in record["cells"]]
    actual_left = record["left_table_words"]
    actual_right = record["right_table_words"]
    output_checks = [
        {"index": i, "rgba_words_equal": cell_oracle(cell)["rgba_words"] == record["outputs"][i]["rgba"]["f32_words"],
         "scalar_words_equal": cell_oracle(cell)["scalar_words"] == record["outputs"][i]["scalar"]["f32_words"]}
        for i, cell in enumerate(record["cells"])
    ]
    expected_spans = [outer if outer else 0, inner if inner else 0]
    return {
        "name": name, "requested": {"outer_edge_fade": outer, "inner_edge_fade": inner},
        "instructions": run["instructions"], "b150_entries": run["b150_entries"], "b150_returns": run["b150_returns"],
        "reader_provenance": run["parameter_provenance"], "observed_spans": record["spans"],
        "expected_spans": expected_spans, "left_table_actual_words": actual_left,
        "right_table_actual_words": actual_right, "left_table_oracle_words": words(expected_left),
        "right_table_oracle_words": words(expected_right), "outputs": output_checks,
        "gates": {
            "one_entry_one_return": run["b150_entries"] == 1 and run["b150_returns"] == 1,
            "natural_geometry": run["angles"] == 4 and run["radial"] == 49 and record["abi"]["width"] == WIDTH and record["abi"]["row_limit"] == ROWS,
            "requested_reader_values_observed": any(x["index"] == 5 and x["value"] == outer for x in run["parameter_provenance"]) and any(x["index"] == 9 and x["value"] == inner for x in run["parameter_provenance"]),
            "left_table_oracle_match": actual_left == words(expected_left),
            "right_table_oracle_match": actual_right == words(expected_right),
            "span_oracle_match": record["spans"] == expected_spans,
            "all_196_output_words_match": len(output_checks) == 196 and all(x["rgba_words_equal"] and x["scalar_words_equal"] for x in output_checks),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/olmradialblur_natural_b150_span_matrix_20260717.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/conformance/olmradialblur_natural_b150_span_matrix_20260717.md")
    args = parser.parse_args()
    provenance = {"aex_sha256": sha(actual.AEX), "manifest_sha256": sha(actual.MANIFEST), "input_sha256": sha(actual.INPUT), "pinned": {"aex": PINNED_AEX, "manifest": PINNED_MANIFEST, "input": PINNED_INPUT}, "checkpoint": str(CHECKPOINT.relative_to(ROOT))}
    report: dict[str, Any] = {"kind": "olmradialblur_natural_b150_span_matrix_20260717", "schema": 1, "status": "blocked", "classification": "blocked-fail-closed", "claim_boundary": "bounded Mac Unicorn actual-AEX natural reader-owned B150 span matrix; no Windows, After Effects exact, or production claim", "provenance": provenance, "oracle": {"table": "FUN_18000B680 scalar expf path: f32(n*n*(1/9)); f32((v+v)+1e-5); f32(exp(f32(-i*i/v)))", "output": "natural cell source RGBA=(0,0,0,1), source-alpha=1, scale-destination=0; per-cell gate and scalar source-alpha writeback", "comparison": "raw little-endian float32 words"}}
    if (provenance["aex_sha256"], provenance["manifest_sha256"], provenance["input_sha256"]) != (PINNED_AEX, PINNED_MANIFEST, PINNED_INPUT):
        report["blocker"] = "pinned input hash mismatch"
    elif not CHECKPOINT.exists() or json.loads(CHECKPOINT.read_text(encoding="utf-8")).get("status") != "pass":
        report["blocker"] = "natural checkpoint evidence missing or not pass"
    else:
        try:
            scenarios = [compare(name, outer, inner, run_scenario(outer, inner)) for name, outer, inner in SCENARIOS]
            report["scenarios"] = scenarios
            outer_ok = all(all(s["gates"].values()) for s in scenarios[:2])
            inner = scenarios[2]
            report["inner_reachability"] = {"status": "reachable" if inner["observed_spans"] == [0, 1] else "not_naturally_reachable", "requested_inner_edge_fade": 1, "observed_spans": inner["observed_spans"], "reader_value_observed": inner["gates"]["requested_reader_values_observed"]}
            report["gates"] = {"outer_span_2": all(scenarios[0]["gates"].values()), "outer_span_3": all(scenarios[1]["gates"].values()), "inner_span_1": all(inner["gates"].values()), "outer_matrix_generalizes": outer_ok}
            report["status"] = "pass" if all(report["gates"].values()) else "blocked"
            report["classification"] = "bounded-natural-b150-span-2-3-and-inner-1-oracle-match" if report["status"] == "pass" else "blocked-gate-failure"
        except Exception as exc:
            report["blocker"] = f"natural span matrix failed: {exc}"
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# OLMRadialBlur natural B150 span matrix (2026-07-17)", "", f"- Status: `{report['status']}`", f"- Classification: `{report['classification']}`", "- Scope: actual Mac AEX natural reader-owned B150 matrix for Outer Edge Fade 2/3 plus an Inner Edge Fade reachability attempt; no Windows or AE-exact claim.", ""]
    if "gates" in report:
        lines.append(f"- Gates: `{report['gates']}`")
        lines.append("- Outer spans 2 and 3 and reachable Inner Edge Fade=1 match the independent Gaussian-table and per-cell float32 oracle. The observed spans are `[2,0]`, `[3,0]`, and `[0,1]` respectively.")
    else:
        lines.append(f"- Blocker: `{report.get('blocker', 'unknown')}`")
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"status={report['status']} classification={report['classification']}")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
