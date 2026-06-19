#!/usr/bin/env python3
"""Smoke-test OLMKiraKira OpenCV two-temp stage trace JSON output."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_PYTHON = Path("/tmp/olm_cv455_probe_venv/bin/python")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    probe_python = Path(os.environ.get("OLM_PROBE_PYTHON", str(DEFAULT_PYTHON)))
    if not probe_python.exists():
        print(
            f"[SKIP] missing OLMKiraKira OpenCV probe Python: {probe_python}; "
            "run refs/scripts/setup_olmkirakira_opencv455_probe_env.sh"
        )
        return 0

    reference = root / "refs" / "win_references" / "olm_reference_return_windows_20260614" / "OLMKiraKira"
    manifest = json.loads((reference / "reference_manifest.json").read_text(encoding="utf-8"))
    case = next(
        row
        for row in manifest["cases"]
        if row["request_id"] == "kirakira_single_ray_20260606"
        and row["id"] == "kk_vertical_len50_brightness1_strength100"
        and "__software__" in row["frame"]
    )

    with tempfile.TemporaryDirectory(prefix="olmkirakira_trace_json_smoke_") as tmp:
        tmp_path = Path(tmp)
        params = tmp_path / "params.json"
        output = tmp_path / "out.png"
        trace_json = tmp_path / "trace.json"
        params.write_text(json.dumps({"effects": case["effects"]}), encoding="utf-8")
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
        proc = subprocess.run(
            command,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if proc.returncode != 0:
            print(proc.stdout)
            return proc.returncode

        if not output.exists() or not trace_json.exists():
            print("[FAIL] KiraKira trace-json smoke did not write expected files")
            return 1
        data = json.loads(trace_json.read_text(encoding="utf-8"))
        if data.get("kind") != "olmkirakira_opencv_two_temp_stage_trace":
            print("[FAIL] trace JSON kind mismatch")
            return 1
        records = data.get("rays", [])
        rays = [record for record in records if record.get("ray")]
        if len(rays) != 1 or rays[0].get("ray") != "vertical":
            print("[FAIL] expected one vertical nonzero ray in trace JSON")
            return 1
        aggregation = [record for record in records if record.get("stage") == "aggregation_and_compose"]
        if len(aggregation) != 1:
            print("[FAIL] expected one aggregation_and_compose trace record")
            return 1
        ray = rays[0]
        if ray.get("length") != 50:
            print("[FAIL] expected vertical ray length 50")
            return 1
        if not ray.get("forward_matrix") or not ray.get("back_matrix"):
            print("[FAIL] trace JSON is missing affine matrices")
            return 1
        sample = ray["sample_points"][0]["values"]
        for key in (
            "seed",
            "after_center_copy",
            "after_forward_warp",
            "after_box_1",
            "after_box_2",
            "after_box_3",
            "after_rotate_back",
            "after_final_center_copy",
        ):
            if key not in sample:
                print(f"[FAIL] trace sample missing {key}")
                return 1
        agg_sample = aggregation[0]["sample_points"][0]["values"]
        for key in ("source_rgba", "glow_rgba", "out_rgba_float", "out_rgba_u8"):
            if key not in agg_sample:
                print(f"[FAIL] aggregation sample missing {key}")
                return 1
        if shutil.which("file"):
            subprocess.run(["file", str(output)], text=True, stdout=subprocess.PIPE)

    print("[OK] OLMKiraKira trace-json smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
