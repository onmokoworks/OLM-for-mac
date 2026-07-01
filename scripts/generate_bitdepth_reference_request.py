#!/usr/bin/env python3
"""Generate a Windows reference request for next bit-depth conformance slices."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "bit_depth_expansion_plan_20260625" / "bit_depth_plan.json",
    )
    parser.add_argument(
        "--request-id",
        default=None,
        help="request_id to write into the generated request JSON.",
    )
    parser.add_argument(
        "--bit-depth",
        choices=("16bpc", "32bpc"),
        default="16bpc",
        help="Generate a 16bpc conformance request or a 32bpc float-output probe request.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--preview-dir",
        type=Path,
        default=None,
        help=(
            "Optional report directory to populate with request_preview.json and README.md "
            "for the generated request."
        ),
    )
    parser.add_argument(
        "--plugin",
        action="append",
        default=[],
        help="Restrict the request to one or more plug-in names from the bit-depth plan.",
    )
    parser.add_argument(
        "--feature",
        action="append",
        default=[],
        help="Restrict the request to one or more feature names from the bit-depth plan.",
    )
    return parser.parse_args()


def default_request_id(bit_depth: str) -> str:
    if bit_depth == "32bpc":
        return "olm_bitdepth_32bpc_float_output_probe_YYYYMMDD"
    return "olm_bitdepth_16bpc_normalized_exact_20260625"


def default_output(bit_depth: str, request_id: str) -> Path:
    if bit_depth == "32bpc":
        return ROOT / "refs" / "reference_requests" / f"{request_id}.json"
    return ROOT / "refs" / "reference_requests" / "olm_bitdepth_16bpc_normalized_exact_20260625.json"


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def param_map(effect: dict[str, Any]) -> dict[str, Any]:
    params = {}
    for param in effect.get("params", []):
        if not isinstance(param, dict):
            continue
        name = param.get("name")
        if not isinstance(name, str) or not name:
            continue
        if param.get("property_value_type") == "NO_VALUE":
            continue
        params[name] = param.get("value")
    return params


def param_records(effect: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for param in effect.get("params", []):
        if not isinstance(param, dict):
            continue
        if param.get("property_value_type") == "NO_VALUE":
            continue
        records.append(
            {
                "name": param.get("name"),
                "match_name": param.get("match_name"),
                "property_index": param.get("property_index"),
                "property_value_type": param.get("property_value_type"),
                "value": param.get("value"),
            }
        )
    return records


def manifest_cases(feature: dict[str, Any]) -> dict[str, dict[str, Any]]:
    manifest = read_json(resolve(feature["normalized_ref_dir"]) / "reference_manifest.json")
    cases = {}
    for row in manifest.get("cases", []):
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            cases[row["id"]] = row
    return cases


def effect_for_case(case: dict[str, Any]) -> dict[str, Any]:
    effects = [row for row in case.get("effects", []) if isinstance(row, dict)]
    if len(effects) != 1:
        raise ValueError(f"expected exactly one effect for {case.get('id')}, got {len(effects)}")
    return effects[0]


def input_id_for(feature_name: str, case_id: str) -> str:
    safe_feature = feature_name.lower().replace(" ", "_")
    return f"{safe_feature}_{case_id}_source"


def default_preview_title(bit_depth: str, plugin_filter: list[str], feature_filter: list[str]) -> str:
    if bit_depth != "32bpc":
        return "Bit-Depth Request Preview"
    if len(plugin_filter) == 1 and not feature_filter:
        return f"32bpc {plugin_filter[0]} Probe Preview"
    if len(feature_filter) == 1:
        return f"32bpc {feature_filter[0]} Probe Preview"
    return "32bpc Float-Output Probe Preview"


def preview_readme(
    request: dict[str, Any],
    *,
    bit_depth: str,
    plugin_filter: list[str],
    feature_filter: list[str],
    command: str,
) -> str:
    cases = request["cases"]
    plugins = sorted({str(row["plugin"]) for row in cases})
    case_ids = sorted(str(row["source_case_id"]) for row in cases)
    title = default_preview_title(bit_depth, plugin_filter, feature_filter)
    scope_line = ", ".join(plugin_filter or feature_filter or plugins)
    lines = [
        f"# {title}",
        "",
        f"This preview captures the next Windows AE `{bit_depth}` float-output probe request for `{scope_line}`.",
        "",
        "- Request preview: `request_preview.json`",
        f"- Scope: `{scope_line}`",
        f"- Cases: `{len(cases)}` total (`{case_ids[0]}..{case_ids[-1]}`)",
        f"- Renderer target: Windows AE `{request['render_sets'][0]['project_gpu_accel_type.current_name']}` only",
        "- Output requirement: prefer EXR or raw float RGBA samples; PNG-only returns stay probe-only",
        "- Completion note: this is not `AE exact` evidence until the return preserves float samples and a 32bpc comparator policy is fixed.",
        "",
        "Regenerate from the repo root with:",
        "",
        "```sh",
        command,
        "```",
        "",
        "When the Windows return arrives, import it with `scripts/intake_olm_return.py ... --quick` and keep the result labeled as probe-only unless the payload is float-preserving.",
    ]
    return "\n".join(lines) + "\n"


def build_request(args: argparse.Namespace) -> dict[str, Any]:
    plan = read_json(args.plan_json)
    plugin_filter = {item for item in args.plugin if item}
    feature_filter = {item for item in args.feature if item}
    request_id = args.request_id or default_request_id(args.bit_depth)
    bits_per_channel = 32 if args.bit_depth == "32bpc" else 16
    render_set_id = f"software_{args.bit_depth}"
    if args.bit_depth == "32bpc":
        case_reason = (
            "32bpc float-output probe for a normalized 8bpc Software exact case. "
            "This is not AE exact evidence unless the return includes float-preserving output."
        )
        why = [
            "The listed feature groups are normalized 8bpc Windows Software exact and need 32bpc output-format probing before 32bpc exactness can be claimed.",
            "This request asks the Windows helper to render a 32bpc project and return float-preserving output if available, preferably EXR or raw float samples.",
            "PNG output from this request is only a smoke/probe artifact and must not be used as 32bpc completion evidence.",
        ]
        manifest_requirements = [
            "AE version",
            "project_gpu_accel_type.current_name and raw value",
            "project bit depth / bits per channel",
            "project color management settings",
            "before_effects_frame PNG or float-preserving input snapshot for every case",
            "effect output in a float-preserving format when possible, such as EXR or raw float RGBA samples",
            "if only PNG output is possible, record output_format=png and float_preserving=false",
            "all effect property names, match_names, indices, values, enabled/active state",
        ]
        mac_follow_up = [
            "Import with scripts/intake_olm_return.py path/to/returned_reference.zip --quick.",
            "Do not claim 32bpc exact unless the return preserves float samples and a 32bpc comparator verifies exact float equality or a documented exception profile.",
        ]
        stop_lines = [
            "Do not render CUDA/GPU as the conformance target for this request.",
            "Do not use PNG-only 32bpc returns as AE exact evidence.",
            "Do not mix legacy 20260604/20260605 drift references into this bit-depth batch.",
        ]
    else:
        case_reason = (
            "16bpc expansion of a normalized 8bpc Software exact case. "
            "Do not use this to retune 8bpc legacy drift."
        )
        why = [
            "The listed feature groups are normalized 8bpc Windows Software exact and need the next declared bit-depth proof.",
            "This request deliberately starts with 16bpc only; 32bpc waits until the float comparison policy is fixed.",
            "Legacy 8bpc drift and AE-free CLI residuals are not tuning targets for this request.",
        ]
        manifest_requirements = [
            "AE version",
            "project_gpu_accel_type.current_name and raw value",
            "project bit depth / bits per channel",
            "project color management settings",
            "before_effects_frame PNG for every case",
            "effect output image for every case, preserving 16bpc data if the runner can export it",
            "all effect property names, match_names, indices, values, enabled/active state",
        ]
        mac_follow_up = [
            "Import with scripts/intake_olm_return.py path/to/returned_reference.zip --quick.",
            "Do not claim 16bpc exact until a 16bpc-aware comparator verifies zero diff.",
        ]
        stop_lines = [
            "Do not render CUDA/GPU as the conformance target for this request.",
            "Do not include 32bpc in this request.",
            "Do not mix legacy 20260604/20260605 drift references into this bit-depth batch.",
        ]
    cases = []
    inputs: dict[str, dict[str, Any]] = {}
    effects: dict[str, dict[str, str]] = {}

    for feature in plan.get("features", []):
        if not isinstance(feature, dict):
            continue
        if plugin_filter and str(feature.get("plugin")) not in plugin_filter:
            continue
        if feature_filter and str(feature.get("name")) not in feature_filter:
            continue
        by_id = manifest_cases(feature)
        for case_id in feature.get("case_ids", []):
            if case_id not in by_id:
                raise ValueError(f"{feature['name']} missing manifest case {case_id}")
            source_case = by_id[case_id]
            effect = effect_for_case(source_case)
            effect_key = str(effect.get("name") or effect.get("match_name") or feature["plugin"])
            effects.setdefault(
                effect_key,
                {
                    "name": str(effect.get("name") or ""),
                    "match_name": str(effect.get("match_name") or ""),
                },
            )
            input_id = input_id_for(str(feature["name"]), case_id)
            inputs[input_id] = {
                "id": input_id,
                "description": (
                    f"Use the same source image as normalized 8bpc {feature['name']} {case_id}. "
                    f"Recorded before_effects_frame: {source_case.get('before_effects_frame') or source_case.get('frame')}"
                ),
                "source_manifest": str(resolve(feature["normalized_ref_dir"]) / "reference_manifest.json"),
                "source_case_id": case_id,
                "before_effects_frame": source_case.get("before_effects_frame"),
            }
            cases.append(
                {
                    "id": f"{feature['name'].lower().replace(' ', '_')}__{case_id}",
                    "feature": feature["name"],
                    "plugin": feature["plugin"],
                    "source_case_id": case_id,
                    "input": input_id,
                    "reason": case_reason,
                    "effect": effects[effect_key],
                    "params": param_map(effect),
                    "params_full": param_records(effect),
                }
            )

    if not cases:
        detail = []
        if plugin_filter:
            detail.append(f"plugin={sorted(plugin_filter)}")
        if feature_filter:
            detail.append(f"feature={sorted(feature_filter)}")
        suffix = f" ({', '.join(detail)})" if detail else ""
        raise ValueError(f"no bit-depth request cases selected{suffix}")

    return {
        "request_id": request_id,
        "scope": {
            "bit_depth": args.bit_depth,
            "plugin_filters": sorted(plugin_filter),
            "feature_filters": sorted(feature_filter),
            "plugin_count": len({str(row["plugin"]) for row in cases}),
            "case_count": len(cases),
        },
        "effect": {
            "name": "OLM bit-depth conformance batch",
            "match_name": "mixed",
            "contains_mixed_effects": True,
        },
        "why": why,
        "render_sets": [
            {
                "id": render_set_id,
                "project_gpu_accel_type.current_name": "SOFTWARE",
                "bit_depth": args.bit_depth,
                "bits_per_channel": bits_per_channel,
                "required": True,
            }
        ],
        "inputs": list(inputs.values()),
        "cases": cases,
        "manifest_requirements": manifest_requirements,
        "mac_follow_up": mac_follow_up,
        "stop_lines": stop_lines,
    }


def main() -> int:
    args = parse_args()
    if args.request_id is None:
        args.request_id = default_request_id(args.bit_depth)
    if args.output is None and args.preview_dir is not None:
        args.output = args.preview_dir / "request_preview.json"
    if args.output is None:
        args.output = default_output(args.bit_depth, args.request_id)
    request = build_request(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(request, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.preview_dir is not None:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        command_parts = [
            "python3 scripts/generate_bitdepth_reference_request.py",
            "--bit-depth",
            args.bit_depth,
        ]
        for plugin in args.plugin:
            command_parts.extend(["--plugin", plugin])
        for feature in args.feature:
            command_parts.extend(["--feature", feature])
        command_parts.extend(["--request-id", request["request_id"]])
        command_parts.extend(["--preview-dir", str(args.preview_dir)])
        readme_path = args.preview_dir / "README.md"
        readme_path.write_text(
            preview_readme(
                request,
                bit_depth=args.bit_depth,
                plugin_filter=args.plugin,
                feature_filter=args.feature,
                command=" ".join(command_parts),
            ),
            encoding="utf-8",
        )
    print(f"request_json={args.output}")
    print(f"request_id={request['request_id']}")
    print(f"cases={len(request['cases'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
