#!/usr/bin/env python3
"""Smoke test the uncompressed FLOAT EXR comparator."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPARE = ROOT / "scripts" / "compare_float_exr.py"
sys.path.insert(0, str(ROOT / "refs" / "scripts"))
from smoke_verify_32bpc_float_return import make_exr


def run(reference: Path, candidate: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(COMPARE), str(reference), str(candidate)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="compare_float_exr_") as tmp:
        root = Path(tmp)
        reference, candidate = root / "reference.exr", root / "candidate.exr"
        make_exr(reference)
        candidate.write_bytes(reference.read_bytes())
        passed = run(reference, candidate)
        assert passed.returncode == 0, passed.stdout
        data = bytearray(candidate.read_bytes())
        data[-1] ^= 1
        candidate.write_bytes(data)
        failed = run(reference, candidate)
        assert failed.returncode != 0 and "mismatched_values=1" in failed.stdout, failed.stdout
    print("[OK] float EXR exact comparison and one-value mismatch detection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
