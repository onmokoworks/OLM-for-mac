#!/usr/bin/env python3
"""PF16 nominal-white/extended-range boundary through production EffectMain."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import test_colorkeep_effectmain_padded_frame_20260805 as adapter
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/colorkeep_pf16_extended_range_effectmain_actual_aex_20260805.json"
ACTUAL_RAW = ROOT / "refs/conformance/colorkeep_pf16_extended_range_actual_aex_20260805.argb16"
PRODUCTION_RAW = ROOT / "refs/conformance/colorkeep_pf16_extended_range_mac_production_20260805.argb16"
ENTRY = 0x180001280

COLORS = (
    (1.0, 1.0, 1.0, 1.0),
    (0.0, 0.0, 0.0, 0.0),
    (0.5, 0.25, 0.75, 1.0),
)

# AE's nominal PF16 white is 32768, while the storage type extends to 65535.
# The fixture crosses that boundary in each ARGB channel and also proves that a
# no-match clears alpha without narrowing or clamping the three RGB words.
PIXELS = (
    (32768, 32768, 32768, 32768),
    (32769, 32768, 32768, 32768),
    (32768, 32769, 32768, 32768),
    (32768, 32768, 32769, 32768),
    (32768, 32768, 32768, 32769),
    (65535, 65535, 65535, 65535),
    (0, 65535, 32769, 49152),
    (16384, 8192, 24576, 32768),
)

MATCH = (True, False, False, False, False, False, False, True)
CASE_NAMES = (
    "nominal_white_exact_match",
    "alpha_one_above_nominal_white",
    "red_one_above_nominal_white",
    "green_one_above_nominal_white",
    "blue_one_above_nominal_white",
    "all_channels_uint16_max",
    "zero_alpha_extended_rgb_no_match",
    "fractional_key_exact_match",
)


def build_input() -> bytes:
    rows = []
    for y in range(3):
        row = b"".join(struct.pack("<4H", *PIXELS[(y * 4 + x) % len(PIXELS)]) for x in range(4))
        rows.append(row + b"\xcc" * 8)
    return b"".join(rows)


def main() -> int:
    oracle.COLORS = COLORS
    expected = oracle.actual_frame(ENTRY, "<4H", PIXELS)
    input16 = build_input()
    combined = adapter.compile_and_run({
        "PF8": b"\xcc" * 72,
        "PF16": input16,
        "PF32": b"\xcc" * 216,
    })
    # Adapter output order: legacy PF8, legacy PF16, Smart PF8, Smart PF16, Smart PF32.
    legacy = combined[72:192]
    smart = combined[264:384]
    assert legacy == expected
    assert smart == expected

    rowbytes = 40
    witnesses = []
    for index in range(12):
        y, x = divmod(index, 4)
        case = index % len(PIXELS)
        source_raw = struct.pack("<4H", *PIXELS[case])
        output_raw = expected[y * rowbytes + x * 8:y * rowbytes + (x + 1) * 8]
        output = struct.unpack("<4H", output_raw)
        assert output[1:] == PIXELS[case][1:]
        assert output[0] == (PIXELS[case][0] if MATCH[case] else 0)
        if index < len(PIXELS):
            witnesses.append({
                "case": CASE_NAMES[case],
                "source_argb_u16": list(PIXELS[case]),
                "output_argb_u16": list(output),
                "expected_match": MATCH[case],
            })
    for y in range(3):
        assert expected[y * rowbytes + 32:(y + 1) * rowbytes] == b"\xee" * 8

    ACTUAL_RAW.write_bytes(expected)
    PRODUCTION_RAW.write_bytes(smart)
    digest = hashlib.sha256(expected).hexdigest()
    report = {
        "status": "exact_raw_output",
        "selected_gap": "PF16 storage values above AE nominal white (32768) were not covered by an actual-AEX-to-production EffectMain fixture.",
        "actual_aex_sha256": oracle.AEX_SHA256,
        "actual_worker_entry": f"0x{ENTRY:x}",
        "production_source": "mac/ColorKeep/ColorKeep.cpp",
        "production_public_entrypoints": [
            "EffectMain(PF_Cmd_RENDER)->Render->PF16 iterate",
            "EffectMain(PF_Cmd_SMART_PRE_RENDER)->EffectMain(PF_Cmd_SMART_RENDER)->PF16 iterate",
        ],
        "boundary": {
            "nominal_white": 32768,
            "first_extended_value": 32769,
            "storage_max": 65535,
            "semantics": "PF16 key colors are quantized from float parameters into nominal AE units. Extended source words do not match nominal-white keys; output preserves all RGB uint16 words and clears alpha only.",
        },
        "fixture": "4x3 PF16, rowbytes40, 8-byte input/output padding, three enabled keys",
        "witnesses": witnesses,
        "legacy_matches_actual": True,
        "smart_matches_actual": True,
        "smart_dependencies": {"checkout_count": 101, "ordered_indices": list(range(1, 102))},
        "padding": "all 8 output padding bytes per row remain 0xee",
        "actual_raw_payload": str(ACTUAL_RAW.relative_to(ROOT)),
        "production_raw_payload": str(PRODUCTION_RAW.relative_to(ROOT)),
        "raw_payload_bytes": len(expected),
        "actual_raw_sha256": digest,
        "production_raw_sha256": hashlib.sha256(smart).hexdigest(),
        "remaining_gaps": [
            "After Effects host execution/export and loaded-binary identity",
            "PF16 behavior for malformed parameter floats outside the public color-control range",
            "host-managed worlds with negative rowbytes or non-zero origin",
            "public UI entrypoints USER_CHANGED_PARAM and UPDATE_PARAMS_UI against actual AEX host callbacks",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
