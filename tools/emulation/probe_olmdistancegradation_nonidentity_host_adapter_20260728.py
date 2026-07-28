#!/usr/bin/env python3
"""Fail-closed Mac-only probe for DistanceGradation non-identity host staging.

This is a source-contract probe, not an AE-host model.  It records the world
descriptors that RenderBits receives and refuses to invent allocation, copy,
resize, or depth-conversion behavior when those descriptors are non-identity.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from dataclasses import asdict, dataclass


ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"


@dataclass(frozen=True)
class WorldDescriptor:
    width: int
    height: int
    rowbytes: int
    pixel_size: int
    origin_x: int = 0
    origin_y: int = 0


@dataclass(frozen=True)
class DownsampleDescriptor:
    x_num: int
    x_den: int
    y_num: int
    y_den: int


def _renderbits_body(source: str) -> str:
    marker = "RenderBits(PF_InData *in_data, PF_ParamDef *params[],"
    start = source.index(marker)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1:index]
    raise AssertionError("RenderBits body is unterminated")


def source_contract() -> dict[str, object]:
    body = _renderbits_body(SOURCE.read_text(encoding="utf-8"))
    forbidden_host_ops = {
        "allocation": (r"\bPF_NEW_WORLD\b", r"\bnew_world\b", r"\bPF_NewWorld\b"),
        "copy": (r"\bPF_COPY\b", r"\bcopy_world\b", r"\bPF_Copy\b"),
        "resize": (r"\bresize_world\b", r"\bPF_Resize\b", r"\bcvResize\b"),
        "conversion": (r"\bconvert_world\b", r"\bPF_Convert\b", r"\bcvConvertScale\b"),
    }
    observed = {
        kind: [pattern for pattern in patterns if re.search(pattern, body)]
        for kind, patterns in forbidden_host_ops.items()
    }
    assert "long w = output->width;" in body
    assert "long h = output->height;" in body
    assert "(char *)input->data + (size_t)y * input->rowbytes" in body
    assert "load_rgba_norm(&row[x]" in body
    assert all(not hits for hits in observed.values()), observed
    return {
        "fact": "RenderBits uses output dimensions to index both input and output",
        "host_operations_observed_in_renderbits": observed,
        "source": str(SOURCE.relative_to(ROOT)),
    }


def classify(
    source: WorldDescriptor,
    output: WorldDescriptor,
    downsample: DownsampleDescriptor,
) -> dict[str, object]:
    reasons: list[str] = []
    if (source.width, source.height) != (output.width, output.height):
        reasons.append("world_dimensions_differ")
    if source.pixel_size != output.pixel_size:
        reasons.append("pixel_depth_differ")
    if (source.origin_x, source.origin_y) != (output.origin_x, output.origin_y):
        reasons.append("world_origins_differ")
    if (downsample.x_num, downsample.x_den, downsample.y_num, downsample.y_den) != (1, 1, 1, 1):
        reasons.append("downsample_is_nonidentity")
    if source.rowbytes < source.width * source.pixel_size:
        reasons.append("source_rowbytes_undersized")
    if output.rowbytes < output.width * output.pixel_size:
        reasons.append("output_rowbytes_undersized")

    if reasons:
        return {
            "status": "unknown_host_behavior_rejected",
            "reasons": reasons,
            "operation_order": [],
            "allocation_count": 0,
            "copy_count": 0,
            "conversion_count": 0,
            "resize_count": 0,
        }
    return {
        "status": "identity_direct_renderbits_only",
        "reasons": [],
        "operation_order": ["RenderBits"],
        "allocation_count": 0,
        "copy_count": 0,
        "conversion_count": 0,
        "resize_count": 0,
    }


def run() -> dict[str, object]:
    contract = source_contract()
    fixtures = [
        (
            "identity_padded_pf8",
            WorldDescriptor(6, 4, 28, 4),
            WorldDescriptor(6, 4, 32, 4),
            DownsampleDescriptor(1, 1, 1, 1),
            "identity_direct_renderbits_only",
        ),
        (
            "half_size_pf8",
            WorldDescriptor(6, 4, 28, 4),
            WorldDescriptor(3, 2, 16, 4),
            DownsampleDescriptor(1, 2, 1, 2),
            "unknown_host_behavior_rejected",
        ),
        (
            "nonidentity_x_only_pf16",
            WorldDescriptor(8, 3, 72, 8),
            WorldDescriptor(4, 3, 40, 8),
            DownsampleDescriptor(1, 2, 1, 1),
            "unknown_host_behavior_rejected",
        ),
        (
            "depth_conversion_pf8_to_pf16",
            WorldDescriptor(5, 3, 24, 4),
            WorldDescriptor(5, 3, 48, 8),
            DownsampleDescriptor(1, 1, 1, 1),
            "unknown_host_behavior_rejected",
        ),
        (
            "origin_shift_pf32",
            WorldDescriptor(5, 3, 96, 16, 2, 1),
            WorldDescriptor(5, 3, 96, 16, 0, 0),
            DownsampleDescriptor(1, 1, 1, 1),
            "unknown_host_behavior_rejected",
        ),
    ]
    results = []
    for name, source, output, downsample, expected in fixtures:
        result = classify(source, output, downsample)
        assert result["status"] == expected
        if expected == "unknown_host_behavior_rejected":
            assert result["operation_order"] == []
            assert sum(result[key] for key in (
                "allocation_count", "copy_count", "conversion_count", "resize_count"
            )) == 0
        results.append({
            "name": name,
            "source_world": asdict(source),
            "output_world": asdict(output),
            "downsample": asdict(downsample),
            **result,
        })
    return {
        "scope": "Mac source only; no AE host, Windows AEX, or production mutation",
        "contract": contract,
        "fixtures": results,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), indent=2, sort_keys=True))
    except (AssertionError, OSError, ValueError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
