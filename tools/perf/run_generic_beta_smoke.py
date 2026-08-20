#!/usr/bin/env python3
"""Run bounded hostless generic-beta smokes and emit a machine-readable report.

The command catalog is intentionally explicit. A lane/geometry without an exact
hostless driver is recorded as ``not_measured`` rather than being represented by
a smaller fixture. Commands may be added as generic lanes acquire scalable
drivers; this runner itself does not depend on the Adobe host.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GEOMETRIES = {"hd": [1920, 1080], "uhd": [3840, 2160]}
LANES = [
    "ColorKeep", "OLMBlur", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur", "OLMSmoother",
    "OLMSmoother2", "OLMToonDilate",
]

# Only commands proven to execute the exact requested geometry belong here.
# Each driver uses safe/default parameters and is independently time-limited.
COMMANDS: dict[tuple[str, str], list[str]] = {
    ("ColorKeep", "hd"): [
        sys.executable, "tools/perf/run_colorkeep_generic_production_perf.py",
        "--geometry", "hd",
    ],
    ("ColorKeep", "uhd"): [
        sys.executable, "tools/perf/run_colorkeep_generic_production_perf.py",
        "--geometry", "uhd",
    ],
    ("OLMBlur", "hd"): [
        sys.executable, "tools/perf/run_olmblur_generic_production_perf.py",
        "--geometry", "hd",
    ],
    ("OLMBlur", "uhd"): [
        sys.executable, "tools/perf/run_olmblur_generic_production_perf.py",
        "--geometry", "uhd",
    ],
    ("OLMColorKey", "hd"): [
        sys.executable, "tests/test_olmcolorkey_generic_pixel_local_pairwise.py",
        "--geometry", "hd",
    ],
    ("OLMColorKey", "uhd"): [
        sys.executable, "tests/test_olmcolorkey_generic_pixel_local_pairwise.py",
        "--geometry", "uhd",
    ],
    ("OLMDirectionalBlur", "hd"): [sys.executable, "tools/emulation/test_dblur_generic_pf8_geometry_beta_20260820.py"],
    ("OLMDistanceGradation", "hd"): [
        sys.executable, "-m", "unittest",
        "tests/test_olmdistancegradation_generic_production_beta_20260820.py",
    ],
    ("OLMDistanceGradation", "uhd"): [
        sys.executable, "-m", "unittest",
        "tests/test_olmdistancegradation_generic_production_beta_20260820.py",
    ],
    ("OLMKiraKira", "hd"): [
        sys.executable, "tools/perf/run_olmkirakira_generic_production_perf.py",
        "--geometry", "hd",
    ],
    ("OLMKiraKira", "uhd"): [
        sys.executable, "tools/perf/run_olmkirakira_generic_production_perf.py",
        "--geometry", "uhd",
    ],
    ("OLMRadialBlur", "hd"): [
        sys.executable, "tools/perf/run_olmradialblur_generic_production_perf.py",
        "--geometry", "hd",
    ],
    ("OLMRadialBlur", "uhd"): [
        sys.executable, "tools/perf/run_olmradialblur_generic_production_perf.py",
        "--geometry", "uhd",
    ],
    ("OLMSmoother", "hd"): [
        sys.executable, "tests/run_olmsmoother_v1_generic_production_perf.py",
        "--depth", "both", "--width", "1920", "--height", "1080",
        "--input-padding", "18", "--output-padding", "34",
        "--tolerance", "255", "--use-key",
    ],
    ("OLMSmoother", "uhd"): [
        sys.executable, "tests/run_olmsmoother_v1_generic_production_perf.py",
        "--depth", "both", "--width", "3840", "--height", "2160",
        "--input-padding", "18", "--output-padding", "34",
        "--tolerance", "255", "--use-key",
    ],
    ("OLMSmoother2", "hd"): [
        sys.executable, "-m", "unittest",
        "tests.test_olmsmoother2_default_beta_lane_20260820."
        "OLMSmoother2DefaultBetaLane."
        "test_effectmain_accepts_arbitrary_source_at_all_depths",
    ],
    ("OLMSmoother2", "uhd"): [
        sys.executable, "-m", "unittest",
        "tests.test_olmsmoother2_default_beta_lane_20260820."
        "OLMSmoother2DefaultBetaLane."
        "test_effectmain_accepts_arbitrary_source_at_all_depths",
    ],
    ("OLMToonDilate", "hd"): [
        sys.executable, "tools/perf/run_olmtoondilate_generic_production_perf.py",
        "--geometry", "hd",
    ],
    ("OLMToonDilate", "uhd"): [
        sys.executable, "tools/perf/run_olmtoondilate_generic_production_perf.py",
        "--geometry", "uhd",
    ],
}
SUPPORT_PREDICATES = {
    "ColorKeep": (
        "smart && pf8_pf16_pf32 && full_frame && zero_origin && "
        "1 <= count <= 100 && width <= 3840 && height <= 2160"
    ),
    "OLMBlur": (
        "smart && pf8_pf16_pf32 && full_frame && width <= 4096 && "
        "height <= 2160 && amount <= 1000 && repeat <= 10 && "
        "pixels*ceil(amount)*repeat <= 3600000000"
    ),
    "OLMDirectionalBlur": (
        "full_frame && pf8_pf16_pf32 && neutral_front_only && finite_angle_gain && "
        "scale_1_for_pf16_pf32 && pf16_sdr_0_32768 && pf32_finite_sdr_0_1 && "
        "estimated_diagonal_work_bytes_14xf32 <= 536870912"
    ),
    "OLMKiraKira": (
        "classic_or_smart && pf8_pf16_pf32 && full_frame && zero_origin && "
        "width >= 9 && height >= 7 && oracle_tuple && mode_geometry_admitted"
    ),
    "OLMSmoother": (
        "classic && (pf8 || pf16) && (key_off || key_on) && "
        "width <= 3840 && height <= 2160"
    ),
    "OLMSmoother2": (
        "smart && pf8_pf16_pf32 && v1_v2 && smoothing_ui_ranges && "
        "key_off_on_invert && (gamma_none || gamma_all) && "
        "full_frame && 16 <= width,height <= 8192"
    ),
    "OLMToonDilate": (
        "smart && pf8_pf16_pf32 && full_frame && zero_origin && "
        "0 <= search_radius <= 100 && positive_independent_rowbytes"
    ),
}

TIMEOUT_SECONDS = {"hd": 120, "uhd": 180}
RSS_BUDGET_BYTES = {"hd": 2 * 1024**3, "uhd": 3 * 1024**3}
_RSS = re.compile(r"^\s*(\d+)\s+maximum resident set size\s*$", re.MULTILINE)
_CASE_RESULTS = re.compile(r"^OLM_PERF_CASES_JSON=(.+)$", re.MULTILINE)


def measure(command: list[str], geometry: str) -> dict[str, object]:
    timeout = TIMEOUT_SECONDS[geometry]
    started = time.monotonic()
    wrapped = ["/usr/bin/time", "-lp", *command]
    try:
        run = subprocess.run(
            wrapped, cwd=ROOT, text=True, capture_output=True, timeout=timeout,
            env={**os.environ, "OLM_PERF_GEOMETRY": geometry},
        )
    except subprocess.TimeoutExpired as error:
        return {
            "status": "timeout", "timeout_seconds": timeout,
            "wall_seconds": round(time.monotonic() - started, 6),
            "stdout_tail": (error.stdout or "")[-1000:],
            "stderr_tail": (error.stderr or "")[-1000:],
        }
    elapsed = time.monotonic() - started
    match = _RSS.search(run.stderr)
    rss = int(match.group(1)) if match else None
    status = "passed" if run.returncode == 0 else "failed"
    if status == "passed" and rss is not None and rss > RSS_BUDGET_BYTES[geometry]:
        status = "rss_budget_exceeded"
    result = {
        "status": status, "returncode": run.returncode,
        "wall_seconds": round(elapsed, 6), "peak_rss_bytes": rss,
        "rss_budget_bytes": RSS_BUDGET_BYTES[geometry],
        "timeout_seconds": timeout,
        "stdout_tail": run.stdout[-1000:], "stderr_tail": run.stderr[-1000:],
    }
    case_match = _CASE_RESULTS.search(run.stdout)
    if case_match:
        result["case_results"] = json.loads(case_match.group(1))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=ROOT / "reports/generic_beta_perf_smoke.json")
    parser.add_argument("--lane", choices=LANES,
                        help="measure only this lane (all lanes by default)")
    parser.add_argument("--geometry", choices=GEOMETRIES,
                        help="measure only this geometry (both by default)")
    args = parser.parse_args()
    rows: list[dict[str, object]] = []
    selected_lanes = [args.lane] if args.lane else LANES
    selected_geometries = ({args.geometry: GEOMETRIES[args.geometry]}
                           if args.geometry else GEOMETRIES)
    for lane in selected_lanes:
        for geometry, dimensions in selected_geometries.items():
            command = COMMANDS.get((lane, geometry))
            base: dict[str, object] = {
                "lane": lane, "geometry": geometry, "dimensions": dimensions,
                "parameters": (
                    "pixel_local_pairwise_no_edge_lab76_excluded"
                    if lane == "OLMColorKey" else
                    "key_on_arbitrary_color_tolerance_255"
                    if lane == "OLMSmoother" else "safe_default"
                ),
                "hostless": True,
            }
            if lane == "OLMRadialBlur":
                base["parameters"] = (
                    "generic_baseline_center_23_71_ratio_2.25_angle_-137.5_"
                    "quality_1_strength_1_independent_strides"
                )
            if lane == "OLMBlur":
                base["parameters"] = (
                    "hd_representative_all_depths_mixed_legacy_amount3_repeat1;"
                    "hd_high_pf8_nonlegacy_amount500_repeat1;"
                    "uhd_budget_all_depths_nonlegacy_amount1_repeat1_"
                    "independent_strides"
                )
            if lane == "ColorKeep":
                base["parameters"] = (
                    "smart_typed_workers_all_depths_counts_1_13_100_"
                    "independent_strides_production_O2"
                )
            if lane == "OLMSmoother2":
                base["parameters"] = (
                    "hd_representative_v1_v2_key_invert_gamma_none_all_"
                    "smoothing_axes;uhd_safe_default;independent_strides"
                )
            if lane == "OLMToonDilate":
                base["parameters"] = (
                    "production_O2_pf8_radius13_scale1_pf16_radius2.5_scale0.5_"
                    "pf32_radius0.99_scale1_independent_strides_chebyshev_oracle"
                )
            if lane == "OLMDistanceGradation":
                base["parameters"] = (
                    "oracle_profile_linear_power_gaussian_sphere_median_"
                    "bilateral_all_depths_independent_strides"
                )
            if lane in SUPPORT_PREDICATES:
                base["support_predicate"] = SUPPORT_PREDICATES[lane]
            if command is None:
                if lane == "OLMDirectionalBlur" and geometry == "uhd":
                    base.update({
                        "status": "unsupported",
                        "reason": (
                            "3840x2160 exceeds the DirectionalBlur generic beta "
                            "512 MiB diagonal-work memory budget"
                        ),
                    })
                else:
                    base.update({
                        "status": "not_measured",
                        "reason": "no exact-geometry hostless driver is available",
                    })
            else:
                base["command"] = command
                base.update(measure(command, geometry))
            rows.append(base)
    report = {
        "schema_version": 1,
        "generated_at_epoch_seconds": int(time.time()),
        "policy": {
            "exact_geometry_required": True,
            "timeouts_seconds": TIMEOUT_SECONDS,
            "rss_budgets_bytes": RSS_BUDGET_BYTES,
            "note": "Peak RSS is /usr/bin/time maximum resident set size for the hostless driver process.",
        },
        "results": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    measured = [row for row in rows
                if row["status"] not in {"not_measured", "unsupported"}]
    failed = [row for row in measured if row["status"] != "passed"]
    print(f"wrote {args.output}: measured={len(measured)} unavailable={len(rows)-len(measured)} failed={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
