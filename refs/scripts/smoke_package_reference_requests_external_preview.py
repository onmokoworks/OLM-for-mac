#!/usr/bin/env python3
"""Smoke-test packaging an external request_preview.json."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    package_script = root / "refs" / "scripts" / "package_reference_requests.py"
    verify_script = root / "refs" / "scripts" / "verify_reference_request_package.py"

    with tempfile.TemporaryDirectory(prefix="olm_request_preview_smoke_") as tmp:
        tmp_root = Path(tmp)
        preview_dir = tmp_root / "preview_plan"
        preview_dir.mkdir(parents=True)
        request = preview_dir / "request_preview.json"
        request.write_text(
            json.dumps(
                {
                    "request_id": "olm_external_preview_smoke",
                    "effect": {"name": "Smoke Effect", "match_name": "OLMSmoke"},
                    "manifest_requirements": [],
                    "cases": [{"id": "case_0001", "params": {"amount": 1}}],
                    "render_sets": [
                        {
                            "id": "software_8bpc",
                            "project_gpu_accel_type.current_name": "SOFTWARE",
                            "required": True,
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        output = tmp_root / "requests.zip"
        subprocess.run(
            [
                sys.executable,
                str(package_script),
                "--only",
                str(request),
                "--output",
                str(output),
            ],
            cwd=root,
            check=True,
        )
        subprocess.run(
            [sys.executable, str(verify_script), str(output)],
            cwd=root,
            check=True,
        )
        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())
            expected = "refs/reference_requests/request_preview.json"
            if expected not in names:
                raise AssertionError(f"missing {expected} in packaged zip")
            payload = json.loads(archive.read(expected).decode("utf-8"))
            if payload["request_id"] != "olm_external_preview_smoke":
                raise AssertionError("packaged preview JSON was not preserved")

    print("[OK] external preview packaging smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
