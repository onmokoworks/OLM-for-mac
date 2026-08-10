#!/usr/bin/env python3
"""Gate the bounded Mode-4 canonical-angle family against actual AEX stages."""

from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmkirakira_mode4_canonical_angles_actual_aex_20260810.json"
CPP = ROOT / "tools/emulation/test_kirakira_mode4_canonical.cpp"
PRODUCTION = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
EXPECTED_AEX_SHA = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"
EXPECTED = ((9, 7, 0), (9, 9, 45), (9, 9, -45), (9, 9, 90))


def extent(major: int, minor: int, angle: float) -> int:
    radians = math.radians(angle)
    return max(major + 4, int(major * abs(math.cos(radians)) +
                              minor * abs(math.sin(radians)) + 4.0))


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "captured"
    assert report["aex_sha256"] == EXPECTED_AEX_SHA
    assert [(c["width"], c["height"], c["angle_degrees"]) for c in report["cases"]] == list(EXPECTED)
    source = PRODUCTION.read_text(encoding="utf-8")
    for expression in ("90.0 + glow_rotation", "glow_rotation",
                       "45.0 + glow_rotation", "-45.0 + glow_rotation"):
        assert expression in source
    assert "if (blur_mode == 4)" in source
    assert "mode4_rotated_scalar_admitted(" in source
    assert "return input;" in source
    # Public source work geometry 5x3 at default Glow Rotation 0 reaches these
    # exact rotated-leaf tuples for the four named directional controls.
    for angle, expected_wh in ((0, (9, 7)), (45, (9, 9)), (-45, (9, 9)), (90, (9, 9))):
        assert (extent(5, 3, angle), extent(3, 5, angle)) == expected_wh

    with tempfile.TemporaryDirectory(prefix="kira_mode4_canonical_") as td:
        executable = Path(td) / "canonical"
        subprocess.run(["c++", "-std=c++20", "-O2", "-ffp-contract=off",
                        str(CPP), "-o", str(executable)], check=True)
        digests = set()
        for case in report["cases"]:
            output = subprocess.check_output([
                str(executable), str(case["width"]), str(case["height"]),
                str(case["radius"]), str(case["angle_degrees"]),
            ], input="\n".join(case["source"]["words_u32"]) + "\n", text=True).splitlines()
            actual = {stage: [] for stage in ("forward", "recurrence", "final")}
            for line in output:
                stage, _index, word = line.split()
                actual[stage].append(f"0x{int(word, 16):08x}")
            for stage in actual:
                expected = case[stage]["words_u32"]
                assert len(actual[stage]) == len(expected) == case["width"] * case["height"]
                assert actual[stage] == expected
            digests.add(tuple(actual["final"]))
    assert len(digests) == 4
    print("PASS_OLMKIRAKIRA_MODE4_CANONICAL_ANGLES_ACTUAL_AEX_20260810 cases=4 stages=12 max_ulp=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
