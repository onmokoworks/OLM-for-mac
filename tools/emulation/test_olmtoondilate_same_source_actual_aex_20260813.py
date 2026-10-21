#!/usr/bin/env python3
"""Read-only regression gate for the corrected ToonDilate actual-AEX replay."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/probe_olmtoondilate_same_source_actual_aex_20260813.py"
EXPECTED_OUTPUT = {
    "PF8_copy": "28fcdd1bae528a5ca9b3d0ed04599003b0c244d62c2a49c7c7600cbdd3a0d87e",
    "PF8_fractional": "9e22bace19f7dae26258e99573917c68b7327e6d1ccaf141940be94e2d70e27d",
    "PF8_tie_semialpha": "05dd195813a594c4185a488a0433eaca16b8668cd6588f48fb77ca7c0050eb0c",
    "PF8_high_downsample": "5aeed3ca62bc73ecc24a4fa05fc3db2b9b5ac258de2ce90c98724ea055d4707a",
    "PF16_copy": "29728fe4ef8dbec47f7fd68da5a9a582b59066038b27add5ebe87071c8f09b54",
    "PF16_fractional": "b57f15217528ebbe5b1b61415688f3d046c417d39c361a6a07dfda9c24faac59",
    "PF16_tie_semialpha": "d52a4cadf64b8177fba642b054fad4fef99e5f769124989f5844d31fde1bccb7",
    "PF16_high_downsample": "ab2480b2e58e3c575b9cacdbe2d483174898d5eab6024a7d170ceadabcf9d036",
    "PF32_copy": "d4bf63076bba553b519d80af8678f0bae141ab2512d2f5ef3139904ef6623807",
    "PF32_fractional": "b9767fdbd1733f8281566ca003c19514e1b60072e054cda53923f5b85b0c430e",
    "PF32_tie_semialpha": "87de042025825f99d43cd8b7b3441cea78dbc0afcd5410786d7952f2bfc013e6",
    "PF32_high_downsample": "162e0f47588045812bdfad5f4a13347d02486fb3c4d6e5ebf4bbff4b97d2755d",
}
EXPECTED_INPUT = {
    "PF8_copy": "28fcdd1bae528a5ca9b3d0ed04599003b0c244d62c2a49c7c7600cbdd3a0d87e",
    "PF8_fractional": "b0bb2f13a7b1df3715f3166e8c170801f3e547e6261e9af40ceb309b0b74f593",
    "PF8_tie_semialpha": "3e82a3170b01e243044550f4ec7c73823901e3d9decb21441fe9850d517545ef",
    "PF8_high_downsample": "10a8f71efc874ad922ad1784eab5f0eec57a623eeca2742e54ef2de55148c902",
    "PF16_copy": "29728fe4ef8dbec47f7fd68da5a9a582b59066038b27add5ebe87071c8f09b54",
    "PF16_fractional": "3bcb46077510265bd25eec45104f439f587bd03495df5edce01c61cecba21037",
    "PF16_tie_semialpha": "31af1cb49d73db7b803b95a653d51bf583a00fae9ff78cd98847e35d14bb7cbe",
    "PF16_high_downsample": "79653684e48ad270e5ba921be40d938cc15f1017402da54536fd35ff8f3bf002",
    "PF32_copy": "d4bf63076bba553b519d80af8678f0bae141ab2512d2f5ef3139904ef6623807",
    "PF32_fractional": "fef7add0856a28eab2b61dbf3427ab5f799caa6188d65b27d825398ca45d3b96",
    "PF32_tie_semialpha": "1c2b046b5ea08eb1aa3ed19b940c3e162ecbfbe5d562ce51b95e3eaa6fe0c0d7",
    "PF32_high_downsample": "ca82e46d2885daaa63de2920207b385573dcc2ede60ec7036bbc5e8bf05c66b0",
}


def main() -> int:
    run = subprocess.run(
        [sys.executable, str(PROBE)], cwd=ROOT, check=True, capture_output=True, text=True
    )
    report = json.loads(run.stdout)
    assert len(report["cases"]) == 12
    assert len({case["id"] for case in report["cases"]}) == 12
    actual = {case["id"]: case["output_active_sha256"] for case in report["cases"]}
    inputs = {case["id"]: case["input_active_sha256"] for case in report["cases"]}
    assert report["schema"] == "olmtoondilate.same-source-actual-aex/3"
    assert report["status"] == "PASS_SAME_SOURCE_ACTUAL_AEX_12"
    assert report["matrix"]["case_count"] == 12
    assert all(report["gates"].values())
    assert actual == EXPECTED_OUTPUT
    assert inputs == EXPECTED_INPUT
    assert not any(case["preserve_rgb_requested"] for case in report["cases"])
    assert all(case["input_storage_unchanged"] for case in report["cases"])
    assert all(case["input_row0_data_aligned"] and case["output_row0_data_aligned"] for case in report["cases"])
    assert all(case["downsample_y"] == [0, 0] for case in report["cases"])
    assert all(case["world_flags"] == [0, 0] for case in report["cases"])
    assert all(case["input_origin"] == [0, 0] and case["output_origin"] == [0, 0] for case in report["cases"])
    assert all(case["radius_materialized_f32_le"] for case in report["cases"])
    assert report["sdk_abi"]["PF_EffectWorld"]["sizeof"] == 0x78
    assert report["sdk_abi"]["PF_CheckoutResult"]["ref_width"] == 0x2C
    assert report["sdk_abi"]["PF_RenderRequest"]["preserve_rgb_of_zero_alpha"] == 0x18
    print("PASS: corrected actual-AEX same-source matrix is exact for all 12 cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
