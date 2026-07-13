#!/usr/bin/env python3
"""Bounded actual-AEX PF16 compose sweep for the 0024..0027 max-2 family.

This is binary evidence only.  The field words are representative harness
inputs derived from retained 0026/0027 field-X samples; they are not claimed
Windows live values for cases 0024..0027.  The sweep reuses the existing
exact-address witness helpers and calls FUN_181170480 once for each n-1/n/n+1
row. It also recalculates retained case_0026 PF16 store quantization
witnesses; that is not an AE-exact or Windows-live-field claim.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from olmdg_compose_exact_address_witness_20260710 import (  # noqa: E402
    FUN_181170480,
    POINTS as EXISTING_EXACT_ADDRESS_POINTS,
    ROWBYTES,
    WIDTH,
    HEIGHT,
    call_actual_aex,
    read_u64,
)
from test_dg_compose import (  # noqa: E402
    WORLD_DATA_PTR,
    WORLD_HEIGHT,
    WORLD_ROWBYTES,
    WORLD_WIDTH,
    alloc_refcon,
    build_world,
    make_loader,
)

AEX = ROOT / "aex" / "OLMDistanceGradation" / "Plugins" / "64" / "2025" / "DistanceGradation.aex"
OUTPUT = ROOT / "refs" / "conformance" / "olmdistancegradation_16bpc_max2_compose_sweep_20260713.json"
QUANTIZATION_INPUT = ROOT / "refs" / "reports" / "runtime_trace_comparisons" / "olmdistancegradation_depthgate_quantization_witness_20260708.json"

OFF_FIELD_WORLD_PTR = 0x08
OFF_SOURCE_WORLD_PTR = 0x00
OFF_DEGENERATE = 0x90
OFF_INOUT_MODE = 0x94
OFF_GRAD_G = 0x9C
OFF_GRAD_R = 0xA0
OFF_GRAD_B = 0xA4
OFF_BG_G = 0xAC
OFF_BG_R = 0xB0
OFF_BG_B = 0xB4
OFF_USE_BG = 0xC0
OFF_INVERT = 0xC1
OFF_RENDER_MODE = 0xC8
OFF_INTERP_MODE = 0xCC
OFF_POWER = 0xD0

# Inputs are retained field-X samples converted to PF16 words where available,
# used as a compact low/mid/high representative sweep for the four case shapes.
CASES = (
    {"case_id": "case_0024", "xy": (6, 40), "field_word": 3989, "inside_threshold": 158, "outside_threshold": 17, "invert": 0, "render_mode": 1, "interp_mode": 3, "power": 1.0},
    {"case_id": "case_0025", "xy": (901, 394), "field_word": 7774, "inside_threshold": 158, "outside_threshold": 13, "invert": 1, "render_mode": 1, "interp_mode": 3, "power": 1.0},
    {"case_id": "case_0026", "xy": (907, 222), "field_word": 25680, "inside_threshold": 158, "outside_threshold": 13, "invert": 1, "render_mode": 1, "interp_mode": 4, "power": 2.59740734100342},
    {"case_id": "case_0027", "xy": (1234, 443), "field_word": 30473, "inside_threshold": 158, "outside_threshold": 13, "invert": 1, "render_mode": 2, "interp_mode": 4, "power": 2.59740734100342},
)


def quantize_floor_255(word: int) -> int:
    return min(255, (word * 255) // 32768)


def quantize_round_128(word: int) -> int:
    return min(255, (word + 64) // 128)


def quantize_truncate_128(word: int) -> int:
    return min(255, word // 128)


def recalculate_case0026_witnesses() -> dict[str, object]:
    source = json.loads(QUANTIZATION_INPUT.read_text(encoding="utf-8"))
    rows = []
    for witness in source["windows"]["witness_pixels"]:
        words = witness["pf_pixel16_words_after_store"]
        observed = witness["same_run_exported_rgba16_or_png_bytes"]
        channels = (0, 1, 2)  # Retained PF16 witness is RGBA16 -> RGB export order.
        predictions = {
            "floor_word_times_255_over_32768": [quantize_floor_255(words[i]) for i in channels],
            "round_word_over_128": [quantize_round_128(words[i]) for i in channels],
            "truncate_word_over_128": [quantize_truncate_128(words[i]) for i in channels],
        }
        windows_rgb = observed[:3]
        rows.append({
            "xy": witness["xy"],
            "source_classification": witness["classification"],
            "mac_pf16_store_words_rgba": words,
            "windows_observed_rgba8": observed,
            "predictions_rgb": predictions,
            "matches_windows_rgb": {name: value == windows_rgb for name, value in predictions.items()},
            "matching_rgb_channels": {name: sum(a == b for a, b in zip(value, windows_rgb)) for name, value in predictions.items()},
            "classification_basis": "retained witness classification; formula comparison is mechanical and does not promote AE exactness",
        })
    classified = [row for row in rows if row["source_classification"] == "export-quantization"]
    unresolved = [row for row in rows if row["source_classification"] == "unresolved"]
    return {
        "source": str(QUANTIZATION_INPUT.relative_to(ROOT)),
        "scope": "four retained case_0026 Mac PF16 store witnesses; RGB channels compared to retained Windows RGBA8 observations",
        "formulae": {
            "floor_word_times_255_over_32768": "floor(word * 255 / 32768)",
            "round_word_over_128": "round-half-up(word / 128)",
            "truncate_word_over_128": "truncate(word / 128)",
        },
        "classified_count": len(classified),
        "unresolved_count": len(unresolved),
        "classified_points": [row["xy"] for row in classified],
        "unresolved_points": [row["xy"] for row in unresolved],
        "fact_3_of_4_classified_and_only_907_222_unresolved": len(classified) == 3 and [row["xy"] for row in unresolved] == [[907, 222]],
        "witnesses": rows,
    }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_refcon(loader, source_world: int, field_world: int, case: dict[str, object]) -> int:
    refcon = alloc_refcon(loader)
    loader.write_bytes(refcon + OFF_SOURCE_WORLD_PTR, struct.pack("<Q", source_world))
    loader.write_bytes(refcon + OFF_FIELD_WORLD_PTR, struct.pack("<Q", field_world))
    loader.write_bytes(refcon + OFF_DEGENERATE, b"\x00")
    loader.write_bytes(refcon + OFF_INOUT_MODE, struct.pack("<i", 3))
    loader.write_bytes(refcon + OFF_GRAD_G, struct.pack("<f", 0.0))
    loader.write_bytes(refcon + OFF_GRAD_R, struct.pack("<f", 0.1098041459918))
    loader.write_bytes(refcon + OFF_GRAD_B, struct.pack("<f", 0.93333333730698))
    loader.write_bytes(refcon + OFF_BG_G, struct.pack("<f", 0.0))
    loader.write_bytes(refcon + OFF_BG_R, struct.pack("<f", 1.0))
    loader.write_bytes(refcon + OFF_BG_B, struct.pack("<f", 0.0))
    loader.write_bytes(refcon + OFF_USE_BG, b"\x01")
    loader.write_bytes(refcon + OFF_INVERT, bytes([int(case["invert"])]))
    loader.write_bytes(refcon + OFF_RENDER_MODE, struct.pack("<i", int(case["render_mode"])))
    loader.write_bytes(refcon + OFF_INTERP_MODE, struct.pack("<i", int(case["interp_mode"])))
    loader.write_bytes(refcon + OFF_POWER, struct.pack("<f", float(case["power"])))
    return refcon


def run() -> dict[str, object]:
    loader = make_loader()
    points = [tuple(case["xy"]) for case in CASES]
    field_pixels = {point: (0, int(case["field_word"]), 0, 0) for point, case in zip(points, CASES)}
    # Source is zero except at the render-mode-2 representative, where the
    # callback's source-world reads are intentionally supplied and observable.
    source_pixels = {points[-1]: (32768, 0, 32768, 0)}
    field_world = build_world(loader, WIDTH, HEIGHT, field_pixels)
    source_world = build_world(loader, WIDTH, HEIGHT, source_pixels)
    field_base = read_u64(loader, field_world + WORLD_DATA_PTR)
    source_base = read_u64(loader, source_world + WORLD_DATA_PTR)

    results = []
    total_instructions = 0
    for case in CASES:
        rows = []
        for offset in (-1, 0, 1):
            x, y = case["xy"]
            field_word = int(case["field_word"]) + offset
            field_addr = field_base + y * ROWBYTES + x * 8
            loader.write_bytes(field_addr + 2, struct.pack("<H", field_word))
            refcon = build_refcon(loader, source_world, field_world, case)
            output = loader.bump_alloc(8, align=16)
            loader.write_bytes(output, b"\xEE" * 8)
            instructions = call_actual_aex(loader, refcon, x, y, output)
            total_instructions += instructions
            source_addr = source_base + y * ROWBYTES + x * 8
            field_words = list(struct.unpack("<4H", loader.read_bytes(field_addr, 8)))
            source_words = list(struct.unpack("<4H", loader.read_bytes(source_addr, 8)))
            output_words = list(struct.unpack("<4H", loader.read_bytes(output, 8)))
            if output_words == [0xEEEE] * 4:
                raise AssertionError(f"AEX did not write output for {case['case_id']} offset {offset}")
            if field_words[1] != field_word:
                raise AssertionError(f"field word changed for {case['case_id']}: {field_words[1]}")
            rows.append({
                "offset_from_n": offset,
                "field_word": field_word,
                "field_addr": hex(field_addr),
                "source_addr": hex(source_addr),
                "output_addr": hex(output),
                "field_words_agrb": field_words,
                "source_words_agrb": source_words,
                "field_scalar_x": field_word / 32768.0,
                "aex_output_words_agrb": output_words,
                "instructions": instructions,
            })
        results.append({
            **case,
            "xy": list(case["xy"]),
            "neighborhood": rows,
            "output_transition_n_minus_1_to_n": [b - a for a, b in zip(rows[0]["aex_output_words_agrb"], rows[1]["aex_output_words_agrb"])],
            "output_transition_n_to_n_plus_1": [b - a for a, b in zip(rows[1]["aex_output_words_agrb"], rows[2]["aex_output_words_agrb"])],
            "threshold_crossing": {
                "ui_thresholds": {"inside": case["inside_threshold"], "outside": case["outside_threshold"]},
                "field_word_units_available": False,
                "observed_output_word_transition": rows[0]["aex_output_words_agrb"] != rows[1]["aex_output_words_agrb"] or rows[1]["aex_output_words_agrb"] != rows[2]["aex_output_words_agrb"],
                "note": "UI threshold values are distance-domain parameters, not PF16 field-word thresholds; this records the actual AEX output transition across n-1/n/n+1 without inventing a unit conversion.",
            },
        })

    return {
        "schema": 1,
        "kind": "olmdistancegradation_pf16_max2_actual_aex_compose_sweep",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "pass_bounded_actual_aex",
        "scope": "twelve FUN_181170480 calls; representative PF16 field-word inputs at n-1/n/n+1 for 0024..0027",
        "binary": {
            "path": str(AEX.relative_to(ROOT)),
            "sha256": sha256_file(AEX),
            "function": hex(FUN_181170480),
            "calls": len(CASES) * 3,
            "max_instructions_per_call": 200000,
            "instructions_total": total_instructions,
        },
        "address_contract": {
            "reused_witness": "tools/emulation/olmdg_compose_exact_address_witness_20260710.py",
            "field": "field_base + y * field_rowbytes + x * field_pixel_size",
            "source": "source_base + y * source_rowbytes + x * source_pixel_size",
            "field_read": "field_addr + 0x2",
            "rowbytes": ROWBYTES,
            "pixel_size": 8,
            "dimensions": [WIDTH, HEIGHT],
            "existing_exact_address_points": [list(point) for point in EXISTING_EXACT_ADDRESS_POINTS],
            "local_addresses_are_not_windows_addresses": True,
        },
        "input_provenance": {
            "field_words_are_windows_live_values": False,
            "basis": "retained case_0026/case_0027 field-X samples converted to PF16 words; 0024/0025 are representative branch-shape inputs",
            "source": "refs/conformance/olmdistancegradation_depthgate_nearmiss_witness_20260708.md",
            "case_parameters": "refs/conformance/olmdistancegradation_depthgate_nearmiss_family_20260708.md",
        },
        "claims_boundary": {
            "windows_live_field_values": False,
            "ae_exact": False,
            "broad_png_tuning": False,
            "production_source_changed": False,
        },
        "points": results,
        "case0026_store_export_recalculation": recalculate_case0026_witnesses(),
    }


def main() -> int:
    report = run()
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"wrote={OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
