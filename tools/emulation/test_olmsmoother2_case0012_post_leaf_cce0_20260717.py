#!/usr/bin/env python3
"""Bitwise local witness for the synthetic c280/cce0 Smoother2 fixture."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THIS_SCRIPT = Path(__file__).resolve().relative_to(ROOT)
ADAPTER_SOURCE = Path("tools/emulation/smoother2_case0012_post_leaf_cce0_adapter_20260717.cpp")
CANONICAL_JSON = Path("refs/conformance/olmsmoother2_case0012_post_leaf_cce0_20260717.json")
CANONICAL_MD = Path("refs/conformance/olmsmoother2_case0012_post_leaf_cce0_20260717.md")
sys.path.insert(0, str(ROOT / "tools" / "emulation"))
from aex_loader import AexLoader  # noqa: E402
from test_smoother2_fullchain_diff import (  # noqa: E402
    call_c280_entry,
    call_cce0_entry,
)
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402

X = 5
Y = 6
FIXTURE = {
    "name": "c2_witness",
    "width": 16,
    "height": 16,
    "xy": [X, Y],
    "source_pixels": [
        [X, Y - 1, 0.8, 0.1, 0.1, 0.99607843],
        [X, Y, 1, 1, 1, 1],
    ],
    "class_pixels": [
        [X, Y, 0, 1, 0, 1],
        [X + 1, Y, 1, 0, 0, 0],
        [X + 1, Y + 1, 0, 0, 1, 0],
        [X, Y - 1, 1, 0, 0, 0],
    ],
}
CALLER_CONFIG = {
    "version": 2,
    "scale_fixed": [65536, 65536],
    "normalized": [655.36, 655.36],
    "gamma_mode_byte": 0,
}
WORD_SEQUENCE = [
    "c280_rgba.r",
    "c280_rgba.g",
    "c280_rgba.b",
    "c280_rgba.a",
    "c280_weight",
    "cce0_rgba.r",
    "cce0_rgba.g",
    "cce0_rgba.b",
    "cce0_rgba.a",
]
CLAIMS_NOT_MADE = [
    "No live Windows or After Effects host claim",
    "No case_0012 continuation claim",
    "No post-leaf state transfer claim",
    "No production correctness claim",
    "No ledger change",
]
BINARY_GROUNDING = {
    "aex_function": "FUN_18000b120",
    "aex_divss_addresses": ["0x18000b17c", "0x18000b181", "0x18000b18f"],
    "portable_source": "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp",
    "portable_rule": "divide r, g, and b directly by alpha; do not compute one reciprocal and multiply",
}


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def f32_u32(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def format_f32_list(values: list[float]) -> list[float]:
    return [f32(value) for value in values]


def format_u32_hex(value: int) -> str:
    return f"0x{value:08x}"


def lowest_differing_bit_lsb0(a: int, b: int) -> int | None:
    diff = a ^ b
    if diff == 0:
        return None
    return (diff & -diff).bit_length() - 1


def fixture_trace_from_portable(payload: dict) -> dict:
    return {
        "fixture": payload.get("fixture"),
        "caller_config": payload.get("caller_config"),
        "c280_count": payload.get("c280_count"),
        "c280_vertices": payload.get("c280_vertices"),
        "cce0": payload.get("cce0"),
    }


def validate_trace_shape(trace: dict) -> tuple[bool, list[str]]:
    problems: list[str] = []
    if trace.get("fixture") != FIXTURE:
        problems.append("fixture_exact")
    if trace.get("caller_config") != CALLER_CONFIG:
        problems.append("caller_config_exact")
    if trace.get("c280_count") != 1:
        problems.append("c280_count_is_one")
    vertices = trace.get("c280_vertices")
    if not isinstance(vertices, list) or len(vertices) != 1:
        problems.append("single_c280_vertex")
    else:
        vertex = vertices[0]
        rgba_f32 = vertex.get("rgba_f32")
        rgba_u32 = vertex.get("rgba_u32")
        if not isinstance(rgba_f32, list) or len(rgba_f32) != 4:
            problems.append("c280_rgba_f32_shape")
        if not isinstance(rgba_u32, list) or len(rgba_u32) != 4:
            problems.append("c280_rgba_u32_shape")
        if "weight_f32" not in vertex:
            problems.append("c280_weight_f32_present")
        if "weight_u32" not in vertex:
            problems.append("c280_weight_u32_present")
    cce0 = trace.get("cce0")
    if not isinstance(cce0, dict):
        problems.append("cce0_present")
    else:
        rgba_f32 = cce0.get("rgba_f32")
        rgba_u32 = cce0.get("rgba_u32")
        if not isinstance(rgba_f32, list) or len(rgba_f32) != 4:
            problems.append("cce0_rgba_f32_shape")
        if not isinstance(rgba_u32, list) or len(rgba_u32) != 4:
            problems.append("cce0_rgba_u32_shape")
    return (not problems, problems)


def canonicalize_trace(trace: dict) -> dict:
    vertex = trace["c280_vertices"][0]
    cce0 = trace["cce0"]
    vertex_rgba_u32 = [int(value) for value in vertex["rgba_u32"]]
    cce0_rgba_u32 = [int(value) for value in cce0["rgba_u32"]]
    vertex_rgba_f32 = [f32(value) for value in vertex["rgba_f32"]]
    cce0_rgba_f32 = [f32(value) for value in cce0["rgba_f32"]]
    return {
        "fixture": trace["fixture"],
        "caller_config": trace["caller_config"],
        "c280_count": int(trace["c280_count"]),
        "c280_vertices": [
            {
                "rgba_f32": vertex_rgba_f32,
                "rgba_u32": vertex_rgba_u32,
                "rgba_u32_hex": [format_u32_hex(value) for value in vertex_rgba_u32],
                "weight_f32": f32(vertex["weight_f32"]),
                "weight_u32": int(vertex["weight_u32"]),
                "weight_u32_hex": format_u32_hex(int(vertex["weight_u32"])),
            }
        ],
        "cce0": {
            "rgba_f32": cce0_rgba_f32,
            "rgba_u32": cce0_rgba_u32,
            "rgba_u32_hex": [format_u32_hex(value) for value in cce0_rgba_u32],
        },
    }


def run_aex() -> dict:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls()
    ss = SmootherStruct(loader, 16, 16)
    ss.set_src_pixel(X, Y - 1, (0.8, 0.1, 0.1, 0.99607843))
    ss.set_src_pixel(X, Y, (1.0, 1.0, 1.0, 1.0))
    ss.set_class_pixel(X, Y, 0, 1, 0, 1)
    ss.set_class_pixel(X + 1, Y, 1, 0, 0, 0)
    ss.set_class_pixel(X + 1, Y + 1, 0, 0, 1, 0)
    ss.set_class_pixel(X, Y - 1, 1, 0, 0, 0)
    c280 = call_c280_entry(loader, ss, X, Y)
    cce0 = call_cce0_entry(loader, ss, X, Y, gamma_colors=False)
    return {
        "fixture": FIXTURE,
        "caller_config": {
            "version": 2,
            "scale_fixed": c280["scale_fixed"],
            "normalized": [655.36, 655.36],
            "gamma_mode_byte": cce0["config"]["gamma_mode_byte"],
        },
        "c280_count": int(c280["count"]),
        "c280_vertices": [
            {
                "rgba_f32": format_f32_list(list(c280["vertices"][0]["rgba"])) if c280["vertices"] else [],
                "rgba_u32": [f32_u32(value) for value in c280["vertices"][0]["rgba"]] if c280["vertices"] else [],
                "weight_f32": f32(c280["vertices"][0]["weight"]) if c280["vertices"] else None,
                "weight_u32": f32_u32(c280["vertices"][0]["weight"]) if c280["vertices"] else None,
            }
        ] if c280["vertices"] else [],
        "cce0": {
            "rgba_f32": format_f32_list(list(cce0["rgba"])),
            "rgba_u32": [f32_u32(value) for value in cce0["rgba"]],
        },
    }


def build_word_rows(aex: dict, portable: dict) -> list[dict]:
    aex_vertex = aex["c280_vertices"][0]
    portable_vertex = portable["c280_vertices"][0]
    rows: list[dict] = []
    for index, label in enumerate(WORD_SEQUENCE):
        if index < 4:
            aex_u32 = aex_vertex["rgba_u32"][index]
            portable_u32 = portable_vertex["rgba_u32"][index]
            aex_f32 = aex_vertex["rgba_f32"][index]
            portable_f32 = portable_vertex["rgba_f32"][index]
        elif index == 4:
            aex_u32 = aex_vertex["weight_u32"]
            portable_u32 = portable_vertex["weight_u32"]
            aex_f32 = aex_vertex["weight_f32"]
            portable_f32 = portable_vertex["weight_f32"]
        else:
            channel = index - 5
            aex_u32 = aex["cce0"]["rgba_u32"][channel]
            portable_u32 = portable["cce0"]["rgba_u32"][channel]
            aex_f32 = aex["cce0"]["rgba_f32"][channel]
            portable_f32 = portable["cce0"]["rgba_f32"][channel]
        rows.append(
            {
                "sequence_index": index,
                "label": label,
                "aex_u32": aex_u32,
                "aex_u32_hex": format_u32_hex(aex_u32),
                "aex_f32": aex_f32,
                "portable_u32": portable_u32,
                "portable_u32_hex": format_u32_hex(portable_u32),
                "portable_f32": portable_f32,
                "bitwise_equal": aex_u32 == portable_u32,
                "xor_u32": aex_u32 ^ portable_u32,
                "xor_u32_hex": format_u32_hex(aex_u32 ^ portable_u32),
                "lowest_differing_bit_lsb0": lowest_differing_bit_lsb0(aex_u32, portable_u32),
            }
        )
    return rows


def classify(aex: dict, portable: dict) -> tuple[str, dict, dict]:
    aex_ok, aex_problems = validate_trace_shape(aex)
    portable_ok, portable_problems = validate_trace_shape(portable)
    comparison = {
        "aex_shape_valid": aex_ok,
        "portable_shape_valid": portable_ok,
        "aex_shape_problems": aex_problems,
        "portable_shape_problems": portable_problems,
        "fixture_exact": aex.get("fixture") == portable.get("fixture") == FIXTURE,
        "caller_config_exact": aex.get("caller_config") == portable.get("caller_config") == CALLER_CONFIG,
        "c280_count_exact": aex.get("c280_count") == portable.get("c280_count") == 1,
        "word_sequence": WORD_SEQUENCE,
        "bitwise_word_results": [],
        "all_words_bitwise_equal": False,
    }
    if not aex_ok or not portable_ok:
        first = "aex_shape" if not aex_ok else "portable_shape"
        return (
            "FAIL_CLOSED_MALFORMED_SHAPE_FIXTURE_OR_CONFIG",
            comparison,
            {
                "stage": first,
                "reason": aex_problems if not aex_ok else portable_problems,
            },
        )

    word_rows = build_word_rows(aex, portable)
    comparison.update(
        {
            "bitwise_word_results": [
                {
                    "sequence_index": row["sequence_index"],
                    "label": row["label"],
                    "bitwise_equal": row["bitwise_equal"],
                }
                for row in word_rows
            ],
            "all_words_bitwise_equal": all(row["bitwise_equal"] for row in word_rows),
        }
    )
    if not comparison["fixture_exact"] or not comparison["caller_config_exact"] or not comparison["c280_count_exact"]:
        stage = "fixture" if not comparison["fixture_exact"] else "caller_config"
        if comparison["fixture_exact"] and comparison["caller_config_exact"] and not comparison["c280_count_exact"]:
            stage = "c280_count"
        return (
            "FAIL_CLOSED_MALFORMED_SHAPE_FIXTURE_OR_CONFIG",
            comparison,
            {
                "stage": stage,
                "reason": "exact fixture/config/count contract not satisfied",
            },
        )

    first_diff = next((row for row in word_rows if not row["bitwise_equal"]), None)
    if first_diff is None:
        return (
            "LOCAL_SYNTHETIC_BITWISE_MATCH",
            comparison,
            {
                "stage": "bitwise_match",
                "word_rows": word_rows,
            },
        )
    return (
        "LOCAL_SYNTHETIC_FIRST_DIFFERING_FLOAT32_WORD",
        comparison,
        {
            "stage": first_diff["label"],
            "sequence_index": first_diff["sequence_index"],
            "aex_u32": first_diff["aex_u32"],
            "aex_u32_hex": first_diff["aex_u32_hex"],
            "aex_f32": first_diff["aex_f32"],
            "portable_u32": first_diff["portable_u32"],
            "portable_u32_hex": first_diff["portable_u32_hex"],
            "portable_f32": first_diff["portable_f32"],
            "xor_u32": first_diff["xor_u32"],
            "xor_u32_hex": first_diff["xor_u32_hex"],
            "lowest_differing_bit_lsb0": first_diff["lowest_differing_bit_lsb0"],
            "word_rows": word_rows,
        },
    )


def assert_fail_closed_classification(aex: dict, portable: dict) -> None:
    def assert_renderable(verdict: str, comparison: dict, first: dict) -> None:
        rendered = render_md(
            {
                "verdict": verdict,
                "scope": "fail-closed self-test",
                "comparison": comparison,
                "first_divergence": first,
                "word_rows": [],
            }
        )
        assert "FAIL_CLOSED_MALFORMED_SHAPE_FIXTURE_OR_CONFIG" in rendered

    malformed = copy.deepcopy(portable)
    del malformed["cce0"]["rgba_u32"]
    verdict, comparison, first = classify(aex, malformed)
    assert verdict == "FAIL_CLOSED_MALFORMED_SHAPE_FIXTURE_OR_CONFIG"
    assert not comparison["portable_shape_valid"]
    assert "cce0_rgba_u32_shape" in comparison["portable_shape_problems"]
    assert_renderable(verdict, comparison, first)

    wrong_fixture = copy.deepcopy(portable)
    wrong_fixture["fixture"] = {"name": "wrong_fixture"}
    verdict, comparison, first = classify(aex, wrong_fixture)
    assert verdict == "FAIL_CLOSED_MALFORMED_SHAPE_FIXTURE_OR_CONFIG"
    assert comparison["portable_shape_valid"] is False
    assert "fixture_exact" in comparison["portable_shape_problems"]
    assert_renderable(verdict, comparison, first)


def render_md(report: dict) -> str:
    verdict = report["verdict"]
    first = report["first_divergence"]
    lines = [
        "# OLMSmoother2 synthetic c280/cce0 float32 witness",
        "",
        "Artifact suffix: `20260717`.",
        "",
        "## Verdict",
        "",
        f"- Verdict: `{verdict}`.",
        f"- Scope: `{report['scope']}`.",
        f"- Fixture exact on both sides: `{report['comparison']['fixture_exact']}`.",
        f"- Caller config exact on both sides: `{report['comparison']['caller_config_exact']}`.",
        f"- All compared float32 words bitwise equal: `{report['comparison']['all_words_bitwise_equal']}`.",
        "",
        "## Caller Config",
        "",
        "- Fixed-point words: `65536/65536`.",
        "- Normalized values: `655.36/655.36`.",
        "- Gamma mode byte: `0`.",
        "",
        "## Binary Grounding",
        "",
        "- AEX function: `FUN_18000b120`.",
        "- Direct scalar divides: `0x18000b17c`, `0x18000b181`, `0x18000b18f` (`DIVSS`).",
        "- Portable rule: divide each RGB channel directly by alpha; a shared reciprocal followed by multiplication changes the float32 rounding point.",
        "",
        "## First Divergence",
        "",
    ]
    if verdict == "LOCAL_SYNTHETIC_FIRST_DIFFERING_FLOAT32_WORD":
        lines.extend(
            [
                f"- Stage: `{first['stage']}` at sequence index `{first['sequence_index']}`.",
                f"- AEX: `{first['aex_u32_hex']}` (`{first['aex_f32']}`).",
                f"- Portable: `{first['portable_u32_hex']}` (`{first['portable_f32']}`).",
                f"- XOR: `{first['xor_u32_hex']}`; lowest differing bit (lsb0): `{first['lowest_differing_bit_lsb0']}`.",
            ]
        )
    elif verdict == "LOCAL_SYNTHETIC_BITWISE_MATCH":
        lines.append("- No differing float32 word was observed in the bounded c280/cce0 sequence.")
    else:
        lines.append(f"- Fail-closed stage: `{first['stage']}`.")
        if "reason" in first:
            lines.append(f"- Reason: `{first['reason']}`.")
    lines.extend(
        [
            "",
            "## Compared Words",
            "",
            "| Index | Label | AEX u32 | Portable u32 | Equal |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["word_rows"]:
        lines.append(
            f"| {row['sequence_index']} | `{row['label']}` | `{row['aex_u32_hex']}` | `{row['portable_u32_hex']}` | `{row['bitwise_equal']}` |"
        )
    lines.extend(
        [
            "",
            "## Reproduction",
            "",
            "```sh",
            "tmp=$(mktemp -d)",
            "clang++ -std=c++17 -O2 \\",
            "  -Icli/OLMSmoother2/shim -Imac/OLMSmoother2/Mac \\",
            f"  {ADAPTER_SOURCE.as_posix()} \\",
            "  -o \"$tmp/synthetic_c280_cce0\"",
            f"python3 {THIS_SCRIPT.as_posix()} \\",
            "  --adapter \"$tmp/synthetic_c280_cce0\" \\",
            f"  --output-json {CANONICAL_JSON.as_posix()} \\",
            f"  --output-md {CANONICAL_MD.as_posix()}",
            "```",
            "",
            "## Claims Not Made",
            "",
        ]
    )
    lines.extend([f"- {claim}." for claim in CLAIMS_NOT_MADE])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    output_json = args.output_json if args.output_json.is_absolute() else ROOT / args.output_json
    output_md = args.output_md if args.output_md.is_absolute() else ROOT / args.output_md

    aex_raw = run_aex()
    portable_raw = json.loads(subprocess.check_output([str(args.adapter)], text=True))
    portable_raw_trace = fixture_trace_from_portable(portable_raw)
    verdict, comparison, first_divergence = classify(aex_raw, portable_raw_trace)
    if verdict.startswith("FAIL_CLOSED"):
        aex_trace = aex_raw
        portable_trace = portable_raw_trace
    else:
        assert_fail_closed_classification(aex_raw, portable_raw_trace)
        aex_trace = canonicalize_trace(aex_raw)
        portable_trace = canonicalize_trace(portable_raw_trace)
        verdict, comparison, first_divergence = classify(aex_trace, portable_trace)
    if verdict.startswith("FAIL_CLOSED"):
        word_rows = []
    else:
        word_rows = (
            first_divergence.get("word_rows")
            if isinstance(first_divergence.get("word_rows"), list)
            else build_word_rows(aex_trace, portable_trace)
        )
    report = {
        "verdict": verdict,
        "scope": "local checked-in AEX versus portable c280/cce0 float32-word witness; not live Windows, not After Effects host truth, not case_0012 continuation",
        "fixture": FIXTURE,
        "caller_config": CALLER_CONFIG,
        "binary_grounding": BINARY_GROUNDING,
        "aex": {
            "path": str(AEX_PATH.relative_to(ROOT)),
            "sha256": hashlib.sha256(AEX_PATH.read_bytes()).hexdigest(),
            "trace": aex_trace,
        },
        "portable": {
            "adapter_source": ADAPTER_SOURCE.as_posix(),
            "trace": portable_trace,
        },
        "comparison": comparison,
        "first_divergence": {k: v for k, v in first_divergence.items() if k != "word_rows"},
        "word_rows": word_rows,
        "claims_not_made": CLAIMS_NOT_MADE,
        "artifact_paths": {
            "json": CANONICAL_JSON.as_posix(),
            "md": CANONICAL_MD.as_posix(),
        },
    }
    json_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    md_text = render_md(report)
    output_json.write_text(json_text, encoding="utf-8")
    output_md.write_text(md_text, encoding="utf-8")
    print(json_text, end="")
    return 0 if not verdict.startswith("FAIL_CLOSED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
