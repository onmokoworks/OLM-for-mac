#!/usr/bin/env python3
"""Extract UI parameter schemas from the macOS AE plug-in sources."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


PLUGIN_SPECS = [
    {
        "plugin": "ColorKeep",
        "source": Path("mac/ColorKeep/ColorKeep.cpp"),
        "strings": Path("mac/ColorKeep/ColorKeep_Strings.cpp"),
        "status": "UI schema source-backed; helper utility, not main exact target.",
    },
    {
        "plugin": "OLMBlur",
        "source": Path("mac/OLMBlur/OLMBlur.cpp"),
        "strings": Path("mac/OLMBlur/OLMBlur_Strings.cpp"),
        "status": "UI schema source-backed; 16bpc writer/helper behavior still binary-proof work.",
    },
    {
        "plugin": "OLMColorKey",
        "source": Path("mac/OLMColorKey/OLMColorKey.cpp"),
        "strings": Path("mac/OLMColorKey/OLMColorKey_Strings.cpp"),
        "status": "UI schema source-backed; 8/16bpc behavior mostly settled, 32bpc still unverified.",
    },
    {
        "plugin": "OLMDirectionalBlur",
        "source": Path("mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"),
        "strings": Path("mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.cpp"),
        "status": "UI schema source-backed; internal effect behavior still blocked on runtime/asm proof.",
    },
    {
        "plugin": "OLMDistanceGradation",
        "source": Path("mac/OLMDistanceGradation/OLMDistanceGradation.cpp"),
        "strings": Path("mac/OLMDistanceGradation/OLMDistanceGradation_Strings.cpp"),
        "status": "UI schema source-backed; 16bpc internal ownership/boundary rules still under proof.",
    },
    {
        "plugin": "OLMKiraKira",
        "source": Path("mac/OLMKiraKira/OLMKiraKira.cpp"),
        "strings": Path("mac/OLMKiraKira/OLMKiraKira_Strings.cpp"),
        "status": "UI schema source-backed; compose/writeback behavior still blocked on narrow witness.",
    },
    {
        "plugin": "OLMRadialBlur",
        "source": Path("mac/OLMRadialBlur/OLMRadialBlur.cpp"),
        "strings": Path("mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp"),
        "status": "UI schema source-backed; sampler/prepass/writeback still need runtime proof.",
    },
    {
        "plugin": "OLMSmoother",
        "source": Path("mac/OLMSmoother/Mac/OLMSmoother_port.cpp"),
        "strings": Path("mac/OLMSmoother/OLMSmoother_Strings.cpp"),
        "status": "UI schema source-backed; v1 compatibility policy separate from schema.",
    },
    {
        "plugin": "OLMSmoother2",
        "source": Path("mac/OLMSmoother2/OLMSmoother2.cpp"),
        "strings": Path("mac/OLMSmoother2/OLMSmoother2_Strings.cpp"),
        "status": "UI schema source-backed; legacy/key-gamma path still needs internal proof.",
    },
    {
        "plugin": "OLMToonDilate",
        "source": Path("mac/OLMToonDilate/OLMToonDilate.cpp"),
        "strings": Path("mac/OLMToonDilate/OLMToonDilate_Strings.cpp"),
        "status": "UI schema source-backed; 16/32bpc expansion still pending.",
    },
]


@dataclass
class ParamRow:
    plugin: str
    label: str
    macro: str
    default: str
    hard_min: str | None
    hard_max: str | None
    ui_min: str | None
    ui_max: str | None
    extra: str | None
    source_file: str


def clone_row(row: ParamRow, label: str) -> ParamRow:
    return ParamRow(
        plugin=row.plugin,
        label=label,
        macro=row.macro,
        default=row.default,
        hard_min=row.hard_min,
        hard_max=row.hard_max,
        ui_min=row.ui_min,
        ui_max=row.ui_max,
        extra=row.extra,
        source_file=row.source_file,
    )


def split_top_level(arg_string: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    depth = 0
    in_string = False
    prev = ""
    for ch in arg_string:
        if ch == '"' and prev != "\\":
            in_string = not in_string
        if not in_string:
            if ch in "({[":
                depth += 1
            elif ch in ")}]":
                depth -= 1
            elif ch == "," and depth == 0:
                items.append("".join(current).strip())
                current = []
                prev = ch
                continue
        current.append(ch)
        prev = ch
    tail = "".join(current).strip()
    if tail:
        items.append(tail)
    return items


def load_strings(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    pairs = re.findall(r'\{\s*(StrID_[A-Za-z0-9_]+)\s*,\s*"([^"]*)"\s*\}', text)
    return {key: value for key, value in pairs}


def resolve_label(expr: str, strings: dict[str, str]) -> str:
    match = re.search(r"GetStringPtr\((StrID_[A-Za-z0-9_]+)\)", expr)
    if match:
        return strings.get(match.group(1), match.group(1))
    if expr.startswith('"') and expr.endswith('"'):
        return expr[1:-1]
    return expr


def resolve_choices(expr: str, strings: dict[str, str]) -> str | None:
    match = re.search(r"GetStringPtr\((StrID_[A-Za-z0-9_]+)\)", expr)
    if match:
        return strings.get(match.group(1), match.group(1))
    return None


def collapse_source(text: str) -> str:
    text = re.sub(r"//.*", "", text)
    return text


def extract_macros(plugin: str, source_path: Path, strings: dict[str, str]) -> list[ParamRow]:
    text = collapse_source(source_path.read_text(encoding="utf-8"))
    pattern = re.compile(r"PF_ADD_([A-Z0-9_]+)\s*\((.*?)\);", re.DOTALL)
    rows: list[ParamRow] = []
    for match in pattern.finditer(text):
        macro = match.group(1)
        args = split_top_level(match.group(2))
        if not args:
            continue
        label = resolve_label(args[0], strings)
        hard_min = hard_max = ui_min = ui_max = default = extra = None
        if macro == "CHECKBOX":
            default = args[2] if len(args) > 2 else None
        elif macro == "COLOR":
            default = f"[{', '.join(args[1:4])}]" if len(args) >= 4 else None
        elif macro == "POINT":
            default = f"[{', '.join(args[1:3])}]" if len(args) >= 3 else None
            extra = f"point-space={args[3]}" if len(args) > 3 else None
        elif macro == "POPUP":
            hard_min = "1"
            hard_max = args[1] if len(args) > 1 else None
            default = args[2] if len(args) > 2 else None
            choices = resolve_choices(args[3], strings) if len(args) > 3 else None
            extra = f"choices={choices}" if choices else None
        elif macro in {"SLIDER", "FLOAT_SLIDERX", "FIXED"}:
            if len(args) >= 6:
                hard_min, hard_max, ui_min, ui_max, default = args[1:6]
            if len(args) > 6:
                extra = ", ".join(args[6:-1])
        else:
            extra = ", ".join(args[1:-1]) if len(args) > 2 else None
        rows.append(
            ParamRow(
                plugin=plugin,
                label=label,
                macro=macro,
                default=default or "",
                hard_min=hard_min,
                hard_max=hard_max,
                ui_min=ui_min,
                ui_max=ui_max,
                extra=extra,
                source_file=str(source_path.relative_to(ROOT)),
            )
        )
    expanded: list[ParamRow] = []
    if plugin == "ColorKeep":
        for row in rows:
            expanded.append(row)
            if row.label == "Color":
                for i in range(2, 101):
                    expanded.append(clone_row(row, f"Color {i}"))
        return expanded
    if plugin == "OLMColorKey":
        indexed_templates: list[ParamRow] = []
        for row in rows:
            if row.label == "name":
                indexed_templates.append(row)
            else:
                expanded.append(row)
        indexed_bases = [
            "Color",
            "Threshold",
            "Threshold(R,H,L,Y,Y)",
            "Threshold(G,S,a,U,Cr)",
            "Threshold(B,V,b,V,Cb)",
            "Use Color",
            "Use Replace Color",
            "Replace Color",
        ]
        for color_index in range(1, 26):
            for group_index, base in enumerate(indexed_bases):
                template = indexed_templates[group_index]
                expanded.append(clone_row(template, f"{base} {color_index}"))
        return expanded
    if plugin == "OLMSmoother2":
        for row in rows:
            expanded.append(row)
            if row.label == "Gamma Color":
                for i in range(2, 6):
                    expanded.append(clone_row(row, f"Gamma Color {i}"))
        return expanded
    return rows


def build_report() -> dict[str, object]:
    plugins: list[dict[str, object]] = []
    for spec in PLUGIN_SPECS:
        strings = load_strings(ROOT / spec["strings"])
        params = extract_macros(spec["plugin"], ROOT / spec["source"], strings)
        plugins.append(
            {
                "plugin": spec["plugin"],
                "source": str(spec["source"]),
                "strings": str(spec["strings"]),
                "schema_status": "source-backed",
                "internal_behavior_status": spec["status"],
                "params": [row.__dict__ for row in params],
            }
        )
    return {
        "kind": "mac_plugin_param_schema",
        "generated_at": "2026-06-29",
        "scope": "UI parameter schema only; internal response curves and hidden branch rules are tracked separately.",
        "notes": [
            "This report fixes visible parameter defaults, ranges, and control types from source.",
            "It does not prove internal response curves, hidden branches, rounding, or writeback behavior.",
        ],
        "plugins": plugins,
    }


def write_outputs(report: dict[str, object]) -> tuple[Path, Path]:
    json_path = ROOT / "refs/reports/mac_plugin_param_schema_20260629.json"
    md_path = ROOT / "refs/reports/mac_plugin_param_schema_20260629.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Mac Plug-in Parameter Schema",
        "",
        "- Generated from `PF_ADD_*` definitions in the macOS plug-in sources.",
        "- Scope: UI schema only. This fixes defaults/ranges/types, not algorithm response curves.",
        "- Meaning: if we want to know the default value or allowed UI range, this file is authoritative.",
        "- Non-goal: this file does not prove that a parameter's internal effect strength matches Windows yet.",
        "",
    ]
    for plugin in report["plugins"]:
        lines.append(f"## {plugin['plugin']}")
        lines.append("")
        lines.append(f"- UI schema status: `{plugin['schema_status']}`")
        lines.append(f"- Internal behavior status: {plugin['internal_behavior_status']}")
        lines.append(f"- Source: `{plugin['source']}`")
        lines.append("")
        lines.append("| Param | Type | Default | Hard min | Hard max | UI min | UI max | Extra |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for row in plugin["params"]:
            lines.append(
                "| {label} | `{macro}` | `{default}` | `{hard_min}` | `{hard_max}` | `{ui_min}` | `{ui_max}` | `{extra}` |".format(
                    label=row["label"],
                    macro=row["macro"],
                    default=row["default"] or "",
                    hard_min=row["hard_min"] or "",
                    hard_max=row["hard_max"] or "",
                    ui_min=row["ui_min"] or "",
                    ui_max=row["ui_max"] or "",
                    extra=row["extra"] or "",
                )
            )
        lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    report = build_report()
    json_path, md_path = write_outputs(report)
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
