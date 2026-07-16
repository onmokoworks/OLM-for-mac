#!/usr/bin/env python3
"""Localize the DG PF16 AEX/source boundary on a non-degenerate mask.

This uses the actual AEX wrapper and the production Mac RenderBits source with
identical 8x5 input pixels and 1/1 downsample ratios.  It is intentionally a
Mac-local binary/source differential, not an AE-exact test.
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
sys.path.insert(0, str(HERE))

import probe_dg_pf16_wrapper_entry_20260717 as actual  # noqa: E402
import test_dg_pf16_source_oracle_20260717 as source  # noqa: E402


def alpha_fixture() -> list[int]:
    return [
        32768 if 1 <= y < 4 and 2 <= x < 6 and not (x == 3 and y == 2) else 0
        for y in range(source.HEIGHT)
        for x in range(source.WIDTH)
    ]


def active(data: bytes) -> bytes:
    return b"".join(
        data[y * source.ROWBYTES : y * source.ROWBYTES + source.WIDTH * 8]
        for y in range(source.HEIGHT)
    )


def run() -> dict[str, object]:
    alphas = alpha_fixture()
    aex = actual.run(degenerate=False, source_alpha_words=alphas)
    if aex["status"] != "PASS":
        return {"status": "blocked", "blocker": "actual AEX wrapper did not complete", "actual": aex}

    input_bytes = bytearray([source.CANARY] * (source.ROWBYTES * source.HEIGHT))
    output_bytes = bytearray([source.CANARY] * (source.ROWBYTES * source.HEIGHT))
    for y in range(source.HEIGHT):
        for x in range(source.WIDTH):
            struct.pack_into(
                "<4H",
                input_bytes,
                y * source.ROWBYTES + x * 8,
                alphas[y * source.WIDTH + x],
                0,
                0,
                0,
            )

    with tempfile.TemporaryDirectory(prefix="dg_pf16_field_staging_20260717.") as directory:
        library, compile_command = source.build_source_oracle(Path(directory))
        input_buffer = (ctypes.c_uint16 * (len(input_bytes) // 2)).from_buffer(input_bytes)
        output_buffer = (ctypes.c_uint16 * (len(output_bytes) // 2)).from_buffer(output_bytes)
        field_x = (ctypes.c_float * (source.WIDTH * source.HEIGHT))()
        d_alpha = (ctypes.c_float * (source.WIDTH * source.HEIGHT))()
        field_words = (ctypes.c_uint16 * (source.WIDTH * source.HEIGHT))()
        field_rc = library.dg_pf16_source_field_20260717(
            input_buffer, source.ROWBYTES, field_x, d_alpha, field_words,
            source.WIDTH * source.HEIGHT,
        )
        render_rc = library.dg_pf16_source_oracle_20260717(
            input_buffer, source.ROWBYTES, output_buffer, source.ROWBYTES,
            source.WIDTH, source.HEIGHT,
        )

    actual_field_rows = aex["field_capture"]["raw_words_agrb"]
    actual_field = [int(row[0]) for row in actual_field_rows]
    replicated_field_channels = all(len(set(row)) == 1 for row in actual_field_rows)
    source_field = [int(value) for value in field_words]
    field_diffs = [
        {"index": i, "actual": actual_field[i], "source": source_field[i]}
        for i in range(len(actual_field))
        if actual_field[i] != source_field[i]
    ]

    # The Windows AEX PF16 world is captured as A,G,R,B; PF_Pixel16 is A,R,G,B.
    actual_output = [
        (int(row[0]), int(row[2]), int(row[1]), int(row[3]))
        for row in aex["output_active_words_agrb"]
    ]
    source_output = list(struct.iter_unpack("<4H", active(output_bytes)))
    output_diffs = [
        {"index": i, "actual_argb": list(actual_output[i]), "source_argb": list(source_output[i])}
        for i in range(len(actual_output))
        if actual_output[i] != source_output[i]
    ]
    passed = (
        field_rc == 0
        and render_rc == 0
        and replicated_field_channels
        and not field_diffs
        and aex["fieldgen_entry_hook_hits"] == 2
        and aex["compose_entry_hook_hits"] == source.WIDTH * source.HEIGHT
        and aex["padding_canary"]["preserved"]
        and not output_diffs
    )
    return {
        "schema": "olmdistancegradation.pf16-field-staging-differential/1",
        "date": "2026-07-17",
        "status": "PASS" if passed else "blocked",
        "classification": (
            "fieldgen_staging_compose_and_pf16_store_exact"
            if passed else "contract_or_comparison_failure"
        ),
        "fixture": {
            "width": source.WIDTH,
            "height": source.HEIGHT,
            "rowbytes": source.ROWBYTES,
            "downsample_x": [1, 1],
            "downsample_y": [1, 1],
            "opaque_pixels": sum(value != 0 for value in alphas),
            "transparent_pixels": sum(value == 0 for value in alphas),
        },
        "actual_aex": {
            "fieldgen_hits": aex["fieldgen_entry_hook_hits"],
            "compose_hits": aex["compose_entry_hook_hits"],
            "padding_preserved": aex["padding_canary"]["preserved"],
            "binary_sha256": aex["binary_sha256"],
        },
        "source_oracle": {
            "field_return_code": field_rc,
            "render_return_code": render_rc,
            "compile_command": compile_command,
        },
        "field_comparison": {
            "pixel_count": len(actual_field),
            "replicated_aex_channels": replicated_field_channels,
            "word_diff_count": len(field_diffs),
            "diffs": field_diffs,
            "actual_sha256": hashlib.sha256(struct.pack("<40H", *actual_field)).hexdigest(),
            "source_sha256": hashlib.sha256(struct.pack("<40H", *source_field)).hexdigest(),
        },
        "output_comparison": {
            "pixel_diff_count": len(output_diffs),
            "diffs": output_diffs,
            "residual_family": "none",
        },
        "claims": {
            "fieldgen_exact_for_fixture": passed,
            "staging_exact_for_fixture": passed,
            "compose_or_store_exact": passed,
            "windows_claim": False,
            "ae_exact_claim": False,
        },
    }


if __name__ == "__main__":
    report = run()
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 2)
