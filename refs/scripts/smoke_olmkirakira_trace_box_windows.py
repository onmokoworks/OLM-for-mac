#!/usr/bin/env python3
"""Smoke-test OLMKiraKira trace JSON boxFilter input windows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_TRACE = Path("refs/reports/olmkirakira_trace_baseline_20260622_box_windows_mac/trace.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-json", type=Path, default=DEFAULT_TRACE)
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    args = parse_args()
    root = repo_root()
    trace_path = args.trace_json if args.trace_json.is_absolute() else root / args.trace_json
    data = json.loads(trace_path.read_text(encoding="utf-8"))
    ray = next(row for row in data.get("rays", []) if row.get("ray") == "vertical")
    checked = 0
    for box_filter in ray.get("box_filters", []):
        for sample in box_filter.get("samples", []):
            window = sample.get("input_window")
            if not window:
                raise AssertionError(f"missing input_window for pass {box_filter.get('pass')} {sample.get('label')}")
            values = window.get("values") or []
            if len(values) != 50:
                raise AssertionError(f"expected 50 samples, got {len(values)}")
            mean = float(window["mean"])
            output = float(sample["value"])
            if abs(mean - output) > 1.0e-6:
                raise AssertionError(
                    f"window mean mismatch pass {box_filter.get('pass')} {sample.get('label')}: "
                    f"mean={mean} output={output}"
                )
            checked += 1
    if checked != 9:
        raise AssertionError(f"expected 9 box windows, checked {checked}")
    print("[OK] OLMKiraKira box window trace smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
