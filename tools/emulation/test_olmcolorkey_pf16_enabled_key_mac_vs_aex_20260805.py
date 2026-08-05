#!/usr/bin/env python3
"""Compare the bounded PF16 enabled-black-key contract across AEX and Mac source."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AEX_REPORT = ROOT / "refs/conformance/olmcolorkey_pf16_full_worker_actual_aex_20260805.json"
MAC_FIXTURE = ROOT / "tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py"


def argb16_from_hex(value: str) -> list[int]:
    raw = bytes.fromhex(value)
    assert len(raw) == 8
    return [int.from_bytes(raw[index:index + 2], "little") for index in range(0, 8, 2)]


def main() -> int:
    aex = json.loads(AEX_REPORT.read_text(encoding="utf-8"))
    aex_case = next(case for case in aex["cases"] if case["case"] == "enabled_black_key_edge_blur_1_single")
    proc = subprocess.run(
        ["python3", str(MAC_FIXTURE)], cwd=ROOT, text=True, capture_output=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    mac = json.loads(proc.stdout)
    mac_case = next(case for case in mac["cases"] if case["case"] == "enabled_black_key_edge_blur_1_pf16")
    numerical = mac_case["numerical_contract"]

    aex_input = argb16_from_hex(aex_case["captures"]["input_first_pixel_hex"])
    aex_output = argb16_from_hex(aex_case["captures"]["worker_first_pixel_hex"])
    assert aex_input == numerical["input_first_argb16"] == [32768, 0, 0, 0]
    assert aex_output == numerical["output_first_argb16"] == [16384, 0, 0, 0]
    assert numerical["changed_pixel_count"] == 1
    assert numerical["other_active_pixels"] == "byte_exact_input"
    assert aex_case["acceptance_gates"]["enabled_key_changes_first_pixel_only"] is True
    assert aex_case["acceptance_gates"]["output_padding_preserved"] is True
    assert mac_case["input_padding_preserved"] is True
    assert mac_case["output_padding_preserved"] is True
    assert aex_case["parameter_record"]["enabled_black_key_count"] == 1
    assert "parameter materialization" in aex_case["claim_boundary"]
    assert "No AE-host or general case0001 exact claim" in aex_case["claim_boundary"]
    print("PASS: bounded PF16 enabled black key matches actual-AEX and Mac production source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
