#!/usr/bin/env python3
"""AE-free current-production replay of retained case_0006 actual-AEX values."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from test_olmblur_case0006_fullentry import (  # noqa: E402
    compile_and_run_portable,
    guest_argb_words,
    png_rgba16,
)


REPORT = ROOT / "refs/conformance/olmblur_case0006_actual_aex_fullworker_20260713.json"
AE_EVIDENCE = ROOT / "refs/conformance/olmblur_32bpc_case0006_ae_exact_20260727.json"
INPUT = ROOT / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006_before_effects.png"
REPORT_SHA256 = "e0ee8bcf5520cd2f9d890b079be23e1d86a30dd2d3797cf627a56760b16eb394"
AE_EVIDENCE_SHA256 = "542fd65d9d3730dabd564ea1c486e4c437016f49c32becae34ecd4dbc3b31cd0"
INPUT_SHA256 = "01fe02e7d14f670c9c21564e6962ecae7a5d23ff6cb67c8f19df244a6c098105"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
CURRENT_MAC_SHA256 = "c6a9e54b1760fc2c916f4551367666b58c100520b2c6644ebd809d60e3d9d83e"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    assert sha256(REPORT) == REPORT_SHA256
    assert sha256(AE_EVIDENCE) == AE_EVIDENCE_SHA256
    assert sha256(INPUT) == INPUT_SHA256

    report = json.loads(REPORT.read_text(encoding="utf-8"))
    ae = json.loads(AE_EVIDENCE.read_text(encoding="utf-8"))
    assert report["identity"]["case_id"] == "olmblur__case_0006"
    assert report["identity"]["aex_sha256"] == AEX_SHA256
    assert report["identity"]["params"] == {
        "blur": 5.0, "smoothness": 100.0, "repeat": 10,
        "bias": 1, "legacy": 0,
    }
    assert ae["case_id"] == "OLMBlur/case_0006"
    assert ae["contract"]["params"] == {
        "Blur Amount": 5, "Blur Amount readback": 5,
        "Blur Smoothness": 100, "Number of Repeat": 10,
        "Bias Direction": 1, "Legacy": 0,
    }
    assert ae["mac"]["loaded_plugin_proof"]["module_sha256"] == CURRENT_MAC_SHA256
    assert ae["windows"]["loaded_plugin_proof"]["aex_sha256"] == AEX_SHA256
    for branch in ("no_effect_control", "effect_on"):
        assert ae["comparison"][branch]["mismatched_values"] == 0
        assert ae["comparison"][branch]["max_raw_u32_delta"] == 0

    width, height, rgba = png_rgba16(INPUT)
    assert (width, height) == (1920, 1080)
    # This compiles probe_olmblur_case0006_portable.cpp together with the
    # current production core sources, then executes the real case parameters.
    current = compile_and_run_portable(guest_argb_words(rgba))
    retained = report["portable"]
    assert current["self_check"] is True
    assert current == retained

    stage_comparisons = report["comparison"]["stage_comparisons"]
    assert len(stage_comparisons) == 40
    assert all(row["exact"] for row in stage_comparisons)
    assert report["comparison"]["first_portable_difference"] is None
    for point, expected in {
        "(314,14)": (["0x45098f32"] * 3, [2201] * 3),
        "(29,71)": (["0x4435beb4"] * 3, [727] * 3),
    }.items():
        actual = current["final"][point]
        assert actual["pre_store_bits_hex"] == expected[0]
        assert actual["stored_rgb_words"] == expected[1]

    print(json.dumps({
        "status": "exact",
        "case_id": "olmblur__case_0006",
        "execution": "AE-free current production sources",
        "actual_aex_stage_boundaries": 40,
        "final_witnesses": current["final"],
        "current_exact_mac_binary_sha256": CURRENT_MAC_SHA256,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
