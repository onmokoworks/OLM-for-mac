#!/usr/bin/env python3
"""Smoke-test focused OLMBlur final-word runtime trace package."""

from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix="olmblur_final_word_pkg_") as tmp:
        output = Path(tmp) / "olmblur_final_word_witness.zip"
        subprocess.run(
            [
                "python3",
                str(root / "scripts/package_runtime_trace_requests.py"),
                "--profile",
                "olmblur-final-word-witness",
                "--output",
                str(output),
            ],
            cwd=root,
            check=True,
        )
        with zipfile.ZipFile(output) as zf:
            names = set(zf.namelist())
            manifest = json.loads(zf.read("runtime_trace_package_manifest.json").decode("utf-8"))
            template = json.loads(zf.read("RETURN_RUNTIME_TRACE_TEMPLATE.json").decode("utf-8"))
        required = {
            "notes/IR_OLMBlur.md",
            "notes/CONFORMANCE_LEDGER.md",
            "refs/conformance/olmblur_pending_final_word_proof_20260629.md",
            "refs/conformance/olmblur_last1px_family_probe_20260629.md",
        }
        missing = sorted(required - names)
        if missing:
            raise AssertionError(f"missing package files: {missing}")
        actions = manifest.get("runtime_actions", [])
        if len(actions) != 1 or actions[0].get("request_id") != "olmblur_final_word_witness_20260630":
            raise AssertionError(f"unexpected actions: {actions}")
        observations = template["results"][0]["observations"]
        cases = observations.get("cases", [])
        if [case.get("case_id") for case in cases] != ["case_0007", "olmblur__case_0007"]:
            raise AssertionError(f"unexpected template cases: {cases}")
    print("[OK] OLMBlur final-word witness package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
