#!/usr/bin/env python3
"""Audit returned Windows fresh-instance range metadata against the Mac source schema."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "refs/reports/mac_plugin_param_schema_20260629.json"


PLUGIN_NAME_ALIASES = {
    "OLM Blur": "OLMBlur",
    "OLM Color Key": "OLMColorKey",
    "OLM DirectionalBlur": "OLMDirectionalBlur",
    "OLM Kira Kira": "OLMKiraKira",
    "OLM RadialBlur": "OLMRadialBlur",
    "OLM Smoother": "OLMSmoother",
    "OLM Smoother v2": "OLMSmoother2",
    "OLM Toon Dilate": "OLMToonDilate",
    "Distance Gradation": "OLMDistanceGradation",
}

IGNORED_PARAM_NAMES = {
    "",
    "Effect Opacity",
    "GPU Rendering",
    "Threshold Parameters",
    "Front Blur Parameters",
    "Back Blur Parameters",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Returned Windows fresh range reference_manifest.json")
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/reports/windows_fresh_ranges_audit_20260629.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/reports/windows_fresh_ranges_audit_20260629.md")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_plugin(name: str | None) -> str | None:
    if not name:
        return None
    if name.startswith("OLM") and " " not in name:
        return name
    return PLUGIN_NAME_ALIASES.get(name, name)


def normalize_manifest_param(plugin: str, path_parts: list[str], leaf: str, property_index: int | None = None) -> tuple[str | None, str]:
    path_parts = [part.strip() for part in path_parts if part is not None]
    leaf = (leaf or "").strip()
    parent = path_parts[-2].strip() if len(path_parts) >= 2 else ""
    if leaf in IGNORED_PARAM_NAMES:
        return None, "ignored-ui-scaffold"
    if plugin == "OLMDistanceGradation" and leaf == "BG Color":
        return "BG Color", "alias-trimmed-whitespace"
    if plugin == "OLMKiraKira":
        aliases = {
            "Merge mode": "Merge Mode",
            "Strength multiplier": "Strength Multiplier",
            "Diagonal 2 length": "Diagonal2 Length",
            "Diagonal Color2": "Diagonal2 Color",
        }
        if leaf in aliases:
            return aliases[leaf], "alias-legacy-label"
        if leaf in {"Vertical Color Ramp", "Horizontal Color Ramp", "Diagonal Color Ramp", "Diagonal 2 Color Ramp", "Highlight Color Ramp", "Ramp"}:
            return None, "windows-only-legacy-ui"
    if plugin == "OLMRadialBlur":
        aliases = {
            ("Outer Blur", "Outer Blur"): "Outer Blur",
            ("Inner Blur", "Inner Blur"): "Inner Blur",
            ("Ellipse", "Ellipse"): "Ellipse",
            ("Noise Parameters", "Noise Parameters"): "Noise Parameters",
            ("Outer Blur", "Strength"): "Strength",
            ("Outer Blur", "Offset Mode"): "Offset Mode",
            ("Outer Blur", "Offset"): "Offset",
            ("Outer Blur", "Edge Fade"): "Edge Fade",
            ("Inner Blur", "Strength"): "Inner Strength",
            ("Inner Blur", "Offset Mode"): "Offset Mode",
            ("Inner Blur", "Offset"): "Offset",
            ("Inner Blur", "Edge Fade"): "Edge Fade",
            ("Noise Parameters", "Size Variation"): "Size Variation",
            ("Noise Parameters", "Noise Variation"): "Noise Variation",
            ("Noise Parameters", "Noise Type"): "Noise Type",
            ("Noise Parameters", "Noise Layer"): "Noise Layer",
            ("Noise Parameters", "Seed"): "Seed",
            ("Noise Parameters", "Offset"): "Offset",
            ("Noise Parameters", "Thickness"): "Thickness",
        }
        if (parent, leaf) in aliases:
            return aliases[(parent, leaf)], "alias-grouped-ui"
    if plugin == "OLMDirectionalBlur":
        aliases = {
            ("Front Blur Parameters", "Front Blur Parameters"): "Front Blur Parameters",
            ("Front Blur Parameters", "Blur Strength"): "Front Blur Strength",
            ("Front Blur Parameters", "Alpha Fade"): "Front Alpha Fade",
            ("Front Blur Parameters", "Sharp Tail"): "Front Sharp Tail",
            ("Back Blur Parameters", "Back Blur Parameters"): "Back Blur Parameters",
            ("Back Blur Parameters", "Blur Strength"): "Back Blur Strength",
            ("Back Blur Parameters", "Alpha Fade"): "Back Alpha Fade",
            ("Back Blur Parameters", "Sharp Tail"): "Back Sharp Tail",
            ("Noise Parameters", "Noise Parameters"): "Noise Parameters",
            ("Noise Parameters", "Noise Variation"): "Noise Variation",
            ("Noise Parameters", "Noise Type"): "Noise Type",
            ("Noise Parameters", "Noise Layer"): "Noise Layer",
            ("Noise Parameters", "Seed"): "Seed",
            ("Noise Parameters", "Offset"): "Offset",
            ("Noise Parameters", "Thickness"): "Thickness",
        }
        if (parent, leaf) in aliases:
            return aliases[(parent, leaf)], "alias-grouped-ui"
        if property_index in {5, 6, 7}:
            direct_front = {5: "Front Blur Strength", 6: "Front Alpha Fade", 7: "Front Sharp Tail"}
            return direct_front[property_index], "alias-ordinal-ui"
        if property_index in {10, 11, 12}:
            direct_back = {10: "Back Blur Strength", 11: "Back Alpha Fade", 12: "Back Sharp Tail"}
            return direct_back[property_index], "alias-ordinal-ui"
    if plugin == "OLMColorKey":
        aliases = {
            ("Edge Thin", "Amount"): "Edge Thin Amount",
            ("Edge Blur", "Amount"): "Edge Blur Amount",
            ("Edge Thin", "Distance Type"): "Distance Type",
            ("Edge Blur", "Distance Type"): "Distance Type",
        }
        if (parent, leaf) in aliases:
            return aliases[(parent, leaf)], "alias-grouped-ui"
    if plugin == "OLMSmoother" and leaf == "Do Smooth Range":
        return None, "likely-semantic-alias"
    return leaf or None, "direct"


def schema_index() -> dict[str, dict[str, dict]]:
    schema = load_json(SCHEMA_PATH)
    out: dict[str, dict[str, dict]] = {}
    for plugin in schema["plugins"]:
        out[plugin["plugin"]] = {param["label"]: param for param in plugin["params"]}
    return out


def parse_source_number(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def floats_equal(a: float | None, b: float | None, tol: float = 1e-6) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tol


def classify_range(window_min: float | None, window_max: float | None, source_min: float | None, source_max: float | None, raw_source_min: str | None, raw_source_max: str | None) -> str:
    if source_min is None and raw_source_min not in {None, ""}:
        return "source-symbolic"
    if source_max is None and raw_source_max not in {None, ""}:
        return "source-symbolic"
    if window_min is None and window_max is None:
        return "windows-no-range"
    if source_min is None and source_max is None:
        return "source-no-range"
    if floats_equal(window_min, source_min) and floats_equal(window_max, source_max):
        return "match"
    return "range-mismatch"


def audit(manifest_path: Path) -> dict:
    schema = schema_index()
    manifest = load_json(manifest_path)
    plugins: list[dict] = []
    for case in manifest.get("cases", []):
        effect = (case.get("effects") or [{}])[0]
        plugin = normalize_plugin(effect.get("name"))
        if plugin not in schema:
            continue
        params_by_label = schema[plugin]
        counts = Counter()
        mismatches: list[dict] = []
        for param in effect.get("params", []):
            normalized, reason = normalize_manifest_param(plugin, param.get("path", []), param.get("name", ""), param.get("property_index"))
            if normalized is None:
                counts["ignored-or-unmapped"] += 1
                continue
            source = params_by_label.get(normalized)
            if source is None:
                counts["windows-only-or-unknown"] += 1
                mismatches.append(
                    {
                        "status": "windows-only-or-unknown",
                        "param": param.get("name"),
                        "normalized": normalized,
                        "reason": reason,
                    }
                )
                continue
            rm = param.get("range_metadata") or {}
            status = classify_range(
                rm.get("minValue"),
                rm.get("maxValue"),
                parse_source_number(source.get("hard_min")),
                parse_source_number(source.get("hard_max")),
                source.get("hard_min"),
                source.get("hard_max"),
            )
            counts[status] += 1
            if status != "match":
                mismatches.append(
                    {
                        "status": status,
                        "param": param.get("name"),
                        "normalized": normalized,
                        "reason": reason,
                        "windows_min": rm.get("minValue"),
                        "windows_max": rm.get("maxValue"),
                        "source_hard_min": source.get("hard_min"),
                        "source_hard_max": source.get("hard_max"),
                        "source_ui_min": source.get("ui_min"),
                        "source_ui_max": source.get("ui_max"),
                    }
                )
        plugins.append(
            {
                "plugin": plugin,
                "case_id": case.get("id"),
                "counts": dict(counts),
                "mismatches": mismatches,
            }
        )
    return {
        "kind": "windows_fresh_ranges_audit",
        "manifest": str(manifest_path),
        "source_schema": str(SCHEMA_PATH),
        "plugins": plugins,
    }


def write_report(report: dict, out_json: Path, out_md: Path) -> None:
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Windows Fresh Ranges Audit",
        "",
        f"- Manifest: `{report['manifest']}`",
        f"- Source schema: `{report['source_schema']}`",
        "- Purpose: compare Windows fresh-instance `range_metadata` against current Mac source-backed hard min/max.",
        "- `match` means Windows `minValue/maxValue` numerically matched Mac `hard_min/hard_max`.",
        "- `source-symbolic` means the Mac schema still uses a symbolic source expression that needs human interpretation.",
        "",
    ]
    for row in report["plugins"]:
        lines.append(f"## {row['plugin']}")
        lines.append("")
        lines.append(f"- Case: `{row['case_id']}`")
        lines.append(f"- Counts: `{json.dumps(row['counts'], ensure_ascii=False, sort_keys=True)}`")
        sample = row["mismatches"][:12]
        if sample:
            lines.append("- Non-match examples:")
            for item in sample:
                lines.append(
                    f"  - `{item['param']} -> {item['normalized']}` `{item['status']}` "
                    f"(Windows `{item.get('windows_min')}..{item.get('windows_max')}`, "
                    f"Mac hard `{item.get('source_hard_min')}..{item.get('source_hard_max')}`)"
                )
        lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    report = audit(args.manifest.resolve())
    write_report(report, args.output_json.resolve(), args.output_md.resolve())
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
