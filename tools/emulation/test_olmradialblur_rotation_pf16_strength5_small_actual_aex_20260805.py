#!/usr/bin/env python3
"""PF16 Rotation Outer Strength 5 natural actual-AEX/production fixture."""

import json
import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as fixture

fixture.FIXTURE_OUTER_STRENGTH = 5
fixture.FIXTURE_OUTER_OFFSET_MODE = 1
fixture.FIXTURE_OUTER_OFFSET = 0
fixture.FIXTURE = fixture.ROOT / "refs/fixtures/olmradialblur_rotation_pf16_strength5_small_20260805"
fixture.REPORT = fixture.ROOT / "refs/conformance/olmradialblur_rotation_pf16_strength5_small_actual_aex_20260805.json"
fixture.EXPECTED = {
    "source_pf16": ("d059727f9096038fea75037a9ba49b82f99c9dd84fd74b15fb11b09f72ca6f85", "5a57d8c8f898bfc576ba38654a81eccf47635c5c30314d59c7c86e8a8ab29f55"),
    "polar": ("aa822e3d1353b5eeff97581c7bf20bf4c73e8def305a9f2e4cb00f140aaa9ce3", "5a083bd125c501c5d2b3aba8b02f7c7d366917e9bfaf289a92ca91bb6a9e2690"),
    "source_scalar": ("7b4468c91d59a9b63747818dfcd672e87646e3c9b05bc3d7ce8d4efc160826bc", "21d9bf07a607e761267078f796e5c6462d90df31d4e2d66f900655de740a75a4"),
    "accum": ("1f2b04046a3ae0c60407af8a928d74e27a17bdf0c73c6e8473154beb97d91ae7", "d6752684d3c1f78f2624e57d3bf35087187f53928cc314d9eb797e383e90dade"),
    "max_alpha": ("4b63bcde7212e5bf5854c9dbd67b29ac20e8e47f3256ddf05870723b0c495acc", "b82e5eab50766b23897b967342757a0ec474abf6a47c5e2b79df369aa60fbe0e"),
    "coordinates": ("e9c455c90aa39569783043925d1b890ae7cd67728a09a729b665d8b67976d07b", "aaccf447e96339787ca82d3003a056cae7c03cab57f626370fb06ce1d60d1937"),
    "final_rgba": ("7c3f8b5a19e9e8559539f779050d0ed6f900024ede6683cf44ab190eb814ce12", "5bf0d427ee6369dbcd0dfe9ffd2f0a6005f000e62336c5329d69fb7e8e2b2a9e"),
    "output": ("eef9dc55ee40ef0c5b1428af5c7b7fcc76cb12049f0aa966e63d519a716b0632", "147cd4f26bf5c92507832ac641e984243a726653e6da6689803a164be0600aff"),
}


def main():
    code = fixture.main()
    report = json.loads(fixture.REPORT.read_text())
    report["kind"] = "olmradialblur_rotation_pf16_strength5_small_actual_aex_20260805"
    report["scope"] = (
        "independent PF16 Rotation Outer Strength 5, mode 1/offset 0, padded 9x7; "
        "distinct from Strength 4 baseline and PF32 Strength 5; no other depth or AE-host claim"
    )
    report["parameter_branch"] = {
        "outer_strength": 5,
        "baseline_outer_strength": 4,
        "outer_offset_mode": 1,
        "outer_offset": 0,
        "effective_span": 5,
        "actual_accum_differs_from_pf16_strength4": True,
        "actual_output_differs_from_pf16_strength4": True,
    }
    report["typed_pf16_contract"] = {
        "source": "PF_Pixel16 ARGB words normalized independently by float32 multiply with 1/32768",
        "writer": "FUN_180017440: float32 multiply by 32768, CVTTSS2SI, low u16 ARGB stores",
        "pf8_or_pf32_quantization_reused": False,
        "rowbytes": 80,
        "visible_bytes": 72,
        "padding_bytes": 8,
    }
    fixture.REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
