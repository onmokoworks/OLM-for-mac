#!/usr/bin/env python3
"""Validate the bounded Mode 3 ray-population witness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=Path("refs/conformance/olmkirakira_mode3_ray_population_actual_aex_20260713.json"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    path = args.json if args.json.is_absolute() else root / args.json
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["schema"] == "olmkirakira-mode3-ray-population-actual-aex/1"
    assert report["status"] == "captured_nonzero_pre_gaussian"
    contract = report["producer_contract"]
    assert contract["function"] == "FUN_181150790"
    assert contract["roi_after_copy"] == "0x181150898"
    assert contract["forward_warp_after"] == "0x181150946"
    assert contract["gaussian_target"] == "0x181272ec0"
    roi = report["ray_population_capture"]["roi_after_copy"]
    warp = report["ray_population_capture"]["warp_after"]
    assert roi and warp
    assert roi[0]["roi_xywh_from_fun_locals"] == [0, 0, 9, 7]
    roi_values = roi[0]["temp_a"]["values_f32"]
    assert any(value != 0.0 for row in roi_values for value in row)
    warp_values = warp[0]["temp_a"]["values_f32"]
    assert any(value != 0.0 for row in warp_values for value in row)
    hit = report["target_capture"]["hits"][0]
    assert hit["size"] == [0, 1]
    assert hit["sigma_x_f64"] == 2.5
    assert hit["input_array"]["mat"]["values_f32"] == warp_values
    assert report["nonzero_coordinates"]
    assert any(item["stage"] == "roi_after_copy" for item in report["nonzero_coordinates"])
    assert any(item["stage"] == "warp_after" for item in report["nonzero_coordinates"])
    print("[OK] OLMKiraKira Mode 3 actual-AEX ray-population witness passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
