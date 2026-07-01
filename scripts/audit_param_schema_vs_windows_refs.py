#!/usr/bin/env python3
"""Audit Mac source-backed UI schema against Windows reference/request parameter names."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "refs/reports/mac_plugin_param_schema_20260629.json"
OUT_JSON = ROOT / "refs/reports/param_schema_windows_ref_audit_20260629.json"
OUT_MD = ROOT / "refs/reports/param_schema_windows_ref_audit_20260629.md"


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
        if leaf in {"Use Ramp", "Highlight Color"}:
            return leaf, "direct"
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
        if leaf == "Sharp Tail" and property_index in {7, 12}:
            direct_tail = {
                7: "Front Sharp Tail",
                12: "Back Sharp Tail",
            }
            return direct_tail[property_index], "alias-ordinal-ui"
        if leaf == "Sharp Tail" and property_index in {8, 13}:
            return None, "ignored-ui-scaffold"
        if property_index in {5, 6, 7}:
            direct_front = {
                5: "Front Blur Strength",
                6: "Front Alpha Fade",
                7: "Front Sharp Tail",
            }
            return direct_front[property_index], "alias-ordinal-ui"
        if property_index in {10, 11, 12}:
            direct_back = {
                10: "Back Blur Strength",
                11: "Back Alpha Fade",
                12: "Back Sharp Tail",
            }
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
    if plugin == "OLMSmoother":
        if leaf == "Do Smooth Range":
            return None, "likely-semantic-alias"
    return leaf or None, "direct"


def normalize_request_param(plugin: str, key: str) -> tuple[str | None, str]:
    key = key.strip()
    if not key:
        return None, "ignored-ui-scaffold"
    if plugin == "OLMDistanceGradation" and key == "BG Color":
        return "BG Color", "direct"
    if plugin == "OLMKiraKira" and key == "Strength":
        return "Strength Multiplier", "alias-request-shortname"
    if plugin == "OLMRadialBlur":
        aliases = {
            "Outer Blur/Strength": "Strength",
            "Outer Blur/Offset Mode": "Offset Mode",
            "Outer Blur/Offset": "Offset",
            "Outer Blur/Edge Fade": "Edge Fade",
            "Inner Blur/Strength": "Inner Strength",
            "Inner Blur/Offset Mode": "Offset Mode",
            "Inner Blur/Offset": "Offset",
            "Inner Blur/Edge Fade": "Edge Fade",
            "Outer Edge Fade": "Edge Fade",
            "Inner Edge Fade": "Edge Fade",
        }
        if key in aliases:
            target = aliases[key]
            return target, "alias-request-grouped"
    if plugin == "OLMColorKey":
        aliases = {
            "Edge Thin Distance Type": "Distance Type",
            "Edge Blur Distance Type": "Distance Type",
            "Edge Blur Direction": "Direction",
        }
        if key in aliases:
            return aliases[key], "alias-request-expanded"
    return key, "direct"


def build_schema_index() -> dict[str, set[str]]:
    schema = load_json(SCHEMA_PATH)
    out: dict[str, set[str]] = {}
    for plugin in schema["plugins"]:
        out[plugin["plugin"]] = {param["label"] for param in plugin["params"]}
    return out


def audit() -> dict:
    schema_index = build_schema_index()
    plugin_rows: dict[str, dict] = {
        plugin: {
            "source_schema_param_count": len(params),
            "source_schema_params": sorted(params),
            "manifest_exact": Counter(),
            "manifest_alias": Counter(),
            "manifest_windows_only": Counter(),
            "manifest_unknown": Counter(),
            "request_exact": Counter(),
            "request_alias": Counter(),
            "request_windows_only": Counter(),
            "request_unknown": Counter(),
        }
        for plugin, params in schema_index.items()
    }

    manifest_paths = sorted(ROOT.glob("refs/win_references/**/reference_manifest.json"))
    request_paths = sorted((ROOT / "refs/reference_requests").glob("*.json"))

    for path in manifest_paths:
        obj = load_json(path)
        for case in obj.get("cases", []):
            for effect in case.get("effects", []):
                plugin = normalize_plugin(effect.get("name"))
                if plugin not in plugin_rows:
                    continue
                schema_params = schema_index[plugin]
                for param in effect.get("params", []):
                    raw_name = param.get("name", "")
                    normalized, reason = normalize_manifest_param(
                        plugin,
                        param.get("path", []),
                        raw_name,
                        param.get("property_index"),
                    )
                    if normalized is None:
                        target = plugin_rows[plugin]["manifest_windows_only" if "windows-only" in reason or "likely-semantic" in reason else "manifest_alias"]
                        target[raw_name or "(blank)"] += 1
                    elif normalized in schema_params:
                        target = plugin_rows[plugin]["manifest_exact" if reason == "direct" else "manifest_alias"]
                        target[normalized if reason == "direct" else f"{raw_name} -> {normalized}"] += 1
                    else:
                        plugin_rows[plugin]["manifest_unknown"][f"{raw_name} -> {normalized}"] += 1

    for path in request_paths:
        obj = load_json(path)
        top_level_plugin = normalize_plugin(obj.get("plugin"))
        top_level_effect = obj.get("effect")
        if isinstance(top_level_effect, dict):
            top_level_plugin = normalize_plugin(top_level_effect.get("name")) or top_level_plugin
        elif isinstance(top_level_effect, str):
            top_level_plugin = normalize_plugin(top_level_effect) or top_level_plugin
        for case in obj.get("cases", []):
            case_effect = case.get("effect")
            plugin = normalize_plugin(case.get("plugin"))
            if isinstance(case_effect, dict):
                plugin = normalize_plugin(case_effect.get("name")) or plugin
            elif isinstance(case_effect, str):
                plugin = normalize_plugin(case_effect) or plugin
            plugin = plugin or top_level_plugin
            if plugin not in plugin_rows:
                continue
            schema_params = schema_index[plugin]
            params = case.get("params_full") or case.get("params") or {}
            if not isinstance(params, dict):
                continue
            for raw_name in params:
                normalized, reason = normalize_request_param(plugin, raw_name)
                if normalized is None:
                    target = plugin_rows[plugin]["request_windows_only" if "windows-only" in reason else "request_alias"]
                    target[raw_name] += 1
                elif normalized in schema_params:
                    target = plugin_rows[plugin]["request_exact" if reason == "direct" else "request_alias"]
                    target[normalized if reason == "direct" else f"{raw_name} -> {normalized}"] += 1
                else:
                    plugin_rows[plugin]["request_unknown"][f"{raw_name} -> {normalized}"] += 1

    plugin_summaries = []
    for plugin, row in plugin_rows.items():
        plugin_summaries.append(
            {
                "plugin": plugin,
                "source_schema_param_count": row["source_schema_param_count"],
                "manifest_exact_unique": len(row["manifest_exact"]),
                "manifest_alias_unique": len(row["manifest_alias"]),
                "manifest_windows_only_unique": len(row["manifest_windows_only"]),
                "manifest_unknown_unique": len(row["manifest_unknown"]),
                "request_exact_unique": len(row["request_exact"]),
                "request_alias_unique": len(row["request_alias"]),
                "request_windows_only_unique": len(row["request_windows_only"]),
                "request_unknown_unique": len(row["request_unknown"]),
                "manifest_alias_examples": row["manifest_alias"].most_common(12),
                "manifest_windows_only_examples": row["manifest_windows_only"].most_common(12),
                "manifest_unknown_examples": row["manifest_unknown"].most_common(12),
                "request_alias_examples": row["request_alias"].most_common(12),
                "request_windows_only_examples": row["request_windows_only"].most_common(12),
                "request_unknown_examples": row["request_unknown"].most_common(12),
            }
        )
    return {
        "kind": "param_schema_windows_ref_audit",
        "generated_at": "2026-06-29",
        "source_schema": str(SCHEMA_PATH.relative_to(ROOT)),
        "manifest_count": len(manifest_paths),
        "request_count": len(request_paths),
        "plugins": plugin_summaries,
    }


def write_report(report: dict) -> None:
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Param Schema vs Windows References Audit",
        "",
        "- Purpose: separate UI-name drift from algorithm drift.",
        "- Source of truth for Mac UI schema: `refs/reports/mac_plugin_param_schema_20260629.json`.",
        "- This audit compares that schema against imported Windows `reference_manifest.json` files and `refs/reference_requests/*.json`.",
        "",
        "Legend:",
        "- `manifest_exact` / `request_exact`: same visible parameter name exists in the Mac source schema.",
        "- `alias`: name drift that can be normalized mechanically from group/path context.",
        "- `windows_only`: Windows manifests/requests mention a control that does not exist as a current Mac source-visible parameter.",
        "- `unknown`: still not mapped; investigate before treating the mismatch as algorithm-only.",
        "",
    ]
    for plugin in report["plugins"]:
        lines.append(f"## {plugin['plugin']}")
        lines.append("")
        lines.append(f"- Source schema params: `{plugin['source_schema_param_count']}`")
        lines.append(f"- Windows manifest exact/alias/windows-only/unknown: `{plugin['manifest_exact_unique']}` / `{plugin['manifest_alias_unique']}` / `{plugin['manifest_windows_only_unique']}` / `{plugin['manifest_unknown_unique']}`")
        lines.append(f"- Request exact/alias/windows-only/unknown: `{plugin['request_exact_unique']}` / `{plugin['request_alias_unique']}` / `{plugin['request_windows_only_unique']}` / `{plugin['request_unknown_unique']}`")
        for label, key in [
            ("Manifest alias examples", "manifest_alias_examples"),
            ("Manifest windows-only examples", "manifest_windows_only_examples"),
            ("Manifest unknown examples", "manifest_unknown_examples"),
            ("Request alias examples", "request_alias_examples"),
            ("Request windows-only examples", "request_windows_only_examples"),
            ("Request unknown examples", "request_unknown_examples"),
        ]:
            values = plugin[key]
            if not values:
                continue
            lines.append(f"- {label}:")
            for item, count in values[:8]:
                lines.append(f"  - `{item}` x{count}")
        lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = audit()
    write_report(report)
    print(OUT_JSON)
    print(OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
