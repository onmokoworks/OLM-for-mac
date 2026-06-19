#!/usr/bin/env python3
"""Smoke-test scripts/package_runtime_trace_requests.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def main() -> int:
    root = repo_root()
    script = root / "scripts" / "package_runtime_trace_requests.py"
    with tempfile.TemporaryDirectory(prefix="olm_runtime_trace_package_smoke_") as tmp:
        output = Path(tmp) / "runtime_trace.zip"
        proc = run([sys.executable, str(script), "--output", str(output)], root)
        assert "[OK] runtime trace package:" in proc.stdout
        assert output.exists()
        assert zipfile.is_zipfile(output)
        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())
            required = {
                "README_RUNTIME_TRACE.md",
                "RETURN_RUNTIME_TRACE_TEMPLATE.json",
                "runtime_trace_package_manifest.json",
                "next_reference_actions_snapshot.json",
                "notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md",
                "refs/reference_requests/radialblur_inner_20260605.json",
                "refs/reference_requests/kirakira_single_ray_20260606.json",
                "refs/reference_requests/kirakira_strength0_brightness_20260614.json",
            }
            missing = required - names
            assert not missing, f"missing package entries: {sorted(missing)}"
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
        assert manifest["kind"] == "olm_runtime_trace_request_package"
        action_ids = [action["request_id"] for action in manifest["runtime_actions"]]
        assert action_ids[:2] == [
            "radialblur_inner_runtime_trace_20260618",
            "kirakira_opencv455_primitive_fact_20260618",
        ]
        assert template["kind"] == "olm_runtime_trace_result"
        template_ids = [row["request_id"] for row in template["results"]]
        assert template_ids == action_ids
        assert "r14d_after_0x1d18" in template["results"][0]["observations"]
        assert "fun_181281260_first_boxfilter_branch" in template["results"][1]["observations"]

        colorkey_output = Path(tmp) / "runtime_trace_colorkey.zip"
        proc = run(
            [
                sys.executable,
                str(script),
                "--profile",
                "colorkey-edge",
                "--output",
                str(colorkey_output),
            ],
            root,
        )
        assert "[OK] runtime trace package:" in proc.stdout
        with zipfile.ZipFile(colorkey_output) as archive:
            names = set(archive.namelist())
            required = {
                "README_RUNTIME_TRACE.md",
                "RETURN_RUNTIME_TRACE_TEMPLATE.json",
                "runtime_trace_package_manifest.json",
                "notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md",
                "notes/OLMColorKey_ASM_FACTS.md",
                "notes/CONFORMANCE_LEDGER.md",
            }
            missing = required - names
            assert not missing, f"missing ColorKey package entries: {sorted(missing)}"
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
        assert manifest["profile"] == "colorkey-edge"
        action_ids = [action["request_id"] for action in manifest["runtime_actions"]]
        assert action_ids == ["colorkey_edge_runtime_trace_20260619"]
        observations = template["results"][0]["observations"]
        assert "ctx_0x44_distance_type" in observations
        assert "edge_blur_apply_formula_summary" in observations

        olmblur_output = Path(tmp) / "runtime_trace_olmblur.zip"
        proc = run(
            [
                sys.executable,
                str(script),
                "--profile",
                "olmblur-repeat-threshold",
                "--output",
                str(olmblur_output),
            ],
            root,
        )
        assert "[OK] runtime trace package:" in proc.stdout
        with zipfile.ZipFile(olmblur_output) as archive:
            names = set(archive.namelist())
            required = {
                "README_RUNTIME_TRACE.md",
                "RETURN_RUNTIME_TRACE_TEMPLATE.json",
                "runtime_trace_package_manifest.json",
                "notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md",
                "notes/CONFORMANCE_LEDGER.md",
                "notes/AE_HOST_VALIDATION_20260618.md",
            }
            missing = required - names
            assert not missing, f"missing OLMBlur package entries: {sorted(missing)}"
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
        assert manifest["profile"] == "olmblur-repeat-threshold"
        action_ids = [action["request_id"] for action in manifest["runtime_actions"]]
        assert action_ids == ["olmblur_repeat_threshold_runtime_trace_20260619"]
        observations = template["results"][0]["observations"]
        assert observations["cases"][0]["case_id"] == "case_0006"
        assert observations["cases"][1]["case_id"] == "case_0007"
        assert "aex_pre_writeback_rgb_hex" in observations["cases"][0]["residual_pixels"][0]

        kirakira_output = Path(tmp) / "runtime_trace_kirakira_stage.zip"
        proc = run(
            [
                sys.executable,
                str(script),
                "--profile",
                "kirakira-stage-values",
                "--output",
                str(kirakira_output),
            ],
            root,
        )
        assert "[OK] runtime trace package:" in proc.stdout
        with zipfile.ZipFile(kirakira_output) as archive:
            names = set(archive.namelist())
            required = {
                "README_RUNTIME_TRACE.md",
                "RETURN_RUNTIME_TRACE_TEMPLATE.json",
                "runtime_trace_package_manifest.json",
                "notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md",
                "notes/IR_OLMKiraKira.md",
                "refs/reference_requests/kirakira_single_ray_20260606.json",
            }
            missing = required - names
            assert not missing, f"missing KiraKira package entries: {sorted(missing)}"
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
        assert manifest["profile"] == "kirakira-stage-values"
        action_ids = [action["request_id"] for action in manifest["runtime_actions"]]
        assert action_ids == ["kirakira_fun_181150790_stage_values_20260620"]
        observations = template["results"][0]["observations"]
        assert observations["case_id"] == "kk_vertical_len50_brightness1_strength100"
        assert "boxfilter_calls" in observations
        assert "aggregation_and_compose" in observations
        for witness in observations["witness_pixels"]:
            for key in ("xy", "source_xy", "tmp1_xy", "tmp2_xy", "ray_xy"):
                assert key in witness, f"missing KiraKira witness coordinate field: {key}"
    print("[OK] runtime trace package smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
