#!/usr/bin/env python3
"""Front Alpha Fade PF8 actual-AEX versus production Mac differential."""

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
ACTUAL_RAW = ROOT / "refs/conformance/olmdirectionalblur_front_alpha_fade_actual_aex_pf8_20260805.argb8"
MAC_RAW = ROOT / "refs/conformance/olmdirectionalblur_front_alpha_fade_mac_production_pf8_20260805.argb8"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_front_alpha_fade_pf8_production_20260805.json"
NOTE = ROOT / "refs/conformance/olmdirectionalblur_front_alpha_fade_pf8_production_20260805.md"
EXPECTED_INPUT_SHA256 = "ff3ec821b6f91993890ac82ca6a9da8f931c3b4e2b459bee4d6cebf4e7f24f70"
EXPECTED_ACTUAL_SHA256 = "34be8aa0f98b7ee371de01499f3d17d8ff1c2fefdff8aeed91c4ed8569518978"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if sys.platform != "darwin":
        raise SystemExit("BLOCKED_FAIL_CLOSED: Mac-only production seam")
    base = load(BASE_PATH, "dblur_complete_pf8")
    alpha_fixture = load(ALPHA_PATH, "dblur_alpha_validity")
    base.require_sha256(base.AEX, base.EXPECTED_AEX_SHA256, "OLMDirectionalBlur.aex")
    source = alpha_fixture.build_input()
    if sha256(source) != EXPECTED_INPUT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: alpha/validity input identity mismatch")
    with tempfile.TemporaryDirectory(prefix="olm_dblur_front_alpha_fade_pf8_") as name:
        actual, actual_meta = base.capture_actual(
            0.0, source, front_strength=8, back_strength=0, front_alpha_fade=4
        )
        if sha256(actual) != EXPECTED_ACTUAL_SHA256:
            raise RuntimeError("BLOCKED_FAIL_CLOSED: Front Alpha Fade actual-AEX identity mismatch")
        mac, mac_meta = base.capture_mac(
            source, Path(name), 0.0,
            front_strength=8, back_strength=0, front_alpha_fade=4
        )
    mismatches = [index for index, pair in enumerate(zip(actual, mac)) if pair[0] != pair[1]]
    exact = len(actual) == 1024 and len(mac) == 1024 and not mismatches and mac_meta["exact"] == 1
    ACTUAL_RAW.write_bytes(actual)
    MAC_RAW.write_bytes(mac)
    result = {
        "schema": 1,
        "kind": "olmdirectionalblur_front_alpha_fade_pf8_production_20260805",
        "status": "pass" if exact else "mismatch",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "deterministic 16x16 straight ARGB PF8 with alpha 0/64/128/192/255; angle=0, brightness=1, front-strength=8, front-alpha-fade=4, back/tail/size/noise controls zero, render scale 1/1",
        "identity": {"aex_sha256": base.EXPECTED_AEX_SHA256, "input_argb_sha256": EXPECTED_INPUT_SHA256, "actual_aex_pf8_sha256": EXPECTED_ACTUAL_SHA256},
        "actual_aex": {**actual_meta, "raw": str(ACTUAL_RAW.relative_to(ROOT))},
        "mac_production": {**mac_meta, "sha256": sha256(mac), "raw": str(MAC_RAW.relative_to(ROOT))},
        "comparison": {"byte_for_byte": not mismatches, "byte_count": len(actual), "mismatch_count": len(mismatches), "first_mismatch_byte": mismatches[0] if mismatches else None},
        "boundary": {"production_dispatch_exact": exact, "mac_ae_exact_claim": False},
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    NOTE.write_text(
        "# OLMDirectionalBlur Front Alpha Fade PF8 Production Differential\n\n"
        f"- Status: `{result['status']}`.\n"
        "- Scope: deterministic 16x16 straight ARGB with alpha 0/64/128/192/255; Front Strength 8 and Front Alpha Fade 4; other algorithm controls zero.\n"
        f"- Actual-AEX and production Mac: `{not mismatches}`; {len(mismatches)} differing bytes out of {len(actual)}.\n"
        f"- Actual-AEX PF8 SHA-256: `{EXPECTED_ACTUAL_SHA256}`.\n"
        "- This proves the hash-bound fixture/core/production-dispatch boundary only; Mac AE and other fade values are not claimed.\n\n"
        "Reproduction: `python3 tools/emulation/test_olmdirectionalblur_front_alpha_fade_pf8_production_20260805.py`\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "sha256": sha256(mac), "mismatch_count": len(mismatches), "first_mismatch_byte": mismatches[0] if mismatches else None}))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
