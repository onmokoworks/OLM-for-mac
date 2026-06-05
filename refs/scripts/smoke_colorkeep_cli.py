#!/usr/bin/env python3
"""End-to-end smoke test for the ColorKeep CLI and manifest verifier."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]


def run(command):
    print("+ " + " ".join(str(part) for part in command), flush=True)
    result = subprocess.run([str(part) for part in command])
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def make_input(path):
    img = Image.new("RGBA", (4, 2), (0, 0, 255, 255))
    pixels = img.load()
    pixels[0, 0] = (255, 0, 0, 255)
    pixels[1, 0] = (0, 255, 0, 128)
    pixels[2, 0] = (0, 0, 0, 255)
    pixels[3, 0] = (255, 0, 0, 64)
    img.save(path)


def make_reference(input_path, reference_path):
    arr = Image.open(input_path).convert("RGBA")
    pixels = arr.load()
    for y in range(arr.height):
        for x in range(arr.width):
            r, g, b, a = pixels[x, y]
            if (r, g, b) not in ((255, 0, 0), (0, 0, 0)):
                pixels[x, y] = (r, g, b, 0)
    arr.save(reference_path)


def main():
    with tempfile.TemporaryDirectory(prefix="olm_colorkeep_smoke_") as tmp_name:
        tmp = Path(tmp_name)
        reference = tmp / "reference"
        reference.mkdir()
        input_path = reference / "case_0001_before_effects.png"
        reference_path = reference / "case_0001.png"
        make_input(input_path)
        make_reference(input_path, reference_path)

        manifest = {
            "schema": 2,
            "kind": "ae_effect_reference_manifest",
            "plugin": "ColorKeep",
            "cases": [
                {
                    "id": "case_0001",
                    "frame": "case_0001.png",
                    "before_effects_frame": "case_0001_before_effects.png",
                    "params": {
                        "Enabled Color Num": 2,
                        "Color 1": [255, 0, 0],
                        "Color 2": [0, 0, 0],
                    },
                }
            ],
        }
        manifest_path = tmp / "reference_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        candidate = tmp / "candidate"
        run(
            [
                sys.executable,
                ROOT / "refs" / "scripts" / "run_algorithm_cases.py",
                manifest_path,
                "--root",
                reference,
                "--input-field",
                "before_effects_frame",
                "--out-dir",
                candidate,
                "--command",
                f'{sys.executable} "{ROOT / "refs" / "scripts" / "colorkeep_cli.py"}" --input "{{input}}" --params "{{params}}" --output "{{output}}"',
            ]
        )
        run(
            [
                sys.executable,
                ROOT / "refs" / "scripts" / "verify_manifest.py",
                manifest_path,
                "--reference-dir",
                reference,
                "--candidate-dir",
                candidate,
                "--diff-dir",
                tmp / "diff",
                "--report-dir",
                tmp / "reports",
                "--report-name",
                "colorkeep_smoke",
            ]
        )
        print(f"smoke ok: {tmp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
