#!/usr/bin/env python3
"""Compatibility redirect for the superseded Highlight gradient seam."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "tools/emulation/test_olmkirakira_mode4_highlight_gradient_closure_20260812.py"
CLOSURE = ROOT / "refs/conformance/olmkirakira_mode4_highlight_gradient_closure_20260812.json"
HISTORICAL = ROOT / "refs/conformance/olmkirakira_mode4_highlight_gradient_pf32_seam_20260812.json"
OUT = ROOT / "refs/conformance/olmkirakira_mode4_highlight_gradient_pf32_seam_supersession_20260812.json"
EXPECTED_HISTORICAL_SHA = "531179e93d198d6b794c6e9ba4869df624de24b9cc3464582ab3b13a6a192c82"


def main() -> int:
    subprocess.run(["python3", str(GENERATOR)], cwd=ROOT, check=True)
    closure = json.loads(CLOSURE.read_text(encoding="utf-8"))
    if closure.get("status") != "raw_exact":
        raise RuntimeError("replacement Highlight gradient closure is not exact")
    historical_sha = hashlib.sha256(HISTORICAL.read_bytes()).hexdigest()
    historical = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    if historical_sha != EXPECTED_HISTORICAL_SHA or historical.get("status") != "fail_closed_pf32_seam":
        raise RuntimeError("immutable historical Highlight seam changed")
    report = {
        "kind": "olmkirakira_mode4_highlight_gradient_pf32_seam",
        "date": "2026-08-12",
        "status": "superseded_by_raw_exact_closure",
        "superseded_by": "olmkirakira_mode4_highlight_gradient_closure_20260812.json",
        "closure_sha256": hashlib.sha256(CLOSURE.read_bytes()).hexdigest(),
        "historical_artifact": {
            "path": "olmkirakira_mode4_highlight_gradient_pf32_seam_20260812.json",
            "sha256": historical_sha,
            "status": historical["status"],
        },
        "historical_counterfactual": {
            "old_separable_ray_difference_words": [3, 11],
            "ulp": [1, 1],
            "meaning": "retained as a rejected implementation, not a current production seam",
        },
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "superseded_by": report["superseded_by"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
