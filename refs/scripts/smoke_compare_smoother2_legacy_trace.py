#!/usr/bin/env python3
"""Smoke-test scripts/compare_smoother2_legacy_trace.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


WRITER_FRAME_REQUEST_ID = "olmsmoother2_current_aex_writer_frame_followup_trace_20260625"
PRODUCER_DIFF_REQUEST_ID = "olmsmoother2_current_aex_producer_path_diff_20260702"
WRITER_GATE_REQUEST_ID = "olmsmoother2_current_aex_0004_writer_gate_retry_20260702"
LOAD_PREWARM_REQUEST_ID = "olmsmoother2_current_aex_0004_load_prewarm_retry_20260703"
PRODUCER_BYTES_20260708_REQUEST_ID = "olmsmoother2_current_aex_producer_bytes_20260708"
BIND_THEN_READ_20260708_REQUEST_ID = "olmsmoother2_current_aex_0012_bind_then_read_20260708"


def run_compare(repo: Path, py: str, summary: Path, output_json: Path, output_md: Path) -> dict:
    proc = subprocess.run(
        [
            py,
            "scripts/compare_smoother2_legacy_trace.py",
            "--runtime-summary-json",
            str(summary),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return json.loads(output_json.read_text(encoding="utf-8"))


def assert_focus(comparison: dict, expected: str) -> None:
    if comparison.get("likely_next_focus") != expected:
        print(f"[FAIL] expected focus {expected}, got {comparison.get('likely_next_focus')}")
        raise SystemExit(1)


def assert_request(comparison: dict, expected: str) -> None:
    if comparison.get("request_id") != expected:
        print(f"[FAIL] expected request_id {expected}, got {comparison.get('request_id')}")
        raise SystemExit(1)


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_compare_smoke_") as tmp:
        tmp_path = Path(tmp)
        summary = tmp_path / "runtime_summary.json"
        output_json = tmp_path / "comparison.json"
        output_md = tmp_path / "comparison.md"

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": BIND_THEN_READ_20260708_REQUEST_ID,
                            "status": "failed_partial",
                            "summary": "This package correctly narrows to the 0012-only bind-then-read lane, but it still contains no fresh same-run Windows Stage A bind or Stage B typed byte read.",
                            "observations": {
                                "ae_context": {"project_renderer_name": "SOFTWARE"},
                                "cases": [
                                    {
                                        "case_id": "legacy_case_0012_gamma5_red_blue_current_aex",
                                        "witness_pixels": [
                                            {
                                                "x": 91,
                                                "y": 841,
                                                "intermediate_values": {
                                                    "local_center_b0": 0,
                                                    "local_prev_b0": 1,
                                                    "local_left_b1": 0,
                                                    "local_e170_c": 2,
                                                },
                                            }
                                        ],
                                    }
                                ],
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, BIND_THEN_READ_20260708_REQUEST_ID)
        assert_focus(comparison, "0012-stage-a-bind-missing")
        missing = comparison["windows"]["missing_field_matrix"][0]["missing_windows_fields"]
        if "Windows Stage B center_b0" not in missing:
            print("[FAIL] bind-then-read comparison missing Stage B byte matrix")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": PRODUCER_BYTES_20260708_REQUEST_ID,
                            "status": "failed_partial",
                            "summary": "This package carries strong local Unicorn producer-branch evidence for the active 0012 and 0004 lanes, but it does not contain the requested same-run Windows producer-byte/class-plane witness values.",
                            "observations": {
                                "ae_context": {"project_renderer_name": "SOFTWARE"},
                                "cases": [
                                    {
                                        "case_id": "legacy_case_0012_gamma5_red_blue_current_aex",
                                        "witness_pixels": [
                                            {
                                                "x": 91,
                                                "y": 841,
                                                "intermediate_values": {
                                                    "local_center_b0": 0,
                                                    "local_prev_b0": 1,
                                                    "local_left_b1": 0,
                                                    "local_e170_c": 2,
                                                },
                                            }
                                        ],
                                    },
                                    {
                                        "case_id": "legacy_case_0004_current_aex",
                                        "witness_pixels": [
                                            {
                                                "x": 1903,
                                                "y": 519,
                                                "intermediate_values": {
                                                    "local_no_emit_shape_1": "iVar6 >= 4 && iVar5 >= 4",
                                                },
                                            }
                                        ],
                                    },
                                ],
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, PRODUCER_BYTES_20260708_REQUEST_ID)
        assert_focus(comparison, "producer-byte-class-plane-windows-bind-missing")
        matrices = comparison["windows"]["missing_field_matrix"]
        if "Windows same-run 0004 iVar6" not in matrices[1]["missing_windows_fields"]:
            print("[FAIL] producer-byte comparison missing 0004 scanner matrix")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": WRITER_FRAME_REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "Writer-anchored follow-up captured exact writer frame and final floats for both active witnesses.",
                            "observations": {
                                "ae_context": {"bit_depth": "8bpc"},
                                "cases": [
                                    {"case_id": "legacy_case_0004_current_aex"},
                                    {"case_id": "legacy_case_0012_gamma5_red_blue_current_aex"},
                                ],
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, WRITER_FRAME_REQUEST_ID)
        assert_focus(comparison, "writer-frame-confirmed-producer-unresolved")
        if "first c280/cce0 producer divergence" not in comparison.get("recommended_next_evidence", ""):
            print("[FAIL] writer-frame comparison missing producer-divergence recommendation")
            return 1
        if "local_legacy_lane_state" not in comparison:
            print("[FAIL] writer-frame comparison should include local legacy lane state")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": PRODUCER_DIFF_REQUEST_ID,
                            "status": "failed_partial",
                            "summary": "Fresh Windows CDB pass was run. OLMSmoother2 loaded and broad breakpoints at c280/cce0/350b/3610 fired, proving the producer/writeback path is reachable in the current AE run.",
                            "observations": {
                                "ae_context": {"bit_depth": "8bpc"},
                                "cases": [{"case_id": "legacy_case_0004_current_aex"}],
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, PRODUCER_DIFF_REQUEST_ID)
        assert_focus(comparison, "producer-path-diff-writer-anchor-reached")

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": WRITER_GATE_REQUEST_ID,
                            "status": "failed",
                            "summary": "Fresh exact-gate CDB retry was attempted for legacy_case_0004_current_aex. This run stalled before OLMSmoother2 loaded, so the exact gate was never reached.",
                            "observations": {
                                "ae_context": {"bit_depth": "8bpc"},
                                "cases": [{"case_id": "legacy_case_0004_current_aex"}],
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, WRITER_GATE_REQUEST_ID)
        assert_focus(comparison, "writer-gate-preload-stall")

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": LOAD_PREWARM_REQUEST_ID,
                            "status": "failed_partial",
                            "summary": "Fresh load-only prewarm retry was run for exact case legacy_case_0004_current_aex.",
                            "observations": {
                                "ae_context": {"bit_depth": "8bpc"},
                                "cases": [{"case_id": "legacy_case_0004_current_aex"}],
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, LOAD_PREWARM_REQUEST_ID)
        assert_focus(comparison, "module-load-prewarm")

        markdown = output_md.read_text(encoding="utf-8")
        for needle in (
            "OLMSmoother2 Legacy Trace Comparison",
            "Missing Field Matrix",
            "Local Legacy Lane State",
            "writer-frame-confirmed-producer-unresolved",
            "module-load-prewarm",
        ):
            if needle not in markdown:
                print(f"[FAIL] comparison Markdown missing: {needle}")
                return 1
    print("[OK] Smoother2 legacy trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
