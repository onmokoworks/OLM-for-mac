#!/usr/bin/env python3
"""Smoke-test OLMBlur AEX helper exact replay and remaining readiness gate."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMITTED = ROOT / "core" / "olmblur_cpu_fixture_readiness.json"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmblur_cpu_fixture_") as temp:
        generated = Path(temp) / "readiness.json"
        subprocess.run(
            [
                str(ROOT / "tools/emulation/.venv/bin/python"),
                "tools/emulation/export_olmblur_cpu_fixture_readiness.py",
                "--output",
                str(generated),
            ],
            cwd=ROOT,
            check=True,
        )
        committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
        actual = json.loads(generated.read_text(encoding="utf-8"))
        if actual != committed:
            raise AssertionError("OLMBlur readiness changed; inspect the real AEX witness before updating it")
        if actual["status"] != "portable-core-ready":
            raise AssertionError("OLMBlur helper portable core is no longer fixture-ready")
        ids = {item["id"] for item in actual["blockers"]}
        required = {"full-entry-host-layout-missing"}
        if not required <= ids:
            raise AssertionError(f"missing required blockers: {sorted(required - ids)}")
        if "portable-core-contract-missing" in ids:
            raise AssertionError("portable helper contract unexpectedly regressed to blocked")
        if not actual["execution"]["import_free"]:
            raise AssertionError("helper readiness unexpectedly used an imported AEX symbol")
    subprocess.run(
        [str(ROOT / "tools/emulation/.venv/bin/python"), "tools/emulation/smoke_olmblur_helper.py"],
        cwd=ROOT,
        check=True,
    )
    print("[OK] OLMBlur helper exact replay is deterministic; full-entry remains explicitly blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
