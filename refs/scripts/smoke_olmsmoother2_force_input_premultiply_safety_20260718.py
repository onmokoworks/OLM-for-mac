#!/usr/bin/env python3
"""Verify the OLMSmoother2 diagnostic premultiply gate is fail-closed by default."""

from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASE_TOKEN = "case_0012_gamma5_red_blue_current_aex"
REFERENCE_ROOT = (
    ROOT / "refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/reference"
)
PARAM_ROOT = (
    ROOT / "refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/candidate/_params"
)


def one(pattern: str, root: Path) -> Path:
    matches = sorted(root.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {pattern!r} under {root}, got {matches}")
    return matches[0]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_lines(log: str) -> list[str]:
    return [line for line in log.splitlines() if not line.startswith("wrote: ")]


def run_case(env_override: dict[str, str | None]) -> tuple[str, str]:
    cli = ROOT / "cli/OLMSmoother2/olmsmoother2_cli"
    input_png = one(f"*{CASE_TOKEN}*before_effects.png", REFERENCE_ROOT)
    params_json = one(f"*{CASE_TOKEN}*.json", PARAM_ROOT)
    env = os.environ.copy()
    env.pop("OLMSMOOTHER2_FORCE_INPUT_PREMULTIPLY", None)
    for key, value in env_override.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value

    with tempfile.TemporaryDirectory(prefix="olmsmoother2_force_input_gate_") as tmp:
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
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stdout)
        return sha256(output), proc.stdout


def main() -> int:
    absent_hash, absent_log = run_case({})
    zero_hash, zero_log = run_case({"OLMSMOOTHER2_FORCE_INPUT_PREMULTIPLY": "0"})
    one_hash, one_log = run_case({"OLMSMOOTHER2_FORCE_INPUT_PREMULTIPLY": "1"})

    if absent_hash != zero_hash:
        print("unset and explicit 0 diverged")
        print(f"unset={absent_hash}")
        print(f"zero ={zero_hash}")
        return 1

    if stable_lines(absent_log) != stable_lines(zero_log):
        print("unset and explicit 0 stable logs diverged")
        return 1

    if one_hash == absent_hash:
        print("explicit 1 did not change output")
        print(f"hash={one_hash}")
        return 1

    required = (
        "trace cardinal6 desc=(92,841,1,92,842,2) key=20",
        "trace e170 p2=(92,841,1,92,842,2) bits Axy-1=1 R x-1y=1 Axy=1 -> c=7",
    )
    missing = [line for line in required if line not in one_log]
    if missing:
        print("explicit 1 missing diagnostic witness")
        for line in missing:
            print(f"- {line}")
        return 1

    print("PASS_OLMSMOOTHER2_FORCE_INPUT_PREMULTIPLY_SAFETY")
    print(f"unset_sha256={absent_hash}")
    print(f"zero_sha256={zero_hash}")
    print(f"one_sha256={one_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
