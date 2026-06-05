#!/usr/bin/env python3
"""AE-free ColorKeep CLI.

Contract:
  colorkeep_cli.py --input input.png --params params.json --output output.png

Expected params examples:
  {"Enabled Color Num": 2, "Color 1": [255, 0, 0], "Color 2": [0, 0, 0]}
  {"colors": [[255, 0, 0], [0, 0, 0]]}
"""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def normalize_color(value):
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("#") and len(value) in (7, 9):
            return [int(value[i : i + 2], 16) for i in (1, 3, 5)]
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        rgb = []
        for channel in value[:3]:
            f = float(channel)
            if 0.0 <= f <= 1.0:
                f *= 255.0
            rgb.append(max(0, min(255, int(round(f)))))
        return rgb
    raise ValueError(f"unsupported color value: {value!r}")


def flatten_params(payload):
    params = payload.get("params", payload)
    if isinstance(params, dict) and "effects" in params:
        for effect in params.get("effects", []):
            if effect.get("name") == "ColorKeep":
                return {p.get("name"): p.get("value") for p in effect.get("params", [])}
    if isinstance(params, dict):
        return params
    return {}


def read_colors(params_path):
    with Path(params_path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    params = flatten_params(payload)

    if "colors" in params:
        return [normalize_color(c) for c in params["colors"]]

    count = int(float(params.get("Enabled Color Num", params.get("enabled_color_num", 0))))
    colors = []
    for i in range(1, count + 1):
        for key in (f"Color {i}", f"color_{i}", f"Color"):
            if key in params:
                colors.append(normalize_color(params[key]))
                break
    return colors


def render(image, colors):
    arr = np.asarray(image.convert("RGBA"), dtype=np.uint8).copy()
    if not colors:
        arr[..., 3] = 0
        return Image.fromarray(arr, "RGBA")

    rgb = arr[..., :3]
    keep = np.zeros(arr.shape[:2], dtype=bool)
    for color in colors:
        c = np.array(color, dtype=np.uint8)
        keep |= np.all(rgb == c, axis=-1)
    arr[..., 3] = np.where(keep, arr[..., 3], 0).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--params", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    colors = read_colors(args.params)
    output = render(Image.open(args.input), colors)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    output.save(out_path)
    print(f"wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
