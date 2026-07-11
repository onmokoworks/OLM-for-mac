#!/usr/bin/env python3
"""Materialize one 32bpc reference spec as a Mac AE Render Queue request dir."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def find_case(manifest: dict[str, Any], case_id: str) -> dict[str, Any]:
    for case in manifest.get("cases", []):
        if isinstance(case, dict) and case.get("id") == case_id:
            return case
    suffixed = [
        case for case in manifest.get("cases", [])
        if isinstance(case, dict) and str(case.get("id", "")).endswith("__" + case_id)
    ]
    if len(suffixed) == 1:
        return suffixed[0]
    raise ValueError(f"source reference case not found: {case_id}")


def image_path(reference_dir: Path, frame: str) -> Path:
    for candidate in (reference_dir / frame, reference_dir / "png" / frame):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"input image not found for {frame!r} under {reference_dir}")


def params_with_effect_path(effect: dict[str, Any], rows: list[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item = copy.deepcopy(row)
        item["path_full"] = [
            {
                "name": effect["name"],
                "match_name": effect["match_name"],
                "property_index": 1,
            },
            {
                "name": item.get("name", ""),
                "match_name": item.get("match_name", ""),
                "property_index": item.get("property_index", 0),
            },
        ]
        result.append(item)
    return result


def materialize(spec_path: Path, source_reference: Path, output: Path, case_id: str) -> Path:
    spec = load(spec_path)
    if spec.get("scope", {}).get("bit_depth") != "32bpc":
        raise ValueError("spec is not a 32bpc request")
    requested = find_case(spec, case_id)
    source_case_id = requested.get("source_case_id")
    if not isinstance(source_case_id, str) or not source_case_id:
        raise ValueError(f"{case_id}: source_case_id is required")
    raw_params = requested.get("params_full")
    if not isinstance(raw_params, list) or not raw_params:
        raise ValueError(f"{case_id}: params_full is required")
    effect = requested.get("effect")
    if not isinstance(effect, dict) or not effect.get("name") or not effect.get("match_name"):
        raise ValueError(f"{case_id}: effect name/match_name is required")

    reference_manifest = load(source_reference / "reference_manifest.json")
    try:
        source_case = copy.deepcopy(find_case(reference_manifest, case_id))
    except ValueError:
        source_case = copy.deepcopy(find_case(reference_manifest, source_case_id))
    before = source_case.get("before_effects_frame")
    if not isinstance(before, str) or not before:
        raise ValueError(f"{source_case_id}: before_effects_frame is required")
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    (output / "input").mkdir(parents=True)

    source_case["id"] = case_id
    source_case["effects"] = [{
        "name": effect["name"],
        "match_name": effect["match_name"],
        "property_index": 1,
        "enabled": True,
        "active": True,
        "params": params_with_effect_path(effect, raw_params),
    }]
    # The source PNG may be smaller than the requested 32bpc comp. Preserve it
    # as an unscaled layer, but render inside the request's declared geometry.
    requested_comp = copy.deepcopy(reference_manifest.get("comp", {}))
    common_setup = spec.get("common_setup")
    if isinstance(common_setup, dict):
        for source_key, target_key in (("comp_width", "width"), ("comp_height", "height"), ("frame_rate", "frame_rate")):
            if common_setup.get(source_key) is not None:
                requested_comp[target_key] = common_setup[source_key]
    bridge_reference = {
        "schema": "olm_mac_ae_32bpc_bridge/v1",
        "kind": "olm_ae_32bpc_render_queue_request",
        "request_id": spec["request_id"],
        "project": {"bits_per_channel": 32, "renderer": "SOFTWARE"},
        "comp": requested_comp,
        "cases": [source_case],
    }
    render_set = next(
        (entry for entry in spec.get("render_sets", []) if isinstance(entry, dict) and entry.get("bits_per_channel") == 32),
        None,
    )
    if not isinstance(render_set, dict):
        raise ValueError("spec has no 32bpc render set")
    request_manifest = {
        "kind": "olm_ae_32bpc_render_queue_request",
        "request_id": spec["request_id"],
        "effect_name": effect["name"],
        "effect_match_name": effect["match_name"],
        "reference_manifest": "reference_manifest.json",
        "raw_32bpc_request": "raw_32bpc_request.json",
        "input_dir": "input",
        "render_set": render_set,
        "cases": [{
            "id": case_id,
            "before_effects_frame": before,
            "frame": case_id + ".exr",
            "source_case_id": source_case_id,
        }],
    }
    result_template = {
        "kind": "olm_ae_32bpc_render_queue_result",
        "request_id": spec["request_id"],
        "ae_version": "",
        "cases": [{
            "id": case_id,
            "render_set_id": render_set.get("id", ""),
            "output_format": "exr",
            "float_preserving": None,
            "artifact": "",
            "sha256": "",
            "channel_order": [],
            "color_space": "",
            "alpha_mode": "",
        }],
    }
    shutil.copy2(image_path(source_reference, before), output / "input" / before)
    (output / "request_manifest.json").write_text(json.dumps(request_manifest, indent=2) + "\n", encoding="utf-8")
    (output / "reference_manifest.json").write_text(json.dumps(bridge_reference, indent=2) + "\n", encoding="utf-8")
    (output / "raw_32bpc_request.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    (output / "AE_32BPC_RESULT.template.json").write_text(json.dumps(result_template, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--source-reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    args = parser.parse_args()
    output = materialize(args.spec.resolve(), args.source_reference.resolve(), args.output.resolve(), args.case_id)
    print(f"[OK] materialized 32bpc Mac AE bridge: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
