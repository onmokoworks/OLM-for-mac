#!/usr/bin/env python3
"""Smoke-test Windows reference request package handoff contents."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    output = Path(tempfile.gettempdir()) / "olm_reference_requests_handoff_smoke.zip"
    proc = subprocess.run(
        [
            sys.executable,
            "refs/scripts/package_reference_requests.py",
            "--pending",
            "--output",
            str(output),
        ],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="")
    if proc.returncode != 0:
        return proc.returncode

    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert "refs/reference_requests/WIN_CODEX_HANDOFF.md" in names
        assert "refs/reference_requests/README.md" in names
        assert any(name.endswith(".json") for name in names)
        handoff = archive.read("refs/reference_requests/WIN_CODEX_HANDOFF.md").decode("utf-8")
        readme = archive.read("refs/reference_requests/README.md").decode("utf-8")

    assert "project_gpu_accel_type.current_name = SOFTWARE" in handoff
    assert "ADBE Force CPU GPU" in handoff
    assert "python3 scripts/intake_olm_return.py path/to/returned_reference.zip --quick" in handoff
    assert "python3 refs/scripts/import_and_check_win_reference.py path/to/returned_reference.zip --quick" in handoff
    assert "Import with refs/scripts/import_win_reference.py" not in handoff
    assert "python3 refs/scripts/next_reference_actions.py" in readme
    assert "python3 scripts/intake_olm_return.py path/to/packed_reference.zip --quick" in readme

    print("[OK] reference request package handoff smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
