#!/usr/bin/env python3
"""Build an 8bpc PNG AEXCompat oracle campaign for multiple images and sizes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image


GEOMETRY_RE = re.compile(r"^(?P<width>[1-9][0-9]*)x(?P<height>[1-9][0-9]*)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, action="append", required=True, help="Source image; repeatable.")
    parser.add_argument("--geometry", action="append", required=True, help="WIDTHxHEIGHT; repeatable.")
    parser.add_argument("--params-json", type=Path, required=True, help="JSON array of complete effect parameter objects.")
    parser.add_argument("--effect-name", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_geometry(value: str) -> tuple[int, int]:
    match = GEOMETRY_RE.fullmatch(value)
    if match is None:
        raise ValueError(f"invalid geometry {value!r}; expected WIDTHxHEIGHT")
    return int(match["width"]), int(match["height"])


def premultiply(source: Image.Image) -> Image.Image:
    rgba = np.asarray(source.convert("RGBA"), dtype=np.uint16)
    alpha = rgba[..., 3:4]
    rgb = (rgba[..., :3] * alpha + 127) // 255
    return Image.fromarray(np.concatenate((rgb, alpha), axis=2).astype(np.uint8), "RGBA")


def build_campaign(
    inputs: list[Path], geometries: list[tuple[int, int]], parameter_sets: list[list[dict]],
    effect_name: str, output_dir: Path,
) -> Path:
    if not parameter_sets or not all(isinstance(row, list) for row in parameter_sets):
        raise ValueError("params JSON must be a non-empty array of parameter arrays")
    (output_dir / "source").mkdir(parents=True, exist_ok=True)
    (output_dir / "input").mkdir(parents=True, exist_ok=True)
    cases: list[dict] = []
    source_inputs: list[dict] = []
    for input_index, input_path in enumerate(inputs):
        with Image.open(input_path) as opened:
            base = opened.convert("RGBA")
        for geometry_index, geometry in enumerate(geometries):
            resized = base.resize(geometry, Image.Resampling.LANCZOS)
            input_id = f"input_{input_index:03d}_g{geometry_index:03d}"
            source_name = f"{input_id}.png"
            before_name = f"{input_id}.png"
            source_path = output_dir / "source" / source_name
            before_path = output_dir / "input" / before_name
            resized.save(source_path)
            premultiply(resized).save(before_path)
            source_inputs.append({"id": input_id, "file": f"source/{source_name}", "sha256": sha256(source_path)})
            for params_index, params in enumerate(parameter_sets):
                cases.append({
                    "id": f"{input_id}_p{params_index:03d}",
                    "input_id": input_id,
                    "before_effects_frame": before_name,
                    "effects": [{"name": effect_name, "params": params}],
                })
    manifest = {
        "schema": 1,
        "kind": "aexcompat_oracle_campaign",
        "project": {"bits_per_channel": 8},
        "source_inputs": source_inputs,
        "cases": cases,
    }
    manifest_path = output_dir / "reference_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest_path


def main() -> int:
    args = parse_args()
    parameter_sets = json.loads(args.params_json.read_text(encoding="utf-8"))
    manifest = build_campaign(
        [path.resolve() for path in args.input],
        [parse_geometry(value) for value in args.geometry],
        parameter_sets,
        args.effect_name,
        args.output_dir.resolve(),
    )
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
