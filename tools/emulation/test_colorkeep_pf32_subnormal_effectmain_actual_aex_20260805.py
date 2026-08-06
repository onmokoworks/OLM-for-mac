#!/usr/bin/env python3
"""PF32 subnormal source/key raw-copy proof through production EffectMain."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_MXCSR

import test_colorkeep_effectmain_padded_frame_20260805 as adapter
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle
from aex_loader import AexLoader

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
ENTRY = 0x180001850
REPORT = ROOT / "refs/conformance/colorkeep_pf32_subnormal_effectmain_actual_aex_20260805.json"
ACTUAL_RAW = ROOT / "refs/conformance/colorkeep_pf32_subnormal_actual_aex_20260805.argb32f"
PRODUCTION_RAW = ROOT / "refs/conformance/colorkeep_pf32_subnormal_mac_production_20260805.argb32f"


def f32(word: int) -> float:
    return struct.unpack("<f", struct.pack("<I", word))[0]


def words(values: tuple[float, float, float, float]) -> list[str]:
    return [f"0x{word:08x}" for word in struct.unpack("<4I", struct.pack("<4f", *values))]


P_MIN = f32(0x00000001)
N_MIN = f32(0x80000001)
P_MAX = f32(0x007FFFFF)
N_MAX = f32(0x807FFFFF)

# Alpha is deliberately distinct per key and matched by each positive fixture.
# ColorKeep compares ARGB and clears only output alpha for a no-match.
COLORS = (
    (0.11, 0.0, 0.25, 0.50),
    (0.22, P_MIN, 0.35, 0.60),
    (0.33, N_MIN, 0.45, 0.70),
    (0.44, 0.80, P_MAX, 0.20),
    (0.55, 0.90, N_MAX, 0.30),
)

PIXELS = (
    (0.11, P_MIN, 0.25, 0.50),       # source-side +min vs zero key
    (0.11, N_MIN, 0.25, 0.50),       # source-side -min vs zero key
    (0.22, 0.0, 0.35, 0.60),         # key-side +min vs zero source
    (0.33, -0.0, 0.45, 0.70),        # key-side -min vs -zero source
    (0.44, 0.80, P_MAX, 0.20),       # exact +max-subnormal source/key
    (0.55, 0.90, N_MAX, 0.30),       # exact -max-subnormal source/key
    (0.11, P_MIN, 0.99, 0.50),       # source subnormal, independent RGB no-match
    (0.22, 0.99, P_MIN, 0.60),       # key subnormal exists, independent RGB no-match
)

MATCH = (True, True, True, True, True, True, False, False)
CASE_NAMES = (
    "source_positive_min_subnormal_vs_zero_key",
    "source_negative_min_subnormal_vs_zero_key",
    "key_positive_min_subnormal_vs_zero_source",
    "key_negative_min_subnormal_vs_negative_zero_source",
    "source_key_positive_max_subnormal_exact",
    "source_key_negative_max_subnormal_exact",
    "source_positive_subnormal_independent_no_match",
    "key_positive_subnormal_independent_no_match",
)


def direct(source: tuple[float, float, float, float], color: tuple[float, float, float, float]) -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    refcon = loader.host_alloc(0x38)
    src = loader.host_alloc(16)
    dst = loader.host_alloc(16)
    loader.write_bytes(refcon + 0x24, struct.pack("<i", 1))
    loader.write_bytes(refcon + 0x28, struct.pack("<4f", *color))
    loader.write_bytes(src, struct.pack("<4f", *source))
    loader.write_bytes(dst, b"\xa5" * 16)
    before = loader.uc.reg_read(UC_X86_REG_MXCSR)
    result = loader.call_function(ENTRY, int_args=[refcon, 0, 0, src, dst], max_instructions=10_000)
    after = loader.uc.reg_read(UC_X86_REG_MXCSR)
    return {
        "source_bits": words(source),
        "key_bits": words(color),
        "output_bits": [f"0x{word:08x}" for word in struct.unpack("<4I", loader.read_bytes(dst, 16))],
        "mxcsr_before": f"0x{before:08x}",
        "mxcsr_after": f"0x{after:08x}",
        "instructions": result["instructions"],
    }


def main() -> int:
    oracle.COLORS = COLORS
    oracle.DEPTHS = {"PF32": (ENTRY, "<4f", PIXELS)}
    rows = []
    for y in range(3):
        row = b"".join(struct.pack("<4f", *PIXELS[(y * 4 + x) % len(PIXELS)]) for x in range(4))
        rows.append(row + b"\xcc" * 8)
    raw = b"".join(rows)
    expected = oracle.actual_frame(ENTRY, "<4f", PIXELS)
    observed = adapter.compile_and_run({"PF8": b"\xcc" * 72, "PF16": b"\xcc" * 120, "PF32": raw}, pf32_only=True)
    assert observed == expected

    witnesses = []
    rowbytes = 72
    for index in range(12):
        y, x = divmod(index, 4)
        case = index % len(PIXELS)
        source_raw = struct.pack("<4f", *PIXELS[case])
        output_raw = expected[y * rowbytes + x * 16:y * rowbytes + (x + 1) * 16]
        assert output_raw[4:] == source_raw[4:]
        assert output_raw[:4] == (source_raw[:4] if MATCH[case] else b"\0" * 4)
        if index < len(PIXELS):
            witnesses.append({
                "case": CASE_NAMES[case],
                "source_bits": words(PIXELS[case]),
                "output_bits": [f"0x{word:08x}" for word in struct.unpack("<4I", output_raw)],
                "expected_match": MATCH[case],
                "observed_alpha_bits": f"0x{struct.unpack_from('<I', output_raw)[0]:08x}",
            })
    for y in range(3):
        assert expected[y * rowbytes + 64:(y + 1) * rowbytes] == b"\xee" * 8

    direct_witnesses = {
        "source_positive_min": direct(PIXELS[0], COLORS[0]),
        "source_negative_min": direct(PIXELS[1], COLORS[0]),
        "key_positive_min": direct(PIXELS[2], COLORS[1]),
        "key_negative_min": direct(PIXELS[3], COLORS[2]),
        "positive_max_exact": direct(PIXELS[4], COLORS[3]),
        "negative_max_exact": direct(PIXELS[5], COLORS[4]),
    }

    ACTUAL_RAW.write_bytes(expected)
    PRODUCTION_RAW.write_bytes(observed)
    digest = hashlib.sha256(expected).hexdigest()
    report = {
        "status": "exact_raw_output",
        "actual_aex_sha256": oracle.AEX_SHA256,
        "production_source": "mac/ColorKeep/ColorKeep.cpp",
        "depth": "PF32 only",
        "dynamic_path": "EffectMain(SmartPreRender)->EffectMain(SmartRender)->PF32 iterate",
        "subnormal_bits": {
            "positive_min": "0x00000001",
            "negative_min": "0x80000001",
            "positive_max": "0x007fffff",
            "negative_max": "0x807fffff",
        },
        "comparison_result": "All source/key zero-versus-subnormal cases match because the fixed 0.0001 tolerance is much larger than every binary32 subnormal. Independent RGB mismatches still clear alpha.",
        "raw_copy_result": "Matching output preserves the source subnormal sign and payload bits verbatim in RGB; no-match output preserves source RGB verbatim and clears only alpha.",
        "direct_actual_worker_witnesses": direct_witnesses,
        "effectmain_witnesses": witnesses,
        "smart_dependencies": {"checkout_count": 101, "ordered_indices": list(range(1, 102))},
        "fixture": "4x3 PF32, rowbytes72, 8-byte input/output padding",
        "padding": "all 8 output padding bytes per row remain 0xee",
        "actual_raw_payload": str(ACTUAL_RAW.relative_to(ROOT)),
        "production_raw_payload": str(PRODUCTION_RAW.relative_to(ROOT)),
        "raw_payload_bytes": len(expected),
        "raw_output_sha256": digest,
        "production_raw_sha256": hashlib.sha256(observed).hexdigest(),
        "fp_environment_boundary": {
            "unicorn_mxcsr_observation": "MXCSR read as 0x00000000 before and after the bounded actual-AEX worker calls.",
            "mxcsr_interpretation": "This is a Unicorn register observation, not native Windows evidence of FTZ/DAZ state or exception flags.",
            "native_windows": "MXCSR FTZ, DAZ, exception flags, and trap masks are not proven.",
            "macos_arm": "FPCR/FPSR state during the production EffectMain process is not captured or proven.",
            "ftz_discrimination": "This fixture cannot distinguish gradual underflow from FTZ/DAZ comparison behavior because zero and every subnormal are inside ColorKeep's fixed tolerance. Raw source copying remains bit-exact regardless of the temporary subtraction result.",
        },
        "not_proven": [
            "native Windows MXCSR FTZ/DAZ and exception behavior",
            "macOS arm64 FPCR/FPSR state or exception behavior",
            "After Effects host execution/export",
            "PF8/PF16 generalization",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
