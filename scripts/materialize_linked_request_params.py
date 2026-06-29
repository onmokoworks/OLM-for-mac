#!/usr/bin/env python3
"""Materialize params_full for linked Windows reference requests."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUEST_DIR = ROOT / "refs" / "reference_requests"
REF_GLOB = ROOT.glob("refs/win_references/**/reference_manifest.json")


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


@dataclass
class RefParam:
    key: str
    name: str
    match_name: str | None
    property_index: int | None
    property_value_type: str | None
    value: Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "request_json",
        nargs="*",
        type=Path,
        help="Request JSON file(s) to rewrite. Defaults to all refs/reference_requests/*.json",
    )
    parser.add_argument("--write", action="store_true", help="Rewrite files in place.")
    parser.add_argument("--refresh", action="store_true", help="Replace existing params_full instead of skipping them.")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def normalize_plugin(name: str | None) -> str | None:
    if not name:
        return None
    if name.startswith("OLM") and " " not in name:
        return name
    return PLUGIN_NAME_ALIASES.get(name, name)


def canonical_manifest_key(plugin: str | None, param: dict[str, Any]) -> str | None:
    if param.get("property_value_type") == "NO_VALUE":
        return None
    path = [str(part).strip() for part in param.get("path", []) if part is not None]
    plugin = normalize_plugin(path[0]) if path else plugin
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
    if key == "Effect Opacity":
        return "Compositing Options/Effect Opacity"
    if key == "GPU Rendering":
        return "Compositing Options/GPU Rendering"
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
            "Brightness": "Brightness Gain",
            "Repeat Edge Pixels": "Repeat Border",
        },
    }
    return aliases.get(plugin, {}).get(key, key)


def merge_case_params(common: Any, case_params: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
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


def effect_plugin(effect_value: Any) -> str | None:
    if isinstance(effect_value, dict):
        return normalize_plugin(effect_value.get("name")) or normalize_plugin(effect_value.get("match_name"))
    if isinstance(effect_value, str):
        return normalize_plugin(effect_value)
    return None


def collect_reference_cases() -> dict[tuple[str, str], list[RefParam]]:
    out: dict[tuple[str, str], list[RefParam]] = {}
    for path in sorted(REF_GLOB):
        obj = load_json(path)
        for case in obj.get("cases", []):
            if not isinstance(case, dict):
                continue
            case_id = case.get("id")
            if not isinstance(case_id, str):
                continue
            for effect in case.get("effects", []):
                if not isinstance(effect, dict):
                    continue
                plugin = normalize_plugin(effect.get("name")) or normalize_plugin(effect.get("match_name"))
                if not plugin:
                    continue
                params: list[RefParam] = []
                for param in effect.get("params", []):
                    if not isinstance(param, dict):
                        continue
                    key = canonical_manifest_key(plugin, param)
                    if not key:
                        continue
                    params.append(
                        RefParam(
                            key=key,
                            name=str(param.get("name") or ""),
                            match_name=param.get("match_name"),
                            property_index=param.get("property_index"),
                            property_value_type=param.get("property_value_type"),
                            value=param.get("value"),
                        )
                    )
                out[(plugin, case_id)] = params
    return out


def materialize_case(
    case: dict[str, Any],
    plugin: str,
    common_params: Any,
    refs: dict[tuple[str, str], list[RefParam]],
    *,
    refresh: bool,
) -> tuple[bool, str]:
    if isinstance(case.get("params_full"), list) and case["params_full"] and not refresh:
        return False, "already-has-params_full"
    source_case_id = case.get("source_case_id") or derive_source_case_id(case.get("id"))
    if not source_case_id:
        return False, "unlinked"
    ref_params = refs.get((plugin, source_case_id))
    if not ref_params:
        return False, "missing-reference"
    merged = merge_case_params(common_params, case.get("params"))
    override_by_key = {canonical_request_key(plugin, key): value for key, value in merged.items()}
    ref_keys = {row.key for row in ref_params}
    unknown = sorted(key for key in override_by_key if key not in ref_keys and key not in IGNORED_CANONICAL_KEYS)
    if unknown:
        return False, f"unknown-keys:{','.join(unknown)}"

    case["params_full"] = [
        {
            "name": row.name,
            "match_name": row.match_name,
            "property_index": row.property_index,
            "property_value_type": row.property_value_type,
            "value": override_by_key.get(row.key, row.value),
        }
        for row in ref_params
    ]
    return True, f"materialized:{len(case['params_full'])}"


def iter_request_paths(args: argparse.Namespace) -> list[Path]:
    if args.request_json:
        out = []
        for path in args.request_json:
            path = path if path.is_absolute() else ROOT / path
            out.append(path)
        return out
    return sorted(REQUEST_DIR.glob("*.json"))


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    args = parse_args()
    refs = collect_reference_cases()
    changed_files = 0
    changed_cases = 0
    for path in iter_request_paths(args):
        obj = load_json(path)
        top_plugin = normalize_plugin(obj.get("plugin")) or effect_plugin(obj.get("effect"))
        common_params = obj.get("common_params")
        file_changed = False
        print(f"## {display_path(path)}")
        for case in obj.get("cases", []):
            if not isinstance(case, dict):
                continue
            plugin = normalize_plugin(case.get("plugin")) or effect_plugin(case.get("effect")) or top_plugin
            if not plugin:
                print(f"  - {case.get('id')}: skip no-plugin")
                continue
            changed, note = materialize_case(case, plugin, common_params, refs, refresh=args.refresh)
            if changed:
                file_changed = True
                changed_cases += 1
            print(f"  - {case.get('id')}: {note}")
        if file_changed and args.write:
            path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            changed_files += 1
        elif file_changed:
            changed_files += 1
    print(f"changed_files={changed_files}")
    print(f"changed_cases={changed_cases}")
    if not args.write:
        print("dry_run=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
