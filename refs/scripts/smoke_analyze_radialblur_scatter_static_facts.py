#!/usr/bin/env python3
"""Smoke-test scripts/analyze_radialblur_scatter_static_facts.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="radialblur_static_facts_") as tmp:
        out_json = Path(tmp) / "facts.json"
        out_md = Path(tmp) / "facts.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_radialblur_scatter_static_facts.py",
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads(out_json.read_text(encoding="utf-8"))
        conclusions = report["conclusions"]
        if conclusions["global_loop_minus_one_supported_by_asm"] is not False:
            raise AssertionError("loop-minus-one should stay unsupported by static asm")
        if conclusions["global_circular_wrap_supported_by_asm"] is not False:
            raise AssertionError("circular wrap should stay unsupported by static asm")
        evidence = report["evidence"]
        if "CVTTSS2SI R14D,XMM0" not in evidence["effective_span_truncation"]["text"]:
            raise AssertionError("missing effective span truncation evidence")
        if "IDIV R14D" not in evidence["table_step_divides_30000_by_effective_span"]["text"]:
            raise AssertionError("missing table step evidence")
        if "LEA EDX,[R12 + 0x1]" not in evidence["inner_underflow_advances_to_next_radius_row"]["text"]:
            raise AssertionError("missing next-row underflow evidence")
        markdown = out_md.read_text(encoding="utf-8")
        for needle in ("global_loop_minus_one_supported_by_asm", "offset < R14D", "next radius row"):
            if needle not in markdown:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] RadialBlur scatter static facts smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
