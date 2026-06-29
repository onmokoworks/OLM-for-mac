#!/usr/bin/env python3
"""Decode positional render_rotated preset arguments for OLMDirectionalBlur."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "cli/OLMDirectionalBlur/main.cpp"
OUT_JSON = ROOT / "refs/reports/olmdirectionalblur_algorithm_presets_20260629.json"
OUT_MD = ROOT / "refs/reports/olmdirectionalblur_algorithm_presets_20260629.md"


PARAMS = [
    "input",
    "params",
    "strength_scale",
    "angle_sign",
    "sample_sign",
    "gather_first",
    "alpha_weighted_input_rotate",
    "alpha_weighted_output_rotate",
    "component_map_coeff",
    "premultiply_gather_source",
    "use_alpha_fade_gather",
    "aex_buffer_init",
    "alpha_mode",
    "strict_plain_sampler",
    "alpha_sum_output",
    "alpha_coeff_output",
    "aex_pad_size",
    "dest_component_coeff",
    "front_strength_rgb_denom",
    "rowdriver_prepass",
    "aex_two_stage_input",
    "aex_two_stage_output",
    "row_init_mode",
    "truncate_component_span",
    "truncate_output_quantize",
    "exact_component_half_height",
    "aex_rotate_math",
    "float_component_center_y",
    "component_tail_only",
    "source_alpha_binary_validity",
    "source_rgb_straight",
    "disable_component_tail",
    "preserve_invalid_input_rotate",
    "source_driven_scatter",
    "rotateback_denom_alpha",
]

DEFAULTS = {
    "alpha_sum_output": "false",
    "alpha_coeff_output": "false",
    "aex_pad_size": "false",
    "dest_component_coeff": "false",
    "front_strength_rgb_denom": "false",
    "rowdriver_prepass": "false",
    "aex_two_stage_input": "false",
    "aex_two_stage_output": "false",
    "row_init_mode": "-1",
    "truncate_component_span": "false",
    "truncate_output_quantize": "false",
    "exact_component_half_height": "false",
    "aex_rotate_math": "false",
    "float_component_center_y": "false",
    "component_tail_only": "false",
    "source_alpha_binary_validity": "false",
    "source_rgb_straight": "false",
    "disable_component_tail": "false",
    "preserve_invalid_input_rotate": "false",
    "source_driven_scatter": "false",
    "rotateback_denom_alpha": "false",
}


TARGETS = [
    "rotated-aex-choreo",
    "rotated-aex-full-choreo",
    "rotated-aex-prepass-full-choreo",
    "rotated-aex-exact-scatter-helper",
    "rotated-aex-exact-rowdriver",
    "rotated-aex-truncated-span",
    "rotated-aex-trunc-output",
    "rotated-aex-binary-alpha",
    "rotated-aex-straight-source-rgb",
]


def split_args(argstr: str) -> list[str]:
    items: list[str] = []
    cur: list[str] = []
    depth = 0
    in_str = False
    prev = ""
    for ch in argstr:
        if ch == '"' and prev != "\\":
            in_str = not in_str
        if not in_str:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "," and depth == 0:
                items.append("".join(cur).strip())
                cur = []
                prev = ch
                continue
        cur.append(ch)
        prev = ch
    tail = "".join(cur).strip()
    if tail:
        items.append(tail)
    return items


def parse_preset(text: str, name: str) -> dict[str, str]:
    pat = re.compile(
        r'args\.algorithm == "' + re.escape(name) + r'"\) \{\s*output = render_rotated\((.*?)\);',
        re.S,
    )
    match = pat.search(text)
    if not match:
        raise RuntimeError(f"preset not found: {name}")
    values = split_args(" ".join(line.strip() for line in match.group(1).splitlines()))
    parsed = {}
    for idx, param in enumerate(PARAMS):
        if idx < len(values):
            parsed[param] = values[idx]
        elif param in DEFAULTS:
            parsed[param] = DEFAULTS[param]
        else:
            parsed[param] = None
    return parsed


def changed_fields(base: dict[str, str], other: dict[str, str]) -> dict[str, dict[str, str]]:
    out = {}
    for key in PARAMS[5:]:
        if base.get(key) != other.get(key):
            out[key] = {"base": base.get(key), "other": other.get(key)}
    return out


def analyze() -> dict:
    text = SOURCE.read_text(encoding="utf-8")
    presets = {name: parse_preset(text, name) for name in TARGETS}
    full = presets["rotated-aex-full-choreo"]
    exact = presets["rotated-aex-exact-rowdriver"]
    prepass = presets["rotated-aex-prepass-full-choreo"]
    scatter = presets["rotated-aex-exact-scatter-helper"]
    return {
        "kind": "olmdirectionalblur_algorithm_presets",
        "generated_at": "2026-06-29",
        "source": str(SOURCE.relative_to(ROOT)),
        "presets": presets,
        "comparisons": {
            "full_vs_prepass": changed_fields(full, prepass),
            "full_vs_scatter": changed_fields(full, scatter),
            "scatter_vs_exact_rowdriver": changed_fields(scatter, exact),
            "full_vs_exact_rowdriver": changed_fields(full, exact),
        },
    }


def write_report(report: dict) -> None:
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# OLMDirectionalBlur Algorithm Presets",
        "",
        "- Source: `cli/OLMDirectionalBlur/main.cpp`",
        "- Purpose: decode positional `render_rotated(...)` preset booleans mechanically, so AEX-shaped candidates are compared by actual toggles rather than memory.",
        "",
    ]
    for label, key in [
        ("`rotated-aex-full-choreo` vs `rotated-aex-prepass-full-choreo`", "full_vs_prepass"),
        ("`rotated-aex-full-choreo` vs `rotated-aex-exact-scatter-helper`", "full_vs_scatter"),
        ("`rotated-aex-exact-scatter-helper` vs `rotated-aex-exact-rowdriver`", "scatter_vs_exact_rowdriver"),
        ("`rotated-aex-full-choreo` vs `rotated-aex-exact-rowdriver`", "full_vs_exact_rowdriver"),
    ]:
        lines.append(f"## {label}")
        lines.append("")
        changes = report["comparisons"][key]
        if not changes:
            lines.append("- No toggle differences.")
            lines.append("")
            continue
        for field, values in changes.items():
            lines.append(f"- `{field}`: `{values['base']}` -> `{values['other']}`")
        lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = analyze()
    write_report(report)
    print(OUT_JSON)
    print(OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
