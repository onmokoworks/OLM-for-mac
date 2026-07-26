#!/usr/bin/env python3
"""Verify the native OLMSmoother2 PF8 plane through the proven AE export boundary."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops

from check_reference_request_status import load_status_rows


REQUEST_ID = "smoother2_legacy_full_current_aex_recapture_20260621"
EXPECTED_EFFECT = "OLM Smoother v2"
CASE_IDS = [
    "legacy_case_0001_current_aex",
    "legacy_case_0002_current_aex",
    "legacy_case_0003_current_aex",
    "legacy_case_0004_current_aex",
    "legacy_case_0005_current_aex",
    "legacy_case_0006_current_aex",
    "legacy_case_0007_current_aex",
    "legacy_case_0008_current_aex",
    "legacy_case_0009_v1mode_current_aex",
    "legacy_case_0010_gamma3_current_aex",
    "legacy_case_0011_gamma5_blue_current_aex",
    "legacy_case_0012_gamma5_red_blue_current_aex",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def covered_manifest(root: Path) -> Path | None:
    rows = load_status_rows(root / "refs" / "reference_requests", root / "refs" / "win_references")
    for row in rows:
        if row.get("request_id") != REQUEST_ID or row.get("status") != "covered":
            continue
        manifest = (row.get("best") or {}).get("manifest")
        if isinstance(manifest, str) and manifest:
            path = Path(manifest)
            return path if path.is_absolute() else (root / path).resolve()
    return None


def source_input_path(manifest_path: Path) -> Path:
    manifest = load_json(manifest_path)
    for entry in manifest.get("source_inputs", []):
        if not isinstance(entry, dict):
            continue
        name = entry.get("file")
        if not isinstance(name, str) or not name:
            continue
        for candidate in [
            manifest_path.parent / name,
            manifest_path.parent / name.replace("/", "\\"),
            manifest_path.parent / name.replace("\\", "/"),
        ]:
            if candidate.exists():
                return candidate
    matches = [path for path in manifest_path.parent.iterdir() if path.name.startswith("input")]
    if matches:
        return matches[0]
    raise FileNotFoundError(f"could not find source input PNG for {manifest_path}")


def render_cases(root: Path, manifest_dir: Path, source_png: Path) -> Path:
    run_dir = Path("/tmp/olmsmoother2_legacy_current_aex_exact")
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = '"cli/OLMSmoother2/olmsmoother2_cli" --input "{input}" --params "{params}" --output "{output}"'
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(manifest_dir),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        EXPECTED_EFFECT,
        "--command",
        command,
        "--input",
        str(source_png),
        "--max-diff",
        "255",
        "--mean-diff",
        "255",
        "--nonzero-px-percent",
        "100",
    ]
    for case_id in CASE_IDS:
        args.extend(["--case-id", case_id])
    subprocess.run(args, cwd=root, check=True)
    return run_dir


def write_ae_export_plane(raw_path: Path, output_path: Path) -> None:
    with Image.open(raw_path) as image:
        rgba = np.asarray(image.convert("RGBA"), dtype=np.uint16)
    alpha = rgba[..., 3:4]
    rgb = (rgba[..., :3] * alpha + 127) // 255
    output = np.concatenate((rgb, alpha), axis=2).astype(np.uint8)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(output, mode="RGBA").save(output_path)


def exact_diff(actual_path: Path, expected_path: Path) -> tuple[int, int]:
    with Image.open(actual_path) as actual_image, Image.open(expected_path) as expected_image:
        actual = actual_image.convert("RGBA")
        expected = expected_image.convert("RGBA")
        if actual.size != expected.size:
            return 255, actual.width * actual.height
        difference = ImageChops.difference(actual, expected)
        max_diff = max(high for _, high in difference.getextrema())
        pixels = (
            difference.get_flattened_data()
            if hasattr(difference, "get_flattened_data")
            else difference.getdata()
        )
        return max_diff, sum(1 for pixel in pixels if any(pixel))


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    manifest_path = covered_manifest(root)
    if manifest_path is None:
        print(f"[SKIP] {REQUEST_ID} is still pending; import the Windows recapture first.")
        return 0

    subprocess.run([str(root / "refs" / "scripts" / "build_olmsmoother2_cli.sh")], cwd=root, check=True)
    run_dir = render_cases(root, manifest_path.parent, source_input_path(manifest_path))
    manifest = load_json(manifest_path)
    by_id = {
        case["id"]: case
        for case in manifest.get("cases", [])
        if isinstance(case, dict) and case.get("id") in CASE_IDS
    }

    failures = 0
    for case_id in CASE_IDS:
        case = by_id.get(case_id)
        if case is None:
            print(f"[FAIL] manifest is missing {case_id}", file=sys.stderr)
            failures += 1
            continue
        frame = case["frame"]
        raw_path = run_dir / "candidate" / frame
        normalized_path = run_dir / "normalized" / frame
        expected_path = manifest_path.parent / frame
        write_ae_export_plane(raw_path, normalized_path)
        max_diff, differing = exact_diff(normalized_path, expected_path)
        print(f"{case_id}: max={max_diff} differing_px={differing}")
        if max_diff != 0 or differing != 0:
            failures += 1

    if failures:
        print(f"[FAIL] OLMSmoother2 legacy exact cases: {failures}/{len(CASE_IDS)}", file=sys.stderr)
        return 1
    print(f"[OK] OLMSmoother2 legacy current-AEX CLI exact {len(CASE_IDS)}/{len(CASE_IDS)}")
    print(f"run_dir={run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
