#!/usr/bin/env python3
"""Audit how fully Windows reference request files pin effect parameters."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST_DIR = ROOT / "refs/reference_requests"
REF_GLOB = ROOT.glob("refs/win_references/**/reference_manifest.json")
SCHEMA_PATH = ROOT / "refs/reports/mac_plugin_param_schema_20260629.json"
OUT_JSON = ROOT / "refs/reports/request_param_pinning_20260629.json"
OUT_MD = ROOT / "refs/reports/request_param_pinning_20260629.md"


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
    "ColorKeep": "ColorKeep",
}


IGNORED_CANONICAL_KEYS = {
    "",
    "Compositing Options/Effect Opacity",
    "Compositing Options/GPU Rendering",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_plugin(name: str | None) -> str | None:
    if not name:
        return None
    if name.startswith("OLM") and " " not in name:
        return name
    return PLUGIN_NAME_ALIASES.get(name, name)


def canonical_manifest_key(param: dict) -> str | None:
    if param.get("property_value_type") == "NO_VALUE":
        return None
    path = [str(part).strip() for part in param.get("path", []) if part is not None]
    plugin = normalize_plugin(path[0]) if path else None
    leaf = (param.get("name") or "").strip()
    property_index = param.get("property_index")
    if plugin == "OLMDirectionalBlur":
        if leaf == "Blur Strength":
            return {5: "Front Blur Strength", 10: "Back Blur Strength"}.get(property_index, leaf)
        if leaf == "Alpha Fade":
            return {6: "Front Alpha Fade", 11: "Back Alpha Fade"}.get(property_index, leaf)
        if leaf == "Sharp Tail":
            return {7: "Front Sharp Tail", 12: "Back Sharp Tail"}.get(property_index, leaf)
        if leaf in {"Front Blur Parameters", "Back Blur Parameters", "Noise Parameters"}:
            return None
    if plugin == "OLMRadialBlur":
        radial_by_index = {
            4: "Outer Strength",
            5: "Outer Offset Mode",
            6: "Outer Offset",
            7: "Outer Edge Fade",
            10: "Inner Strength",
            11: "Inner Offset Mode",
            12: "Inner Offset",
            13: "Inner Edge Fade",
            15: "Repeat Border",
            17: "Ratio",
            18: "Angle",
            20: "Quality",
            21: "Brightness Gain",
            22: "Size Variation",
            24: "Noise Variation",
            25: "Noise Type",
            26: "Noise Layer",
            27: "Seed",
            28: "Noise Offset",
            29: "Thickness",
        }
        if property_index in radial_by_index:
            return radial_by_index[property_index]
    if len(path) <= 1:
        key = leaf
    else:
        key = "/".join(path[1:])
    key = key.strip()
    if key in IGNORED_CANONICAL_KEYS:
        return None
    return key


def canonical_request_key(plugin: str, key: str) -> str:
    key = key.strip()
    aliases = {
        "OLMColorKey": {
            "Edge Thin Amount": "Edge Thin/Amount",
            "Edge Thin Distance Type": "Edge Thin/Distance Type",
            "Edge Blur Amount": "Edge Blur/Amount",
            "Edge Blur Distance Type": "Edge Blur/Distance Type",
            "Edge Blur Direction": "Edge Blur/Direction",
        },
        "OLMKiraKira": {
            "Strength": "Strength multiplier",
            "Strength Multiplier": "Strength multiplier",
            "Diagonal2 Length": "Diagonal 2 length",
            "Diagonal2 Color": "Diagonal Color2",
        },
        "OLMDirectionalBlur": {
            "Noise Offset": "Offset",
        },
        "OLMRadialBlur": {
            "Outer Blur/Strength": "Outer Strength",
            "Outer Blur/Offset Mode": "Outer Offset Mode",
            "Outer Blur/Offset": "Outer Offset",
            "Outer Blur/Edge Fade": "Outer Edge Fade",
            "Inner Blur/Strength": "Inner Strength",
            "Inner Blur/Offset Mode": "Inner Offset Mode",
            "Inner Blur/Offset": "Inner Offset",
            "Inner Blur/Edge Fade": "Inner Edge Fade",
            "Outer Edge Fade": "Outer Edge Fade",
            "Inner Edge Fade": "Inner Edge Fade",
            "Brightness": "Brightness Gain",
            "Repeat Edge Pixels": "Repeat Border",
            "Noise Offset": "Noise Offset",
        },
    }
    plugin_aliases = aliases.get(plugin, {})
    return plugin_aliases.get(key, key)


def parse_default_value(raw: object) -> object:
    if raw is None:
        return None
    if isinstance(raw, (int, float, list, bool)):
        return raw
    text = str(raw).strip()
    if text == "":
        return None
    if text == "FALSE":
        return 0
    if text == "TRUE":
        return 1
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        parts = [part.strip() for part in inner.split(",")]
        parsed = []
        for part in parts:
            try:
                parsed.append(float(part) if "." in part else int(part))
            except ValueError:
                parsed.append(part)
        return parsed
    try:
        return float(text) if "." in text else int(text)
    except ValueError:
        return text


def same_value(a: object, b: object) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-6
    return a == b


def build_default_index() -> dict[str, dict[str, object]]:
    schema = load_json(SCHEMA_PATH)
    out: dict[str, dict[str, object]] = {}
    for plugin in schema["plugins"]:
        name = plugin["plugin"]
        rows = plugin["params"]
        defaults: dict[str, object] = {}
        if name == "OLMRadialBlur":
            strength_seen = 0
            offset_mode_seen = 0
            offset_seen = 0
            edge_fade_seen = 0
            for row in rows:
                label = row["label"]
                if row["macro"] == "NULL":
                    continue
                key = label
                if label == "Strength":
                    strength_seen += 1
                    key = "Outer Strength" if strength_seen == 1 else "Inner Strength"
                elif label == "Offset Mode":
                    offset_mode_seen += 1
                    key = "Outer Offset Mode" if offset_mode_seen == 1 else "Inner Offset Mode"
                elif label == "Offset":
                    offset_seen += 1
                    key = {1: "Outer Offset", 2: "Inner Offset", 3: "Noise Offset"}.get(offset_seen, "Offset")
                elif label == "Edge Fade":
                    edge_fade_seen += 1
                    key = "Outer Edge Fade" if edge_fade_seen == 1 else "Inner Edge Fade"
                defaults[key] = parse_default_value(row["default"])
        else:
            for row in rows:
                if row["macro"] == "NULL":
                    continue
                defaults[row["label"]] = parse_default_value(row["default"])
        out[name] = defaults
    return out


def collect_reference_cases() -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    for path in sorted(REF_GLOB):
        obj = load_json(path)
        for case in obj.get("cases", []):
            for effect in case.get("effects", []):
                plugin = normalize_plugin(effect.get("name"))
                if not plugin:
                    continue
                param_map: dict[str, dict] = {}
                for param in effect.get("params", []):
                    key = canonical_manifest_key(param)
                    if not key:
                        continue
                    param_map[key] = param
                out[(plugin, case["id"])] = {
                    "manifest_path": str(path.relative_to(ROOT)),
                    "case_id": case["id"],
                    "plugin": plugin,
                    "param_keys": sorted(param_map),
                    "param_map": param_map,
                }
    return out


def merge_case_params(common: dict | None, case_params: dict | None) -> dict[str, object]:
    merged: dict[str, object] = {}
    if isinstance(common, dict):
        merged.update(common)
    if isinstance(case_params, dict):
        merged.update(case_params)
    return merged


def derive_source_case_id(case_id: str | None) -> str | None:
    if not case_id:
        return None
    match = re.search(r"(?:case_|existing_)(\d{4})", case_id)
    if not match:
        return None
    return f"case_{match.group(1)}"


def audit() -> dict:
    reference_cases = collect_reference_cases()
    default_index = build_default_index()
    results = []
    by_request = defaultdict(lambda: Counter())

    for path in sorted(REQUEST_DIR.glob("*.json")):
        obj = load_json(path)
        top_plugin = normalize_plugin(obj.get("plugin"))
        effect = obj.get("effect")
        if isinstance(effect, dict):
            top_plugin = normalize_plugin(effect.get("name")) or top_plugin
        elif isinstance(effect, str):
            top_plugin = normalize_plugin(effect) or top_plugin
        common_params = obj.get("common_params")

        for case in obj.get("cases", []):
            plugin = normalize_plugin(case.get("plugin")) or top_plugin
            case_effect = case.get("effect")
            if isinstance(case_effect, dict):
                plugin = normalize_plugin(case_effect.get("name")) or plugin
            elif isinstance(case_effect, str):
                plugin = normalize_plugin(case_effect) or plugin

            merged = merge_case_params(common_params, case.get("params"))
            request_keys = sorted(canonical_request_key(plugin or "", key) for key in merged)
            request_key_set = set(request_keys)
            has_params_full = isinstance(case.get("params_full"), list) and len(case.get("params_full")) > 0
            source_case_id = case.get("source_case_id") or derive_source_case_id(case.get("id"))
            ref = reference_cases.get((plugin or "", source_case_id)) if source_case_id else None

            if has_params_full:
                status = "fully-pinned"
                missing = []
                extra = []
                note = "params_full present"
            elif ref is None:
                status = "unlinked"
                missing = []
                extra = []
                note = "no linked source_case_id reference"
            else:
                ref_key_set = set(ref["param_keys"])
                missing = sorted(ref_key_set - request_key_set)
                extra = sorted(request_key_set - ref_key_set)
                if not missing:
                    status = "fully-pinned"
                    note = "request keys cover linked reference params"
                else:
                    status = "partially-pinned"
                    note = "request omits one or more linked reference params"

            default_matches = []
            nondefault_missing = []
            unknown_default_missing = []
            if ref and missing:
                defaults = default_index.get(plugin or "", {})
                for key in missing:
                    ref_value = ref["param_map"][key].get("value")
                    if key in defaults:
                        if same_value(ref_value, defaults[key]):
                            default_matches.append(key)
                        else:
                            nondefault_missing.append(key)
                    else:
                        unknown_default_missing.append(key)

            by_request[path.name][status] += 1
            results.append(
                {
                    "request_file": path.name,
                    "plugin": plugin,
                    "case_id": case.get("id"),
                    "source_case_id": source_case_id,
                    "status": status,
                    "request_param_count": len(request_keys),
                    "has_params_full": has_params_full,
                    "linked_reference_manifest": ref["manifest_path"] if ref else None,
                    "linked_reference_param_count": len(ref["param_keys"]) if ref else None,
                    "missing_against_reference": missing[:20],
                    "missing_count": len(missing),
                    "missing_equal_source_default": default_matches[:20],
                    "missing_equal_source_default_count": len(default_matches),
                    "missing_nondefault_against_source_default": nondefault_missing[:20],
                    "missing_nondefault_against_source_default_count": len(nondefault_missing),
                    "missing_unknown_default_compare": unknown_default_missing[:20],
                    "missing_unknown_default_compare_count": len(unknown_default_missing),
                    "extra_against_reference": extra[:20],
                    "extra_count": len(extra),
                    "note": note,
                }
            )

    summary = Counter(row["status"] for row in results)
    request_summaries = []
    for request_file, counts in sorted(by_request.items()):
        request_rows = [row for row in results if row["request_file"] == request_file]
        partial_examples = [
            f"{row['case_id']} missing {row['missing_count']} "
            f"(default-equal {row['missing_equal_source_default_count']}, "
            f"nondefault {row['missing_nondefault_against_source_default_count']})"
            for row in request_rows
            if row["status"] == "partially-pinned"
        ][:6]
        request_summaries.append(
            {
                "request_file": request_file,
                "counts": dict(counts),
                "partial_examples": partial_examples,
            }
        )

    return {
        "kind": "request_param_pinning_audit",
        "generated_at": "2026-06-29",
        "request_dir": str(REQUEST_DIR.relative_to(ROOT)),
        "reference_case_count": len(reference_cases),
        "summary": dict(summary),
        "requests": request_summaries,
        "cases": results,
    }


def write_report(report: dict) -> None:
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Request Parameter Pinning Audit",
        "",
        "- Purpose: decide whether a Windows rerender request can be replayed without guessing hidden defaults.",
        "- `fully-pinned`: either `params_full` is present, or request keys cover the linked Windows reference case's visible effect params.",
        "- `partially-pinned`: request omits one or more visible params from the linked Windows reference case, so replay may rely on defaults or operator memory.",
        "- `unlinked`: no `source_case_id`-based comparison was possible.",
        "- `default-equal`: omitted key exists in the Mac source-backed schema and the linked Windows reference value equals that source default.",
        "- `nondefault`: omitted key exists in the Mac source-backed schema but the linked Windows reference value does not equal that source default.",
        "",
        f"- Reference cases indexed: `{report['reference_case_count']}`",
        f"- Overall counts: `fully-pinned={report['summary'].get('fully-pinned', 0)}`, `partially-pinned={report['summary'].get('partially-pinned', 0)}`, `unlinked={report['summary'].get('unlinked', 0)}`",
        "",
    ]
    for request in report["requests"]:
        counts = request["counts"]
        lines.append(f"## {request['request_file']}")
        lines.append("")
        lines.append(
            f"- Counts: `fully-pinned={counts.get('fully-pinned', 0)}`, "
            f"`partially-pinned={counts.get('partially-pinned', 0)}`, "
            f"`unlinked={counts.get('unlinked', 0)}`"
        )
        if request["partial_examples"]:
            lines.append("- Partial examples:")
            for item in request["partial_examples"]:
                lines.append(f"  - `{item}`")
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
