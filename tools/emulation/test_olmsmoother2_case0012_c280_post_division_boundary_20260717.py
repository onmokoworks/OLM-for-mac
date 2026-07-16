#!/usr/bin/env python3
"""Fail-closed case0012 c280 boundary probe after the cce0 division proof.

The retained live witness has only three class pixels. Unknown neighborhood
bytes are zero-filled solely to make the AEX call executable; a zero polygon
under that scaffold is not treated as a case result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

from test_smoother2_fullchain_diff import call_c280_entry, call_cce0_entry  # noqa: E402
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402
from aex_loader import AexLoader  # noqa: E402

X, Y = 92, 841
DESCRIPTOR = [92, 841, 1, 92, 842, 2]
CASE_ID = "legacy_case_0012_gamma5_red_blue_current_aex"
SOURCE = {
    "previous": [0.18447503, 0.18447503, 0.18447503, 0.68235296],
    "center": [1.0, 1.0, 1.0, 1.0],
    "second": [0.125, 0.25, 0.75, 0.625],
}
# Exact retained live bytes. Every other class byte is explicitly unknown.
CLASS_PIXELS = {
    "center": [255, 255, 0, 255],
    "previous": [255, 0, 0, 0],
    "left": [0, 255, 0, 255],
}


def install(loader: AexLoader) -> SmootherStruct:
    ss = SmootherStruct(loader, 128, 850)
    ss.set_src_pixel(X, Y - 1, SOURCE["previous"])
    ss.set_src_pixel(X, Y, SOURCE["center"])
    ss.set_src_pixel(X, Y + 2, SOURCE["second"])
    ss.set_class_pixel(X, Y, *CLASS_PIXELS["center"])
    ss.set_class_pixel(X, Y - 1, *CLASS_PIXELS["previous"])
    ss.set_class_pixel(X - 1, Y, *CLASS_PIXELS["left"])
    return ss


def run_aex() -> dict:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls()
    ss = install(loader)
    c280 = call_c280_entry(loader, ss, X, Y)
    cce0 = call_cce0_entry(loader, ss, X, Y, gamma_colors=False)
    return {
        "c280": {"count": c280["count"], "vertices": c280["vertices"]},
        "cce0": cce0["rgba"],
        "engine": "checked_in_aex_unicorn_mac_local",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    aex = run_aex()
    portable = json.loads(subprocess.check_output([str(args.adapter)], text=True))
    differential = {
        "c280_count_equal": aex["c280"]["count"] == portable["c280"]["count"],
        "c280_vertices_equal": aex["c280"]["vertices"] == portable["c280"]["vertices"],
        "cce0_rgba_equal_1e-6": all(abs(a - b) <= 1e-6 for a, b in zip(aex["cce0"], portable["cce0"])),
    }
    non_diagnostic = aex["c280"]["count"] == 0 and portable["c280"]["count"] == 0
    result = {
        "verdict": "BLOCKED_CASE0012_POST_DIVISION_C280_NEIGHBOR_SEAM" if non_diagnostic else (
            "PASS_CASE0012_POST_DIVISION_C280_BOUNDARY" if all(differential.values()) else
            "FAIL_CASE0012_POST_DIVISION_C280_BOUNDARY"
        ),
        "scope": "Mac-only actual AEX c280/cce0 execution versus portable oracle; not Windows or AE exact",
        "case": {"id": CASE_ID, "descriptor": DESCRIPTOR},
        "aex": {"path": str(AEX_PATH.relative_to(ROOT)), "sha256": hashlib.sha256(AEX_PATH.read_bytes()).hexdigest(), "trace": aex},
        "portable": portable,
        "differential": differential,
        "retained_live_inputs": {"class_pixels": CLASS_PIXELS, "source_pixels": SOURCE},
        "blocker": (
            "Only center, previous, and left class pixels are retained from the live witness. "
            "All other class bytes were zero-filled; both paths therefore produce c280 count=0 "
            "and cce0 center pass-through. This cannot localize the live post-division c280 seam."
        ) if non_diagnostic else None,
        "claims_not_made": ["No Windows execution", "No After Effects host claim", "No AE exactness", "No live case continuation"],
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if non_diagnostic else (0 if result["verdict"].startswith("PASS") else 1)


if __name__ == "__main__":
    raise SystemExit(main())
