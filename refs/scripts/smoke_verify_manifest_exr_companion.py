#!/usr/bin/env python3
"""Smoke-test verify_manifest.py preferring EXR companions when present."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "refs" / "fixtures" / "test_cellanim.png"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def main() -> int:
    magick = shutil.which("magick")
    if not magick:
        print("[SKIP] missing ImageMagick")
        return 0

    with tempfile.TemporaryDirectory(prefix="olm_verify_exr_smoke_") as tmp_name:
        tmp = Path(tmp_name)
        reference_dir = tmp / "reference"
        candidate_dir = tmp / "candidate"
        reference_dir.mkdir()
        candidate_dir.mkdir()

        frame = "case_0001.png"
        shutil.copy2(FIXTURE, reference_dir / frame)
        shutil.copy2(FIXTURE, candidate_dir / frame)
        subprocess.run([magick, str(reference_dir / frame), str(reference_dir / "case_0001.exr")], check=True)
        subprocess.run([magick, str(candidate_dir / frame), str(candidate_dir / "case_0001.exr")], check=True)

        manifest = {
            "schema": 2,
            "kind": "ae_effect_reference_manifest",
            "cases": [{"id": "case_0001", "frame": frame, "effects": []}],
        }
        manifest_path = tmp / "reference_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        proc = run(
            [
                sys.executable,
                str(ROOT / "refs" / "scripts" / "verify_manifest.py"),
                str(manifest_path),
                "--reference-dir",
                str(reference_dir),
                "--candidate-dir",
                str(candidate_dir),
                "--diff-dir",
                str(tmp / "diff"),
                "--report-dir",
                str(tmp / "reports"),
                "--report-name",
                "exr_companion",
            ]
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads((tmp / "reports" / "exr_companion.json").read_text(encoding="utf-8"))
        row = report["cases"][0]
        if row.get("resolved_reference") != "case_0001.exr" or row.get("resolved_candidate") != "case_0001.exr":
            print("[FAIL] verify_manifest did not prefer EXR companions", file=sys.stderr)
            return 1
    print("[OK] verify_manifest EXR companion smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
