#!/usr/bin/env python3
"""Bounded, serial measurements of existing oracle and resident diagnostics.

This does not implement resident oracle rendering or claim its equivalence.
All child trees are owned, terminated and awaited by oracle.run_process.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "oracle"))
import olm_oracle as oracle

ORIGINALS = Path(r"D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex")
NAMES = ("ColorKeep", "DistanceGradation", "OLMBlur", "OLMColorKey",
         "OLMDirectionalBlur", "OLMKiraKira", "OLMRadialBlur", "OLMSmoother",
         "OLMSmoother2", "OLMToonDilate")


def stats(values):
    values = list(values)
    if not values:
        return {"count": 0, "median": None, "min": None, "max": None}
    return {"count": len(values), "median": statistics.median(values),
            "min": min(values), "max": max(values)}


def process_sample(result):
    """The worker clock is nested in wall, not a separate additive expense."""
    report = json.loads(result["stdout"]) if result["stdout"].strip() else {}
    if not isinstance(report, dict):
        report = {}
    worker_ms = report.get("worker_diagnostics", {}).get("elapsed_ms")
    wall_ms = result["elapsed_seconds"] * 1000
    return {"pid": result["pid"], "wall_ms": wall_ms,
            "render_worker_lifetime_ms": worker_ms,
            "outside_render_worker_ms": None if worker_ms is None else wall_ms - worker_ms,
            "ok": result["returncode"] == 0 and not result["timeout"],
            "freshness_warning": report.get("worker_diagnostics", {}).get("worker_freshness_warning")}


def summarize_cases(rows):
    samples = [sample for row in rows for sample in row["sides"].values()]
    return {"pairs": len(rows), "exact_pairs": sum(r["status"] == "exact" for r in rows),
            "failures": [r["status"] for r in rows if r["status"] != "exact"],
            **{key: stats(s[key] for s in samples if s[key] is not None)
               for key in ("wall_ms", "render_worker_lifetime_ms", "outside_render_worker_ms")}}


def summarize_performance(reports):
    if any(r.get("status") != "available" for r in reports):
        raise ValueError("incomplete performance report cannot support a speed estimate")
    samples = [s for r in reports for s in r["samples"]]
    result = []
    for width, height in sorted({(s["width"], s["height"]) for s in samples}):
        group = [s for s in samples if (s["width"], s["height"]) == (width, height)]
        cold = [s for s in group if s["cold"]]
        warm = [s for s in group if not s["cold"]]
        fields = {}
        for key in ("wall_ns", "input_write_ns", "worker_setup_ns", "worker_render_ns",
                    "selector_dispatch_ns", "worker_finalize_ns", "output_verify_ns"):
            fields[key.removesuffix("_ns") + "_ms"] = stats(s[key] / 1e6 for s in warm if s[key] is not None)
        open_ms = statistics.median(s["session_open_ns"] / 1e6 for s in cold)
        cold_ms = statistics.median(s["wall_ns"] / 1e6 for s in cold)
        warm_ms = fields["wall_ms"]["median"]
        result.append({"size": [width, height], "cold_count": len(cold), "warm_count": len(warm),
                       "open_ms": open_ms, "cold_frame_ms": cold_ms, "warm": fields,
                       "open_plus_cold_over_warm": (open_ms + cold_ms) / warm_ms,
                       "note": "Measured repeated-frame diagnostic ratio, not independent-case speed-up"})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--harness", type=Path, default=oracle.DEFAULT_HARNESS)
    parser.add_argument("--originals", type=Path, default=ORIGINALS)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261112)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10:
        parser.error("--repeats must be 1..10")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    harness = oracle.identity(args.harness)
    summary = {"schema_version": 1, "harness": harness, "tool": oracle.identity(__file__),
               "oracle": oracle.identity(oracle.__file__), "seed": args.seed, "jobs": 1,
               "repeats": args.repeats, "parameters": "all untouched defaults",
               "scope": "existing per-process self comparisons and advisory repeated-frame timing",
               "complete": False, "cases": {}, "controls": [], "performance": []}
    oracle.write_json(out / "summary.json", summary)
    try:
        for index in range(args.repeats):
            for name, flag, tail in (("help", "--help", []),
                                      ("inspect-blur", "--inspect-experimental",
                                       [args.originals / "OLMBlur.aex"])):
                r = oracle.run_process([args.harness, "--headless", flag, *tail], 120)
                oracle.write_json(out / f"{name}-{index}.process.json", r)
                summary["controls"].append({"name": name, **process_sample(r)} if name != "help"
                                           else {"name": name, "pid": r["pid"],
                                                 "wall_ms": r["elapsed_seconds"] * 1000,
                                                 "ok": r["returncode"] == 0})
        for name in NAMES:
            plugin = oracle.identity(args.originals / f"{name}.aex")
            identities = {"harness": harness, "reference": plugin, "candidate": plugin}
            route = "classic8" if name == "OLMSmoother" else "smart8"
            sizes = [(97, 61), (320, 180)] if name == "OLMBlur" else [(97, 61)]
            for width, height in sizes:
                key = f"{name}-{width}x{height}"
                directory = out / key
                directory.mkdir()
                rows = []
                for index in range(args.repeats):
                    case = {"index": index, "size": [width, height], "input_seed": args.seed + index,
                            "assignments": [], "downsample": "1"}
                    start = time.perf_counter()
                    row = oracle.run_case(directory, case, route, identities, (), None, 120)
                    elapsed = time.perf_counter() - start
                    sides = {}
                    for side in ("reference", "candidate"):
                        result = json.loads((directory / row["directory"] / f"{side}.process.json").read_text(encoding="utf-8"))
                        sides[side] = process_sample(result)
                    rows.append({"case": index, "status": row["status"], "pair_wall_ms": elapsed * 1000,
                                 "sides": sides})
                summary["cases"][key] = {"plugin": plugin, "route": route, "rows": rows,
                                          "stats": summarize_cases(rows)}
                oracle.write_json(out / "summary.json", summary)
                print(key, json.dumps(summary["cases"][key]["stats"]), flush=True)
        reports = []
        for index in range(args.repeats):
            r = oracle.run_process([args.harness, "--headless", "--render-performance-diagnostics",
                                    args.originals / "OLMBlur.aex", "smart", "argb8"], 120)
            oracle.write_json(out / f"blur-performance-{index}.process.json", r)
            if r["returncode"] != 0 or r["timeout"]:
                raise RuntimeError("resident performance diagnostic failed; see process log")
            report = json.loads(r["stdout"])
            oracle.write_json(out / f"blur-performance-{index}.json", report)
            reports.append(report)
        summary["performance"] = summarize_performance(reports)
        summary["complete"] = True
        summary["all_pairs_exact"] = all(not c["stats"]["failures"] for c in summary["cases"].values())
        summary["cleanup"] = "Every invocation returned through oracle.run_process finally: owned Job ActiveProcesses=0 and child waited."
        print(json.dumps(summary["performance"], indent=2))
    finally:
        oracle.write_json(out / "summary.json", summary)
    return 0 if summary["all_pairs_exact"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
