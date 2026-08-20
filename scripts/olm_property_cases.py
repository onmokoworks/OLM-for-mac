#!/usr/bin/env python3
"""Deterministic property-style cases for OLM render generalization.

This module deliberately has no AE or plugin dependency.  Campaign runners can
consume its JSON cases in a hostless harness, AEXCompat, or live After Effects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA_VERSION = 1
PIXEL_BYTES = {8: 4, 16: 8, 32: 16}
RECIPES = ("constant", "impulse", "checker", "gradient", "alpha_edge", "random")


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    kind: str
    default: float | int
    minimum: float | int
    maximum: float | int
    match_name: str = ""

    def validate(self) -> None:
        if self.kind not in {"integer", "float", "checkbox", "popup"}:
            raise ValueError(f"unsupported parameter kind: {self.kind}")
        if self.minimum > self.default or self.default > self.maximum:
            raise ValueError(f"default outside range for {self.name}")


@dataclass(frozen=True)
class PropertyCase:
    case_id: str
    seed: int
    plugin: str
    width: int
    height: int
    depth: int
    input_rowbytes: int
    output_rowbytes: int
    input_padding: int
    output_padding: int
    recipe: str
    recipe_seed: int
    parameters: Mapping[str, float | int]

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


TOON_DILATE_PARAMETERS = (
    ParameterSpec(
        name="Search Radius",
        match_name="ADBE OLMToonDilate-0001",
        kind="float",
        default=13.0,
        minimum=0.0,
        maximum=100.0,
    ),
)


def _stable_seed(seed: int, *parts: object) -> int:
    encoded = "\0".join([str(seed), *(str(part) for part in parts)]).encode()
    return int.from_bytes(hashlib.sha256(encoded).digest()[:8], "big")


def geometry_cases(seed: int, count: int = 100) -> list[tuple[int, int]]:
    """Return unique, deterministic geometries with edge cases first."""
    if count < 1:
        raise ValueError("count must be positive")
    curated = [
        (1, 1), (1, 2), (2, 1), (2, 2), (3, 5), (5, 3), (7, 7),
        (11, 7), (16, 9), (17, 11), (31, 17), (32, 18), (63, 37),
        (64, 36), (127, 71), (320, 240), (640, 360), (720, 480),
        (1280, 720), (1920, 1080), (3840, 2160),
    ]
    result = list(dict.fromkeys(curated[:count]))
    rng = random.Random(_stable_seed(seed, "geometry"))
    # Bias toward small cases so 100-case hostless suites stay cheap, while the
    # curated list retains representative SD/HD/4K smoke geometries.
    while len(result) < count:
        mode = rng.randrange(4)
        if mode == 0:
            width, height = rng.randrange(1, 65), rng.randrange(1, 65)
        elif mode == 1:
            width, height = rng.randrange(1, 257), rng.randrange(1, 145)
        elif mode == 2:
            width = rng.randrange(1, 129) * 2 + 1
            height = rng.randrange(1, 73) * 2 + 1
        else:
            width = rng.choice((160, 240, 320, 480, 640, 960, 1280))
            height = max(1, round(width * rng.choice((9 / 16, 3 / 4, 1.0))))
        if (width, height) not in result:
            result.append((width, height))
    return result


def stride_cases(width: int, depth: int, seed: int) -> list[int]:
    """Return legal rowbytes covering tight, odd padding, and alignments."""
    try:
        active = width * PIXEL_BYTES[depth]
    except KeyError as exc:
        raise ValueError(f"unsupported depth: {depth}") from exc
    rng = random.Random(_stable_seed(seed, "stride", width, depth))
    values = [active, active + 1, active + PIXEL_BYTES[depth] - 1]
    for alignment in (16, 32, 64):
        values.append(math.ceil(active / alignment) * alignment)
        values.append(math.ceil((active + 1) / alignment) * alignment)
    values.append(active + rng.randrange(1, 2 * PIXEL_BYTES[depth] + 1))
    return sorted(set(values))


def parameter_values(spec: ParameterSpec, seed: int, random_count: int = 4) -> list[float | int]:
    """Boundary/default/interior samples, stable for a given seed and spec."""
    spec.validate()
    if spec.kind == "checkbox":
        return [0, 1]
    if spec.kind == "popup":
        return list(range(int(spec.minimum), int(spec.maximum) + 1))
    values: list[float | int] = [spec.minimum, spec.default, spec.maximum]
    span = spec.maximum - spec.minimum
    if span:
        values.extend((spec.minimum + span * 0.25, spec.minimum + span * 0.5, spec.minimum + span * 0.75))
    rng = random.Random(_stable_seed(seed, "parameter", spec.name, spec.match_name))
    for _ in range(random_count):
        if spec.kind == "integer":
            values.append(rng.randint(int(spec.minimum), int(spec.maximum)))
        else:
            values.append(rng.uniform(float(spec.minimum), float(spec.maximum)))
    if spec.kind == "integer":
        values = [int(round(value)) for value in values]
    return list(dict.fromkeys(values))


def generate_cases(
    plugin: str,
    parameter_specs: Sequence[ParameterSpec],
    *,
    seed: int,
    count: int = 100,
    depths: Sequence[int] = (8, 16, 32),
) -> list[PropertyCase]:
    """Generate a deterministic pairwise-ish campaign of exactly ``count`` cases."""
    if not plugin:
        raise ValueError("plugin must not be empty")
    geometries = geometry_cases(seed, count)
    value_tables = [parameter_values(spec, seed) for spec in parameter_specs]
    result = []
    for index, (width, height) in enumerate(geometries):
        depth = depths[index % len(depths)]
        strides = stride_cases(width, depth, seed + index)
        input_rowbytes = strides[index % len(strides)]
        output_rowbytes = strides[(index * 3 + 1) % len(strides)]
        params = {
            spec.match_name or spec.name: values[(index * (position + 1)) % len(values)]
            for position, (spec, values) in enumerate(zip(parameter_specs, value_tables))
        }
        recipe = RECIPES[index % len(RECIPES)]
        result.append(PropertyCase(
            case_id=f"{plugin.lower().replace(' ', '_')}__property_{index + 1:04d}",
            seed=seed, plugin=plugin, width=width, height=height, depth=depth,
            input_rowbytes=input_rowbytes, output_rowbytes=output_rowbytes,
            input_padding=input_rowbytes - width * PIXEL_BYTES[depth],
            output_padding=output_rowbytes - width * PIXEL_BYTES[depth],
            recipe=recipe, recipe_seed=_stable_seed(seed, "pixels", index), parameters=params,
        ))
    return result


def pixel_value(recipe: str, x: int, y: int, width: int, height: int, seed: int) -> tuple[float, float, float, float]:
    """Return deterministic straight RGBA values in [0, 1]."""
    if recipe not in RECIPES:
        raise ValueError(f"unsupported recipe: {recipe}")
    if recipe == "constant":
        return (0.125, 0.5, 0.875, 1.0)
    if recipe == "impulse":
        return (1.0, 0.25, 0.0, 1.0) if (x, y) == (width // 2, height // 2) else (0.0, 0.0, 0.0, 0.0)
    if recipe == "checker":
        value = float((x + y) & 1)
        return (value, 1.0 - value, value, 1.0)
    if recipe == "gradient":
        return (x / max(1, width - 1), y / max(1, height - 1), (x + y) / max(1, width + height - 2), 1.0)
    if recipe == "alpha_edge":
        alpha = 0.0 if x < width // 2 else (0.5 if x == width // 2 else 1.0)
        return (0.8, 0.2, 0.6, alpha)
    rng = random.Random(_stable_seed(seed, x, y))
    return (rng.random(), rng.random(), rng.random(), rng.random())


def manifest(plugin: str, seed: int, cases: Iterable[PropertyCase]) -> dict[str, Any]:
    rows = [case.to_json() for case in cases]
    return {"schema": "olm.property-campaign/1", "schema_version": SCHEMA_VERSION,
            "plugin": plugin, "seed": seed, "case_count": len(rows), "cases": rows}


def report(campaign: Mapping[str, Any], results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_id = {str(row["case_id"]): dict(row) for row in results}
    expected = [row["case_id"] for row in campaign["cases"]]
    missing = [case_id for case_id in expected if case_id not in by_id]
    failures = [row for row in by_id.values() if row.get("status") != "pass"]
    return {"schema": "olm.property-report/1", "schema_version": SCHEMA_VERSION,
            "plugin": campaign["plugin"], "seed": campaign["seed"],
            "case_count": len(expected), "result_count": len(by_id),
            "status": "pass" if not missing and not failures else "fail",
            "missing_case_ids": missing, "failure_count": len(failures),
            "results": [by_id[case_id] for case_id in expected if case_id in by_id]}


def write_campaign(output_dir: Path, campaign: Mapping[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    cases_dir = output_dir / "cases"
    cases_dir.mkdir(exist_ok=True)
    for row in campaign["cases"]:
        (cases_dir / f"{row['case_id']}.json").write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
    path = output_dir / "campaign_manifest.json"
    path.write_text(json.dumps(campaign, indent=2, sort_keys=True) + "\n")
    return path


def write_report(output_dir: Path, data: Mapping[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "campaign_report.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin", default="OLM Toon Dilate")
    parser.add_argument("--seed", type=int, default=0x0A1C0DE)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    specs = TOON_DILATE_PARAMETERS if args.plugin == "OLM Toon Dilate" else ()
    data = manifest(args.plugin, args.seed, generate_cases(args.plugin, specs, seed=args.seed, count=args.count))
    print(write_campaign(args.output_dir, data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
