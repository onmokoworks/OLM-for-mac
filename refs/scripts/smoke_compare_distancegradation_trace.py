#!/usr/bin/env python3
"""Smoke-test scripts/compare_distancegradation_trace.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REQUEST_ID = "olmdistancegradation_field_prep_runtime_trace_20260619"
CONSTANT_REQUEST_ID = "olmdistancegradation_16bpc_constant_boundary_witness_20260630"
THRESHOLD_REQUEST_ID = "olmdistancegradation_case0023_threshold_family_followup_20260701"
TRIPLET_XY_REQUEST_ID = "olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701"
FINAL_SOURCE_OWNERSHIP_REQUEST_ID = "olmdistancegradation_case0023_final_source_ownership_20260707"
CASE0014_LAYER_SOURCE_REQUEST_ID = "olmdistancegradation_case0014_layer_source_witness_20260708"
CASE0010_0011_FIELD_STORE_REQUEST_ID = "olmdistancegradation_0010_0011_field_store_witness_20260709"
CASE0010_0011_FIELD_STORE_PREWARM_REQUEST_ID = (
    "olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709"
)
CASE0010_0011_COMPOSE_EXACT_ADDRESS_REQUEST_ID = (
    "olmdistancegradation_0010_0011_compose_exact_address_witness_20260710"
)
SINGLE_SITE_FOLLOWUP_REQUEST_ID = "olmdistancegradation_0010_compose_single_site_followup_20260710"
SINGLE_SITE_BREAK_IGNORE_RETRY_REQUEST_ID = (
    "olmdistancegradation_0010_compose_single_site_break_ignore_retry_20260710"
)


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="olmdistancegradation_compare_smoke_") as tmp:
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
                            "request_id": REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic DistanceGradation field prep trace",
                            "source_file": "synthetic.zip",
                            "observations": {
                                "cases": ["case_0020", "case_0022", "case_0029"],
                                "requested_for_each_pixel": {
                                    "source_input_rgba_8bit": [
                                        {"case_id": "case_0020", "x": 64, "y": 32, "rgba": [0, 0, 0, 255]}
                                    ],
                                    "distance_field_before_constant_rgba_or_mat_values": [
                                        {"case_id": "case_0020", "x": 64, "y": 32, "value": 0.0}
                                    ],
                                    "distance_field_after_constant_rgba_or_mat_values": [
                                        {"case_id": "case_0020", "x": 64, "y": 32, "value": 255.0}
                                    ],
                                    "distance_transform_call": "not reached in this synthetic branch",
                                    "threshold_and_normalization": None,
                                    "gaussian_blur_call_if_case_0029": None,
                                    "fun_181170870_field_pixel_bytes": [
                                        {"case_id": "case_0020", "x": 64, "y": 32, "g": 255}
                                    ],
                                    "final_rgba_8bit": [
                                        {"case_id": "case_0020", "x": 64, "y": 32, "rgba": [255, 255, 255, 255]}
                                    ],
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("request_id") != REQUEST_ID:
            print("[FAIL] comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "constant-field-prep":
            print("[FAIL] comparison did not choose expected next focus")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        for needle in ("OLMDistanceGradation Trace Comparison", "Local Assumptions", "Field values"):
            if needle not in markdown:
                print(f"[FAIL] comparison Markdown missing: {needle}")
                return 1
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "synthetic sparse DistanceGradation trace",
                            "observations": {
                                "requested_for_each_pixel": {
                                    "distance_field_before_constant_rgba_or_mat_values": [
                                        "not isolated; upstream pre-Constant field value still needs debugger trace"
                                    ],
                                    "distance_field_after_constant_rgba_or_mat_values": [
                                        "not isolated; current best guard says Constant mode binarizes upstream"
                                    ],
                                    "distance_transform_call": {
                                        "dist_type": "inferred OpenCV DIST_L2; Windows runtime arg still untraced",
                                    },
                                    "gaussian_blur_call_if_case_0029": {
                                        "border_type": "likely BORDER_REFLECT_101; runtime arg still untraced",
                                    },
                                    "fun_181170870_field_pixel_bytes": [
                                        "not isolated; decomp shows distance field is read from green byte"
                                    ],
                                }
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("likely_next_focus") != "trace-too-sparse":
            print("[FAIL] placeholder observations should stay trace-too-sparse")
            return 1
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": CONSTANT_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic constant-boundary witness",
                            "observations": {
                                "cases": [
                                    {"case_id": "olmdistancegradation_extended__case_0020"},
                                    {"case_id": "olmdistancegradation_extended__case_0022"},
                                ],
                                "requested_for_each_pixel": {
                                    "binary_mask_before_distance_transform": [
                                        {"case_id": "olmdistancegradation_extended__case_0020", "x": 434, "y": 676, "mask": 1}
                                    ],
                                    "inside_or_outside_distance_before_threshold": [
                                        {"case_id": "olmdistancegradation_extended__case_0020", "x": 434, "y": 676, "inside": 78.00641, "outside": 0.0}
                                    ],
                                    "comparison_rule": "<= inside threshold for In mode",
                                    "selected_side_inside_outside_or_both": "inside",
                                    "final_rgba16": [
                                        {"case_id": "olmdistancegradation_extended__case_0020", "x": 434, "y": 676, "rgba": [7195, 0, 61165, 65535]}
                                    ],
                                },
                                "case_level_contract": {
                                    "must_explain": [
                                        "threshold ownership at the boundary"
                                    ]
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("request_id") != CONSTANT_REQUEST_ID:
            print("[FAIL] constant-boundary comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "constant-boundary-threshold-ownership":
            print("[FAIL] constant-boundary witness should classify as threshold ownership")
            return 1
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": CASE0010_0011_FIELD_STORE_REQUEST_ID,
                            "status": "failed_partial",
                            "summary": "synthetic missing field/store witness",
                            "observations": {
                                "effect": "OLMDistanceGradation 16bpc case_0010/0011 sparse R/A PF16 store proof",
                                "cases": [
                                    {
                                        "case_id": "olmdistancegradation_extended__case_0010",
                                        "witness_pixels": [
                                            {
                                                "x": 6,
                                                "y": 40,
                                                "pre_writeback_rgba_float_hex": [None, None, None, None],
                                                "final_rgba": [None, None, None, None],
                                                "intermediate_values": {
                                                    "local_store_a": 3267,
                                                    "windows_implied_store_a": 3268,
                                                    "missing_reason": "No same-run Windows source/field/pre-store/store/export values are bundled.",
                                                },
                                            }
                                        ],
                                    }
                                ],
                                "directly_observed_vs_inferred": {
                                    "directly_observed": ["package-local local field/store probe values"],
                                    "not_isolated": ["same-run Windows PF16 stored RGBA words"],
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("request_id") != CASE0010_0011_FIELD_STORE_REQUEST_ID:
            print("[FAIL] case0010/0011 comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "case0010-0011-field-store-witness-missing":
            print("[FAIL] missing case0010/0011 witness should stay in witness-missing lane")
            return 1
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": CASE0010_0011_FIELD_STORE_PREWARM_REQUEST_ID,
                            "status": "failed_partial",
                            "summary": "synthetic prewarm missing module-load witness",
                            "observations": {
                                "effect": "OLMDistanceGradation 16bpc case_0010/0011 sparse R/A PF16 store proof with module prewarm",
                                "cases": [
                                    {
                                        "case_id": "olmdistancegradation_extended__case_0010",
                                        "witness_pixels": [
                                            {
                                                "x": 6,
                                                "y": 40,
                                                "intermediate_values": {
                                                    "missing_reason": "DistanceGradation.aex module-load stop was not reached.",
                                                },
                                            }
                                        ],
                                    }
                                ],
                                "directly_observed_vs_inferred": {
                                    "directly_observed": ["AE/CDB launched"],
                                    "not_isolated": ["DistanceGradation.aex module-load stop"],
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("request_id") != CASE0010_0011_FIELD_STORE_PREWARM_REQUEST_ID:
            print("[FAIL] prewarm case0010/0011 comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "case0010-0011-field-store-witness-missing":
            print("[FAIL] prewarm missing case0010/0011 witness should stay in witness-missing lane")
            return 1
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": CASE0010_0011_FIELD_STORE_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic typed case0010/0011 field/store witness",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "olmdistancegradation_extended__case_0010",
                                        "witness_pixels": [
                                            {
                                                "x": 6,
                                                "y": 40,
                                                "classification": "pf16-conversion",
                                                "source_rgba16": [0, 0, 0, 65535],
                                                "raw_distance": {"inside": 12.25, "outside": 0.0},
                                                "normalized_field": 0.9002838730812073,
                                                "compose_out_a": 0.09971612691879272,
                                                "pre_store_rgba_float": [65535.0, 0.0, 0.0, 3267.498046875],
                                                "pf_pixel16_words_after_store": [65535, 0, 0, 3268],
                                                "exported_rgba16": [65335, 0, 0, 6535],
                                            },
                                            {
                                                "x": 901,
                                                "y": 394,
                                                "classification": "pf16-conversion",
                                                "source_rgba16": [0, 0, 0, 65535],
                                                "raw_distance": {"inside": 28.5, "outside": 0.0},
                                                "normalized_field": 0.6985930800437927,
                                                "compose_out_a": 0.3014069199562073,
                                                "pre_store_rgba_float": [65535.0, 0.0, 0.0, 9876.501953125],
                                                "pf_pixel16_words_after_store": [65535, 0, 0, 9876],
                                                "exported_rgba16": [45789, 0, 0, 19753],
                                            },
                                        ],
                                    }
                                ],
                                "directly_observed_vs_inferred": {
                                    "directly_observed": ["same-run field/prestore/store/export values"],
                                    "not_isolated": [],
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("likely_next_focus") != "case0010-0011-pf16-conversion-proof":
            print("[FAIL] typed case0010/0011 witness should classify pf16 conversion proof")
            return 1
        windows = comparison.get("windows", {})
        if not windows.get("typed_witness_pixels") or windows.get("classification_counts", {}).get("pf16-conversion") != 2:
            print("[FAIL] typed case0010/0011 witness fields were not surfaced")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": CASE0010_0011_FIELD_STORE_REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "synthetic partial case0010/0011 field/store witness",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "olmdistancegradation_extended__case_0010",
                                        "witness_pixels": [
                                            {
                                                "x": 6,
                                                "y": 40,
                                                "raw_distance": {"inside": 12.25, "outside": 0.0},
                                                "normalized_field": 0.9002838730812073,
                                            }
                                        ],
                                    }
                                ]
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("likely_next_focus") != "case0010-0011-field-store-partial":
            print("[FAIL] partial case0010/0011 witness should stay partial")
            return 1
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": CASE0010_0011_COMPOSE_EXACT_ADDRESS_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic partial exact-address compose binding",
                            "observations": {
                                "classification": "answered_partial",
                                "focus": "16bpc case_0010 exact-address compose input binding.",
                                "address_model": {
                                    "source_base": "0x0000021d8d7b0000",
                                    "source_rowbytes": 15360,
                                    "source_pixel_size": 8,
                                    "source_channel_layout": "PF_Pixel16 RGBA",
                                    "output_base": "0x0000021d8e790000",
                                    "output_rowbytes": 15360,
                                    "output_pixel_size": 8,
                                    "output_channel_layout": "PF_Pixel16 RGBA",
                                },
                                "targets": [
                                    {
                                        "case_id": "olmdistancegradation_extended__case_0010",
                                        "xy": [6, 40],
                                        "field_addr": None,
                                        "source_addr": "0x0000021d8d7b2930",
                                        "output_addr": "0x0000021d8e792930",
                                        "rcx_field_words_at_0x117057d": None,
                                        "rdx_source_words_at_0x11705f1": None,
                                        "xmm1_after_field_read": None,
                                        "xmm2_after_field_transform": None,
                                        "final_writer_scalars": {},
                                        "final_pf16_words": None,
                                    },
                                    {
                                        "case_id": "olmdistancegradation_extended__case_0010",
                                        "xy": [901, 394],
                                        "field_addr": None,
                                        "source_addr": "0x0000021d8d8f7528",
                                        "output_addr": "0x0000021d8e8d7528",
                                        "rcx_field_words_at_0x117057d": None,
                                        "rdx_source_words_at_0x11705f1": None,
                                        "xmm1_after_field_read": None,
                                        "xmm2_after_field_transform": None,
                                        "final_writer_scalars": {},
                                        "final_pf16_words": None,
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
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("request_id") != CASE0010_0011_COMPOSE_EXACT_ADDRESS_REQUEST_ID:
            print("[FAIL] compose exact-address comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "case0010-0011-compose-exact-address-partial-address-binding":
            print("[FAIL] compose exact-address witness should stay partial-address-binding only")
            return 1
        windows = comparison.get("windows", {})
        if windows.get("status") != "answered_partial":
            print("[FAIL] compose exact-address witness should normalize to answered_partial")
            return 1
        progress = windows.get("address_binding", {}).get("progress", {})
        if progress.get("derived_target_count") != 2 or progress.get("fully_typed_target_count") != 0:
            print("[FAIL] compose exact-address progress summary mismatch")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        for needle in ("Address model", "Exact-address targets", "Address binding"):
            if needle not in markdown:
                print(f"[FAIL] compose exact-address Markdown missing: {needle}")
                return 1

        router_dir = tmp_path / "router_comparisons"
        proc = subprocess.run(
            [
                py,
                "scripts/compare_runtime_trace_summary.py",
                "--runtime-summary-json",
                str(summary),
                "--output-dir",
                str(router_dir),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        router_index = json.loads((router_dir / "index.json").read_text(encoding="utf-8"))
        router_rows = {row["slug"]: row for row in router_index.get("comparisons", [])}
        router_row = router_rows.get("olmdistancegradation_0010_0011_compose_exact_address_witness")
        if not isinstance(router_row, dict):
            print("[FAIL] router did not emit dedicated compose exact-address artifact row")
            return 1
        if router_row.get("likely_next_focus") != "case0010-0011-compose-exact-address-partial-address-binding":
            print("[FAIL] router compose exact-address focus mismatch")
            return 1
        if not (router_dir / "olmdistancegradation_0010_0011_compose_exact_address_witness.json").exists():
            print("[FAIL] router compose exact-address JSON artifact missing")
            return 1
        if not (router_dir / "olmdistancegradation_0010_0011_compose_exact_address_witness.md").exists():
            print("[FAIL] router compose exact-address Markdown artifact missing")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": SINGLE_SITE_FOLLOWUP_REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "synthetic single-site followup with no exact downstream hit",
                            "observations": {
                                "case_id": "olmdistancegradation_extended__case_0010",
                                "xy": [6, 40],
                                "site_runs": [
                                    {
                                        "site": "field",
                                        "site_address": "DistanceGradation+0x117057d",
                                        "exact_rdi_gate_hit": False,
                                        "console_artifact": "first-chance 80000003 before downstream gate",
                                        "failed_reason": "downstream breakpoint never evaluated",
                                    },
                                    {
                                        "site": "source",
                                        "site_address": "DistanceGradation+0x11705f1",
                                        "exact_rdi_gate_hit": False,
                                        "console_artifact": "first-chance 80000003 before downstream gate",
                                        "failed_reason": "downstream breakpoint never evaluated",
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
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("request_id") != SINGLE_SITE_FOLLOWUP_REQUEST_ID:
            print("[FAIL] single-site followup comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "single-site-witness-missing":
            print("[FAIL] single-site followup should stay witness-missing without exact site hit")
            return 1
        site_runs = comparison.get("windows", {}).get("site_runs", [])
        if len(site_runs) != 2 or site_runs[0].get("exact_rdi_gate_hit") is not False:
            print("[FAIL] single-site followup site runs were not surfaced")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": SINGLE_SITE_BREAK_IGNORE_RETRY_REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "synthetic single-site retry with typed source words",
                            "observations": {
                                "case_id": "olmdistancegradation_extended__case_0010",
                                "xy": [6, 40],
                                "ignored_first_chance_80000003": True,
                                "site_runs": [
                                    {
                                        "site": "source",
                                        "site_address": "DistanceGradation+0x11705f1",
                                        "exact_rdi_gate_hit": True,
                                        "rdx_source_words": [
                                            "0x0000",
                                            "0x8000",
                                            "0x0000",
                                            "0xffff",
                                        ],
                                        "console_artifact": "gate satisfied after sxi 80000003",
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
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("request_id") != SINGLE_SITE_BREAK_IGNORE_RETRY_REQUEST_ID:
            print("[FAIL] single-site retry comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "single-site-input-bound":
            print("[FAIL] typed single-site source words should classify as input-bound")
            return 1
        branch = comparison.get("windows", {}).get("branch_decision", {})
        if branch.get("ignored_first_chance_80000003") is not True:
            print("[FAIL] single-site retry should surface ignored first-chance flag")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": SINGLE_SITE_FOLLOWUP_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic single-site writer words",
                            "observations": {
                                "case_id": "olmdistancegradation_extended__case_0010",
                                "target_xy": [6, 40],
                                "site_runs": {
                                    "writer": {
                                        "downstream_address": "DistanceGradation+0x1170814",
                                        "status": "hit",
                                        "final_pf16_words_at_rdi": [
                                            "0x0cc4",
                                            "0x8000",
                                            "0x0000",
                                            "0x0000",
                                        ],
                                        "console_log": "writer stop retained",
                                    }
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("likely_next_focus") != "single-site-writeback-bound":
            print("[FAIL] writer words should classify as writeback-bound")
            return 1
        compose = comparison.get("windows", {}).get("compose", {}).get("typed_final_words", [])
        if len(compose) != 1 or compose[0].get("words") is None:
            print("[FAIL] single-site writer words were not surfaced")
            return 1
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": THRESHOLD_REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "synthetic threshold-family triplet witness",
                            "observations": {
                                "case": {
                                    "case_id": "olmdistancegradation_extended__case_0023",
                                    "params": {
                                        "in_out": 3,
                                        "inside_threshold": 36,
                                        "outside_threshold": 0,
                                        "interpolation_mode": 1,
                                        "render_mode": 1,
                                        "use_background_color": 1,
                                    },
                                },
                                "threshold_triplet": [
                                    {"role": "below_threshold_same_row", "x": 414, "y": 393},
                                    {"role": "first_above_threshold_same_row", "x": 415, "y": 393},
                                    {"role": "deeper_plateau_same_row", "x": 416, "y": 393},
                                ],
                                "requested_for_each_pixel": {
                                    "raw_inside_distance_before_threshold": [
                                        {"x": 414, "y": 393, "value": 35.0142822},
                                        {"x": 415, "y": 393, "value": 36.0138855},
                                        {"x": 416, "y": 393, "value": 37.0135117},
                                    ],
                                    "raw_outside_distance_before_threshold": [
                                        {"x": 414, "y": 393, "value": 0.0},
                                        {"x": 415, "y": 393, "value": 0.0},
                                        {"x": 416, "y": 393, "value": 0.0},
                                    ],
                                    "helper_stage_field_value_before_compose": [
                                        {"x": 414, "y": 393, "value": 0.0},
                                        {"x": 415, "y": 393, "value": 1.0},
                                        {"x": 416, "y": 393, "value": 1.0},
                                    ],
                                    "threshold_equality_or_plateau_decision": "ownership flips between 35.014 and 36.013 at helper stage",
                                    "constant_binary_fork_order": "binary fork observes field after ownership decision",
                                    "field_value_finally_consumed_by_FUN_181170480": [
                                        {"x": 414, "y": 393, "value": 0.0},
                                        {"x": 415, "y": 393, "value": 1.0},
                                        {"x": 416, "y": 393, "value": 1.0},
                                    ],
                                    "fun_181170480_output_rgba_before_word_store": [
                                        {"x": 414, "y": 393, "rgba": [7195.0, 0.0, 61165.0, 65535.0]},
                                        {"x": 415, "y": 393, "rgba": [65535.0, 0.0, 0.0, 65535.0]},
                                        {"x": 416, "y": 393, "rgba": [65535.0, 0.0, 0.0, 65535.0]},
                                    ],
                                    "final_rgba16": [
                                        {"x": 414, "y": 393, "rgba": [7195, 0, 61165, 65535]},
                                        {"x": 415, "y": 393, "rgba": [65535, 0, 0, 65535]},
                                        {"x": 416, "y": 393, "rgba": [65535, 0, 0, 65535]},
                                    ],
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("request_id") != THRESHOLD_REQUEST_ID:
            print("[FAIL] threshold-family comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "case0023-threshold-family-provenance-split":
            print("[FAIL] threshold-family witness should classify as provenance split")
            return 1
        if "local_case0023_threshold_context" not in comparison:
            print("[FAIL] threshold-family comparison should include local case_0023 context")
            return 1
        if "local_case0023_lane_state" not in comparison:
            print("[FAIL] threshold-family comparison should include local case_0023 lane state")
            return 1
        if "local_case0023_aex_cpu_simu_fullframe" not in comparison:
            print("[FAIL] threshold-family comparison should include local AEX CPU simu fullframe evidence")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        for needle in (
            "Local case_0023 Context",
            "Local case_0023 Lane State",
            "Local case_0023 AEX CPU Simu",
            "Threshold triplet",
            "Live Mac triplet",
        ):
            if needle not in markdown:
                print(f"[FAIL] threshold-family Markdown missing: {needle}")
                return 1
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": TRIPLET_XY_REQUEST_ID,
                            "status": "failed_partial",
                            "summary": "synthetic triplet xy compose followup with endpoint flip confirmed but case-local compose hook still missing",
                            "observations": {
                                "case": {
                                    "case_id": "olmdistancegradation_extended__case_0023",
                                    "params": {
                                        "in_out": 3,
                                        "inside_threshold": 36,
                                        "outside_threshold": 0,
                                        "interpolation_mode": 1,
                                        "render_mode": 1,
                                        "use_background_color": 1,
                                    },
                                },
                                "requested_for_each_pixel": {
                                    "threshold_values": {"inside_threshold": 36, "outside_threshold": 0},
                                    "comparison_rule": "endpoint-observed only; direct helper ownership not isolated",
                                    "selected_side_for_both_mode": "blue_low_endpoint_observed",
                                    "field_value_finally_consumed_by_FUN_181170480": None,
                                    "fun_181170480_output_rgba_before_word_store": [None, None, None, None],
                                    "final_rgba16": [7195, 0, 61165, 65535],
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("request_id") != TRIPLET_XY_REQUEST_ID:
            print("[FAIL] triplet-xy comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "case0023-edge-family-output-binding":
            print("[FAIL] triplet-xy followup should stay on edge-family output binding")
            return 1
        simu = comparison.get("local_case0023_aex_cpu_simu_fullframe")
        if not isinstance(simu, dict) or simu.get("status") != "diagnostic_binary_grounded_field_witness":
            print("[FAIL] triplet-xy followup should include local AEX CPU simu fullframe evidence")
            return 1
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": FINAL_SOURCE_OWNERSHIP_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic final/source ownership witness",
                            "observations": {
                                "case": {
                                    "case_id": "olmdistancegradation_extended__case_0023",
                                    "representative_pixels": [
                                        {"x": 1699, "y": 7, "role": "mismatch_representative"},
                                        {"x": 415, "y": 393, "role": "mismatch_representative"},
                                    ],
                                },
                                "answer_classification": {
                                    "1699,7": "export-path-split: final stored words match Mac model but exported PNG differs",
                                    "415,393": "final-compose/writeback: consumed field differs at pre-store",
                                },
                                "requested_for_each_pixel": {
                                    "source_input_rgba16": [
                                        {"x": 1698, "y": 7, "rgba": [0, 0, 0, 65535]},
                                        {"x": 1699, "y": 7, "rgba": [0, 0, 0, 65535]},
                                        {"x": 1700, "y": 7, "rgba": [0, 0, 0, 65535]},
                                        {"x": 414, "y": 393, "rgba": [0, 0, 0, 65535]},
                                        {"x": 415, "y": 393, "rgba": [0, 0, 0, 65535]},
                                        {"x": 415, "y": 394, "rgba": [0, 0, 0, 65535]},
                                        {"x": 416, "y": 393, "rgba": [0, 0, 0, 65535]},
                                    ],
                                    "source_alpha_or_mask_used_for_ownership": [
                                        {"x": 1699, "y": 7, "mask": 1},
                                        {"x": 415, "y": 393, "mask": 1},
                                    ],
                                    "field_value_consumed_by_final_compose_or_store": [
                                        {"x": 1699, "y": 7, "value": 1.0},
                                        {"x": 415, "y": 393, "value": 1.0},
                                    ],
                                    "fun_181170480_or_final_writeback_output_rgba_before_word_store": [
                                        {"x": 1699, "y": 7, "rgba": [65535, 0, 0, 65535]},
                                        {"x": 415, "y": 393, "rgba": [65535, 0, 0, 65535]},
                                    ],
                                    "final_stored_rgba16": [
                                        {"x": 1699, "y": 7, "rgba": [65535, 0, 0, 65535]},
                                        {"x": 415, "y": 393, "rgba": [65535, 0, 0, 65535]},
                                    ],
                                    "exported_rgba16": [
                                        {"x": 1699, "y": 7, "rgba": [65535, 0, 0, 65535]},
                                        {"x": 415, "y": 393, "rgba": [65535, 0, 0, 65535]},
                                    ],
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("request_id") != FINAL_SOURCE_OWNERSHIP_REQUEST_ID:
            print("[FAIL] final/source ownership comparison request_id mismatch")
            return 1
        final_source = comparison.get("windows", {}).get("final_source_ownership")
        if not isinstance(final_source, dict):
            print("[FAIL] final/source ownership summary missing")
            return 1
        classes = final_source.get("classes", [])
        if "final-compose/writeback" not in classes or "export-path-split" not in classes:
            print("[FAIL] final/source ownership classes missing expected split")
            return 1
        if final_source.get("acceptance_read") != "answered_candidate":
            print("[FAIL] final/source ownership answered candidate not recognized")
            return 1
        coverage = final_source.get("pixel_coverage", {})
        if coverage.get("all_expected_pixels_present") is not True:
            print("[FAIL] final/source ownership expected pixel coverage incomplete")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        if "Final/source ownership" not in markdown:
            print("[FAIL] final/source ownership Markdown missing")
            return 1
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": FINAL_SOURCE_OWNERSHIP_REQUEST_ID,
                            "status": "answered",
                            "summary": "older case_0023 result that must not win over case_0014",
                            "observations": {},
                        },
                        {
                            "request_id": CASE0014_LAYER_SOURCE_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic case_0014 Layer-source typed witness",
                            "observations": {
                                "case_id": "olmdistancegradation_extended__case_0014",
                                "witness_pixels": [
                                    {"x": 1652, "y": 2, "role": "primary"},
                                    {"x": 461, "y": 6, "role": "secondary"},
                                ],
                                "requested_for_each_pixel": {
                                    "consumed_source_layer_rgba16": [
                                        {"x": 1652, "y": 2, "rgba": [44025, 44025, 44025, 43843]},
                                    ],
                                    "source_rgb_before_unpremultiply": [
                                        {"x": 1652, "y": 2, "rgb": [19713, 19713, 19713]},
                                    ],
                                    "source_rgb_after_unpremultiply": [
                                        {"x": 1652, "y": 2, "rgb": [29399, 29399, 29399]},
                                    ],
                                    "source_alpha_used_for_ownership_or_mask": [
                                        {"x": 1652, "y": 2, "alpha": 43843},
                                    ],
                                    "field_channels_presented_to_compose": [
                                        {"x": 1652, "y": 2, "rgba": [0, 0, 0, 43843]},
                                    ],
                                    "X": [{"x": 1652, "y": 2, "value": 0.4486}],
                                    "d_alpha": [{"x": 1652, "y": 2, "value": 0.6690}],
                                    "out_a": [{"x": 1652, "y": 2, "value": 0.6690}],
                                    "output_rgba_float_immediately_before_cvttss2si": [
                                        {"x": 1652, "y": 2, "rgba": [29399.0, 29399.0, 29399.0, 43843.0]},
                                    ],
                                    "final_stored_rgba16": [
                                        {"x": 1652, "y": 2, "rgba": [29399, 29399, 29399, 43843]},
                                    ],
                                    "exported_rgba16": [
                                        {"x": 1652, "y": 2, "rgba": [29399, 29399, 29399, 43843]},
                                    ],
                                },
                            },
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
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
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("request_id") != CASE0014_LAYER_SOURCE_REQUEST_ID:
            print("[FAIL] case_0014 Layer-source comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "layer-source-case0014-source-rgb-prestore-proof":
            print("[FAIL] case_0014 Layer-source focus mismatch")
            return 1
        values = comparison.get("windows", {}).get("requested_values", {})
        if not values.get("final_stored_rgba16"):
            print("[FAIL] case_0014 Layer-source final stored values missing")
            return 1
    print("[OK] DistanceGradation trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
