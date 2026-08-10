#!/usr/bin/env python3
"""Gate the bounded geometry-general Mode-3 Length 3/50 contract."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmkirakira_mode3_geometry_generalization_actual_aex_20260810.json"
CPP = ROOT / "tools/emulation/test_kirakira_mode3_default50_canonical.cpp"
CORE = ROOT / "core/kirakira_gaussian.h"
PRODUCTION = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
EXPECTED_AEX_SHA = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "captured" and report["aex_sha256"] == EXPECTED_AEX_SHA
    assert len(report["cases"]) == 32
    assert {(c["width"], c["height"]) for c in report["cases"]} == {
        (36, 22), (39, 39), (39, 30), (68, 40), (74, 74), (75, 57),
    }
    assert {c["length"] for c in report["cases"]} == {3, 5, 7, 9, 50}
    assert {c["angle_degrees"] for c in report["cases"]} == {0, 17, 45, -45}
    assert all(c["crt_initializer_callbacks"] == 50 and
               c["gaussian_entry_hits"] == c["gaussian_return_hits"] == 1 and
               c["warp_call_count"] == 2 for c in report["cases"])

    core = CORE.read_text(encoding="utf-8")
    assert "length == 3 || length == 5 || length == 7 || length == 9 || length == 50" in core
    production = PRODUCTION.read_text(encoding="utf-8")
    assert "mode3_gaussian_admitted(rw, rh, length)" in production
    assert "if (blur_mode == 3 && !mode3_admitted) return input;" in production
    assert "prepare_actual_aex_nonfused(length)" in production
    assert "if (bitdepth == 8) return RenderTyped<PF_Pixel8>" in production
    assert "if (bitdepth == 16) return RenderTyped<PF_Pixel16>" in production
    assert "if (bitdepth == 32) return RenderTyped<PF_PixelFloat>" in production

    total_words = 0
    finals = set()
    with tempfile.TemporaryDirectory(prefix="kira_mode3_geometry_general_") as td:
        executable = Path(td) / "mode3"
        subprocess.run(["c++", "-std=c++20", "-O2", "-ffp-contract=off",
                        str(CPP), "-o", str(executable)], check=True)
        for case in report["cases"]:
            lines = subprocess.check_output([
                str(executable), str(case["width"]), str(case["height"]),
                str(case["angle_degrees"]), str(case["length"]),
            ], input="\n".join(case["source"]["words_u32"]) + "\n", text=True).splitlines()
            actual = {stage: [] for stage in ("forward", "gaussian", "final")}
            for line in lines:
                stage, _index, word = line.split()
                actual[stage].append(f"0x{int(word, 16):08x}")
            for stage, words in actual.items():
                assert words == case[stage]["words_u32"]
                total_words += len(words)
            finals.add((case["width"], case["height"], case["length"],
                        case["angle_degrees"], tuple(actual["final"])))
    assert total_words == 248436 and len(finals) == 32
    print("PASS_OLMKIRAKIRA_MODE3_GEOMETRY_GENERALIZATION_ACTUAL_AEX_20260810 cases=32 words=248436 max_ulp=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
