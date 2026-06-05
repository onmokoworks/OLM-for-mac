#!/usr/bin/env python3
"""Summarize OLMDirectionalBlur Windows reference cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_REFERENCE = (
    Path(__file__).resolve().parents[1]
    / "win_references"
    / "20260604_olm"
    / "OLMDirectionalBlur"
)


def grouped_params(case: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for effect in case.get("effects", []):
        if effect.get("name") != "OLM DirectionalBlur" and effect.get("match_name") != "OLM Directional Blur":
            continue
        group = "root"
        sharp_count = {"front": 0, "back": 0}
        for param in effect.get("params", []):
            name = param.get("name") or ""
            if name == "Front Blur Parameters":
                group = "front"
                continue
            if name == "Back Blur Parameters":
                group = "back"
                continue
            if name == "Noise Parameters":
                group = "noise"
                continue
            if param.get("value") is None:
                continue

            key = name.lower().replace(" ", "_")
            if group in {"front", "back"} and name in {"Blur Strength", "Alpha Fade"}:
                key = f"{group}_{key}"
            elif group in {"front", "back"} and name == "Sharp Tail":
                sharp_count[group] += 1
                key = f"{group}_sharp_tail_{sharp_count[group]}"
            elif group == "noise" and name == "Offset":
                key = "noise_offset"
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
        help="OLMDirectionalBlur reference folder or reference_manifest.json",
    )
    args = parser.parse_args()

    manifest = args.reference
    if manifest.is_dir():
        manifest = manifest / "reference_manifest.json"

    data = json.loads(manifest.read_text())
    print(f"manifest={manifest}")
    print(f"cases={len(data.get('cases', []))}")
    print(
        "case,angle,brightness,size_var,"
        "front_strength,front_alpha_fade,front_sharp_tail,"
        "back_strength,back_alpha_fade,back_sharp_tail,"
        "noise_var,noise_type,noise_layer,seed,noise_offset,thickness"
    )

    for case in data.get("cases", []):
        p = grouped_params(case)
        row = [
            case["id"],
            value(p, "angle"),
            value(p, "brightness_gain"),
            value(p, "size_variation"),
            value(p, "front_blur_strength"),
            value(p, "front_alpha_fade"),
            value(p, "front_sharp_tail_1"),
            value(p, "back_blur_strength"),
            value(p, "back_alpha_fade"),
            value(p, "back_sharp_tail_1"),
            value(p, "noise_variation"),
            value(p, "noise_type"),
            value(p, "noise_layer"),
            value(p, "seed"),
            value(p, "noise_offset"),
            value(p, "thickness"),
        ]
        print(",".join(str(x) for x in row))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
