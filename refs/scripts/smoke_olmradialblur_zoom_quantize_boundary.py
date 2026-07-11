#!/usr/bin/env python3
"""Guard the OLMRadialBlur Zoom case_0009 quantize-boundary finding."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], root: Path) -> None:
    proc = subprocess.run(cmd, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def diff_stats(reference: Path, candidate: Path) -> tuple[int, int]:
    ref = Image.open(reference).convert("RGBA")
    cand = Image.open(candidate).convert("RGBA")
    diff = ImageChops.difference(ref, cand)
    max_diff = max(channel[1] for channel in diff.getextrema())
    raw = diff.tobytes()
    nonzero = sum(1 for i in range(0, len(raw), 4) if raw[i : i + 4] != b"\x00\x00\x00\x00")
    return max_diff, nonzero


def pixel(path: Path, xy: tuple[int, int]) -> tuple[int, int, int, int]:
    return Image.open(path).convert("RGBA").getpixel(xy)


def main() -> int:
    root = repo_root()
    reference_dir = root / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
    manifest_path = reference_dir / "reference_manifest.json"
    with manifest_path.open(encoding="utf-8-sig") as handle:
        manifest = json.load(handle)
    case = next(row for row in manifest["cases"] if row["id"] == "case_0009")

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmradialblur_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    tmp = Path(tempfile.mkdtemp(prefix="olmradialblur_zoom_quantize_"))
    try:
        params = tmp / "case_0009_params.json"
        params.write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")
        input_png = reference_dir / case["before_effects_frame"]
        reference_png = reference_dir / case["frame"]

        variants = {
            "default": [],
            "aex_repeat": ["--zoom-grid-mode", "aex-float", "--rgba-sampler-alpha-mode", "repeat-raw-f32"],
            "polar_alpha": [
                "--zoom-grid-mode",
                "aex-float",
                "--rgba-sampler-alpha-mode",
                "repeat-raw-f32",
                "--outer-caller-collapse-mode",
                "polar-alpha",
            ],
            "polar_alpha_trunc": [
                "--zoom-grid-mode",
                "aex-float",
                "--rgba-sampler-alpha-mode",
                "repeat-raw-f32",
                "--outer-caller-collapse-mode",
                "polar-alpha",
                "--outer-alpha-quantize-mode",
                "truncate",
            ],
        }
        results: dict[str, dict[str, object]] = {}
        for name, extra in variants.items():
            output = tmp / f"{name}.png"
            witness = tmp / f"{name}.json"
            run(
                [
                    str(root / "cli" / "OLMRadialBlur" / "olmradialblur_cli"),
                    "--input",
                    str(input_png),
                    "--params",
                    str(params),
                    "--output",
                    str(output),
                    *extra,
                    "--witness-dump",
                    str(witness),
                    "--witness-x",
                    "6",
                    "--witness-y",
                    "0",
                ],
                root,
            )
            max_diff, nonzero = diff_stats(reference_png, output)
            witness_data = json.loads(witness.read_text(encoding="utf-8"))
            results[name] = {
                "pixel": pixel(output, (6, 0)),
                "max_diff": max_diff,
                "nonzero": nonzero,
                "alpha": witness_data.get("alpha"),
                "sample_u8": witness_data.get("sample_u8"),
            }

        if pixel(reference_png, (6, 0)) != (20, 3, 3, 254):
            raise AssertionError(f"unexpected Windows reference witness pixel: {pixel(reference_png, (6, 0))}")
        if results["default"]["pixel"] != (20, 3, 3, 255):
            raise AssertionError(f"default witness drifted: {results['default']}")
        if results["polar_alpha"]["sample_u8"] != [20, 3, 3, 255]:
            raise AssertionError(f"polar-alpha should still quantize to 255 with epsilon: {results['polar_alpha']}")
        alpha = float(results["polar_alpha"]["alpha"])
        if not (0.9999999 < alpha < 1.0):
            raise AssertionError(f"polar-alpha should expose a just-below-one alpha: {alpha}")
        if results["polar_alpha_trunc"]["pixel"] != (20, 3, 3, 254):
            raise AssertionError(f"truncate should match the witness pixel only: {results['polar_alpha_trunc']}")
        if int(results["polar_alpha_trunc"]["nonzero"]) < 500000:
            raise AssertionError(f"truncate must remain rejected as overbroad: {results['polar_alpha_trunc']}")
        if int(results["polar_alpha"]["nonzero"]) >= int(results["polar_alpha_trunc"]["nonzero"]):
            raise AssertionError("polar-alpha truncate should be much broader than polar-alpha epsilon")

        print("[OK] RadialBlur Zoom quantize-boundary guard")
        print(json.dumps(results, indent=2, default=list))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
