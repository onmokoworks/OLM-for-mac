#!/usr/bin/env python3
"""Run image-processing CLI cases from a reference manifest.

The command receives placeholders:
  {input}       input image path
  {params}      per-case params JSON path
  {output}      output image path to write
  {case_id}     case id
  {manifest}    manifest path

Example:
  run_algorithm_cases.py reference_manifest.json \
    --command './olmblur_cli --input {input} --params {params} --output {output}'
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def case_params(case):
    if "params" in case:
        return case["params"]
    if "effects" in case:
        return {"effects": case["effects"]}
    return {}


def case_metadata(case, manifest):
    metadata = {
        "comp": case.get("comp") or manifest.get("comp"),
        "project_gpu_accel_type": case.get("project_gpu_accel_type") or manifest.get("project_gpu_accel_type"),
        "render_set": case.get("render_set") or case.get("render_set_id") or manifest.get("render_set"),
    }
    for key in ("ctx_render_scale", "render_scale", "ctx_0x11c", "ctx_0x120", "render_context",
                "ctx_render_scale_x", "render_scale_x", "ctx_0x11c_x", "ctx_0x120_x",
                "ctx_render_scale_y", "render_scale_y", "ctx_0x11c_y", "ctx_0x120_y"):
        if key in case:
            metadata[key] = case[key]
        elif key in manifest:
            metadata[key] = manifest[key]
    return metadata


def case_has_effect(case, expected_effect):
    if not expected_effect:
        return True
    for effect in case.get("effects", []):
        if effect.get("name") == expected_effect or effect.get("match_name") == expected_effect:
            return True
    return False


def resolve_input(root, manifest, case, override, input_field):
    value = override
    if value is None and input_field:
        value = case.get(input_field)
    if value is None:
        value = case.get("input") or manifest.get("input")
    if isinstance(value, dict):
        value = value.get("path") or value.get("file")
    if not value:
        raise ValueError(f"{case.get('id', '<case>')}: no input path in case or manifest")
    path = Path(value)
    return path if path.is_absolute() else root / path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", help="reference manifest JSON")
    parser.add_argument("--command", required=True, help="CLI command template")
    parser.add_argument("--input", default=None, help="override input image for all cases")
    parser.add_argument("--input-field", default=None, help="case field to use as input image, e.g. before_effects_frame")
    parser.add_argument("--root", default=None, help="manifest-relative root for input paths")
    parser.add_argument("--out-dir", default="refs/mac_cli", help="candidate output directory")
    parser.add_argument("--params-dir", default=None, help="per-case params JSON directory")
    parser.add_argument("--case-id", action="append", default=None, help="run only this case id; may be repeated")
    parser.add_argument("--expected-effect", default=None, help="skip cases that do not contain this effect name/matchName")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    with manifest_path.open(encoding="utf-8-sig") as handle:
        manifest = json.load(handle)

    if args.root:
        root = Path(args.root).resolve()
    elif manifest_path.parent.name == "cases":
        root = manifest_path.parent.parent
    else:
        root = manifest_path.parent
    out_dir = Path(args.out_dir).resolve()
    params_dir = Path(args.params_dir).resolve() if args.params_dir else out_dir / "_params"
    out_dir.mkdir(parents=True, exist_ok=True)
    params_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    allow_cases = set(args.case_id or [])
    for index, case in enumerate(manifest.get("cases", []), start=1):
        case_id = case.get("id") or f"case_{index:04d}"
        if allow_cases and case_id not in allow_cases:
            continue
        if not case_has_effect(case, args.expected_effect):
            print(f"[SKIP] {case_id:20s} missing effect {args.expected_effect}", flush=True)
            continue
        frame = case.get("frame") or f"{case_id}.png"
        input_path = resolve_input(root, manifest, case, args.input, args.input_field)
        output_path = out_dir / frame
        params_path = params_dir / f"{Path(frame).stem}.json"

        with params_path.open("w", encoding="utf-8") as handle:
            metadata = case_metadata(case, manifest)
            json.dump(
                {
                    "case_id": case_id,
                    "comp": metadata.get("comp"),
                    "frame": frame,
                    "metadata": metadata,
                    "time": case.get("time"),
                    "params": case_params(case),
                },
                handle,
                indent=2,
                sort_keys=True,
            )

        values = {
            "input": str(input_path),
            "params": str(params_path),
            "output": str(output_path),
            "case_id": case_id,
            "manifest": str(manifest_path),
        }
        command = args.command.format(**values)
        print(f"[RUN] {case_id} -> {output_path}", flush=True)
        print(f"      {command}", flush=True)

        if args.dry_run:
            continue

        result = subprocess.run(command, shell=True)
        if result.returncode != 0:
            print(f"[FAIL] {case_id}: exit={result.returncode}", file=sys.stderr)
            failures += 1

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
