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
        if kirakira_compose["status"] != "pending":
            raise AssertionError(
                f"KiraKira compose/writeback request should be pending, got {kirakira_compose['status']}"
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
        if radial["status"] != "pending":
            raise AssertionError(f"focused RadialBlur request should be pending, got {radial['status']}")
        if radial["priority"] != 9:
            raise AssertionError(f"focused RadialBlur request priority should be 9, got {radial['priority']}")
        if "compare_radialblur_trace.py" not in radial["comparison_command"]:
            raise AssertionError("focused RadialBlur request should point to the RadialBlur comparator")
        blur_final = by_id.get("olmblur_final_word_witness_20260630")
        if blur_final is None:
            raise AssertionError("missing OLMBlur final-word request")
        if blur_final["status"] != "pending":
            raise AssertionError(f"OLMBlur final-word request should be pending, got {blur_final['status']}")
        if blur_final["priority"] != 19:
            raise AssertionError(f"OLMBlur final-word priority should be 19, got {blur_final['priority']}")
        if "compare_olmblur_trace.py" not in blur_final["comparison_command"]:
            raise AssertionError("OLMBlur final-word request should point to the OLMBlur comparator")
        kirakira = by_id.get("kirakira_boxfilter_pass1_microprobe_20260622")
        if kirakira is None or kirakira["status"] != "answered":
            raise AssertionError("KiraKira microprobe request should be answered")
        directional = by_id.get("olmdirectionalblur_angle0_diagonal_residual_witness_20260622")
        if directional is None or directional["status"] != "answered":
            raise AssertionError("DirectionalBlur residual request should be answered")
        directional_new = by_id.get("olmdirectionalblur_helper_coverage_witness_20260630")
        if directional_new is not None:
            if directional_new["status"] != "pending":
                raise AssertionError(
                    f"DirectionalBlur helper-coverage request should be pending, got {directional_new['status']}"
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
        smoother_old = by_id.get("olmsmoother2_legacy_u8_writer_trace_20260620")
        if smoother_old is not None and smoother_old["status"] != "superseded":
            raise AssertionError("old Smoother2 trace should not be treated as active")
        markdown = out_md.read_text(encoding="utf-8")
        for needle in (
            "Pending Runtime Trace Packages",
            "Pending: `4`",
            "kirakira_aggregation_compose_bt709_20260624",
            "kirakira_compose_writeback_witness_20260630",
            "olmblur_final_word_witness_20260630",
            "olmradialblur_caller_collapse_witness_20260630",
            "olmdirectionalblur_helper_coverage_witness_20260630",
            "olmdistancegradation_16bpc_layer_no_bg_source_ownership_20260629",
            "Send First",
        ):
            if needle not in markdown:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] pending runtime trace package smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
