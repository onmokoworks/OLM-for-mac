#!/usr/bin/env python3
"""Compile the fail-closed OLMKiraKira Mode2 compose/writeback request."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "refs/windows_witness_specs/olmkirakira_mode2_compose_writeback_20260716/witness-spec.json"
DEFAULT_DIR = ROOT / "refs/runtime_trace_packages/olmkirakira_mode2_compose_writeback_20260716"

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_DIR)
    p.add_argument("--zip", dest="zip_path", type=Path, default=DEFAULT_DIR.with_suffix(".zip"))
    a = p.parse_args()
    out = a.output_dir if a.output_dir.is_absolute() else ROOT / a.output_dir
    archive = a.zip_path if a.zip_path.is_absolute() else ROOT / a.zip_path
    result = subprocess.run([sys.executable, "-m", "tools.windows_witness.compile", str(SPEC), "--output-dir", str(out), "--zip", str(archive)], cwd=ROOT, check=True, text=True, capture_output=True)
    print(json.dumps({"status":"ok", "compiler":"tools.windows_witness.compile", **json.loads(result.stdout)}, sort_keys=True))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
