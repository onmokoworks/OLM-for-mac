#!/usr/bin/env python3
"""Back-only PF8 actual-AEX versus production Mac differential."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "tools/emulation/test_olmdirectionalblur_complete_pf8_compare_20260718.py"
ALPHA_PATH = ROOT / "tools/emulation/test_olmdirectionalblur_alpha_validity_pf8_production_20260805.py"
ACTUAL_RAW = ROOT / "refs/conformance/olmdirectionalblur_back_strength_actual_aex_pf8_20260805.argb8"
MAC_RAW = ROOT / "refs/conformance/olmdirectionalblur_back_strength_mac_production_pf8_20260805.argb8"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_back_strength_pf8_production_20260805.json"
NOTE = ROOT / "refs/conformance/olmdirectionalblur_back_strength_pf8_production_20260805.md"
EXPECTED_INPUT_SHA256 = "ff3ec821b6f91993890ac82ca6a9da8f931c3b4e2b459bee4d6cebf4e7f24f70"
EXPECTED_ACTUAL_SHA256 = "8151ac88bf148e6748f749012353e58d4654ba3df38020a5ee993f672844c088"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("dblur_complete_pf8", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: cannot load base PF8 fixture")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_alpha_fixture():
    spec = importlib.util.spec_from_file_location("dblur_alpha_validity", ALPHA_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: cannot load alpha/validity fixture")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if sys.platform != "darwin":
        raise SystemExit("BLOCKED_FAIL_CLOSED: Mac-only production seam")
    base = load_base()
    base.require_sha256(base.AEX, base.EXPECTED_AEX_SHA256, "OLMDirectionalBlur.aex")
    argb = load_alpha_fixture().build_input()
    if sha256(argb) != EXPECTED_INPUT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: alpha/validity input identity mismatch")
    with tempfile.TemporaryDirectory(prefix="olm_dblur_back_strength_pf8_") as name:
        actual, actual_meta = base.capture_actual(
            0.0, argb, front_strength=0, back_strength=8
        )
        actual_sha = sha256(actual)
        if actual_sha != EXPECTED_ACTUAL_SHA256:
            raise RuntimeError("BLOCKED_FAIL_CLOSED: back-only actual-AEX identity mismatch")
        mac, mac_meta = base.capture_mac(
            argb, Path(name), 0.0, front_strength=0, back_strength=8
        )
    mismatches = [index for index, pair in enumerate(zip(actual, mac)) if pair[0] != pair[1]]
    exact = len(actual) == 1024 and len(mac) == 1024 and not mismatches and mac_meta["exact"] == 1
    ACTUAL_RAW.write_bytes(actual)
    MAC_RAW.write_bytes(mac)
    result = {
        "schema": 1,
        "kind": "olmdirectionalblur_back_strength_pf8_production_20260805",
        "status": "pass" if exact else "mismatch",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "deterministic 16x16 straight ARGB PF8 with alpha 0/64/128/192/255; angle=0, brightness=1, front-strength=0, back-strength=8, fade/tail/size/noise controls zero, render scale 1/1",
        "identity": {"aex_sha256": base.EXPECTED_AEX_SHA256, "input_argb_sha256": EXPECTED_INPUT_SHA256, "actual_aex_pf8_sha256": actual_sha},
        "actual_aex": {**actual_meta, "raw": str(ACTUAL_RAW.relative_to(ROOT))},
        "mac_production": {**mac_meta, "sha256": sha256(mac), "raw": str(MAC_RAW.relative_to(ROOT))},
        "comparison": {"byte_for_byte": not mismatches, "byte_count": len(actual), "mismatch_count": len(mismatches), "first_mismatch_byte": mismatches[0] if mismatches else None},
        "boundary": {"production_dispatch_exact": exact, "mac_ae_exact_claim": False},
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    NOTE.write_text(
        "# OLMDirectionalBlur Back Strength PF8 Production Differential\n\n"
        f"- Status: `{result['status']}`.\n"
        "- Scope: deterministic 16x16 straight ARGB with alpha 0/64/128/192/255; angle 0, brightness 1, front strength 0, back strength 8; all fade/tail/size/noise controls zero; scale 1/1.\n"
        f"- Actual-AEX and production Mac: `{not mismatches}`; {len(mismatches)} differing bytes out of {len(actual)}.\n"
        f"- Actual-AEX PF8 SHA-256: `{actual_sha}`.\n"
        "- This proves the fixture/core/production-dispatch boundary only; Mac AE and other Back settings are not claimed.\n\n"
        "Reproduction: `python3 tools/emulation/test_olmdirectionalblur_back_strength_pf8_production_20260805.py`\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "actual_sha256": actual_sha, "mac_sha256": sha256(mac), "mismatch_count": len(mismatches), "first_mismatch_byte": mismatches[0] if mismatches else None}))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
