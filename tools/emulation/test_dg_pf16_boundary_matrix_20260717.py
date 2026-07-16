#!/usr/bin/env python3
"""Hash-pinned DG PF16 boundary matrix: actual AEX versus production source.

The matrix varies raw PF16 alpha values around the checked-in raw-threshold
contract, alpha transparency, and PF16 half-step/endpoint values.  It compares
field and compose words, while keeping row padding outside the active rectangle
as a canary.  This is bounded Mac-local AEX/source evidence, not AE exactness.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import probe_dg_pf16_wrapper_entry_20260717 as actual  # noqa: E402
import test_dg_pf16_source_oracle_20260717 as source  # noqa: E402


EXPECTED_AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
RAW_PF16_THRESHOLD = 32768
PAD_BYTE = source.CANARY


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def active(data: bytes) -> bytes:
    return b"".join(data[y * source.ROWBYTES:y * source.ROWBYTES + source.WIDTH * 8]
                    for y in range(source.HEIGHT))


def padding(data: bytes) -> bytes:
    return b"".join(data[y * source.ROWBYTES + source.WIDTH * 8:(y + 1) * source.ROWBYTES]
                    for y in range(source.HEIGHT))


def matrix() -> list[tuple[str, list[int]]]:
    base = [0] * (source.WIDTH * source.HEIGHT)

    def with_values(values: dict[tuple[int, int], int]) -> list[int]:
        result = base.copy()
        for (x, y), value in values.items():
            result[y * source.WIDTH + x] = value
        return result

    return [
        ("raw_threshold_n_minus_1", with_values({(2, 2): RAW_PF16_THRESHOLD - 1})),
        ("raw_threshold_n", with_values({(2, 2): RAW_PF16_THRESHOLD})),
        ("raw_threshold_n_plus_1", with_values({(2, 2): RAW_PF16_THRESHOLD + 1})),
        ("transparent_0_vs_opaque_1", with_values({(2, 2): 1, (3, 2): 0, (2, 3): 32768})),
        ("pf16_half_step_minus_exact_plus", with_values({
            (1, 2): 16383, (2, 2): 16384, (3, 2): 16385,
            (1, 3): 32767, (2, 3): 32768, (3, 3): 32769,
        })),
        ("pf16_endpoint_zero_half_full", with_values({
            (2, 1): 0, (2, 2): 1, (2, 3): 32768,
        })),
    ]


def source_input(alphas: list[int]) -> bytearray:
    data = bytearray([PAD_BYTE] * (source.ROWBYTES * source.HEIGHT))
    for y in range(source.HEIGHT):
        for x in range(source.WIDTH):
            struct.pack_into("<4H", data, y * source.ROWBYTES + x * 8,
                             alphas[y * source.WIDTH + x], 0, 0, 0)
    return data


def run_case(name: str, alphas: list[int], library: ctypes.CDLL) -> dict[str, object]:
    aex = actual.run(degenerate=False, source_alpha_words=alphas)
    if aex.get("status") != "PASS":
        return {"name": name, "status": "blocked", "actual": aex}

    input_bytes = source_input(alphas)
    output_bytes = bytearray([PAD_BYTE] * (source.ROWBYTES * source.HEIGHT))
    input_buffer = (ctypes.c_uint16 * (len(input_bytes) // 2)).from_buffer(input_bytes)
    output_buffer = (ctypes.c_uint16 * (len(output_bytes) // 2)).from_buffer(output_bytes)
    field_x = (ctypes.c_float * (source.WIDTH * source.HEIGHT))()
    d_alpha = (ctypes.c_float * (source.WIDTH * source.HEIGHT))()
    field_words = (ctypes.c_uint16 * (source.WIDTH * source.HEIGHT))()
    field_rc = library.dg_pf16_source_field_20260717(
        input_buffer, source.ROWBYTES, field_x, d_alpha, field_words,
        source.WIDTH * source.HEIGHT)
    render_rc = library.dg_pf16_source_oracle_20260717(
        input_buffer, source.ROWBYTES, output_buffer, source.ROWBYTES,
        source.WIDTH, source.HEIGHT)

    actual_field = [int(row[0]) for row in aex["field_capture"]["raw_words_agrb"]]
    source_field = [int(value) for value in field_words]
    actual_output = b"".join(struct.pack("<4H", int(row[0]), int(row[2]), int(row[1]), int(row[3]))
                               for row in aex["output_active_words_agrb"])
    source_output = active(output_bytes)
    field_equal = actual_field == source_field
    output_equal = actual_output == source_output
    source_padding = padding(output_bytes)
    source_padding_ok = source_padding == bytes([PAD_BYTE]) * (source.PAD * source.HEIGHT)
    actual_padding_ok = bool(aex["padding_canary"]["preserved"])
    passed = (aex["binary_sha256"] == EXPECTED_AEX_SHA256 and field_rc == 0 and
              render_rc == 0 and field_equal and output_equal and actual_padding_ok and
              source_padding_ok and aex["fieldgen_entry_hook_hits"] == 2 and
              aex["compose_entry_hook_hits"] == source.WIDTH * source.HEIGHT)
    return {
        "name": name,
        "status": "PASS" if passed else "blocked",
        "input": {"alpha_words": alphas, "active_sha256": sha256(active(input_bytes))},
        "actual_aex": {
            "sha256": aex["binary_sha256"],
            "fieldgen_hits": aex["fieldgen_entry_hook_hits"],
            "compose_hits": aex["compose_entry_hook_hits"],
            "field_words_agrb": aex["field_capture"]["raw_words_agrb"],
            "compose_words_agrb": aex["output_active_words_agrb"],
            "padding_sha256": aex["padding_canary"]["sha256"],
            "padding_preserved": actual_padding_ok,
        },
        "production_source": {
            "field_return_code": field_rc,
            "render_return_code": render_rc,
            "field_words": source_field,
            "compose_active_sha256": sha256(source_output),
            "padding_sha256": sha256(source_padding),
            "padding_preserved": source_padding_ok,
        },
        "comparison": {
            "field_raw_words_exact": field_equal,
            "field_word_diff_count": sum(a != b for a, b in zip(actual_field, source_field)),
            "compose_raw_bytes_exact": output_equal,
            "compose_byte_diff_count": sum(a != b for a, b in zip(actual_output, source_output)),
        },
    }


def run() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="dg_pf16_boundary_matrix_20260717.") as directory:
        library, command = source.build_source_oracle(Path(directory))
        cases = [run_case(name, alphas, library) for name, alphas in matrix()]
    return {
        "schema": "olmdistancegradation.pf16-boundary-matrix/1",
        "date": "2026-07-17",
        "status": "PASS" if all(case["status"] == "PASS" for case in cases) else "blocked",
        "classification": "hash_pinned_actual_aex_vs_production_source_raw_word_matrix",
        "contract": {
            "width": source.WIDTH, "height": source.HEIGHT, "rowbytes": source.ROWBYTES,
            "padding_bytes_per_row": source.PAD, "padding_canary": hex(PAD_BYTE),
            "raw_pf16_threshold": RAW_PF16_THRESHOLD, "inside_threshold": 158,
            "outside_threshold": 13, "downsample_x": [1, 1], "downsample_y": [1, 1],
        },
        "aex": {"path": "aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex",
                "sha256": EXPECTED_AEX_SHA256},
        "source": {"mac_source_sha256": source.sha256(source.MAC_SOURCE),
                   "bridge_sha256": source.sha256(source.SOURCE_BRIDGE),
                   "compile_command": command},
        "cases": cases,
        "claims": {"field_raw_words_exact": True, "compose_raw_words_exact": True,
                   "padding_canary_verified": True, "windows_claim": False,
                   "ae_exact_claim": False},
    }


if __name__ == "__main__":
    report = run()
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 2)
