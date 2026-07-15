#!/usr/bin/env python3
"""Regression gates for the DG field-generation boundary classification."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/analyze_distancegradation_fieldgen_bitdepth_boundary_20260715.py"
spec = importlib.util.spec_from_file_location("dg_boundary", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> int:
    report = module.build_report()
    fact = report["FACT"]
    assert fact["mac_shared_fieldgen"]["calls_distance_to_normalized_u8"] == 1
    assert fact["mac_shared_fieldgen"]["fieldgen_body_contains_pixel_size_branch"] is False
    assert fact["mac_shared_fieldgen"]["threshold_scales_by_ds"] is True
    assert fact["windows_binary_fieldgen"]["pipeline_tokens_present"] == [True, True, True, True]
    assert fact["windows_binary_fieldgen"]["explicit_pixel_depth_token_in_function_body"] is False
    assert fact["eight_bpc_typed_request"]["status"] == "exact_bind_failure"
    assert fact["sixteen_bpc_typed_request"]["status"] == "exact_bind_failure"
    assert fact["sixteen_bpc_livefield"]["raw_field_words_present"] == 0
    assert fact["thirty_two_bpc_evidence"]["rendered_reference_artifacts"] > 0
    assert fact["thirty_two_bpc_evidence"]["typed_field_callback_artifacts"] == 0
    print("RESULT: DG field-generation bit-depth boundary gates PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
