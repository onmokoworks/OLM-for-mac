#!/usr/bin/env python3
"""Smoke-test smoke_reference_requests_after_import.py with synthetic covered refs."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    runner = repo / "refs/scripts/smoke_reference_requests_after_import.py"
    with tempfile.TemporaryDirectory(prefix="olm_ref_after_import_smoke_") as tmp:
        tmp_path = Path(tmp)
        requests = tmp_path / "requests"
        references = tmp_path / "references"
        request = {
            "request_id": "synthetic_request_20260606",
            "effect": {"name": "Synthetic Effect", "match_name": "Synthetic Effect"},
            "render_sets": [
                {
                    "id": "SOFTWARE",
                    "required": True,
                    "project_gpu_accel_type.current_name": "SOFTWARE",
                }
            ],
            "manifest_requirements": [],
            "cases": [{"id": "case_a"}],
        }
        write_json(requests / "synthetic_request_20260606.json", request)

        ref_dir = references / "synthetic_return" / "SyntheticEffect"
        ref_dir.mkdir(parents=True)
        (ref_dir / "case_a.png").write_bytes(b"png")
        (ref_dir / "case_a_before.png").write_bytes(b"png")
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
                }
            ],
        }
        write_json(ref_dir / "reference_manifest.json", manifest)

        cmd = [
            sys.executable,
            str(runner),
            "--requests-dir",
            str(requests),
            "--references-dir",
            str(references),
        ]
        proc = subprocess.run(cmd, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode

    print("[OK] reference requests after import runner smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
