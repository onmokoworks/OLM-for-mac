#!/usr/bin/env python3
"""Validate the actual-AEX forward-warp contract evidence."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=Path("refs/conformance/olmkirakira_mode3_forward_warp_contract_actual_aex_20260713.json"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    path = args.json if args.json.is_absolute() else root / args.json
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["schema"] == "olmkirakira-mode3-forward-warp-contract-actual-aex/1"
    assert report["status"] == "captured_forward_warp_contract"
    calls = report["forward_warp_contract"]["calls"]
    assert len(calls) == 1
    first = calls[0]
    assert first["rip"] == "0x181297ac0"
    assert first["dsize"] == {"height": 7, "packed": "0x700000009", "source": "R9", "width": 9}
    assert first["optional_stack_args"]["interpolation_flags"] == 1
    assert first["optional_stack_args"]["border_mode"] == 0
    assert first["optional_stack_args"]["border_value_pointer"] != "0x0"
    assert first["src"]["object"] == first["dst"]["object"]
    assert first["src"]["mat"]["data"] == first["dst"]["mat"]["data"]
    assert first["transform"]["mat"]["depth_code"] == 6
    assert first["transform"]["decoded_by_mat_depth"] == [0.9961946980917455, 0.08715574274765817, -0.28792124102965855, -0.08715574274765817, 0.9961946980917455, 0.4055193990433523]
    assert first["src"]["mat"]["values_f32"]
    assert first["dst"]["mat"]["values_f32"]
    assert report["ray_population_capture"]["roi_after_copy"][0]["temp_a"]["values_f32"] != report["ray_population_capture"]["warp_after"][0]["temp_a"]["values_f32"]
    assert any(value != 0.0 for row in report["ray_population_capture"]["warp_after"][0]["temp_a"]["values_f32"] for value in row)
    sidecar = report["forward_warp_sidecar"]
    assert sidecar["status"] == "ok"
    assert sidecar["cv2"] == "4.5.5"
    assert sidecar["exact_words"] == sidecar["total_words"] == 63
    assert sidecar["max_abs"] == 0.0
    print("[OK] OLMKiraKira Mode 3 forward-warp contract smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
