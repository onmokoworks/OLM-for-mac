#!/usr/bin/env python3
"""Smoke-test smoke_reference_request_cli_probe.py with synthetic covered refs."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    runner = repo / "refs" / "scripts" / "smoke_reference_request_cli_probe.py"
    with tempfile.TemporaryDirectory(prefix="olm_ref_cli_probe_smoke_") as tmp:
        tmp_path = Path(tmp)
        requests = tmp_path / "requests"
        references = tmp_path / "references"
        request = {
            "request_id": "synthetic_cli_probe_20260606",
            "effect": {"name": "Synthetic Effect", "match_name": "Synthetic Effect"},
            "render_sets": [
                {
                    "id": "SOFTWARE",
                    "required": True,
                    "project_gpu_accel_type.current_name": "SOFTWARE",
                }
            ],
            "cases": [
                {
                    "id": "case_a",
                    "params": {"Amount": 1, "Mode": "identity"},
                }
            ],
        }
        write_json(requests / "synthetic_cli_probe_20260606.json", request)

        ref_dir = references / "synthetic_return" / "SyntheticEffect"
        ref_dir.mkdir(parents=True)
        fixture = repo / "refs" / "fixtures" / "test_cellanim.png"
        shutil.copy2(fixture, ref_dir / "case_a.png")
        shutil.copy2(fixture, ref_dir / "case_a_before.png")
        manifest = {
            "effect": {"name": "Synthetic Effect", "match_name": "Synthetic Effect"},
            "project_gpu_accel_type": {"current_name": "SOFTWARE", "raw": 1816},
            "cases": [
                {
                    "id": "SOFTWARE_case_a",
                    "request_case_id": "case_a",
                    "render_set": "SOFTWARE",
                    "frame": "case_a.png",
                    "before_effects_frame": "case_a_before.png",
                    "effects": [{"name": "Synthetic Effect", "match_name": "Synthetic Effect"}],
                }
            ],
        }
        write_json(ref_dir / "reference_manifest.json", manifest)

        cmd = [
            sys.executable,
            str(runner),
            "--request-id",
            "synthetic_cli_probe_20260606",
            "--expected-effect",
            "Synthetic Effect",
            "--command",
            'cp "{input}" "{output}"',
            "--requests-dir",
            str(requests),
            "--references-dir",
            str(references),
            "--run-name",
            "synthetic_cli_probe_smoke",
        ]
        proc = subprocess.run(cmd, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode

    print("[OK] reference request CLI probe smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
