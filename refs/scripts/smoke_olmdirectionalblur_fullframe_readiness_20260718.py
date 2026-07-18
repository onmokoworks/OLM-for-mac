#!/usr/bin/env python3
"""Smoke gate for the DirectionalBlur full-frame readiness audit."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmdirectionalblur_fullframe_readiness_20260718.py"


def main() -> int:
    proc = subprocess.run(["python3", str(AUDIT)], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise SystemExit(proc.returncode)
    payload = json.loads(proc.stdout)
    assert payload["status"] == "blocked", payload
    assert payload["fullframe_local_ready"] is False, payload
    assert payload["mac_ae_validation_ready"] is False, payload
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
