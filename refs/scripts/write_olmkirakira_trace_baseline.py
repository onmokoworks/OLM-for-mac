#!/usr/bin/env python3
"""Write a project-local OLMKiraKira OpenCV two-temp trace baseline."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_PYTHON = Path("/tmp/olm_cv455_probe_venv/bin/python")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Project-local directory that will receive params.json, candidate.png, trace.json, and README.md.",
    )
    parser.add_argument(
        "--probe-python",
        type=Path,
        default=Path(os.environ.get("OLM_PROBE_PYTHON", str(DEFAULT_PYTHON))),
        help="Python interpreter with opencv-python-headless available.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    probe_python = args.probe_python
    if not probe_python.exists():
        print(
            f"[FAIL] missing OLMKiraKira OpenCV probe Python: {probe_python}; "
            "run refs/scripts/setup_olmkirakira_opencv455_probe_env.sh",
            file=sys.stderr,
        )
        return 1

    reference = root / "refs" / "win_references" / "olm_reference_return_windows_20260614" / "OLMKiraKira"
    manifest = json.loads((reference / "reference_manifest.json").read_text(encoding="utf-8"))
    case = next(
        row
        for row in manifest["cases"]
        if row["request_id"] == "kirakira_single_ray_20260606"
        and row["id"] == "kk_vertical_len50_brightness1_strength100"
        and "__software__" in row["frame"]
    )

    out_dir = args.out_dir if args.out_dir.is_absolute() else root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    params = out_dir / "params.json"
    output = out_dir / "candidate.png"
    trace_json = out_dir / "trace.json"
    params.write_text(json.dumps({"effects": case["effects"]}, indent=2), encoding="utf-8")

    command = [
        str(probe_python),
        "refs/scripts/olmkirakira_cli.py",
        "--input",
        str(reference / case["before_effects_frame"]),
        "--params",
        str(params),
        "--output",
        str(output),
        "--seed-mode",
        "aex",
        "--falloff",
        "box3",
        "--gain-scale",
        "0.62",
        "--ray-mode",
        "opencv-two-temp",
        "--compose-mode",
        "aex-screen-over",
        "--scale-mode",
        "aex-screen-over",
        "--auto-length-scale",
        "--comp-width",
        "1920",
        "--zero-ray-skip",
        "--trace-json",
        str(trace_json),
    ]
    proc = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        return proc.returncode

    readme = out_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# OLMKiraKira Local Trace Baseline",
                "",
                "- Case: `kk_vertical_len50_brightness1_strength100`",
                "- Reference set: `refs/win_references/olm_reference_return_windows_20260614/OLMKiraKira`",
                "- CLI mode: `opencv-two-temp`, `aex-screen-over`, `box3`",
                "- Purpose: compare against Windows runtime trace request `kirakira_fun_181150790_stage_values_20260620`.",
                "",
                "Files:",
                "",
                "- `params.json`: extracted AE effect parameters",
                "- `candidate.png`: local OpenCV candidate output",
                "- `trace.json`: local stage values for ray helper and aggregation/compose",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"trace_baseline_dir={out_dir}")
    print(f"trace_json={trace_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
