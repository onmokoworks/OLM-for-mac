#!/usr/bin/env python3
"""Smoke-test scripts/print_current_handoff.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from smoke_olm_handoff_package_verifier import (
    make_handoff_package,
    make_mac_package,
    make_reference_package,
)


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
    repo = Path(__file__).resolve().parents[2]
    script = repo / "scripts" / "print_current_handoff.py"

    with tempfile.TemporaryDirectory(prefix="olm_current_handoff_smoke_") as tmp:
        tmp_path = Path(tmp)
        mac_zip = make_mac_package(repo, tmp_path)
        reference_zip = make_reference_package(tmp_path)
        handoff_zip = make_handoff_package(tmp_path, mac_zip, reference_zip)

        human = run([sys.executable, str(script), "--package", str(handoff_zip)], repo)
        assert f"send to Windows: {handoff_zip.resolve()}" in human.stdout
        assert "source commit: " + ("0" * 40) in human.stdout
        assert "next_reference_actions.json inside the zip" in human.stdout
        assert "python3 scripts/print_next_olm_action.py ~/Downloads /tmp" in human.stdout
        assert "python3 scripts/list_olm_return_candidates.py ~/Downloads /tmp" in human.stdout
        assert "python3 scripts/intake_olm_return.py path/to/returned_reference.zip --quick --dispatch-dir" in human.stdout
        assert "python3 refs/scripts/next_reference_actions.py --json" in human.stdout
        assert "--require-all-pass --require-all-pixel-requests" in human.stdout

        machine = run([sys.executable, str(script), "--package", str(handoff_zip), "--json"], repo)
        data = json.loads(machine.stdout)
        assert data["handoff_package"] == str(handoff_zip.resolve())
        assert data["handoff_contents"]["next_reference_actions_json"] == "next_reference_actions.json"
        dispatch = data["handoff_contents"]["next_reference_dispatch"]
        assert dispatch["pending_actions"][0]["copy_paste_prompt"]
        assert data["handoff_contents"]["git_commit"] == "0" * 40
        assert data["handoff_contents"]["git_dirty"] is False
        assert "--quick --dispatch-dir" in data["commands"]["mac_import_windows_refs"]
        assert data["commands"]["list_return_candidates"].endswith("~/Downloads /tmp")
        assert data["commands"]["next_olm_action"].endswith("~/Downloads /tmp")
        assert data["commands"]["next_reference_dispatch_json"].endswith("--json")
        assert "WIN_CODEX_HANDOFF.md" in data["windows_note"]

    print("[OK] print current handoff smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
