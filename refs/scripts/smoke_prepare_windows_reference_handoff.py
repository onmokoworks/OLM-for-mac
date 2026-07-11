#!/usr/bin/env python3
"""Smoke-test scripts/prepare_windows_reference_handoff.sh."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=root,
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
        status = run(
            [
                sys.executable,
                "refs/scripts/check_reference_request_status.py",
                "--json",
            ],
            root,
        )
        assert status.returncode == 0
        status_data = json.loads(status.stdout)
        pending_ids = [
            row["request_id"]
            for row in status_data.get("requests", [])
            if isinstance(row, dict)
            and isinstance(row.get("request_id"), str)
            and row.get("status") != "covered"
        ]
        proc = run([str(script), "--output-dir", str(out_dir), "--stamp", stamp], root)
        request_zip = out_dir / f"olm_reference_requests_pending_{stamp}.zip"
        handoff_zip = out_dir / f"olm_port_handoff_{stamp}_current.zip"
        if pending_ids:
            assert proc.returncode == 0, proc.stdout
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
                or "clear-mac-ae-automation-blocker" in proc.stdout
                or "prove-distancegradation-16bpc-residual-family" in proc.stdout
            )

            verify_request = run(
                [
                    "python3",
                    "refs/scripts/verify_reference_request_package.py",
                    str(request_zip),
                ],
                root,
            )
            assert verify_request.returncode == 0, verify_request.stdout
            handoff_text = subprocess.run(
                ["unzip", "-p", str(request_zip), "refs/reference_requests/WIN_CODEX_HANDOFF.md"],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=True,
            ).stdout
            assert "Why: P\n" not in handoff_text
            if "olmblur_case0006_current_aex_export_20260709" in handoff_text:
                assert "Why: Provenance-only current-AEX export request" in handoff_text
            verify_handoff = run(["python3", "scripts/verify_olm_handoff_package.py", str(handoff_zip)], root)
            assert verify_handoff.returncode == 0, verify_handoff.stdout
        else:
            assert proc.returncode != 0
            assert "[INFO] no pending Windows reference requests; packaging all request specs as a snapshot" in proc.stdout
            assert "missing scope object" in proc.stdout
            next_action = run(
                [
                    sys.executable,
                    "scripts/print_next_olm_action.py",
                    "--json",
                    str(Path.home() / "Downloads"),
                    "/tmp",
                ],
                root,
            )
            assert next_action.returncode == 0, next_action.stdout
            action = json.loads(next_action.stdout)["decision"]["action"]
            assert action in {
                "send-runtime-trace-package",
                "await-runtime-trace-return",
                "send-windows-action-bundle",
                "prove-distancegradation-16bpc-residual-family",
            }

    print("[OK] prepare Windows reference handoff smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
