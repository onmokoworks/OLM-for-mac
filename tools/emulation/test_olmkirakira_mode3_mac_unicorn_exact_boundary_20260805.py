#!/usr/bin/env python3
"""Exact bounded Mode-3 Mac/Unicorn fixture gate.

This reruns the pinned x86 AEX Gaussian body under the checked-in Unicorn
loader, captures its 9x7 CV_32FC1 input/output words, and requires the portable
Mac diagnostic primitive to reproduce all 63 output words exactly.  It is an
emulation boundary, not a live-Windows or AE-render claim.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
PROBE = ROOT / "tools/emulation/probe_olmkirakira_mode3_gaussian_output_actual_aex_20260713.py"
CPP = ROOT / "tools/emulation/test_kirakira_gaussian.cpp"
DISPATCH = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_dispatch_actual_aex_20260713.json"
EXPECTED_AEX_SHA256 = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"


def words(report: dict, path: tuple[str, ...]) -> list[str]:
    value = report
    for key in path:
        value = value[key]
    return [f"0x{int(word, 16):08x}" for word in value]


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == EXPECTED_AEX_SHA256
    dispatch = json.loads(DISPATCH.read_text(encoding="utf-8"))
    assert dispatch["status"] == "captured"
    uniform_allocations = [
        item for item in dispatch["evidence"]["allocation_raw"]
        if item["size"] == 84 and item["uniform_21f_runs"]
    ]
    assert len(uniform_allocations) == 1
    assert uniform_allocations[0]["raw_words_u32"] == ["0x3d430c31"] * 21

    with tempfile.TemporaryDirectory(prefix="olmkirakira_mode3_exact_") as temporary:
        temp = Path(temporary)
        fresh_json = temp / "fresh.json"
        fresh_md = temp / "fresh.md"
        subprocess.run(
            [
                "python3", str(PROBE), "--aex-path", str(AEX),
                "--output-json", str(fresh_json), "--output-md", str(fresh_md),
            ],
            cwd=ROOT,
            check=True,
        )
        report = json.loads(fresh_json.read_text(encoding="utf-8"))
        assert report["status"] == "captured"
        assert report["execution"]["aex_sha256"] == EXPECTED_AEX_SHA256
        assert report["execution"]["entry_hit_count"] == 1
        assert report["execution"]["return_hit_count"] == 1
        assert report["execution"]["input_shape"] == [7, 9]
        assert report["execution"]["length"] == 5
        assert report["execution"]["sigma_x"] == 2.5

        input_words = words(report, ("entry_capture", 0, "input_array", "mat", "words_u32"))
        output_words = words(report, ("output_capture", "output_array_after", "mat", "words_u32"))
        assert len(input_words) == len(output_words) == 63
        assert all(int(word, 16) != 0 for word in output_words)

        executable = temp / "kirakira_gaussian"
        subprocess.run(["c++", "-std=c++17", "-O2", str(CPP), "-o", str(executable)], check=True)
        emitted = subprocess.check_output(
            [str(executable), "--actual-aex-oracle"],
            text=True,
            input="\n".join(input_words) + "\n",
        ).splitlines()
        mac_words = [f"0x{int(line.split()[1], 16):08x}" for line in emitted]
        assert mac_words == output_words

    print("PASS_OLMKIRAKIRA_MODE3_MAC_UNICORN_EXACT_BOUNDARY_20260805 words=63 max_ulp=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
