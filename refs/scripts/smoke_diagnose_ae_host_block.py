#!/usr/bin/env python3
"""Smoke-test the AE host blocker diagnostic script."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str], repo: Path) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    return proc


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="olm_ae_host_diag_smoke_") as tmp:
        tmp_path = Path(tmp)
        sample = tmp_path / "sample.txt"
        sample.write_text(
            "\n".join(
                [
                    "Call graph:",
                    "dvaui::dialogs::UI_MessageBox::RunModal()",
                    "dvaui::ui::OS_Dialog::ModalLoop()",
                ]
            ),
            encoding="utf-8",
        )
        out_dir = tmp_path / "diag"
        proc = run(
            [
                py,
                "scripts/diagnose_ae_host_block.py",
                "--sample-file",
                str(sample),
                "--output-dir",
                str(out_dir),
                "--no-sample",
            ],
            repo,
        )
        if proc.returncode != 0:
            return proc.returncode
        report_path = out_dir / "ae_host_diagnostic.json"
        markdown_path = out_dir / "ae_host_diagnostic.md"
        if not report_path.exists() or not markdown_path.exists():
            print("[FAIL] diagnostic outputs were not written")
            return 1
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report["overall_status"] != "host-blocked-modal-dialog":
            print(f"[FAIL] unexpected overall_status: {report['overall_status']}")
            return 1
        markdown = markdown_path.read_text(encoding="utf-8")
        for needle in ("AE Host Automation Diagnostic", "UI_MessageBox::RunModal", "host-blocked-modal-dialog"):
            if needle not in markdown:
                print(f"[FAIL] diagnostic markdown missing: {needle}")
                return 1
    print("[OK] AE host diagnostic smoke")
    return 0


if __name__ == "__main__":
    sys.exit(main())
