#!/usr/bin/env python3
"""Smoke-test scripts/analyze_pending_runtime_trace_packages.py."""

from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path


def load_analyzer(repo: Path):
    spec = importlib.util.spec_from_file_location(
        "analyze_pending_runtime_trace_packages", repo / "scripts/analyze_pending_runtime_trace_packages.py"
    )
    if spec is None or spec.loader is None:
        raise AssertionError("could not load pending runtime analyzer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    analyzer = load_analyzer(repo)
    with tempfile.TemporaryDirectory(prefix="pending_runtime_trace_superseded_smoke_") as tmp:
        root = Path(tmp)
        report_dir = root / "refs/reports"
        report_dir.mkdir(parents=True)
        (report_dir / "runtime_trace_superseded.json").write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_superseded",
                    "superseded": [{"request_id": "synthetic_request_20260715_retry_20260715"}],
                }
            ),
            encoding="utf-8",
        )
        superseded = analyzer.superseded_request_ids(root)
        if superseded != {"synthetic_request_20260715"}:
            raise AssertionError(f"superseded retry ID must normalize to its queue ID, got {superseded}")
        if analyzer.row_status("synthetic_request_20260715", set(), superseded) != "superseded":
            raise AssertionError("normalized superseded retry ID must prevent a false-pending row")
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
        dg_typed = by_id.get("olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712")
        if dg_typed is None:
            raise AssertionError("missing DistanceGradation 8bpc typed-boundary request")
        if dg_typed["priority"] != 1:
            raise AssertionError(
                "DistanceGradation typed-boundary resend must remain queue head at priority 1, "
                f"got {dg_typed['priority']}"
            )
        if "15 typed records" not in dg_typed.get("stop_condition", ""):
            raise AssertionError("DistanceGradation typed-boundary request must expose the v4 acceptance gate")
        successor_expectations = {
            "olmdirectionalblur_row755_20260713": (
                "refs/runtime_trace_packages/windows_witness_olmdirectionalblur_row755_20260713.zip",
                3,
            ),
            "olmradialblur_case0009_fullframe_postnorm_typed_common_core_20260713": (
                "refs/runtime_trace_packages/windows_witness_olmradialblur_case0009_fullframe_postnorm_typed_common_core_20260713.zip",
                18,
            ),
            "olmsmoother2_case0012_current_aex_20260713": (
                "refs/runtime_trace_packages/windows_witness_olmsmoother2_case0012_20260713.zip",
                214,
            ),
        }
        for request_id, (package, priority) in successor_expectations.items():
            row = by_id.get(request_id)
            if row is None:
                raise AssertionError(f"missing common-core successor request: {request_id}")
            if row["status"] != "pending":
                raise AssertionError(f"common-core successor must remain pending: {request_id}={row['status']}")
            if row["package"] != package or row["priority"] != priority:
                raise AssertionError(
                    f"common-core successor queue metadata drift: {request_id} "
                    f"package={row['package']} priority={row['priority']}"
                )
        for request_id in (
            "olmdirectionalblur_alpha_fade_fullrender_row755_20260712",
            "olmradialblur_case0009_fullframe_postnorm_typed_20260710",
            "olmsmoother2_case0012_live_config_binding_20260713",
        ):
            row = by_id.get(request_id)
            if row is None or row["status"] != "superseded":
                raise AssertionError(f"old witness request must be superseded by common-core package: {request_id}")
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
        if blur_case0006["status"] != "invalid_unverified_values":
            raise AssertionError(
                "OLMBlur case_0006 helper/pre-store request must remain invalid until a retained "
                f"Windows target proves the numeric fields, got {blur_case0006['status']}"
            )
        if blur_case0006["priority"] != 18:
            raise AssertionError(f"OLMBlur case_0006 helper/pre-store priority should be 18, got {blur_case0006['priority']}")
        if "compare_olmblur_trace.py" not in blur_case0006["comparison_command"]:
            raise AssertionError("OLMBlur case_0006 helper/pre-store request should point to the OLMBlur comparator")
        if blur_case0006.get("latest_known_result_status") not in ("answered", "failed_breakpoint_watchpoint"):
            raise AssertionError(
                "OLMBlur case_0006 helper/pre-store request should expose the latest imported state"
            )
        blur_case0006_common = by_id.get("olmblur_case0006_same_run_internal_20260713")
        if blur_case0006_common is None:
            raise AssertionError("missing OLMBlur case_0006 common-core request")
        if blur_case0006_common["status"] != "superseded":
            raise AssertionError(
                "OLMBlur case_0006 common-core request must be superseded after current-plugin AE exact closeout, "
                f"got {blur_case0006_common['status']}"
            )
        pending_ids = {row["request_id"] for row in rows if row.get("status") == "pending"}
        if "olmblur_case0006_same_run_internal_20260713" in pending_ids:
            raise AssertionError("superseded OLMBlur case_0006 common-core request must not remain pending")
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
        if radial_anchor["status"] != "superseded":
            raise AssertionError(
                "RadialBlur anchor-watch follow-up should now be superseded, "
                f"got {radial_anchor['status']}"
            )
        if radial_anchor["priority"] != 5:
            raise AssertionError(
                f"RadialBlur anchor-watch follow-up priority should be 5, got {radial_anchor['priority']}"
            )
        radial_anchor_context = by_id.get("olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702")
        if radial_anchor_context is None:
            raise AssertionError("missing RadialBlur anchor-context follow-up request")
        if radial_anchor_context["status"] != "superseded":
            raise AssertionError(
                "RadialBlur anchor-context follow-up should now be superseded by local AEX emulation, "
                f"got {radial_anchor_context['status']}"
            )
        hard_lane = radial_anchor_context.get("hard_lane_context") or {}
        if hard_lane.get("note") != "refs/conformance/olmradialblur_tiny_rotation_lane_state_20260703.md":
            raise AssertionError("RadialBlur anchor-context follow-up should expose the lane-state note")
        dg_stack = by_id.get("olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702")
        if dg_stack is None:
            raise AssertionError("missing DistanceGradation refcon/stack wordmap follow-up request")
        if dg_stack["status"] != "superseded":
            raise AssertionError(
                "DistanceGradation refcon/stack wordmap follow-up should now be superseded by local AEX CPU simu, "
                f"got {dg_stack['status']}"
            )
        if (dg_stack.get("hard_lane_context") or {}).get("note") != "refs/conformance/olmdistancegradation_case0023_lane_state_20260707.md":
            raise AssertionError("DistanceGradation pending follow-up should expose the lane-state note")
        dg_final_source = by_id.get("olmdistancegradation_case0023_final_source_ownership_20260707")
        if dg_final_source is None:
            raise AssertionError("missing DistanceGradation case_0023 final/source ownership request")
        if dg_final_source["status"] != "answered":
            raise AssertionError(
                "DistanceGradation case_0023 final/source ownership request should be answered after depth-gate closeout, "
                f"got {dg_final_source['status']}"
            )
        if dg_final_source["priority"] != 16:
            raise AssertionError(
                "DistanceGradation case_0023 final/source ownership priority should be 16, "
                f"got {dg_final_source['priority']}"
            )
        if "compare_distancegradation_trace.py" not in dg_final_source["comparison_command"]:
            raise AssertionError(
                "DistanceGradation case_0023 final/source ownership request should point to the DistanceGradation comparator"
            )
        if "olmdistancegradation_case0023_final_source_ownership_20260707" not in dg_final_source["comparison_command"]:
            raise AssertionError("DistanceGradation case_0023 final/source ownership should use its own comparison slug")
        if dg_final_source.get("acceptance_note") != "refs/conformance/olmdistancegradation_case0023_final_source_ownership_contract_20260707.md":
            raise AssertionError("DistanceGradation case_0023 final/source ownership should expose its contract")
        if (dg_final_source.get("hard_lane_context") or {}).get("note") != "refs/conformance/olmdistancegradation_case0023_neighborhood_probe_result_20260707.md":
            raise AssertionError("DistanceGradation case_0023 final/source ownership should expose the neighborhood probe note")
        dg_depthgate = by_id.get("olmdistancegradation_depthgate_quantization_witness_20260708")
        if dg_depthgate is None:
            raise AssertionError("missing DistanceGradation depth-gate quantization witness request")
        if dg_depthgate["status"] != "answered":
            raise AssertionError(
                "DistanceGradation depth-gate quantization witness should be answered after the 2026-07-08 return, "
                f"got {dg_depthgate['status']}"
            )
        if dg_depthgate["priority"] != 17:
            raise AssertionError(
                "DistanceGradation depth-gate quantization witness priority should be 17, "
                f"got {dg_depthgate['priority']}"
            )
        if "compare_distancegradation_trace.py" not in dg_depthgate["comparison_command"]:
            raise AssertionError("DistanceGradation depth-gate quantization witness should point to the DistanceGradation comparator")
        if "olmdistancegradation_depthgate_quantization_witness_20260708" not in dg_depthgate["comparison_command"]:
            raise AssertionError("DistanceGradation depth-gate quantization witness should use its own comparison slug")
        if dg_depthgate.get("acceptance_note") != "refs/conformance/olmdistancegradation_depthgate_quantization_witness_contract_20260708.md":
            raise AssertionError("DistanceGradation depth-gate quantization witness should expose its contract")
        if (dg_depthgate.get("hard_lane_context") or {}).get("note") != "refs/conformance/olmdistancegradation_depthgate_nearmiss_witness_20260708.md":
            raise AssertionError("DistanceGradation depth-gate quantization witness should expose the near-miss witness note")
        dg_depthgate_907 = by_id.get("olmdistancegradation_depthgate_907_store_export_witness_20260708")
        if dg_depthgate_907 is None:
            raise AssertionError("missing DistanceGradation depth-gate 907 store/export witness request")
        if dg_depthgate_907["status"] != "answered_partial":
            raise AssertionError(
                "DistanceGradation depth-gate 907 store/export witness should stay visible as answered_partial, "
                f"got {dg_depthgate_907['status']}"
            )
        if dg_depthgate_907.get("latest_known_result_status") != "answered_partial":
            raise AssertionError("DistanceGradation depth-gate 907 should expose its latest answered_partial result")
        if "compare_distancegradation_trace.py" not in dg_depthgate_907["comparison_command"]:
            raise AssertionError("DistanceGradation depth-gate 907 should point to the DistanceGradation comparator")
        directional_gate = by_id.get("olmdirectionalblur_angle0_helper_gate_retry_20260702")
        if directional_gate is None or directional_gate["status"] != "answered":
            raise AssertionError("DirectionalBlur helper-gate retry should be answered_partial/answered after import")
        if directional_gate["priority"] != 110:
            raise AssertionError(
                "DirectionalBlur helper-gate retry should be the first algorithm runtime pending item, "
                f"got priority {directional_gate['priority']}"
            )
        if (directional_gate.get("hard_lane_context") or {}).get("note") != "refs/conformance/olmdirectionalblur_lane_state_20260703.md":
            raise AssertionError("DirectionalBlur helper-gate retry should expose the lane-state note")
        if directional_gate.get("latest_known_result_status") != "failed":
            raise AssertionError("DirectionalBlur helper-gate retry should expose its latest failed real-case retry result")
        if "directionalblur_angle0_helper_gate_retry" not in directional_gate.get("latest_return_archive", ""):
            raise AssertionError("DirectionalBlur helper-gate retry should expose its raw return zip evidence")
        directional_prewarm = by_id.get("olmdirectionalblur_angle0_load_prewarm_retry_20260703")
        if directional_prewarm is None or directional_prewarm["status"] != "failed_partial":
            raise AssertionError("DirectionalBlur load-prewarm retry should be failed_partial, not pending")
        if directional_prewarm.get("latest_known_result_status") != "failed_partial":
            raise AssertionError("DirectionalBlur load-prewarm retry should expose its latest failed_partial result")
        if "directionalblur_angle0_load_prewarm_retry" not in directional_prewarm.get("latest_return_archive", ""):
            raise AssertionError("DirectionalBlur load-prewarm retry should expose its raw return zip evidence")
        smoother_gate = by_id.get("olmsmoother2_current_aex_0004_writer_gate_retry_20260702")
        if smoother_gate is None or smoother_gate["status"] != "failed":
            raise AssertionError("Smoother2 writer-gate retry should be failed, not pending")
        if (smoother_gate.get("hard_lane_context") or {}).get("note") != "refs/conformance/olmsmoother2_legacy_lane_state_20260703.md":
            raise AssertionError("Smoother2 writer-gate retry should expose the lane-state note")
        if smoother_gate.get("latest_known_result_status") != "failed":
            raise AssertionError("Smoother2 writer-gate retry should expose its latest failed retry result")
        if "smoother2_current_aex_0004_writer_gate_retry" not in smoother_gate.get("latest_return_archive", ""):
            raise AssertionError("Smoother2 writer-gate retry should expose its raw return zip evidence")
        smoother_prewarm = by_id.get("olmsmoother2_current_aex_0004_load_prewarm_retry_20260703")
        if smoother_prewarm is None or smoother_prewarm["status"] != "failed_partial":
            raise AssertionError("Smoother2 load-prewarm retry should be failed_partial, not pending")
        if smoother_prewarm.get("latest_known_result_status") != "failed_partial":
            raise AssertionError("Smoother2 load-prewarm retry should expose its latest failed_partial result")
        if "smoother2_current_aex_0004_load_prewarm_retry" not in smoother_prewarm.get("latest_return_archive", ""):
            raise AssertionError("Smoother2 load-prewarm retry should expose its raw return zip evidence")
        dg_output_word = by_id.get("olmdistancegradation_case0023_output_word_triplet_followup_20260701")
        if dg_output_word is None:
            raise AssertionError("missing DistanceGradation output-word triplet follow-up request")
        if dg_output_word["status"] != "superseded":
            raise AssertionError(
                "DistanceGradation output-word triplet follow-up should now be superseded, "
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
            "Hard lane context",
            "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702",
            "olmradialblur_tiny_rotation_anchor_watch_followup_20260701",
            "olmradialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701",
            "olmdistancegradation_case0023_output_word_triplet_followup_20260701",
            "olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702",
            "olmdistancegradation_case0023_final_source_ownership_20260707",
            "olmdistancegradation_case0023_final_source_ownership_contract_20260707.md",
            "olmdistancegradation_case0023_neighborhood_probe_result_20260707.md",
            "olmdistancegradation_depthgate_quantization_witness_20260708",
            "olmdistancegradation_depthgate_quantization_witness_contract_20260708.md",
            "olmdistancegradation_depthgate_nearmiss_witness_20260708.md",
            "olmdirectionalblur_angle0_helper_gate_retry_20260702",
            "olmsmoother2_current_aex_0004_writer_gate_retry_20260702",
            "olmradialblur_tiny_rotation_lane_state_20260703.md",
            "olmdistancegradation_case0023_lane_state_20260707.md",
            "olmdirectionalblur_lane_state_20260703.md",
            "olmsmoother2_legacy_lane_state_20260703.md",
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
