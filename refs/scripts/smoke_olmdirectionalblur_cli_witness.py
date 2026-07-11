#!/usr/bin/env python3
"""Smoke-test OLMDirectionalBlur CLI witness JSON output."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "refs" / "win_references" / "20260604_olm" / "OLMDirectionalBlur"
MANIFEST = REFERENCE / "reference_manifest.json"
BUILD_SCRIPT = ROOT / "refs" / "scripts" / "build_olmdirectionalblur_cli.sh"
WITNESS_POINTS = "494,169;579,169"
PERSISTENT_WITNESS = Path("/tmp/olmdirectionalblur_cli_witness_smoke.json")


def case_params(case: dict) -> dict:
    if "params" in case:
        return case["params"]
    if "effects" in case:
        return {"effects": case["effects"]}
    return {}


def case_metadata(case: dict, manifest: dict) -> dict:
    metadata = {
        "comp": case.get("comp") or manifest.get("comp"),
        "project_gpu_accel_type": case.get("project_gpu_accel_type") or manifest.get("project_gpu_accel_type"),
        "render_set": case.get("render_set") or case.get("render_set_id") or manifest.get("render_set"),
    }
    for key in (
        "ctx_render_scale",
        "render_scale",
        "ctx_0x11c",
        "ctx_0x120",
        "render_context",
        "ctx_render_scale_x",
        "render_scale_x",
        "ctx_0x11c_x",
        "ctx_0x120_x",
        "ctx_render_scale_y",
        "render_scale_y",
        "ctx_0x11c_y",
        "ctx_0x120_y",
    ):
        if key in case:
            metadata[key] = case[key]
        elif key in manifest:
            metadata[key] = manifest[key]
    return metadata


def build_cli() -> Path:
    result = subprocess.run(
        [str(BUILD_SCRIPT)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    cli_path = Path(result.stdout.strip().splitlines()[-1])
    if not cli_path.exists():
        raise FileNotFoundError(f"built CLI not found: {cli_path}")
    return cli_path


def load_case() -> tuple[dict, dict]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    case = next((row for row in manifest["cases"] if row.get("id") == "case_0001"), None)
    if case is None:
        raise AssertionError("case_0001 not found in reference manifest")
    return manifest, case


def main() -> int:
    if not REFERENCE.exists():
        print(f"missing Windows reference directory: {REFERENCE}", file=sys.stderr)
        return 1

    cli_path = build_cli()
    manifest, case = load_case()

    with tempfile.TemporaryDirectory(prefix="olmdirectionalblur_witness_smoke_", dir="/tmp") as tmp:
        tmp_path = Path(tmp)
        output_path = tmp_path / "case_0001.png"
        params_path = tmp_path / "case_0001_params.json"
        witness_path = tmp_path / "case_0001_witness.json"

        input_name = case.get("before_effects_frame")
        if not input_name:
            raise AssertionError("case_0001 is missing before_effects_frame")
        input_path = REFERENCE / input_name
        if not input_path.exists():
            raise FileNotFoundError(f"missing reference input: {input_path}")

        payload = {
            "case_id": case["id"],
            "comp": (case.get("comp") or manifest.get("comp")),
            "frame": case.get("frame") or "case_0001.png",
            "metadata": case_metadata(case, manifest),
            "time": case.get("time"),
            "params": case_params(case),
        }
        params_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

        subprocess.run(
            [
                str(cli_path),
                "--input",
                str(input_path),
                "--params",
                str(params_path),
                "--output",
                str(output_path),
                "--algorithm",
                "rotated-aex-full-choreo",
                "--angle-sign",
                "-1",
                "--sample-sign",
                "-1",
                "--strength-scale",
                "auto",
                "--rgb-normalize",
                "front-strength",
                "--witness-json",
                str(witness_path),
                "--witness-points",
                WITNESS_POINTS,
            ],
            cwd=ROOT,
            check=True,
        )

        data = json.loads(witness_path.read_text(encoding="utf-8"))
        assert data["kind"] == "olmdirectionalblur_cli_witness"
        assert data["aex_two_stage_output"] is True
        points = data["points"]
        assert isinstance(points, list) and points
        required_point_keys = {
            "x",
            "y",
            "pad_x",
            "pad_y",
            "source_alpha",
            "accum_sum_denominator",
            "effective_rgb_denominator",
            "accum_alpha",
            "source_rgb",
            "accum_rgb",
            "blurred_rgba_pre_rotateback",
            "output_canvas_rgba",
            "final_sample_rgba_pre_quant",
            "final_rgba8",
        }
        missing = required_point_keys - set(points[0])
        if missing:
            raise AssertionError(f"missing witness fields: {sorted(missing)}")

        shutil.copy2(witness_path, PERSISTENT_WITNESS)
        print(f"[OK] witness smoke passed: {PERSISTENT_WITNESS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
