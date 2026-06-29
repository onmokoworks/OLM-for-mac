#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def find_png(reference: Path, frame: str) -> Path:
    for candidate in (reference / frame, reference / "png" / frame, reference / "reference" / frame):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"missing PNG for frame {frame!r} in {reference}")


def effect_names(manifest: dict) -> tuple[str, str]:
    effect = manifest.get("effect")
    if isinstance(effect, dict):
        name = effect.get("name")
        match_name = effect.get("match_name")
        if isinstance(name, str) and name and isinstance(match_name, str) and match_name:
            return name, match_name
    for case in manifest.get("cases", []):
        if not isinstance(case, dict):
            continue
        for effect_item in case.get("effects", case.get("selected_layer_effects", [])) or []:
            if isinstance(effect_item, dict):
                name = effect_item.get("name")
                match_name = effect_item.get("match_name")
                if isinstance(name, str) and name and isinstance(match_name, str) and match_name:
                    return name, match_name
    raise ValueError("could not infer effect name / match_name from reference manifest")


def build_request_manifest(source_manifest: dict, request_id: str, effect_name: str, effect_match_name: str) -> dict:
    cases = []
    case_ids = []
    for index, case in enumerate(source_manifest.get("cases", []), start=1):
        if not isinstance(case, dict):
            continue
        case_id = case.get("id") or f"case_{index:04d}"
        frame = case.get("frame") or f"{case_id}.png"
        before = case.get("before_effects_frame")
        if not isinstance(before, str) or not before:
            raise ValueError(f"{request_id} case {case_id} missing before_effects_frame")
        cases.append({"id": case_id, "frame": frame, "before_effects_frame": before})
        case_ids.append(case_id)

    return {
        "kind": "olm_ae_pixel_validation_request",
        "gate_kind": "host_smoke_pixel_tolerance",
        "request_id": request_id,
        "created_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "reference_profile": "windows-software-holdout",
        "effect_name": effect_name,
        "effect_match_name": effect_match_name,
        "reference_manifest": "reference_manifest.json",
        "input_dir": "input",
        "expected_dir": "expected",
        "candidate_dir_hint": "candidate",
        "cases": cases,
        "threshold_groups": [
            {
                "name": "all_exact",
                "case_ids": case_ids,
                "max_diff": 0,
                "mean_diff": 0.0,
                "nonzero_px_percent": 0.0,
            }
        ],
        "notes": [
            "Final randomized Windows Software holdout set.",
            "Use as a final exact-validation lane after witness-driven implementation work is in place.",
        ],
    }


def build_result_template(request_manifest: dict) -> dict:
    return {
        "kind": "olm_ae_pixel_validation_result",
        "gate_kind": request_manifest["gate_kind"],
        "request_id": request_manifest["request_id"],
        "ae_version": "",
        "macos_version": "",
        "machine": "",
        "project_gpu_accel_type": {"current_name": "", "raw": None},
        "clean_ae_launch_after_install": None,
        "notes": "",
        "candidate_dir": "candidate",
        "cases": [
            {"id": case["id"], "frame": case["frame"], "rendered": None, "error": ""}
            for case in request_manifest["cases"]
        ],
    }


def build_readme(request_manifest: dict) -> str:
    lines = [
        "# OLM AE Pixel Validation Request",
        "",
        f"Request id: `{request_manifest['request_id']}`",
        f"Effect: `{request_manifest['effect_name']}` / `{request_manifest['effect_match_name']}`",
        "",
        "This request was materialized from an imported Windows Software holdout reference set.",
        "Render the same cases in Mac After Effects and return the output PNGs for exact comparison.",
        "",
        "Threshold groups:",
        "",
        f"- `all_exact`: {', '.join(case['id'] for case in request_manifest['cases'])}; max <= 0, mean <= 0.0, nonzero_px_percent <= 0.0",
        "",
        "Input PNGs are in `input/`; expected Windows outputs are in `expected/`.",
    ]
    return "\n".join(lines) + "\n"


def materialize_reference(reference_dir: Path, requests_base: Path, replace: bool) -> Path:
    manifest_path = reference_dir / "reference_manifest.json"
    manifest = load_json(manifest_path)
    effect_name, effect_match_name = effect_names(manifest)
    source_request_id = manifest.get("request_id")
    if not isinstance(source_request_id, str) or not source_request_id:
        source_request_id = reference_dir.name
    request_id = f"ae_pixel_{source_request_id}"

    stage = requests_base / request_id
    if stage.exists():
        if not replace:
            raise FileExistsError(f"request dir already exists: {stage}")
        shutil.rmtree(stage)

    input_dir = stage / "input"
    expected_dir = stage / "expected"
    input_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    request_manifest = build_request_manifest(manifest, request_id, effect_name, effect_match_name)
    shutil.copy2(manifest_path, stage / "reference_manifest.json")
    for case in request_manifest["cases"]:
        shutil.copy2(find_png(reference_dir, case["before_effects_frame"]), input_dir / case["before_effects_frame"])
        shutil.copy2(find_png(reference_dir, case["frame"]), expected_dir / case["frame"])

    (stage / "request_manifest.json").write_text(json.dumps(request_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (stage / "AE_PIXEL_VALIDATION_RESULT.template.json").write_text(
        json.dumps(build_result_template(request_manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (stage / "AE_PIXEL_VALIDATION_REQUEST.md").write_text(build_readme(request_manifest), encoding="utf-8")
    return stage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference_root", type=Path, help="Directory containing one or more imported reference dirs with reference_manifest.json")
    parser.add_argument(
        "--requests-base",
        type=Path,
        default=repo_root() / "handoff" / "ae_pixel_validation_20260618" / "requests",
        help="Destination directory for request subdirectories.",
    )
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    reference_root = args.reference_root.resolve()
    requests_base = args.requests_base.resolve()

    manifests = []
    if (reference_root / "reference_manifest.json").exists():
        manifests = [reference_root]
    else:
        manifests = sorted(path.parent for path in reference_root.glob("*/reference_manifest.json"))
    if not manifests:
        raise SystemExit(f"no reference manifests found under {reference_root}")

    written = []
    for ref_dir in manifests:
        written.append(materialize_reference(ref_dir, requests_base, args.replace))

    print(f"materialized_ae_requests={len(written)}")
    for path in written:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
