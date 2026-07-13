#!/usr/bin/env python3
"""Smoke the owned Gaussian dispatch audit evidence."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_dispatch_actual_aex_20260713.json"


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    evidence = report["evidence"]
    assert report["status"] == "captured"
    assert evidence["entry_hit_count"] == 1
    assert evidence["return_hit_count"] == 1
    assert evidence["output_word_count"] == 63
    before = evidence["dispatch_table_before"]
    after = evidence["dispatch_table_after"]
    assert before["table_nonzero_qwords_0x10000"] > 0
    assert after["table_nonzero_qwords_0x10000"] == before["table_nonzero_qwords_0x10000"]
    assert before["table_first_16_qwords"] == after["table_first_16_qwords"]
    assert len(evidence["indirect_call_static"]) == 31
    assert evidence["indirect_call_runtime"] == []
    assert any(item["target"] == "0x181266730" for item in evidence["direct_call_runtime"])
    taps = [item for item in evidence["allocation_raw"] if item["uniform_21f_runs"]]
    assert len(taps) == 1
    assert taps[0]["pointer"] == "0x400104c0"
    assert taps[0]["size"] == 84
    assert math.isclose(taps[0]["uniform_21f_runs"][0]["value"], 1.0 / 21.0, rel_tol=1e-7)
    sigma = evidence["sigma_propagation"]
    setup = next(item for item in sigma if item["point"] == "FUN_181266730_entry")
    coeff = [item for item in sigma if item["point"] == "FUN_1812754a0_entry"]
    consumers = [item for item in sigma if item["point"] == "FUN_181274e10_entry"]
    assert math.isclose(setup["stack_plus_28_sigma_x_f64"], 2.5, rel_tol=1e-12)
    assert setup["stack_plus_30_sigma_y_f64"] == 0.0
    assert setup["r9_ksize_words_u32"][:2] == ["0x00000000", "0x00000001"]
    assert setup["r8_type_raw_u32"] == 5
    assert [item["ecx_kernel_size_raw_u32"] for item in coeff[:2]] == [21, 1]
    assert all(math.isclose(item["xmm1_sigma_f64"], 2.5, rel_tol=1e-12) for item in coeff)
    assert all(math.isclose(item["xmm2_sigma_f64"], 2.5, rel_tol=1e-12) for item in consumers)
    assert evidence["windows_live_minimum_targets"][1]["address"] == "0x181266730"
    print("PASS: Gaussian dispatch evidence shows AEX-populated backing before entry and stable at return")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
