#!/usr/bin/env python3
"""Lock the PF8 host-premultiply chain from raw source to the first append."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASE_TOKEN = "case_0012_gamma5_red_blue_current_aex"
REFERENCE_ROOT = ROOT / "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621"
PARAM_ROOT = ROOT / "refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/candidate/_params"


def one(root: Path, pattern: str) -> Path:
    matches = sorted(root.rglob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {pattern!r} under {root}, got {matches}")
    return matches[0]


def main() -> int:
    cli = ROOT / "cli/OLMSmoother2/olmsmoother2_cli"
    source = one(REFERENCE_ROOT, "*current_olm_cells.png")
    params = one(PARAM_ROOT, f"*{CASE_TOKEN}*.json")
    env = os.environ.copy()
    env["OLMSMOOTHER2_FORCE_INPUT_PREMULTIPLY"] = "1"

    with tempfile.TemporaryDirectory(prefix="olmsmoother2_pf8_host_adapter_") as tmp:
        proc = subprocess.run(
            [str(cli), "--input", str(source), "--params", str(params),
             "--output", str(Path(tmp) / "output.png"), "--trace-pixel", "92,841"],
            cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    if proc.returncode:
        print(proc.stdout, end="")
        return proc.returncode

    required = (
        "trace neighborhood sample (92,840)=0.18447499,0.18447499,0.18447499,0.68235296 class=ff000000",
        "trace cardinal6 desc=(92,841,1,92,842,2) key=20",
        "trace e170 p2=(92,841,1,92,842,2) bits Axy-1=1 R x-1y=1 Axy=1 -> c=7",
        "trace append src=(92,840) dst_center=(92,841) rgba=(0.18447499,0.18447499,0.18447499,0.68235296) w=0.28448275",
    )
    missing = [line for line in required if line not in proc.stdout]
    if missing:
        print(proc.stdout, end="")
        print("missing PF8 host-adapter witnesses:")
        for line in missing:
            print(f"- {line}")
        return 1

    print("PASS_OLMSMOOTHER2_PF8_HOST_ADAPTER_FIRST_APPEND")
    for line in required:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
