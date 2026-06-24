#!/usr/bin/env python3
"""Smoke-test scripts/prepare_windows_reference_handoff.sh."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def main() -> int:
    root = repo_root()
    script = root / "scripts" / "prepare_windows_reference_handoff.sh"
    with tempfile.TemporaryDirectory(prefix="olm_prepare_handoff_smoke_") as tmp:
        out_dir = Path(tmp)
        stamp = "smoke"
        proc = run([str(script), "--output-dir", str(out_dir), "--stamp", stamp], root)
        request_zip = out_dir / f"olm_reference_requests_pending_{stamp}.zip"
        handoff_zip = out_dir / f"olm_port_handoff_{stamp}_current.zip"
        assert request_zip.exists()
        assert handoff_zip.exists()
        assert "Windows reference handoff is ready:" in proc.stdout
        assert str(request_zip) in proc.stdout
        assert str(handoff_zip) in proc.stdout
        assert (
            "send-windows-reference-package" in proc.stdout
            or "send-runtime-trace-package" in proc.stdout
            or "send-windows-action-bundle" in proc.stdout
            or "send-ae-host-validation-package" in proc.stdout
            or "continue-binary-grounded-followup" in proc.stdout
        )

        run(
            [
                "python3",
                "refs/scripts/verify_reference_request_package.py",
                str(request_zip),
            ],
            root,
        )
        run(["python3", "scripts/verify_olm_handoff_package.py", str(handoff_zip)], root)

    print("[OK] prepare Windows reference handoff smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
