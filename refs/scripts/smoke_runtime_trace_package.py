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

        kirakira_deep_output = Path(tmp) / "runtime_trace_kirakira_stage_deep.zip"
        proc = run(
            [
                sys.executable,
                str(script),
                "--profile",
                "kirakira-stage-values-deep",
                "--output",
                str(kirakira_deep_output),
            ],
            root,
        )
        assert "[OK] runtime trace package:" in proc.stdout
        with zipfile.ZipFile(kirakira_deep_output) as archive:
            names = set(archive.namelist())
            required = {
                "README_RUNTIME_TRACE.md",
                "RETURN_RUNTIME_TRACE_TEMPLATE.json",
                "runtime_trace_package_manifest.json",
                "notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md",
                "notes/IR_OLMKiraKira.md",
                "refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.json",
                "refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.md",
            }
            missing = required - names
            assert not missing, f"missing KiraKira deep package entries: {sorted(missing)}"
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
        assert manifest["profile"] == "kirakira-stage-values-deep"
        action_ids = [action["request_id"] for action in manifest["runtime_actions"]]
        assert action_ids == ["kirakira_fun_181150790_deep_stage_values_20260621"]
        observations = template["results"][0]["observations"]
        assert observations["stage_witnesses"][0]["temp_xy"] == [962, 962]
        assert observations["stage_witnesses"][2]["source_xy"] == [1010, 540]
        assert observations["aggregation_and_compose"]["center_local_expected"]["out_rgba_u8"] == [
            129,
            129,
            129,
            255,
        ]

        kirakira_agg_output = Path(tmp) / "runtime_trace_kirakira_aggregation_compose_bt709.zip"
        proc = run(
            [
                sys.executable,
                str(script),
                "--profile",
                "kirakira-aggregation-compose-bt709",
                "--output",
                str(kirakira_agg_output),
            ],
            root,
        )
        assert "[OK] runtime trace package:" in proc.stdout
        with zipfile.ZipFile(kirakira_agg_output) as archive:
            names = set(archive.namelist())
            required = {
                "README_RUNTIME_TRACE.md",
                "RETURN_RUNTIME_TRACE_TEMPLATE.json",
                "runtime_trace_package_manifest.json",
                "notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md",
                "notes/IR_OLMKiraKira.md",
                "refs/reports/olmkirakira_trace_baseline_20260624_bt709_mac/trace.json",
                "refs/reports/runtime_trace_comparisons/olmkirakira_deep_stage_values_20260624_bt709.md",
            }
            missing = required - names
            assert not missing, f"missing KiraKira aggregation package entries: {sorted(missing)}"
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
            readme = archive.read("README_RUNTIME_TRACE.md").decode("utf-8")
            trace_note = archive.read("notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md").decode("utf-8")
        assert manifest["profile"] == "kirakira-aggregation-compose-bt709"
        action_ids = [action["request_id"] for action in manifest["runtime_actions"]]
        assert action_ids == ["kirakira_aggregation_compose_bt709_20260624"]
        assert "after the BT.709 seed reconciliation" in readme
        assert "(934,118)" in readme
        assert "(1098,202)" in readme
        assert (
            "runtime trace package that should be resent blindly"
            in trace_note
        )
        assert "compose/prewriteback" in trace_note
        assert "KiraKira BT.709 aggregation/compose return" in trace_note
        assert "Status: pending external Windows debugger trace." not in trace_note
        observations = template["results"][0]["observations"]
        assert observations["known_facts_to_keep"]["channel_2_seed_luma"] == "BT.709"
        assert observations["local_bt709_expected"]["center"]["aggregation_and_compose"]["out_rgba_u8"] == [
            130,
            130,
            130,
            255,
        ]
        hotspots = observations["residual_hotspots"]
        assert hotspots[0]["label"] == "primary_vertical_case_hotspot"
        assert hotspots[0]["source_xy"] == [934, 118]
        assert hotspots[0]["windows_reference_rgba"] == [131, 131, 131, 255]
        assert hotspots[0]["mac_bt709_candidate_rgba"] == [145, 145, 145, 255]
        assert hotspots[1]["label"] == "optional_global_software_hotspot"
        assert hotspots[1]["source_xy"] == [1098, 202]
        assert hotspots[1]["windows_reference_rgba"] == [112, 112, 112, 255]
        assert hotspots[1]["mac_bt709_candidate_rgba"] == [46, 46, 46, 255]

        smoother_legacy_output = Path(tmp) / "runtime_trace_smoother_legacy.zip"
        proc = run(
            [
                sys.executable,
                str(script),
                "--profile",
                "smoother2-legacy-key-gamma",
                "--output",
                str(smoother_legacy_output),
            ],
            root,
        )
        assert "[OK] runtime trace package:" in proc.stdout
        with zipfile.ZipFile(smoother_legacy_output) as archive:
            names = set(archive.namelist())
            required = {
                "README_RUNTIME_TRACE.md",
                "RETURN_RUNTIME_TRACE_TEMPLATE.json",
                "runtime_trace_package_manifest.json",
                "notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md",
                "notes/IR_OLMSmoother2.md",
                "notes/CONFORMANCE_LEDGER.md",
            }
            missing = required - names
            assert not missing, f"missing Smoother legacy package entries: {sorted(missing)}"
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
        assert manifest["profile"] == "smoother2-legacy-key-gamma"
        action_ids = [action["request_id"] for action in manifest["runtime_actions"]]
        assert action_ids == ["olmsmoother2_legacy_key_gamma_runtime_trace_20260620"]
        observations = template["results"][0]["observations"]
        assert observations["cases"][0]["case_id"] == "case_0001"
        assert observations["cases"][1]["expected_params"]["invert_color_key"] == 1
        assert "setup_and_keying" in observations["requested_for_each_case"]
        assert "smoothing_and_writeback" in observations["requested_for_each_case"]

        smoother_cce0_internals_output = Path(tmp) / "runtime_trace_smoother_cce0_internals.zip"
        proc = run(
            [
                sys.executable,
                str(script),
                "--profile",
                "smoother2-legacy-cce0-internals-trace",
                "--output",
                str(smoother_cce0_internals_output),
            ],
            root,
        )
        assert "[OK] runtime trace package:" in proc.stdout
        with zipfile.ZipFile(smoother_cce0_internals_output) as archive:
            names = set(archive.namelist())
            required = {
                "README_RUNTIME_TRACE.md",
                "RETURN_RUNTIME_TRACE_TEMPLATE.json",
                "runtime_trace_package_manifest.json",
                "notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md",
                "notes/IR_OLMSmoother2.md",
                "notes/CONFORMANCE_LEDGER.md",
                "refs/reports/smoother2_legacy_cce0_pixel_trace_20260621/runtime_trace_summary_smoother2_legacy_cce0_pixel_trace_20260621_0145.md",
            }
            missing = required - names
            assert not missing, f"missing Smoother cce0 internals package entries: {sorted(missing)}"
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
        assert manifest["profile"] == "smoother2-legacy-cce0-internals-trace"
        action_ids = [action["request_id"] for action in manifest["runtime_actions"]]
        assert action_ids == ["olmsmoother2_legacy_cce0_internals_replay_from_writer_trace_20260621"]
        observations = template["results"][0]["observations"]
        assert observations["target"]["known_writer_store_eax"] == "c8c8c887"
        assert observations["trace_anchor"]["primary_breakpoint"] == "OLMSmoother2+0x3610"
        assert "$t3" in observations["writer_entry_target_address"]["candidate_addr_registers"]
        assert observations["writer_entry_target_address"]["selected_output_world"] == "$t3"
        assert observations["after_fun_18000c280"]["address"] == "OLMSmoother2+0xcd5f"
    print("[OK] runtime trace package smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
