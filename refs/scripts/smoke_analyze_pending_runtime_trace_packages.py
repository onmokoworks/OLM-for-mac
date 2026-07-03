#!/usr/bin/env python3
"""Smoke-test scripts/analyze_pending_runtime_trace_packages.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="pending_runtime_trace_smoke_") as tmp:
        out_json = Path(tmp) / "pending_runtime_trace_packages.json"
        out_md = Path(tmp) / "pending_runtime_trace_packages.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_pending_runtime_trace_packages.py",
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads(out_json.read_text(encoding="utf-8"))
        rows = report.get("requests", [])
        if not isinstance(rows, list) or not rows:
            raise AssertionError("expected runtime trace package rows")
        by_id = {row["request_id"]: row for row in rows}
        kirakira_aggregation = by_id.get("kirakira_aggregation_compose_bt709_20260624")
        if kirakira_aggregation is None:
            raise AssertionError("missing KiraKira aggregation/compose request")
        if kirakira_aggregation["status"] != "answered":
            raise AssertionError(
                f"KiraKira aggregation/compose request should be answered, got {kirakira_aggregation['status']}"
            )
        if kirakira_aggregation["priority"] != 45:
            raise AssertionError(
                f"KiraKira aggregation/compose priority should be 45, got {kirakira_aggregation['priority']}"
            )
        if "compare_kirakira_stage_trace.py" not in kirakira_aggregation["comparison_command"]:
            raise AssertionError("KiraKira aggregation/compose request should point to the KiraKira comparator")
        kirakira_compose = by_id.get("kirakira_compose_writeback_witness_20260630")
        if kirakira_compose is None:
            raise AssertionError("missing KiraKira compose/writeback request")
        if kirakira_compose["status"] != "answered":
            raise AssertionError(
                f"KiraKira compose/writeback request should be answered, got {kirakira_compose['status']}"
            )
        if kirakira_compose["priority"] != 44:
            raise AssertionError(
                f"KiraKira compose/writeback priority should be 44, got {kirakira_compose['priority']}"
            )
        if "compare_kirakira_stage_trace.py" not in kirakira_compose["comparison_command"]:
            raise AssertionError("KiraKira compose/writeback request should point to the KiraKira comparator")
        radial = by_id.get("olmradialblur_caller_collapse_witness_20260630")
        if radial is None:
            raise AssertionError("missing focused RadialBlur request")
        if radial["status"] != "answered":
            raise AssertionError(f"focused RadialBlur request should be answered, got {radial['status']}")
        if radial["priority"] != 9:
            raise AssertionError(f"focused RadialBlur request priority should be 9, got {radial['priority']}")
        if "compare_radialblur_trace.py" not in radial["comparison_command"]:
            raise AssertionError("focused RadialBlur request should point to the RadialBlur comparator")
        blur_final = by_id.get("olmblur_final_word_witness_20260630")
        if blur_final is None:
            raise AssertionError("missing historical OLMBlur final-word request")
        if blur_final["status"] != "answered":
            raise AssertionError(f"historical OLMBlur final-word request should be answered, got {blur_final['status']}")
        blur_case0006 = by_id.get("olmblur_case0006_helper_prestore_witness_20260630")
        if blur_case0006 is None:
            raise AssertionError("missing OLMBlur case_0006 helper/pre-store request")
        if blur_case0006["status"] != "answered":
            raise AssertionError(f"OLMBlur case_0006 helper/pre-store request should be answered, got {blur_case0006['status']}")
        if blur_case0006["priority"] != 18:
            raise AssertionError(f"OLMBlur case_0006 helper/pre-store priority should be 18, got {blur_case0006['priority']}")
        if "compare_olmblur_trace.py" not in blur_case0006["comparison_command"]:
            raise AssertionError("OLMBlur case_0006 helper/pre-store request should point to the OLMBlur comparator")
        if blur_case0006.get("latest_known_result_status") not in ("answered", "failed_breakpoint_watchpoint"):
            raise AssertionError(
                "OLMBlur case_0006 helper/pre-store request should expose the latest imported state"
            )
        dg_case0023_answered = by_id.get("olmdistancegradation_16bpc_constant_case0023_outside0_witness_20260630")
        if dg_case0023_answered is None:
            raise AssertionError("missing answered DistanceGradation case_0023 OutsideThreshold=0 witness request")
        if dg_case0023_answered["status"] != "answered":
            raise AssertionError(
                "DistanceGradation case_0023 OutsideThreshold=0 request should now be answered, "
                f"got {dg_case0023_answered['status']}"
            )
        if dg_case0023_answered["priority"] != 22:
            raise AssertionError(
                "DistanceGradation case_0023 OutsideThreshold=0 priority should stay 22, "
                f"got {dg_case0023_answered['priority']}"
            )
        if "compare_distancegradation_trace.py" not in dg_case0023_answered["comparison_command"]:
            raise AssertionError(
                "DistanceGradation case_0023 OutsideThreshold=0 request should point to the DistanceGradation comparator"
            )
        dg_case0023_pending = by_id.get("olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701")
        if dg_case0023_pending is None:
            raise AssertionError("missing DistanceGradation triplet compose-hook follow-up request")
        if dg_case0023_pending["status"] != "superseded":
            raise AssertionError(
                "DistanceGradation triplet compose-hook follow-up should now be superseded, "
                f"got {dg_case0023_pending['status']}"
            )
        if dg_case0023_pending["priority"] != 20:
            raise AssertionError(
                "DistanceGradation triplet compose-hook follow-up priority should be 20, "
                f"got {dg_case0023_pending['priority']}"
            )
        if "compare_distancegradation_trace.py" not in dg_case0023_pending["comparison_command"]:
            raise AssertionError(
                "DistanceGradation triplet compose-hook follow-up should point to the DistanceGradation comparator"
            )
        radial_backstep = by_id.get("olmradialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701")
        if radial_backstep is None:
            raise AssertionError("missing RadialBlur inverse-sampler backstep follow-up request")
        if radial_backstep["status"] != "superseded":
            raise AssertionError(
                "RadialBlur inverse-sampler backstep follow-up should now be superseded, "
                f"got {radial_backstep['status']}"
            )
        radial_anchor = by_id.get("olmradialblur_tiny_rotation_anchor_watch_followup_20260701")
        if radial_anchor is None:
            raise AssertionError("missing RadialBlur anchor-watch follow-up request")
        if radial_anchor["status"] != "pending":
            raise AssertionError(
                "RadialBlur anchor-watch follow-up should now be pending, "
                f"got {radial_anchor['status']}"
            )
        if radial_anchor["priority"] != 5:
            raise AssertionError(
                f"RadialBlur anchor-watch follow-up priority should be 5, got {radial_anchor['priority']}"
            )
        dg_output_word = by_id.get("olmdistancegradation_case0023_output_word_triplet_followup_20260701")
        if dg_output_word is None:
            raise AssertionError("missing DistanceGradation output-word triplet follow-up request")
        if dg_output_word["status"] != "pending":
            raise AssertionError(
                "DistanceGradation output-word triplet follow-up should now be pending, "
                f"got {dg_output_word['status']}"
            )
        if dg_output_word["priority"] != 19:
            raise AssertionError(
                "DistanceGradation output-word triplet follow-up priority should be 19, "
                f"got {dg_output_word['priority']}"
            )
        kirakira = by_id.get("kirakira_boxfilter_pass1_microprobe_20260622")
        if kirakira is None or kirakira["status"] != "answered":
            raise AssertionError("KiraKira microprobe request should be answered")
        directional = by_id.get("olmdirectionalblur_angle0_diagonal_residual_witness_20260622")
        if directional is None or directional["status"] != "answered":
            raise AssertionError("DirectionalBlur residual request should be answered")
        directional_new = by_id.get("olmdirectionalblur_helper_coverage_witness_20260630")
        if directional_new is not None:
            if directional_new["status"] != "answered":
                raise AssertionError(
                    f"DirectionalBlur helper-coverage request should be answered, got {directional_new['status']}"
                )
            if directional_new["priority"] != 29:
                raise AssertionError(
                    f"DirectionalBlur helper-coverage priority should be 29, got {directional_new['priority']}"
                )
            if "compare_directionalblur_trace.py" not in directional_new["comparison_command"]:
                raise AssertionError("DirectionalBlur helper-coverage request should point to the DirectionalBlur comparator")
        dg_layer = by_id.get("olmdistancegradation_16bpc_layer_no_bg_source_ownership_20260629")
        if dg_layer is None:
            raise AssertionError("missing DistanceGradation layer/no-bg witness request")
        if dg_layer["status"] != "answered":
            raise AssertionError(
                f"DistanceGradation layer/no-bg request should be answered, got {dg_layer['status']}"
            )
        dg_constant = by_id.get("olmdistancegradation_16bpc_constant_boundary_witness_20260630")
        if dg_constant is None:
            raise AssertionError("missing DistanceGradation constant-boundary request")
        if dg_constant["status"] != "answered":
            raise AssertionError(
                f"DistanceGradation constant-boundary request should be answered, got {dg_constant['status']}"
            )
        smoother_old = by_id.get("olmsmoother2_legacy_u8_writer_trace_20260620")
        if smoother_old is not None and smoother_old["status"] != "superseded":
            raise AssertionError("old Smoother2 trace should not be treated as active")
        markdown = out_md.read_text(encoding="utf-8")
        pending_count = sum(1 for row in rows if row.get("status") == "pending")
        for needle in (
            "Pending Runtime Trace Packages",
            f"Pending: `{pending_count}`",
            "olmradialblur_tiny_rotation_anchor_watch_followup_20260701",
            "olmradialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701",
            "olmdistancegradation_case0023_output_word_triplet_followup_20260701",
            "kirakira_aggregation_compose_bt709_20260624",
            "kirakira_compose_writeback_witness_20260630",
            "olmblur_case0006_helper_prestore_witness_20260630",
            "olmdistancegradation_16bpc_constant_case0023_outside0_witness_20260630",
            "olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701",
            "olmradialblur_caller_collapse_witness_20260630",
            "olmdirectionalblur_helper_coverage_witness_20260630",
            "olmdistancegradation_16bpc_constant_boundary_witness_20260630",
            "superseded",
        ):
            if needle not in markdown:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] pending runtime trace package smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
