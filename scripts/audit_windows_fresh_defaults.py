#!/usr/bin/env python3
"""Audit returned Windows fresh-instance defaults against the Mac source schema."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from audit_param_schema_vs_windows_refs import (
    SCHEMA_PATH,
    normalize_manifest_param,
    normalize_plugin,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_JSON = ROOT / "refs/reports/windows_fresh_defaults_audit_latest.json"
DEFAULT_OUT_MD = ROOT / "refs/reports/windows_fresh_defaults_audit_latest.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        type=Path,
        help="Returned Windows reference_manifest.json from olm_fresh_instance_defaults_20260629.",
    )
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_schema_index() -> dict[str, dict[str, dict[str, Any]]]:
    schema = load_json(SCHEMA_PATH)
    by_plugin: dict[str, dict[str, dict[str, Any]]] = {}
    for plugin in schema["plugins"]:
        params: dict[str, dict[str, Any]] = {}
        for param in plugin["params"]:
            params[param["label"]] = param
        by_plugin[plugin["plugin"]] = params
    return by_plugin


def build_schema_rows() -> dict[str, list[dict[str, Any]]]:
    schema = load_json(SCHEMA_PATH)
    return {plugin["plugin"]: list(plugin["params"]) for plugin in schema["plugins"]}


def resolve_source_row(
    plugin: str,
    normalized: str,
    property_index: int | None,
    params_by_label: dict[str, dict[str, Any]],
    params_in_order: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if plugin == "OLMRadialBlur" and normalized in {"Offset", "Offset Mode"} and property_index is not None:
        radial_ordinals = {
            ("Offset Mode", 5): 4,
            ("Offset", 6): 5,
            ("Offset Mode", 11): 10,
            ("Offset", 12): 11,
            ("Offset", 28): 27,
        }
        source_idx = radial_ordinals.get((normalized, property_index))
        if source_idx is not None and source_idx < len(params_in_order):
            return params_in_order[source_idx]
    if plugin == "OLMDirectionalBlur" and normalized in {"Front Sharp Tail", "Back Sharp Tail"} and property_index is not None:
        directional_ordinals = {
            ("Front Sharp Tail", 7): 6,
            ("Back Sharp Tail", 12): 11,
            ("Offset", 19): 18,
        }
        source_idx = directional_ordinals.get((normalized, property_index))
        if source_idx is not None and source_idx < len(params_in_order):
            return params_in_order[source_idx]
    return params_by_label.get(normalized)


def parse_source_default(raw: str) -> Any:
    value = (raw or "").strip()
    if not value:
        return None
    if value == "TRUE":
        return 1
    if value == "FALSE":
        return 0
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        items = [item.strip() for item in inner.split(",")]
        parsed = []
        for item in items:
            try:
                parsed.append(int(item, 0))
                continue
            except Exception:
                pass
            try:
                parsed.append(float(item))
                continue
            except Exception:
                parsed.append(item)
        return parsed
    try:
        return int(value, 0)
    except Exception:
        pass
    try:
        return float(value)
    except Exception:
        return value


def normalize_windows_value(value: Any) -> Any:
    if isinstance(value, list):
        normalized = []
        for item in value:
            if isinstance(item, float):
                normalized.append(round(item, 6))
            else:
                normalized.append(item)
        return normalized
    if isinstance(value, float):
        return round(value, 6)
    return value


def compare_defaults(source_default: Any, windows_value: Any) -> str:
    if source_default is None:
        return "source-empty"
    if isinstance(source_default, str):
        return "source-symbolic"
    if isinstance(source_default, list) and isinstance(windows_value, list):
        if (
            len(source_default) == 3
            and len(windows_value) == 4
            and all(isinstance(item, (int, float)) for item in source_default)
            and all(isinstance(item, (int, float)) for item in windows_value)
        ):
            normalized = [round(float(item) / 255.0, 6) for item in source_default]
            if normalized == [round(float(item), 6) for item in windows_value[:3]] and round(float(windows_value[3]), 6) == 1.0:
                return "match-color-8bit-vs-float"
        return "match" if source_default == windows_value else "mismatch"
    return "match" if source_default == windows_value else "mismatch"


def audit_manifest(manifest_path: Path) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    schema_index = build_schema_index()
    schema_rows = build_schema_rows()
    by_plugin: dict[str, dict[str, Any]] = {}

    for case in manifest.get("cases", []):
        case_id = case.get("id")
        for effect in case.get("effects", []):
            plugin = normalize_plugin(effect.get("name"))
            if not plugin or plugin not in schema_index:
                continue
            entry = by_plugin.setdefault(
                plugin,
                {
                    "cases": [],
                    "params": defaultdict(list),
                    "source_param_count": len(schema_index[plugin]),
                },
            )
            entry["cases"].append(case_id)
            for param in effect.get("params", []):
                raw_name = param.get("name", "")
                normalized, reason = normalize_manifest_param(
                    plugin,
                    param.get("path", []),
                    raw_name,
                    param.get("property_index"),
                )
                if normalized is None:
                    continue
                source_row = resolve_source_row(
                    plugin,
                    normalized,
                    param.get("property_index"),
                    schema_index[plugin],
                    schema_rows[plugin],
                )
                windows_value = normalize_windows_value(param.get("value"))
                record = {
                    "case_id": case_id,
                    "raw_name": raw_name,
                    "normalized_name": normalized,
                    "normalization_reason": reason,
                    "property_index": param.get("property_index"),
                    "windows_value": windows_value,
                    "source_default_raw": source_row["default"] if source_row else None,
                    "source_default": parse_source_default(source_row["default"]) if source_row else None,
                    "macro": source_row["macro"] if source_row else None,
                }
                if source_row is None:
                    record["compare_status"] = "windows-only"
                else:
                    record["compare_status"] = compare_defaults(record["source_default"], windows_value)
                entry["params"][normalized].append(record)

    plugins = []
    for plugin, entry in sorted(by_plugin.items()):
        source_labels = set(schema_index[plugin].keys())
        windows_labels = set(entry["params"].keys())
        compare_counts = defaultdict(int)
        mismatches = []
        symbolic = []
        windows_only = []
        for label, rows in sorted(entry["params"].items()):
            first = rows[0]
            compare_counts[first["compare_status"]] += 1
            if first["compare_status"] == "mismatch":
                mismatches.append(first)
            elif first["compare_status"] == "source-symbolic":
                symbolic.append(first)
            elif first["compare_status"] == "windows-only":
                windows_only.append(first)
        source_only = sorted(source_labels - windows_labels)
        plugins.append(
            {
                "plugin": plugin,
                "case_ids": sorted({case_id for case_id in entry["cases"] if case_id}),
                "source_param_count": entry["source_param_count"],
                "windows_param_count": len(windows_labels),
                "compare_counts": dict(compare_counts),
                "mismatch_examples": mismatches[:20],
                "symbolic_examples": symbolic[:20],
                "windows_only_examples": windows_only[:20],
                "source_only_examples": source_only[:20],
            }
        )

    return {
        "kind": "windows_fresh_defaults_audit",
        "manifest": str(manifest_path),
        "schema": str(SCHEMA_PATH),
        "plugins": plugins,
    }


def write_report(report: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Windows Fresh Defaults Audit",
        "",
        f"- Manifest: `{report['manifest']}`",
        f"- Source schema: `{report['schema']}`",
        "- Purpose: compare Windows AEX cold-start defaults against the current Mac source-backed UI schema.",
        "- `match-color-8bit-vs-float` means a source default like `[255,255,255]` matched a Windows AE manifest color value like `[1,1,1,1]`.",
        "- `source-symbolic` means the source default is a symbolic constant (`SMOOTHER_V2`, `GAMMA_NONE`, etc.) and should be checked manually.",
        "",
    ]
    for plugin in report["plugins"]:
        counts = plugin["compare_counts"]
        lines.extend(
            [
                f"## {plugin['plugin']}",
                "",
                f"- Cases: `{', '.join(plugin['case_ids'])}`",
                f"- Windows params seen: `{plugin['windows_param_count']}` / source params: `{plugin['source_param_count']}`",
                f"- Compare counts: `{json.dumps(counts, ensure_ascii=False, sort_keys=True)}`",
            ]
        )
        if plugin["mismatch_examples"]:
            lines.append("- Mismatch examples:")
            for row in plugin["mismatch_examples"][:8]:
                lines.append(
                    f"  - `{row['normalized_name']}`: Windows `{row['windows_value']}` vs source default `{row['source_default_raw']}`"
                )
        if plugin["symbolic_examples"]:
            lines.append("- Symbolic-source examples:")
            for row in plugin["symbolic_examples"][:8]:
                lines.append(
                    f"  - `{row['normalized_name']}`: Windows `{row['windows_value']}` vs source symbolic `{row['source_default_raw']}`"
                )
        if plugin["windows_only_examples"]:
            lines.append("- Windows-only examples:")
            for row in plugin["windows_only_examples"][:8]:
                lines.append(
                    f"  - `{row['raw_name']}` normalized as `{row['normalized_name']}` but missing from source schema"
                )
        if plugin["source_only_examples"]:
            lines.append("- Source-only examples:")
            for label in plugin["source_only_examples"][:8]:
                lines.append(f"  - `{label}`")
        lines.append("")
    output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    report = audit_manifest(args.manifest.resolve())
    write_report(report, args.output_json, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
