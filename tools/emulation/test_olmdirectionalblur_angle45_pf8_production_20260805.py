#!/usr/bin/env python3
"""Hash-bound 45-degree PF8 actual-AEX versus production Mac differential."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "tools/emulation/test_olmdirectionalblur_complete_pf8_compare_20260718.py"
ACTUAL_RAW = ROOT / "refs/conformance/olmdirectionalblur_angle45_actual_aex_pf8_20260805.argb8"
MAC_RAW = ROOT / "refs/conformance/olmdirectionalblur_angle45_mac_production_pf8_20260805.argb8"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_angle45_pf8_production_20260805.json"
NOTE = ROOT / "refs/conformance/olmdirectionalblur_angle45_pf8_production_20260805.md"
EXPECTED_ACTUAL_SHA256 = "ef5542e38f00b83d1f9135a9ace3511bbcd157f259436a6b261388ab1563b880"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("dblur_complete_pf8", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: cannot load base PF8 fixture")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if sys.platform != "darwin":
        raise SystemExit("BLOCKED_FAIL_CLOSED: Mac-only production seam")
    base = load_base()
    base.require_sha256(base.AEX, base.EXPECTED_AEX_SHA256, "OLMDirectionalBlur.aex")
    base.require_sha256(base.SOURCE, base.EXPECTED_SOURCE_SHA256, "case_0001 source")
    image = Image.open(base.SOURCE).convert("RGBA").crop((472, 262, 488, 278))
    rgba = image.tobytes()
    argb = bytes(
        value
        for pixel in (rgba[index:index + 4] for index in range(0, len(rgba), 4))
        for value in (pixel[3], pixel[0], pixel[1], pixel[2])
    )
    if sha256(argb) != base.EXPECTED_CROP_ARGB_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: input crop identity mismatch")
    with tempfile.TemporaryDirectory(prefix="olm_dblur_angle45_pf8_") as name:
        actual, actual_meta = base.capture_actual(45.0)
        if sha256(actual) != EXPECTED_ACTUAL_SHA256:
            raise RuntimeError("BLOCKED_FAIL_CLOSED: angle45 actual-AEX PF8 identity mismatch")
        mac, mac_meta = base.capture_mac(argb, Path(name), 45.0)
    mismatches = [index for index, pair in enumerate(zip(actual, mac)) if pair[0] != pair[1]]
    exact = len(actual) == 1024 and len(mac) == 1024 and not mismatches and mac_meta["exact"] == 1
    ACTUAL_RAW.write_bytes(actual)
    MAC_RAW.write_bytes(mac)
    result = {
        "schema": 1,
        "kind": "olmdirectionalblur_angle45_pf8_production_20260805",
        "status": "pass" if exact else "mismatch",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "16x16 PF8; angle=45, brightness=1, front-strength=8, all alpha-fade/sharp-tail/back/size/noise controls zero, render scale 1/1",
        "identity": {
            "aex_sha256": base.EXPECTED_AEX_SHA256,
            "source_sha256": base.EXPECTED_SOURCE_SHA256,
            "crop_argb_sha256": base.EXPECTED_CROP_ARGB_SHA256,
            "actual_aex_pf8_sha256": EXPECTED_ACTUAL_SHA256,
        },
        "actual_aex": {**actual_meta, "raw": str(ACTUAL_RAW.relative_to(ROOT))},
        "mac_production": {**mac_meta, "sha256": sha256(mac), "raw": str(MAC_RAW.relative_to(ROOT))},
        "comparison": {
            "byte_for_byte": not mismatches,
            "byte_count": len(actual),
            "mismatch_count": len(mismatches),
            "first_mismatch_byte": mismatches[0] if mismatches else None,
        },
        "boundary": {"production_dispatch_exact": exact, "mac_ae_exact_claim": False},
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    NOTE.write_text(
        "# OLMDirectionalBlur Angle 45 PF8 Production Differential\n\n"
        f"- Status: `{result['status']}`.\n"
        "- Scope: 16x16 PF8, angle 45, brightness 1, front strength 8; all other algorithm controls zero; scale 1/1.\n"
        f"- Actual-AEX and production Mac output: `{len(mismatches) == 0}`; {len(mismatches)} differing bytes out of {len(actual)}.\n"
        f"- Actual-AEX PF8 SHA-256: `{EXPECTED_ACTUAL_SHA256}`.\n"
        "- This proves the hash-bound fixture/core/production-dispatch boundary, not Mac AE rendering or other parameter values.\n\n"
        "Reproduction: `python3 tools/emulation/test_olmdirectionalblur_angle45_pf8_production_20260805.py`\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "mismatch_count": len(mismatches), "sha256": sha256(mac)}))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
