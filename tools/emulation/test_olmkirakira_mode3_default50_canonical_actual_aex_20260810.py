#!/usr/bin/env python3
"""Gate Mode-3 UI-default Length 50 at the four canonical ray angles."""

from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmkirakira_mode3_default50_canonical_actual_aex_20260810.json"
CPP = ROOT / "tools/emulation/test_kirakira_mode3_default50_canonical.cpp"
PRODUCTION = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
EXPECTED_AEX_SHA = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"
EXPECTED = ((9, 7, 0), (9, 9, 45), (9, 9, -45), (9, 9, 90))


def extent(major: int, minor: int, angle: float) -> int:
    radians = math.radians(angle)
    return max(major + 4, int(major * abs(math.cos(radians)) +
                              minor * abs(math.sin(radians)) + 4.0))


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "captured" and report["aex_sha256"] == EXPECTED_AEX_SHA
    assert [(c["width"], c["height"], c["angle_degrees"]) for c in report["cases"]] == list(EXPECTED)
    assert all(c["length"] == 50 and c["gaussian_entry_hits"] == 1 and
               c["gaussian_return_hits"] == 1 and c["warp_call_count"] == 2 and
               c["crt_initializer_callbacks"] == 50 for c in report["cases"])

    source = PRODUCTION.read_text(encoding="utf-8")
    ray_routes = (
        "make_ray(info.vertical_length, 90.0 + glow_rotation)",
        "make_ray(info.horizontal_length, glow_rotation)",
        "make_ray(info.diagonal_length, 45.0 + glow_rotation)",
        "make_ray(info.diagonal2_length, -45.0 + glow_rotation)",
    )
    assert all(route in source for route in ray_routes)
    assert source.count("AddColoredUnion(glow,") >= 5
    assert source.count("AddColoredMerge2(glow,") >= 5
    assert "if (blur_mode == 3 && !mode3_admitted) return input;" in source
    assert "if (bitdepth == 8) return RenderTyped<PF_Pixel8>" in source
    assert "if (bitdepth == 16) return RenderTyped<PF_Pixel16>" in source
    assert "if (bitdepth == 32) return RenderTyped<PF_PixelFloat>" in source
    for angle, expected_wh in ((0, (9, 7)), (45, (9, 9)), (-45, (9, 9)), (90, (9, 9))):
        assert (extent(5, 3, angle), extent(3, 5, angle)) == expected_wh

    with tempfile.TemporaryDirectory(prefix="kira_mode3_default50_") as td:
        executable = Path(td) / "mode3"
        subprocess.run(["c++", "-std=c++20", "-O2", "-ffp-contract=off",
                        str(CPP), "-o", str(executable)], check=True)
        finals = set()
        for case in report["cases"]:
            lines = subprocess.check_output([
                str(executable), str(case["width"]), str(case["height"]),
                str(case["angle_degrees"]),
            ], input="\n".join(case["source"]["words_u32"]) + "\n", text=True).splitlines()
            actual = {stage: [] for stage in ("forward", "gaussian", "final")}
            for line in lines:
                stage, _index, word = line.split()
                actual[stage].append(f"0x{int(word, 16):08x}")
            for stage, words in actual.items():
                assert words == case[stage]["words_u32"]
            finals.add(tuple(actual["final"]))
    assert len(finals) == 4
    print("PASS_OLMKIRAKIRA_MODE3_DEFAULT50_CANONICAL_ACTUAL_AEX_20260810 cases=4 stages=12 max_ulp=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
