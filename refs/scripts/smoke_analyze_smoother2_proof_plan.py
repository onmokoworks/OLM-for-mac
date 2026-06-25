#!/usr/bin/env python3
"""Smoke-test scripts/analyze_smoother2_proof_plan.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_proof_plan_") as tmp:
        tmp_path = Path(tmp)
        output_json = tmp_path / "proof_plan.json"
        output_md = tmp_path / "proof_plan.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_smoother2_proof_plan.py",
                "--output-json",
                str(output_json),
                "--output-md",
                str(output_md),
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads(output_json.read_text(encoding="utf-8"))
        if report.get("kind") != "olmsmoother2_current_aex_proof_plan":
            raise AssertionError(report.get("kind"))
        if report.get("decision") != "runtime-or-asm-first-divergence-required":
            raise AssertionError(report.get("decision"))
        plans = {row["case_id"]: row for row in report["plans"]}
        case_0004 = plans["legacy_case_0004_current_aex"]
        case_0012 = plans["legacy_case_0012_gamma5_red_blue_current_aex"]
        if case_0004["xy"] != [1903, 519]:
            raise AssertionError(case_0004)
        if case_0012["xy"] != [91, 841]:
            raise AssertionError(case_0012)
        if case_0004["static_dispatch"]["hex"] != "0xd0":
            raise AssertionError(case_0004["static_dispatch"])
        if case_0012["static_dispatch"]["hex"] != "0x69":
            raise AssertionError(case_0012["static_dispatch"])
        if "FUN_180013140" not in case_0004["static_dispatch"]["dispatch"]:
            raise AssertionError(case_0004["static_dispatch"])
        if "FUN_1800125c0" not in case_0012["static_dispatch"]["dispatch"]:
            raise AssertionError(case_0012["static_dispatch"])
        helper_0004 = "\n".join(case_0004["static_dispatch"].get("helper_shape") or [])
        helper_0012 = "\n".join(case_0012["static_dispatch"].get("helper_shape") or [])
        if "(x-1,y), (x-1,y-1), and (x,y-1)" not in helper_0004:
            raise AssertionError(helper_0004)
        if "d3b0 and da50" not in helper_0012:
            raise AssertionError(helper_0012)
        if case_0004["ordered_probes"][0]["name"] != "writer-anchor":
            raise AssertionError(case_0004["ordered_probes"])
        if case_0012["ordered_probes"][2]["name"] != "emit-chain":
            raise AssertionError(case_0012["ordered_probes"])
        md = output_md.read_text(encoding="utf-8")
        for needle in (
            "runtime-or-asm-first-divergence-required",
            "Do not add a global transparent-center fallback",
            "Do not suppress f270",
            "writer-anchored runtime trace",
            "0xd0",
            "0x69",
            "side-channel byte",
            "win_cardinal_6 is the local FUN_180010760 model",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle!r}")
    print("[OK] Smoother2 proof plan smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
