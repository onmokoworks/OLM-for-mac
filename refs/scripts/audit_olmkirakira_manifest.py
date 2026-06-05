#!/usr/bin/env python3
"""Summarize OLMKiraKira Windows reference cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_REFERENCE = (
    Path(__file__).resolve().parents[1]
    / "win_references"
    / "20260604_olm"
    / "OLMKiraKira"
)


def grouped_params(case: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for effect in case.get("effects", []):
        if effect.get("name") != "OLM Kira Kira" and effect.get("match_name") != "OLM OLM Kira Kira":
            continue
        for param in effect.get("params", []):
            if param.get("value") is None:
                continue
            name = param.get("name") or ""
            match = param.get("match_name") or ""
            key = name.lower().replace(" ", "_")
            # Names repeat for the ray groups; match IDs are stable.
            if match.endswith("-0003"):
                key = "vertical_length"
            elif match.endswith("-0004"):
                key = "horizontal_length"
            elif match.endswith("-0005"):
                key = "diagonal_length"
            elif match.endswith("-0026"):
                key = "diagonal2_length"
            elif match.endswith("-0006"):
                key = "highlight_radius"
            elif match.endswith("-0013"):
                key = "vertical_color"
            elif match.endswith("-0014"):
                key = "horizontal_color"
            elif match.endswith("-0015"):
                key = "diagonal_color"
            elif match.endswith("-0028"):
                key = "diagonal2_color"
            elif match.endswith("-0016"):
                key = "highlight_color"
            elif match.endswith("-0018"):
                key = "vertical_use_ramp"
            elif match.endswith("-0020"):
                key = "horizontal_use_ramp"
            elif match.endswith("-0022"):
                key = "diagonal_use_ramp"
            elif match.endswith("-0035"):
                key = "diagonal2_use_ramp"
            elif match.endswith("-0024"):
                key = "highlight_use_ramp"
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
        help="OLMKiraKira reference folder or reference_manifest.json",
    )
    args = parser.parse_args()

    manifest = args.reference
    if manifest.is_dir():
        manifest = manifest / "reference_manifest.json"

    data = json.loads(manifest.read_text())
    print(f"manifest={manifest}")
    print(f"cases={len(data.get('cases', []))}")
    print(
        "case,channel,blur_mode,merge_mode,approximated_input,"
        "brightness,strength_multiplier,fade_out,glow_opacity,source_opacity,"
        "vertical,horizontal,diagonal,diagonal2,highlight_radius,rotation,"
        "use_ramps"
    )

    for case in data.get("cases", []):
        p = grouped_params(case)
        use_ramps = "/".join(
            str(value(p, key, 0))
            for key in [
                "vertical_use_ramp",
                "horizontal_use_ramp",
                "diagonal_use_ramp",
                "diagonal2_use_ramp",
                "highlight_use_ramp",
            ]
        )
        row = [
            case["id"],
            value(p, "channel"),
            value(p, "blur_mode"),
            value(p, "merge_mode"),
            value(p, "approximated_input"),
            value(p, "brightness_gain"),
            value(p, "strength_multiplier"),
            value(p, "fade_out"),
            value(p, "glow_opacity"),
            value(p, "source_opacity"),
            value(p, "vertical_length"),
            value(p, "horizontal_length"),
            value(p, "diagonal_length"),
            value(p, "diagonal2_length"),
            value(p, "highlight_radius"),
            value(p, "glow_rotation"),
            use_ramps,
        ]
        print(",".join(str(x) for x in row))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
