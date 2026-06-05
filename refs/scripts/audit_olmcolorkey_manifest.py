#!/usr/bin/env python3
"""Summarize OLMColorKey Windows reference cases.

The raw AE property tree repeats generic names such as Amount and Distance Type
under Edge Thin / Edge Blur. This audit groups those values so unsupported
paths, especially Enable Replace, are visible without hand-reading the large
manifest.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_REFERENCE = (
    Path(__file__).resolve().parents[1]
    / "win_references"
    / "20260604_olm"
    / "OLMColorKey"
)


def grouped_params(case: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for effect in case.get("effects", []):
        if (
            effect.get("name") != "OLM Color Key"
            and effect.get("match_name") != "OLM Color Key"
        ):
            continue

        group = "root"
        for param in effect.get("params", []):
            name = param.get("name") or ""
            if name == "Threshold Parameters":
                group = "threshold"
                continue
            if name == "Edge Thin":
                group = "edge_thin"
                continue
            if name == "Edge Blur":
                group = "edge_blur"
                continue
            if name == "Key Colors":
                group = "key_colors"
                continue
            if name == "Replace Colors":
                group = "replace_colors"
                continue
            if param.get("value") is None:
                continue

            key = name.lower().replace(" ", "_")
            if group in {"edge_thin", "edge_blur"} and name in {"Amount", "Distance Type"}:
                key = f"{group}_{key}"
            elif group == "edge_blur" and name == "Direction":
                key = "edge_blur_direction"

            out[key] = param["value"]
    return out


def value(params: dict[str, Any], key: str, default: Any = None) -> Any:
    return params.get(key, default)


def enabled_indices(params: dict[str, Any], prefix: str, count: int = 25) -> str:
    indices = [str(i) for i in range(1, count + 1) if value(params, f"{prefix}_{i}", 0)]
    return "/".join(indices)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "reference",
        nargs="?",
        type=Path,
        default=DEFAULT_REFERENCE,
        help="OLMColorKey reference folder or reference_manifest.json",
    )
    args = parser.parse_args()

    manifest = args.reference
    if manifest.is_dir():
        manifest = manifest / "reference_manifest.json"

    data = json.loads(manifest.read_text())
    print(f"manifest={manifest}")
    print(f"cases={len(data.get('cases', []))}")
    print(
        "case,color_keep,threshold,color_space,premultiplied,"
        "force_lower_precision,per_color,per_component,number_of_colors,enable_replace,"
        "edge_thin_amount,edge_thin_distance_type,"
        "edge_blur_amount,edge_blur_distance_type,edge_blur_direction,"
        "enabled_key_colors,enabled_replace_colors"
    )

    for case in data.get("cases", []):
        p = grouped_params(case)
        row = [
            case["id"],
            value(p, "color_keep"),
            value(p, "threshold"),
            value(p, "color_space"),
            value(p, "premultiplied_color"),
            value(p, "force_lower_precision"),
            value(p, "per_color"),
            value(p, "per_component"),
            value(p, "number_of_colors"),
            value(p, "enable_replace"),
            value(p, "edge_thin_amount"),
            value(p, "edge_thin_distance_type"),
            value(p, "edge_blur_amount"),
            value(p, "edge_blur_distance_type"),
            value(p, "edge_blur_direction"),
            enabled_indices(p, "use_color"),
            enabled_indices(p, "use_replace_color"),
        ]
        print(",".join(str(x) for x in row))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
