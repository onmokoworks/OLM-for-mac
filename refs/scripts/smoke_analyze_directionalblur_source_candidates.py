#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "analyze_directionalblur_source_candidates.py"
OUT_JSON = ROOT / "refs" / "conformance" / "olmdirectionalblur_source_candidates_audit_20260701.json"
OUT_MD = ROOT / "refs" / "conformance" / "olmdirectionalblur_source_candidates_audit_20260701.md"


def main() -> int:
    subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, check=True)
    payload = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    assert payload["decision"] == "freeze-rejected-global-toggles-keep-two-narrow-lanes"
    assert payload["current_structural_base"]["candidate"] == "rotated-aex-full-choreo"
    rejected = {row["toggle_family"] for row in payload["rejected_as_global_fix"]}
    assert "source_driven_scatter" in rejected
    assert "rowdriver_prepass_and_alpha_fade_gather" in rejected
    lanes = {row["family"] for row in payload["surviving_narrow_lanes"]}
    assert lanes == {"angle0-rowdriver-valid-alpha", "diagonal-rotate-validity"}
    assert "Do not retune prepass/scatter/direct/front-strength globally from PNG means." in payload["forbidden_actions"]
    assert OUT_MD.exists()
    print(f"ok: {OUT_JSON}")
    print(f"ok: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
