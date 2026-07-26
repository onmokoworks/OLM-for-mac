#!/usr/bin/env python3
"""Lock the binary-grounded case_0012 frame-setup/cardinal witness."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASE_TOKEN = "case_0012_gamma5_red_blue_current_aex"
REFERENCE_ROOT = (
    ROOT
    / "refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/reference"
)
PARAM_ROOT = (
    ROOT
    / "refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/candidate/_params"
)


def one(pattern: str, root: Path) -> Path:
    matches = sorted(root.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {pattern!r} under {root}, got {matches}")
    return matches[0]


def main() -> int:
    input_png = one(f"*{CASE_TOKEN}*before_effects.png", REFERENCE_ROOT)
    params_json = one(f"*{CASE_TOKEN}*.json", PARAM_ROOT)
    cli = ROOT / "cli/OLMSmoother2/olmsmoother2_cli"

    with tempfile.TemporaryDirectory(prefix="olmsmoother2_case0012_gate_") as tmp:
        output = Path(tmp) / "output.png"
        proc = subprocess.run(
            [
                str(cli),
                "--input",
                str(input_png),
                "--params",
                str(params_json),
                "--output",
                str(output),
                "--trace-pixel",
                "92,841",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if proc.returncode != 0:
            print(proc.stdout, end="")
            return proc.returncode

    required = (
        "trace cardinal6 cplane y=840 x=92 bytes=255,0,0,0",
        "trace cardinal6 cplane y=841 x=92 bytes=255,255,0,255",
        "trace cardinal6 desc=(92,841,1,92,842,2) key=20",
        "trace e170 p2=(92,841,1,92,842,2) bits Axy-1=1 R x-1y=1 Axy=1 -> c=7",
        "trace append src=(92,840) dst_center=(92,841) rgba=(0.18447502,0.18447502,0.18447502,0.68235296) w=0.28448275",
    )
    missing = [line for line in required if line not in proc.stdout]
    if missing:
        print(proc.stdout, end="")
        print("missing witness lines:")
        for line in missing:
            print(f"- {line}")
        return 1

    print("[OK] OLMSmoother2 case_0012 unpremultiply gate witness")
    for line in required:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
