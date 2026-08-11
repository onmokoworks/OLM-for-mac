#!/usr/bin/env python3
"""Actual-AEX boundary for the unresolved PF32 Linear/Mode5 matrix cell."""
import hashlib
import json
import os
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/probe_olmdistancegradation_pf32_owner_20260805.py"
PYTHON = ROOT / "tools/emulation/.venv/bin/python"
FIELD_SHA256 = "6023adbb0e42b6b1269594e72c2f58f5caf3ce8ece80b68da2f06f384aea623c"

env = os.environ.copy()
env.update({
    "OLM_DG_PF32_SOURCE": "blur_family",
    "OLM_DG_PF32_ALPHA_FIXTURE": "exported_matrix",
    "OLM_DG_PF32_INTERP": "2",
    "OLM_DG_PF32_BG": "0",
    "OLM_DG_PF32_BLUR": "5",
    "OLM_DG_PF32_WRITE_ARTIFACTS": "0",
})
run = subprocess.run([str(PYTHON), str(PROBE)], cwd=ROOT, env=env,
                     text=True, capture_output=True, timeout=20)
assert run.returncode == 0, run.stderr
report = json.loads(run.stdout[run.stdout.index("{"):])
assert report["status"] == "owner_completed_field_captured"
entries = [capture for capture in report["matrix_captures"]
           if capture["label"] == "legacy_cvSmooth_blur" and capture["phase"] == "entry"]
returns = [capture for capture in report["matrix_captures"]
           if capture["label"] == "legacy_cvSmooth_blur" and capture["phase"] == "return"]
assert len(entries) == len(returns) == 1
before = bytes.fromhex(entries[0]["args"][0]["active_hex"])
after = bytes.fromhex(returns[0]["args"][1]["active_hex"])
assert len(before) == len(after) == 17 * 11 * 4
assert hashlib.sha256(before).hexdigest() == FIELD_SHA256
assert before == after
assert len(struct.unpack("<187f", after)) == 187
print("PASS_OLMDISTANCEGRADATION_PF32_MODE5_POST_SMOOTH_BOUNDARY_20260811")
