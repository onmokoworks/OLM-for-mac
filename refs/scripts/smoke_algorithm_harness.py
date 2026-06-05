#!/usr/bin/env python3
"""End-to-end smoke test for the AE-free image algorithm harness."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "refs" / "fixtures" / "test_cellanim.png"


def run(command):
    print("+ " + " ".join(str(part) for part in command), flush=True)
    result = subprocess.run([str(part) for part in command])
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main():
    with tempfile.TemporaryDirectory(prefix="olm_algorithm_harness_") as tmp_name:
        tmp = Path(tmp_name)
        reference_dir = tmp / "reference"
        candidate_dir = tmp / "candidate"
        reference_dir.mkdir()

        manifest = {
            "schema": 2,
            "kind": "ae_effect_reference_manifest",
            "plugin": "HarnessSmoke",
            "input": str(FIXTURE),
            "cases": [],
        }
        for index in range(1, 4):
            case_id = f"case_{index:04d}"
            frame = f"{case_id}.png"
            shutil.copy2(FIXTURE, reference_dir / frame)
            manifest["cases"].append(
                {
                    "id": case_id,
                    "frame": frame,
                    "time": 0,
                    "params": {"example_value": index},
                }
            )

        manifest_path = tmp / "reference_manifest.json"
        with manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)

        command = (
            f'"{sys.executable}" "{ROOT / "refs" / "scripts" / "identity_image_cli.py"}" '
            '--input "{input}" --params "{params}" --output "{output}"'
        )
        run(
            [
                sys.executable,
                ROOT / "refs" / "scripts" / "run_algorithm_cases.py",
                manifest_path,
                "--command",
                command,
                "--out-dir",
                candidate_dir,
            ]
        )
        run(
            [
                sys.executable,
                ROOT / "refs" / "scripts" / "verify_manifest.py",
                manifest_path,
                "--reference-dir",
                reference_dir,
                "--candidate-dir",
                candidate_dir,
                "--diff-dir",
                tmp / "diff",
                "--report-dir",
                tmp / "reports",
                "--report-name",
                "smoke",
            ]
        )
        print(f"smoke ok: {tmp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
