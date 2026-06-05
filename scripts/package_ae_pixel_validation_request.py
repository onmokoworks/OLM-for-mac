#!/usr/bin/env python3
"""Package a macOS AE-host pixel validation request from existing refs.

The output zip is meant to travel with a packaged macOS plug-in build to an AE
host. It contains input PNGs, expected Windows output PNGs, the reference
manifest, and a small result template. The returned AE render PNGs can then be
checked with scripts/verify_ae_pixel_validation_result.py without launching AE.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


OLMBLUR_EXACT_CASES = ["case_0001", "case_0002", "case_0004"]
OLMBLUR_RESIDUAL_CASES = ["case_0003", "case_0005", "case_0006", "case_0007"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preset",
        choices=["olmblur"],
        default="olmblur",
        help="Known validation preset to package.",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=None,
        help="Reference directory containing reference_manifest.json and PNGs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output zip path. Defaults to /tmp/olm_ae_pixel_validation_<preset>_YYYYMMDD.zip.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_manifest(reference: Path) -> dict:
    manifest_path = reference / "reference_manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"missing reference manifest: {manifest_path}")
    with manifest_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("reference manifest top-level JSON must be an object")
    if not isinstance(data.get("cases"), list) or not data["cases"]:
        raise ValueError("reference manifest must contain cases")
    return data


def effect_matches(case: dict, effect_name: str) -> bool:
    for effect in case.get("effects", []):
        if effect.get("name") == effect_name or effect.get("match_name") == effect_name:
            return True
    return False


def find_png(reference: Path, frame: str) -> Path:
    candidates = [reference / frame, reference / "png" / frame, reference / "reference" / frame]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"missing PNG for frame {frame!r} in {reference}")


def preset_config(root: Path, preset: str, reference: Path | None) -> dict:
    if preset != "olmblur":
        raise ValueError(f"unsupported preset: {preset}")
    return {
        "request_id": "ae_pixel_olmblur_20260606",
        "effect_name": "OLM Blur",
        "effect_match_name": "OLM OLM Blur",
        "reference": reference or root / "refs" / "win_references" / "20260604_olm" / "OLMBlur",
        "threshold_groups": [
            {
                "name": "exact",
                "case_ids": OLMBLUR_EXACT_CASES,
                "max_diff": 0,
                "mean_diff": 0.0,
                "nonzero_px_percent": 0.0,
            },
            {
                "name": "residual_max1",
                "case_ids": OLMBLUR_RESIDUAL_CASES,
                "max_diff": 1,
                "mean_diff": 0.01,
                "nonzero_px_percent": 3.0,
            },
        ],
    }


def build_readme(request_manifest: dict) -> str:
    groups = request_manifest["threshold_groups"]
    lines = [
        "# OLM AE Pixel Validation Request",
        "",
        f"Request id: `{request_manifest['request_id']}`",
        f"Effect: `{request_manifest['effect_name']}` / `{request_manifest['effect_match_name']}`",
        "",
        "Use the packaged macOS plug-in in After Effects, recreate the listed cases",
        "from `reference_manifest.json`, render each output PNG, and return the PNGs",
        "plus a filled `AE_PIXEL_VALIDATION_RESULT.template.json`.",
        "",
        "Input PNGs are in `input/`; Windows expected outputs are in `expected/`.",
        "Returned render PNGs should keep the same frame names, for example",
        "`case_0001.png`.",
        "",
        "Threshold groups:",
        "",
    ]
    for group in groups:
        lines.append(
            f"- `{group['name']}`: {', '.join(group['case_ids'])}; "
            f"max <= {group['max_diff']}, mean <= {group['mean_diff']}, "
            f"nonzero_px_percent <= {group['nonzero_px_percent']}"
        )
    lines.extend(
        [
            "",
            "Important metadata to record:",
            "",
            "- AE version",
            "- macOS version",
            "- Project Settings renderer / `project_gpu_accel_type` if available",
            "- Whether AE was launched cleanly after installing the plug-in",
            "- Any missing UI parameter, render error, or crash",
            "",
            "Do not use hidden `ADBE Force CPU GPU` as proof of GPU/CPU execution.",
            "Record it only as reference metadata if it appears.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def package_request(config: dict, output: Path) -> None:
    reference = Path(config["reference"]).resolve()
    manifest = load_manifest(reference)
    effect_name = config["effect_name"]
    cases = []
    allowed_ids = {case_id for group in config["threshold_groups"] for case_id in group["case_ids"]}
    for index, case in enumerate(manifest.get("cases", []), start=1):
        case_id = case.get("id") or f"case_{index:04d}"
        if case_id not in allowed_ids:
            continue
        if not effect_matches(case, effect_name):
            raise ValueError(f"{case_id} does not contain expected effect {effect_name!r}")
        frame = case.get("frame") or f"{case_id}.png"
        before_frame = case.get("before_effects_frame")
        if not before_frame:
            raise ValueError(f"{case_id} is missing before_effects_frame")
        cases.append({"id": case_id, "frame": frame, "before_effects_frame": before_frame})

    found_ids = {case["id"] for case in cases}
    missing_ids = sorted(allowed_ids - found_ids)
    if missing_ids:
        raise ValueError(f"reference manifest is missing requested cases: {', '.join(missing_ids)}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="olm_ae_pixel_request_") as tmp:
        tmp_path = Path(tmp)
        stage = tmp_path / config["request_id"]
        input_dir = stage / "input"
        expected_dir = stage / "expected"
        input_dir.mkdir(parents=True)
        expected_dir.mkdir()

        shutil.copy2(reference / "reference_manifest.json", stage / "reference_manifest.json")
        for case in cases:
            shutil.copy2(find_png(reference, case["before_effects_frame"]), input_dir / case["before_effects_frame"])
            shutil.copy2(find_png(reference, case["frame"]), expected_dir / case["frame"])

        request_manifest = {
            "kind": "olm_ae_pixel_validation_request",
            "request_id": config["request_id"],
            "created_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "effect_name": config["effect_name"],
            "effect_match_name": config["effect_match_name"],
            "reference_manifest": "reference_manifest.json",
            "input_dir": "input",
            "expected_dir": "expected",
            "candidate_dir_hint": "candidate",
            "cases": cases,
            "threshold_groups": config["threshold_groups"],
        }
        write_json(stage / "request_manifest.json", request_manifest)
        write_json(
            stage / "AE_PIXEL_VALIDATION_RESULT.template.json",
            {
                "kind": "olm_ae_pixel_validation_result",
                "request_id": config["request_id"],
                "ae_version": "",
                "macos_version": "",
                "machine": "",
                "project_gpu_accel_type": {"current_name": "", "raw": None},
                "clean_ae_launch_after_install": None,
                "notes": "",
                "candidate_dir": "candidate",
                "cases": [
                    {"id": case["id"], "frame": case["frame"], "rendered": None, "error": ""}
                    for case in cases
                ],
            },
        )
        (stage / "AE_PIXEL_VALIDATION_REQUEST.md").write_text(build_readme(request_manifest), encoding="utf-8")

        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                archive.write(path, path.relative_to(tmp_path))


def main() -> int:
    args = parse_args()
    root = repo_root()
    config = preset_config(root, args.preset, args.reference)
    output = args.output
    if output is None:
        stamp = dt.datetime.now().strftime("%Y%m%d")
        output = Path("/tmp") / f"olm_ae_pixel_validation_{args.preset}_{stamp}.zip"
    output = output.resolve()

    try:
        package_request(config, output)
    except Exception as exc:  # noqa: BLE001 - command-line packager should show exact failure.
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    print(f"wrote {output}")
    print(f"- preset: {args.preset}")
    print(f"- request_id: {config['request_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
