#!/usr/bin/env python3
"""Strict livefield/source replay manifest for DG 16bpc family 0024..0027.

This tool only accepts input facts that are already present in existing
Windows returns/traces. It prepares exact replay candidates for the actual
Windows AEX compose callback `FUN_181170480` and refuses to invent missing
field/source raw words.
"""

from __future__ import annotations

import argparse
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
    ROWBYTES,
    WIDTH,
    HEIGHT,
    call_actual_aex,
    read_u64,
)
from test_dg_compose import (  # noqa: E402
    AEX_PATH,
    WORLD_DATA_PTR,
    alloc_refcon,
    build_world,
    make_loader,
)


SCHEMA = "olmdistancegradation-livefield-source-actual-aex/1"
OUTPUT_JSON = ROOT / "refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.json"
OUTPUT_MD = ROOT / "refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.md"

QUANTIZATION_JSON = ROOT / "refs/reports/runtime_trace_comparisons/olmdistancegradation_depthgate_quantization_witness_20260708.json"
FOLLOWUP_907_JSON = ROOT / "refs/reports/runtime_trace_comparisons/olmdistancegradation_depthgate_907_store_export_witness_20260708.json"
ROW0_RAMP_JSON = ROOT / "refs/reports/runtime_trace_comparisons/olmdistancegradation_16bpc_case0026_x_witness_20260629.json"

OFF_SOURCE_WORLD_PTR = 0x00
OFF_FIELD_WORLD_PTR = 0x08
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

CASE_PARAMS = {
    "case_0024": {
        "invert": 0,
        "in_out": 3,
        "inside_threshold": 158,
        "outside_threshold": 17,
        "render_mode": 1,
        "use_background_color": 1,
        "interp_mode": 3,
        "power": 1.0,
        "gradation_rgba": [0.1098041459918, 0.0, 0.93333333730698, 1.0],
        "background_rgba": [1.0, 0.0, 0.0, 1.0],
    },
    "case_0025": {
        "invert": 1,
        "in_out": 3,
        "inside_threshold": 158,
        "outside_threshold": 13,
        "render_mode": 1,
        "use_background_color": 1,
        "interp_mode": 3,
        "power": 1.0,
        "gradation_rgba": [0.1098041459918, 0.0, 0.93333333730698, 1.0],
        "background_rgba": [1.0, 0.0, 0.0, 1.0],
    },
    "case_0026": {
        "invert": 1,
        "in_out": 3,
        "inside_threshold": 158,
        "outside_threshold": 13,
        "render_mode": 1,
        "use_background_color": 1,
        "interp_mode": 4,
        "power": 2.59740734100342,
        "gradation_rgba": [0.1098041459918, 0.0, 0.93333333730698, 1.0],
        "background_rgba": [1.0, 0.0, 0.0, 1.0],
    },
    "case_0027": {
        "invert": 1,
        "in_out": 3,
        "inside_threshold": 158,
        "outside_threshold": 13,
        "render_mode": 2,
        "use_background_color": 1,
        "interp_mode": 4,
        "power": 2.59740734100342,
        "gradation_rgba": [0.1098041459918, 0.0, 0.93333333730698, 1.0],
        "background_rgba": [1.0, 0.0, 0.0, 1.0],
    },
}

FAMILY_CASES = ("case_0024", "case_0025", "case_0026", "case_0027")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def rgba16_to_raw_words_agrb(rgba16: list[int]) -> list[int]:
    r, g, b, a = rgba16
    return [a, g, r, b]


def build_refcon(loader, source_world: int, field_world: int, params: dict[str, object]) -> int:
    refcon = alloc_refcon(loader)
    loader.write_bytes(refcon + OFF_SOURCE_WORLD_PTR, struct.pack("<Q", source_world))
    loader.write_bytes(refcon + OFF_FIELD_WORLD_PTR, struct.pack("<Q", field_world))
    loader.write_bytes(refcon + OFF_DEGENERATE, b"\x00")
    loader.write_bytes(refcon + OFF_INOUT_MODE, struct.pack("<i", int(params["in_out"])))
    loader.write_bytes(refcon + OFF_GRAD_G, struct.pack("<f", float(params["gradation_rgba"][1])))
    loader.write_bytes(refcon + OFF_GRAD_R, struct.pack("<f", float(params["gradation_rgba"][0])))
    loader.write_bytes(refcon + OFF_GRAD_B, struct.pack("<f", float(params["gradation_rgba"][2])))
    loader.write_bytes(refcon + OFF_BG_G, struct.pack("<f", float(params["background_rgba"][1])))
    loader.write_bytes(refcon + OFF_BG_R, struct.pack("<f", float(params["background_rgba"][0])))
    loader.write_bytes(refcon + OFF_BG_B, struct.pack("<f", float(params["background_rgba"][2])))
    loader.write_bytes(refcon + OFF_USE_BG, bytes([int(params["use_background_color"])]))
    loader.write_bytes(refcon + OFF_INVERT, bytes([int(params["invert"])]))
    loader.write_bytes(refcon + OFF_RENDER_MODE, struct.pack("<i", int(params["render_mode"])))
    loader.write_bytes(refcon + OFF_INTERP_MODE, struct.pack("<i", int(params["interp_mode"])))
    loader.write_bytes(refcon + OFF_POWER, struct.pack("<f", float(params["power"])))
    return refcon


def extract_case0026_candidates() -> list[dict[str, object]]:
    quant = load_json(QUANTIZATION_JSON)
    followup = load_json(FOLLOWUP_907_JSON)
    followup_pixels = {
        tuple(pixel.get("xy", [pixel["x"], pixel["y"]])): pixel
        for pixel in followup["windows"]["witness_pixels"]
    }

    candidates: list[dict[str, object]] = []
    for pixel in quant["windows"]["witness_pixels"]:
        xy = tuple(pixel["xy"])
        followup_pixel = followup_pixels.get(xy)
        source_rgba16 = pixel.get("source_input_rgba16_seen_by_effect")
        missing = []
        if source_rgba16 is None:
            missing.append("source_input_rgba16_seen_by_effect")
        missing.append("field_raw_words_agrb")
        missing.append("field_word_at_rcx_plus_2")

        candidate = {
            "case_id": "case_0026",
            "xy": list(xy),
            "params": CASE_PARAMS["case_0026"],
            "trace_sources": [
                str(QUANTIZATION_JSON.relative_to(ROOT)),
                str(FOLLOWUP_907_JSON.relative_to(ROOT)) if followup_pixel else None,
            ],
            "source_rgba16_seen_by_effect": source_rgba16,
            "source_raw_words_agrb_exact": (
                rgba16_to_raw_words_agrb(source_rgba16) if source_rgba16 is not None else None
            ),
            "field_value_consumed_by_fun_181170480": pixel.get("field_value_consumed_by_FUN_181170480"),
            "field_raw_words_agrb": None,
            "field_word_at_rcx_plus_2": None,
            "x_after_power_interpolation": pixel.get("x_after_power_interpolation"),
            "pre_pf16_output_rgba_float": pixel.get("output_rgba_float_before_pf16_conversion"),
            "carried_pf_pixel16_words_after_store": pixel.get("pf_pixel16_words_after_store"),
            "carried_exported_rgba8": pixel.get("same_run_exported_rgba16_or_png_bytes"),
            "classification": pixel.get("classification"),
            "exact_replay_ready": False,
            "missing_for_exact_replay": missing,
            "notes": [
                "source raw words are recoverable exactly from traced RGBA16 plus known A,G,R,B world layout",
                "field raw words were not returned by the located Windows traces",
            ],
        }
        if followup_pixel:
            candidate["followup_907_return"] = {
                "status": "carried_values_only",
                "source_rgba8": followup_pixel.get("input_rgba"),
                "pre_writeback_rgba_float_hex": followup_pixel.get("pre_writeback_rgba_float_hex"),
            }
        candidate["trace_sources"] = [path for path in candidate["trace_sources"] if path]
        candidates.append(candidate)
    return candidates


def extract_row0_ramp() -> dict[str, object]:
    row0 = load_json(ROW0_RAMP_JSON)
    compose = row0["windows"]["compose"]
    return {
        "case_id": "case_0026",
        "trace_source": str(ROW0_RAMP_JSON.relative_to(ROOT)),
        "y": 0,
        "x_range": [0, 14],
        "source_rgba16_seen_by_effect": row0["windows"]["field_values"]["source_input_rgba16"],
        "x_before_invert": compose["fun_181170480_X_before_invert"],
        "x_after_invert": compose["fun_181170480_X_after_invert"],
        "x_after_power_interpolation": compose["fun_181170480_X_after_power_interp"],
        "missing": [
            "field_raw_words_agrb",
            "field_word_at_rcx_plus_2",
            "per-pixel source raw words beyond semantic zero RGBA16",
            "post-call exact output words",
        ],
    }


def summarize_family(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    by_case: dict[str, list[dict[str, object]]] = {case_id: [] for case_id in FAMILY_CASES}
    for candidate in candidates:
        by_case[candidate["case_id"]].append(candidate)

    for case_id in FAMILY_CASES:
        case_candidates = by_case[case_id]
        if case_candidates:
            missing = sorted({item for candidate in case_candidates for item in candidate["missing_for_exact_replay"]})
            summary.append({
                "case_id": case_id,
                "located_live_trace_points": len(case_candidates),
                "exact_replayable_points": sum(1 for candidate in case_candidates if candidate["exact_replay_ready"]),
                "status": "partial_evidence_only",
                "missing_for_exact_replay": missing,
            })
        else:
            summary.append({
                "case_id": case_id,
                "located_live_trace_points": 0,
                "exact_replayable_points": 0,
                "status": "no_return_trace_point_with_livefield_source_words_located",
                "missing_for_exact_replay": [
                    "live coordinate-bound source input witness",
                    "live field raw words",
                ],
            })
    return summary


def replay_exact_candidates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    runnable = [candidate for candidate in candidates if candidate["exact_replay_ready"]]
    if not runnable:
        return []

    loader = make_loader()
    source_pixels = {
        tuple(candidate["xy"]): tuple(candidate["source_raw_words_agrb_exact"])
        for candidate in runnable
    }
    field_pixels = {
        tuple(candidate["xy"]): tuple(candidate["field_raw_words_agrb"])
        for candidate in runnable
    }
    source_world = build_world(loader, WIDTH, HEIGHT, source_pixels)
    field_world = build_world(loader, WIDTH, HEIGHT, field_pixels)
    source_base = read_u64(loader, source_world + WORLD_DATA_PTR)
    field_base = read_u64(loader, field_world + WORLD_DATA_PTR)

    replays: list[dict[str, object]] = []
    for candidate in runnable:
        params = candidate["params"]
        refcon = build_refcon(loader, source_world, field_world, params)
        x, y = candidate["xy"]
        output = loader.bump_alloc(8, align=16)
        loader.write_bytes(output, b"\xEE" * 8)
        instructions = call_actual_aex(loader, refcon, x, y, output)
        field_addr = field_base + y * ROWBYTES + x * 8
        source_addr = source_base + y * ROWBYTES + x * 8
        field_words = list(struct.unpack("<4H", loader.read_bytes(field_addr, 8)))
        source_words = list(struct.unpack("<4H", loader.read_bytes(source_addr, 8)))
        output_words = list(struct.unpack("<4H", loader.read_bytes(output, 8)))
        replays.append({
            "case_id": candidate["case_id"],
            "xy": [x, y],
            "field_addr": hex(field_addr),
            "source_addr": hex(source_addr),
            "output_addr": hex(output),
            "field_words_agrb": field_words,
            "source_words_agrb": source_words,
            "output_words_agrb": output_words,
            "instructions": instructions,
        })
    return replays


def build_report() -> dict[str, object]:
    candidates = extract_case0026_candidates()
    family_summary = summarize_family(candidates)
    replays = replay_exact_candidates(candidates)
    status = "replayed_exact_livefield_inputs" if replays else "no_exact_livefield_replays"

    return {
        "schema": SCHEMA,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "scope": "OLMDistanceGradation 16bpc max=2 family case_0024..case_0027 live field/source replay manifest",
        "binary": {
            "path": str(AEX_PATH.relative_to(ROOT)),
            "sha256": sha256_file(AEX_PATH),
            "function": hex(FUN_181170480),
        },
        "evidence_sources": [
            str(QUANTIZATION_JSON.relative_to(ROOT)),
            str(FOLLOWUP_907_JSON.relative_to(ROOT)),
            str(ROW0_RAMP_JSON.relative_to(ROOT)),
        ],
        "rules": {
            "exact_replay_requires": [
                "coordinate-bound source raw words",
                "coordinate-bound field raw words",
                "case parameter tuple",
            ],
            "forbidden": [
                "derive missing field words from PNGs",
                "promote rounded float X values into claimed raw words",
            ],
        },
        "family_summary": family_summary,
        "point_candidates": candidates,
        "supplemental_trace_only": {
            "case_0026_row0_ramp": extract_row0_ramp(),
        },
        "replays": replays,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# OLMDistanceGradation 16bpc livefield/source actual-AEX manifest",
        "",
        f"Date: {report['generated_at']}",
        "",
        "## Status",
        "",
        f"- `{report['status']}`",
        "- Strict rule: replay only if both coordinate-bound source raw words and field raw words are already present in existing Windows returns/traces.",
        "- PNGs were not used to invent missing input words.",
        "",
        "## Family summary",
        "",
        "| Case | Located live points | Exact replayable | Status | Missing for exact replay |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for item in report["family_summary"]:
        lines.append(
            f"| {item['case_id']} | {item['located_live_trace_points']} | {item['exact_replayable_points']} | "
            f"{item['status']} | {', '.join(item['missing_for_exact_replay'])} |"
        )

    lines.extend([
        "",
        "## Located candidates",
        "",
        "| Case | XY | Source RGBA16 | Source raw words AGRB | Field X from trace | Carry store AGRB16 | Missing for exact replay |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ])
    for candidate in report["point_candidates"]:
        lines.append(
            f"| {candidate['case_id']} | `{tuple(candidate['xy'])}` | `{candidate['source_rgba16_seen_by_effect']}` | "
            f"`{candidate['source_raw_words_agrb_exact']}` | `{candidate['field_value_consumed_by_fun_181170480']}` | "
            f"`{candidate['carried_pf_pixel16_words_after_store']}` | {', '.join(candidate['missing_for_exact_replay'])} |"
        )

    row0 = report["supplemental_trace_only"]["case_0026_row0_ramp"]
    lines.extend([
        "",
        "## Supplemental trace-only evidence",
        "",
        f"- `case_0026` row0 ramp trace: `y={row0['y']}`, `x={row0['x_range'][0]}..{row0['x_range'][1]}`",
        f"- Source RGBA16: `{row0['source_rgba16_seen_by_effect']}`",
        f"- Missing: {', '.join(row0['missing'])}",
        "",
        "## Verdict",
        "",
    ])

    if report["replays"]:
        lines.append(f"- Actual AEX replay completed for `{len(report['replays'])}` exact candidates.")
    else:
        lines.append("- No exact replays were run because no located family point includes returned field raw words.")
        lines.append("- The strongest usable evidence today is `case_0026` only: exact source semantic RGBA16 is present for four traced points, but the matching field raw word at `[RCX+2]` is still absent from the returns/traces.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=OUTPUT_JSON)
    parser.add_argument("--md-out", type=Path, default=OUTPUT_MD)
    args = parser.parse_args()

    report = build_report()
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"wrote_json={args.json_out}")
    print(f"wrote_md={args.md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
