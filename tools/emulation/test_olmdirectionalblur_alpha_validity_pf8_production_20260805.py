#!/usr/bin/env python3
"""PF8 alpha/validity fixture through actual AEX and production Mac."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "tools/emulation/test_olmdirectionalblur_complete_pf8_compare_20260718.py"
ACTUAL_RAW = ROOT / "refs/conformance/olmdirectionalblur_alpha_validity_actual_aex_pf8_20260805.argb8"
MAC_RAW = ROOT / "refs/conformance/olmdirectionalblur_alpha_validity_mac_production_pf8_20260805.argb8"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_alpha_validity_pf8_production_20260805.json"
NOTE = ROOT / "refs/conformance/olmdirectionalblur_alpha_validity_pf8_production_20260805.md"
EXPECTED_INPUT_SHA256 = "ff3ec821b6f91993890ac82ca6a9da8f931c3b4e2b459bee4d6cebf4e7f24f70"
EXPECTED_ACTUAL_SHA256 = "a92780c3b814a8bf496257f824fe534b7b64703362aee3c15d64033abda9febc"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("dblur_complete_pf8", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: cannot load base PF8 fixture")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_input() -> bytes:
    # Deterministic straight ARGB fixture. It includes zero-alpha pixels with
    # nonzero RGB, partial alpha, opaque pixels, and hard validity boundaries.
    pixels = bytearray()
    alpha_levels = (0, 64, 128, 192, 255)
    for y in range(16):
        for x in range(16):
            alpha = alpha_levels[(x // 3 + y // 4) % len(alpha_levels)]
            red = (x * 37 + y * 11 + 17) & 0xFF
            green = (x * 7 + y * 43 + 29) & 0xFF
            blue = (x * 19 + y * 23 + 71) & 0xFF
            pixels.extend((alpha, red, green, blue))
    return bytes(pixels)


def main() -> int:
    if sys.platform != "darwin":
        raise SystemExit("BLOCKED_FAIL_CLOSED: Mac-only production seam")
    base = load_base()
    base.require_sha256(base.AEX, base.EXPECTED_AEX_SHA256, "OLMDirectionalBlur.aex")
    source = build_input()
    input_sha = sha256(source)
    if input_sha != EXPECTED_INPUT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: alpha fixture input identity mismatch")
    with tempfile.TemporaryDirectory(prefix="olm_dblur_alpha_validity_pf8_") as name:
        actual, actual_meta = base.capture_actual(0.0, source)
        actual_sha = sha256(actual)
        if actual_sha != EXPECTED_ACTUAL_SHA256:
            raise RuntimeError("BLOCKED_FAIL_CLOSED: alpha fixture actual-AEX identity mismatch")
        mac, mac_meta = base.capture_mac(source, Path(name), 0.0)
    mismatches = [index for index, pair in enumerate(zip(actual, mac)) if pair[0] != pair[1]]
    exact = len(actual) == 1024 and len(mac) == 1024 and not mismatches and mac_meta["exact"] == 1
    ACTUAL_RAW.write_bytes(actual)
    MAC_RAW.write_bytes(mac)
    alpha_counts = Counter(source[index] for index in range(0, len(source), 4))
    result = {
        "schema": 1,
        "kind": "olmdirectionalblur_alpha_validity_pf8_production_20260805",
        "status": "pass" if exact else "mismatch",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "deterministic 16x16 straight ARGB PF8 with alpha 0/64/128/192/255; angle=0, brightness=1, front-strength=8, other algorithm controls zero, scale 1/1",
        "input": {"sha256": input_sha, "alpha_counts": {str(key): value for key, value in sorted(alpha_counts.items())}},
        "identity": {"aex_sha256": base.EXPECTED_AEX_SHA256, "actual_aex_pf8_sha256": actual_sha},
        "actual_aex": {**actual_meta, "raw": str(ACTUAL_RAW.relative_to(ROOT))},
        "mac_production": {**mac_meta, "sha256": sha256(mac), "raw": str(MAC_RAW.relative_to(ROOT))},
        "comparison": {"byte_for_byte": not mismatches, "byte_count": len(actual), "mismatch_count": len(mismatches), "first_mismatch_byte": mismatches[0] if mismatches else None},
        "boundary": {"production_dispatch_exact": exact, "mac_ae_exact_claim": False},
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    NOTE.write_text(
        "# OLMDirectionalBlur Alpha/Validity PF8 Production Differential\n\n"
        f"- Status: `{result['status']}`.\n"
        "- Input: deterministic 16x16 straight ARGB with alpha 0, 64, 128, 192, and 255, including nonzero RGB at alpha zero.\n"
        f"- Actual-AEX and production Mac: `{not mismatches}`; {len(mismatches)} differing bytes out of {len(actual)}.\n"
        f"- Input SHA-256: `{input_sha}`.\n- Actual-AEX PF8 SHA-256: `{actual_sha}`.\n"
        "- This proves the fixture/core/production-dispatch boundary only; Mac AE and other alpha/parameter families are not claimed.\n\n"
        "Reproduction: `python3 tools/emulation/test_olmdirectionalblur_alpha_validity_pf8_production_20260805.py`\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "input_sha256": input_sha, "actual_sha256": actual_sha, "mac_sha256": sha256(mac), "mismatch_count": len(mismatches), "first_mismatch_byte": mismatches[0] if mismatches else None}))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
