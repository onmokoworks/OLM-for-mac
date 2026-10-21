#!/usr/bin/env python3
"""Bind actual-AEX powf XMM inputs to the fixed PF32 Power production calls."""
from __future__ import annotations

import argparse
from collections import Counter
import functools
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[2]
REQUEST = ROOT / "tools/emulation/test_olmdistancegradation_pf32_power_ucrt_request_20260813.py"
DOWNSTREAM = ROOT / "tools/emulation/test_olm_math_ucrt_downstream_replay_20260814.py"
PATCH = ROOT / "tools/emulation/aexcompat_olmdistancegradation_powf_xmm_trace_20260814.patch"
AEX = ROOT / "aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex"
CALLBACKS = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout/guest/crates/aex-guest-worker/src/x64/callbacks.rs")
REPORT = ROOT / "refs/conformance/olmdistancegradation_actual_aex_powf_xmm_closure_20260814.json"
NOTE = REPORT.with_suffix(".md")

CELLS = tuple((mode, background) for mode in range(2, 6) for background in (0, 1))
PRODUCTION_ONLY = (
    ("0x00000000", "0x40100000"), ("0x3d30aa30", "0x40100000"),
    ("0x3d800000", "0x40100000"), ("0x3daaaaab", "0x40100000"),
    ("0x3db1a33b", "0x40100000"), ("0x3ded413d", "0x40100000"),
    ("0x3e1a011a", "0x40100000"),
)
WORKER_SHA256 = "03714915d5e19ebe6aa98529881aa6410ec4895ee55d2cc29090b4f5327cec8b"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def identities() -> dict[str, str]:
    return {
        "actual_aex_sha256": sha(AEX), "aexcompat_callbacks_sha256": sha(CALLBACKS),
        "trace_patch_sha256": sha(PATCH), "production_census_generator_sha256": sha(REQUEST),
        "downstream_replay_sha256": sha(DOWNSTREAM), "traced_worker_sha256": WORKER_SHA256,
    }


def parse_trace(path: Path) -> list[dict[str, str]]:
    rows = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        parts = line.split(",")
        if len(parts) != 3 or any(len(word) != 8 or any(c not in "0123456789abcdef" for c in word) for word in parts):
            raise RuntimeError(f"trace row {number}")
        rows.append({"input_bits": "0x" + parts[0], "exponent_bits": "0x" + parts[1],
                     "host_substituted_result_bits": "0x" + parts[2]})
    if len(rows) != 992:
        raise RuntimeError(f"actual trace count {len(rows)}")
    return rows


def match_subsequence(production: list[tuple[str, str, str]], actual: list[tuple[str, str, str]]) -> list[int]:
    positions = []
    cursor = 0
    for row in actual:
        while cursor < len(production) and production[cursor] != row:
            cursor += 1
        if cursor == len(production):
            raise RuntimeError("actual XMM trace is not a production subsequence")
        positions.append(cursor); cursor += 1
    return positions


def counterfactuals(request, downstream, actual_pairs: set[tuple[str, str]]) -> dict[str, object]:
    expf, powf = downstream.maps_from_host()
    _, distance_vectors, _ = request.run_census()
    distance_keys = {(row["input_bits"], row["exponent_bits"]) for row in distance_vectors}
    powf = {key: value for key, value in powf.items() if key in distance_keys}
    extra = sorted(set(powf) - actual_pairs)
    if tuple(extra) != PRODUCTION_ONLY:
        raise RuntimeError(f"production-only pair drift: {extra}")
    results = {}
    for name, replacement in (("all_zero", "0x00000000"), ("all_one", "0x3f800000")):
        changed = dict(powf)
        for key in extra:
            changed[key] = replacement
        with tempfile.TemporaryDirectory(prefix="dg-powf-xmm-counterfactual-") as raw:
            temp = Path(raw); table = temp / "table.txt"
            downstream.write_table(table, expf, changed)
            replay = downstream.replay_distance(temp, table)
        if replay["matching_host_substituted_cells"] != 8:
            raise RuntimeError(f"production-only counterfactual changed output: {name}")
        results[name] = {"replacement_bits": replacement, "matching_cells": 8,
                         "raw_sha256": {row["cell"]: row["raw_sha256"] for row in replay["cells"]}}
    return {"production_only_pairs": [list(key) for key in extra], "pair_count": 7,
            "pixel_calls_per_cell": 63, "replays": results}


def generate(trace_path: Path) -> dict[str, object]:
    request = load(REQUEST, "dg_powf_request_for_xmm")
    downstream = load(DOWNSTREAM, "dg_powf_downstream_for_xmm")
    calls, vectors, _ = request.run_census()
    actual_rows = parse_trace(trace_path)
    cells = []
    actual_pairs = set()
    for cell_index, (mode, background) in enumerate(CELLS):
        production_rows = [row for row in calls if row["blur_mode"] == mode and
                           row["use_background"] == bool(background)]
        production = [(row["input_bits"], row["exponent_bits"], row["host_result_bits"])
                      for row in production_rows]
        selected = actual_rows[cell_index * 124:(cell_index + 1) * 124]
        actual = [(row["input_bits"], row["exponent_bits"], row["host_substituted_result_bits"])
                  for row in selected]
        positions = match_subsequence(production, actual)
        if Counter(actual) - Counter(production):
            raise RuntimeError("actual trace contains non-production call")
        actual_pairs.update((left, right) for left, right, _ in actual)
        cells.append({"blur_mode": mode, "use_background": bool(background),
                      "production_calls": 187, "actual_aex_calls": 124,
                      "skipped_production_calls": 63, "actual_unique_pairs": len(set(actual)),
                      "production_subsequence_positions": positions,
                      "actual_trace": selected, "actual_trace_sha256": digest(selected)})
    if len(actual_pairs) != 56 or len(vectors) != 63:
        raise RuntimeError("unique pair census")
    ignored = counterfactuals(request, downstream, actual_pairs)
    return {
        "schema": "olmdistancegradation.actual-aex-powf-xmm-closure/1",
        "status": "PASS_ACTUAL_AEX_POWER8_XMM_INPUTS_PRODUCTION_SUBSEQUENCE_OUTPUT_IRRELEVANT_EXTRA7",
        "identities": identities(), "cells": cells, "cells_sha256": digest(cells),
        "summary": {"cells": 8, "production_calls": 1496, "actual_aex_calls": 992,
                    "calls_per_actual_cell": 124, "skipped_transparent_calls_per_cell": 63,
                    "production_unique_pairs": 63, "actual_aex_unique_pairs": 56,
                    "actual_nonproduction_pairs": 0, "all_actual_calls_in_order": True},
        "production_only_irrelevance": ignored,
        "boundary": {"aexcompat_host_powf_is_not_native_windows_ucrt": True,
                     "actual_aex_exported_smart_path": True, "native_after_effects": False,
                     "production_admission_changed": False,
                     "remaining_requirement": "native UCRT results followed by eight native-derived final RAW comparisons"},
    }


@functools.lru_cache(maxsize=1)
def live_production_cells() -> tuple[tuple[tuple[str, str, str], ...], ...]:
    request = load(REQUEST, "dg_powf_request_for_xmm_validation")
    calls, _, _ = request.run_census()
    return tuple(tuple((row["input_bits"], row["exponent_bits"], row["host_result_bits"])
                       for row in calls if row["blur_mode"] == mode and
                       row["use_background"] == bool(background))
                 for mode, background in CELLS)


def validate(report: object, *, live: bool = True) -> bool:
    if not isinstance(report, dict) or set(report) != {"schema", "status", "identities", "cells", "cells_sha256", "summary", "production_only_irrelevance", "boundary"}:
        return False
    if report["schema"] != "olmdistancegradation.actual-aex-powf-xmm-closure/1" or not str(report["status"]).startswith("PASS_ACTUAL_AEX_POWER8"):
        return False
    if live and report["identities"] != identities():
        return False
    cells = report["cells"]
    if not isinstance(cells, list) or len(cells) != 8 or report["cells_sha256"] != digest(cells):
        return False
    production_cells = live_production_cells() if live else None
    for cell_index, (expected, cell) in enumerate(zip(CELLS, cells, strict=True)):
        if set(cell) != {"blur_mode", "use_background", "production_calls", "actual_aex_calls", "skipped_production_calls", "actual_unique_pairs", "production_subsequence_positions", "actual_trace", "actual_trace_sha256"}:
            return False
        if (cell["blur_mode"], int(cell["use_background"])) != expected or cell["production_calls"] != 187 or cell["actual_aex_calls"] != 124 or cell["skipped_production_calls"] != 63:
            return False
        if len(cell["actual_trace"]) != 124 or cell["actual_trace_sha256"] != digest(cell["actual_trace"]):
            return False
        if len(cell["production_subsequence_positions"]) != 124 or cell["production_subsequence_positions"] != sorted(cell["production_subsequence_positions"]):
            return False
        if production_cells is not None:
            production = production_cells[cell_index]
            actual = tuple((row.get("input_bits"), row.get("exponent_bits"), row.get("host_substituted_result_bits"))
                           for row in cell["actual_trace"])
            positions = tuple(cell["production_subsequence_positions"])
            if any(not isinstance(position, int) or position < 0 or position >= len(production)
                   for position in positions):
                return False
            if actual != tuple(production[position] for position in positions):
                return False
    if report["summary"] != {"cells": 8, "production_calls": 1496, "actual_aex_calls": 992,
            "calls_per_actual_cell": 124, "skipped_transparent_calls_per_cell": 63,
            "production_unique_pairs": 63, "actual_aex_unique_pairs": 56,
            "actual_nonproduction_pairs": 0, "all_actual_calls_in_order": True}:
        return False
    ignored = report["production_only_irrelevance"]
    if ignored.get("production_only_pairs") != [list(key) for key in PRODUCTION_ONLY] or ignored.get("pair_count") != 7 or ignored.get("pixel_calls_per_cell") != 63:
        return False
    if set(ignored.get("replays", {})) != {"all_zero", "all_one"} or any(row.get("matching_cells") != 8 for row in ignored["replays"].values()):
        return False
    return report["boundary"] == {"aexcompat_host_powf_is_not_native_windows_ucrt": True,
        "actual_aex_exported_smart_path": True, "native_after_effects": False,
        "production_admission_changed": False,
        "remaining_requirement": "native UCRT results followed by eight native-derived final RAW comparisons"}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--trace", type=Path)
    parser.add_argument("--write", action="store_true"); parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.write:
        trace = args.trace
        temporary = None
        if trace is None:
            # The canonical report already stores every one of the 992 trace
            # rows.  Re-materialize those immutable rows when only a dependent
            # tool identity changed; do not require a second AEX execution.
            existing = json.loads(REPORT.read_text())
            rows = [row for cell in existing.get("cells", []) for row in cell.get("actual_trace", [])]
            if len(rows) != 992:
                raise RuntimeError("--write without --trace requires a complete persisted 992-row trace")
            temporary = tempfile.TemporaryDirectory(prefix="dg-powf-xmm-rematerialize-")
            trace = Path(temporary.name) / "powf.csv"
            trace.write_text("\n".join(
                f"{row['input_bits'][2:]},{row['exponent_bits'][2:]},{row['host_substituted_result_bits'][2:]}"
                for row in rows
            ) + "\n")
        report = generate(trace)
        if temporary is not None:
            temporary.cleanup()
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        NOTE.write_text("# OLMDistanceGradation actual-AEX powf XMM closure\n\n"
            "Eight exported Smart PF32 Power cells execute 992 `powf` calls. Every actual XMM0/XMM1/result triple is an in-order production call; no extra pair exists. Production's seven additional unique pairs occur only in 63 transparent skipped pixels per cell. Replacing every production-only result with zero or one leaves all eight final RAW hashes exact. Native Windows UCRT return words and the eight final native-derived RAW comparisons remain required; no production admission or AE claim is made.\n")
    report = json.loads(REPORT.read_text())
    if not validate(report):
        raise RuntimeError("persisted actual-AEX XMM closure drift")
    print(report["status"]); return 0


if __name__ == "__main__":
    raise SystemExit(main())
