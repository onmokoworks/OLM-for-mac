#!/usr/bin/env python3
"""Summarize OLMRadialBlur Windows reference cases.

The raw AE property tree has duplicate names under Outer Blur / Inner Blur.
This audit prints those groups separately so the first implementation slice can
be chosen without hand-reading the large manifest.
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
    / "OLMRadialBlur"
)


def grouped_params(case: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for effect in case.get("effects", []):
        group = "root"
        for param in effect.get("params", []):
            name = param.get("name") or ""
            if name == "Outer Blur":
                group = "outer"
                continue
            if name == "Inner Blur":
                group = "inner"
                continue
            if name == "Ellipse":
                group = "ellipse"
                continue
            if name == "Noise Parameters":
                group = "noise"
                continue
            if param.get("value") is None:
                continue

            key = name
            if group in {"outer", "inner"} and name in {
                "Strength",
                "Offset Mode",
                "Offset",
                "Edge Fade",
            }:
                key = f"{group}_{name.lower().replace(' ', '_')}"
            elif group == "noise" and name == "Offset":
                key = "noise_offset"
            elif name:
                key = name.lower().replace(" ", "_")
            if key:
                out[key] = param["value"]
    return out


def value(params: dict[str, Any], key: str, default: Any = None) -> Any:
    return params.get(key, default)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "reference",
        nargs="?",
        type=Path,
        default=DEFAULT_REFERENCE,
        help="OLMRadialBlur reference folder or reference_manifest.json",
    )
    args = parser.parse_args()

    manifest = args.reference
    if manifest.is_dir():
        manifest = manifest / "reference_manifest.json"

    data = json.loads(manifest.read_text(encoding="utf-8-sig"))
    print(f"manifest={manifest}")
    print(f"cases={len(data.get('cases', []))}")
    print(
        "case,type,outer_strength,outer_mode,outer_offset,"
        "outer_edge_fade,inner_strength,inner_mode,inner_offset,inner_edge_fade,"
        "repeat,ratio,angle,"
        "quality,size_var,noise_var,noise_type,seed"
    )

    for case in data.get("cases", []):
        p = grouped_params(case)
        row = [
            case["id"],
            value(p, "blur_type"),
            value(p, "outer_strength"),
            value(p, "outer_offset_mode"),
            value(p, "outer_offset"),
            value(p, "outer_edge_fade"),
            value(p, "inner_strength"),
            value(p, "inner_offset_mode"),
            value(p, "inner_offset"),
            value(p, "inner_edge_fade"),
            value(p, "repeat_border"),
            value(p, "ratio"),
            value(p, "angle"),
            value(p, "quality"),
            value(p, "size_variation"),
            value(p, "noise_variation"),
            value(p, "noise_type"),
            value(p, "seed"),
        ]
        print(",".join(str(x) for x in row))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
