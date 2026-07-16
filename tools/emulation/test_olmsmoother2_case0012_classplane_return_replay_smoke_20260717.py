#!/usr/bin/env python3
"""Self-contained smoke for the case0012 class-plane return replay."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

from test_olmsmoother2_case0012_classplane_return_replay_20260717 import (  # noqa: E402
    parse_csv,
    parse_trace,
)

ADAPTER = ROOT / "tools/emulation/smoother2_case0012_classplane_replay_adapter_20260717.cpp"
PROBE = ROOT / "tools/emulation/test_olmsmoother2_case0012_classplane_return_replay_20260717.py"
VERDICT = "BLOCKED_CASE0012_LIVE_CLASSPLANE_NOT_RECOVERABLE_LOCALLY"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_classplane_replay_") as temp:
        work = Path(temp)
        binary = work / "adapter"
        output_json = work / "result.json"
        output_md = work / "result.md"
        build = subprocess.run([
            "clang++", "-std=c++17", "-O2", "-Wall", "-Wextra",
            "-I", "cli/OLMSmoother2/shim", "-I", "mac/OLMSmoother2",
            str(ADAPTER), "-o", str(binary),
        ], cwd=ROOT, text=True, capture_output=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([
            sys.executable, str(PROBE), "--adapter", str(binary),
            "--output-json", str(output_json), "--output-md", str(output_md),
        ], cwd=ROOT, text=True, capture_output=True)
        assert run.returncode == 2, run.stdout + run.stderr
        result = json.loads(output_json.read_text(encoding="utf-8"))
        markdown = output_md.read_text(encoding="utf-8")
        invalid_adapter = subprocess.run([str(binary), "unknown"], text=True, capture_output=True)

    assert result["verdict"] == VERDICT
    assert result["replay"]["e170_extracted_code_result"] == 7
    assert result["replay"]["completions"]["zero"]["aex"]["count"] == 0
    assert result["replay"]["completions"]["one"]["aex"]["count"] == 3
    assert all(item["match"] for item in result["replay"]["completions"].values())
    assert len(result["old_neighborhood_conflicts"]) == 2
    assert "cannot be extracted" in markdown
    assert "No AE exact claim" in markdown
    assert invalid_adapter.returncode == 2
    for mutation in (b"S2_EVENT duplicate=1 duplicate=2\n", b"S2_EVENT missing_separator\n"):
        try:
            parse_trace(mutation)
        except RuntimeError as error:
            assert str(error).startswith("FAIL CLOSED:")
        else:
            raise AssertionError("malformed trace did not fail closed")
    try:
        parse_csv("256,0,0,0", 4, "mutated class bytes")
    except RuntimeError as error:
        assert str(error).startswith("FAIL CLOSED:")
    else:
        raise AssertionError("out-of-range class bytes did not fail closed")
    print("PASS: case0012 class-plane return replay fails closed on non-identifiability")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
