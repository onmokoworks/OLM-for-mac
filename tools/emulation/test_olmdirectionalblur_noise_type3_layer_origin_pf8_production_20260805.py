#!/usr/bin/env python3
"""Type 3 Layer extent-origin differential through actual AEX and production."""

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
ACTUAL_RAW = ROOT / "refs/conformance/olmdirectionalblur_noise_type3_layer_origin_actual_aex_pf8_20260805.argb8"
MAC_RAW = ROOT / "refs/conformance/olmdirectionalblur_noise_type3_layer_origin_mac_production_pf8_20260805.argb8"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_noise_type3_layer_origin_pf8_production_20260805.json"
NOTE = ROOT / "refs/conformance/olmdirectionalblur_noise_type3_layer_origin_pf8_production_20260805.md"
EXPECTED_INPUT_SHA256 = "ff3ec821b6f91993890ac82ca6a9da8f931c3b4e2b459bee4d6cebf4e7f24f70"
EXPECTED_PF8_SHA256 = "8668620ad73809172d03a6def3a46a19a5c40ef5529722b97c696bb51b92ef5d"
SOURCE_EXTENT = [0, 0, 16, 16]
LAYER_EXTENT = [2, 1, 18, 17]


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
    source = load(ALPHA_PATH, "dblur_alpha_validity").build_input()
    base.require_sha256(base.AEX, base.EXPECTED_AEX_SHA256, "OLMDirectionalBlur.aex")
    if sha256(source) != EXPECTED_INPUT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: source/Layer identity mismatch")
    settings = dict(front_strength=8, noise_variation=25.0, noise_type=3,
                    seed=1, noise_offset=0, thickness=10.0)
    with tempfile.TemporaryDirectory(prefix="olm_dblur_type3_layer_origin_") as name:
        actual, actual_meta = base.capture_actual(
            0.0, source, **settings,
            noise_layer_row_padding=28, noise_layer_origin=(2, 1)
        )
        if (actual_meta["input_extent_hint"], actual_meta["noise_layer_extent_hint"]) != (SOURCE_EXTENT, LAYER_EXTENT):
            raise RuntimeError("BLOCKED_FAIL_CLOSED: actual-AEX origin contract was not exercised")
        if sha256(actual) != EXPECTED_PF8_SHA256:
            raise RuntimeError("BLOCKED_FAIL_CLOSED: origin actual-AEX PF8 identity mismatch")
        mac, mac_meta = base.capture_mac(
            source, Path(name), 0.0, **settings, noise_layer_argb=source,
            noise_layer_row_padding=28, noise_layer_origin=(2, 1)
        )
        if (mac_meta["input_extent_hint"], mac_meta["noise_layer_extent_hint"]) != (SOURCE_EXTENT, LAYER_EXTENT):
            raise RuntimeError("BLOCKED_FAIL_CLOSED: production origin contract was not exercised")
    mismatches = [index for index, pair in enumerate(zip(actual, mac)) if pair[0] != pair[1]]
    exact = len(actual) == 1024 and len(mac) == 1024 and not mismatches and mac_meta["exact"] == 1
    ACTUAL_RAW.write_bytes(actual)
    MAC_RAW.write_bytes(mac)
    result = {
        "schema": 1,
        "kind": "olmdirectionalblur_noise_type3_layer_origin_pf8_production_20260805",
        "status": "pass" if exact else "mismatch",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "16x16 PF8 Type 3 source extent [0,0,16,16], Layer extent [2,1,18,17], source rowbytes 76, Layer rowbytes 92; Front Strength 8, Noise Variation 25",
        "geometry": {"dimensions": {"source": [16, 16], "layer": [16, 16]}, "extent_hints": {"source": SOURCE_EXTENT, "layer": LAYER_EXTENT}, "rowbytes": {"source": 76, "layer": 92}},
        "semantics": {"actual_aex_equal_dimension_layer_sampling": "checked-out buffer local (0,0) binds to render origin; differing Layer extent origin does not translate the field", "production_binding": "field builder receives render origin for both local Layer buffer and render world"},
        "pre_fix_localization": {"mismatch_count": 363, "first_mismatch_byte": 13, "first_mismatch_pixel": [3, 0], "first_mismatch_channel": "R", "actual": 148, "translated_layer_origin_candidate": 145, "first_divergent_stage": "Layer field coordinate formation before rowdriver/writeback"},
        "identity": {"aex_sha256": base.EXPECTED_AEX_SHA256, "source_and_layer_argb_sha256": EXPECTED_INPUT_SHA256, "actual_aex_pf8_sha256": EXPECTED_PF8_SHA256},
        "actual_aex": {**actual_meta, "raw": str(ACTUAL_RAW.relative_to(ROOT))},
        "mac_production": {**mac_meta, "sha256": sha256(mac), "raw": str(MAC_RAW.relative_to(ROOT))},
        "comparison": {"byte_for_byte": not mismatches, "byte_count": len(actual), "mismatch_count": len(mismatches), "first_mismatch_byte": mismatches[0] if mismatches else None},
        "boundary": {"different_layer_extent_origin_exact": exact, "different_layer_size_claim": False, "mac_ae_exact_claim": False},
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    NOTE.write_text(
        "# OLMDirectionalBlur Type 3 Layer Origin PF8 Differential\n\n"
        f"- Status: `{result['status']}`.\n"
        "- Source extent `[0,0,16,16]`; Layer extent `[2,1,18,17]`; rowbytes 76 and 92 respectively.\n"
        "- Actual AEX treats the equal-dimension checked-out Layer buffer as render-local; the differing extent origin does not translate its field samples.\n"
        f"- Actual-AEX and production: `{not mismatches}`; {len(mismatches)} differing bytes out of {len(actual)}; SHA-256 `{EXPECTED_PF8_SHA256}`.\n"
        "- Before the binding fix, translating by the Layer extent caused 363 differing bytes; the first was R at pixel (3,0), actual 148 versus 145.\n"
        "- Different Layer size and Mac AE remain unclaimed.\n\n"
        "Reproduction: `python3 tools/emulation/test_olmdirectionalblur_noise_type3_layer_origin_pf8_production_20260805.py`\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "extents": [SOURCE_EXTENT, LAYER_EXTENT], "sha256": sha256(mac), "mismatch_count": len(mismatches)}))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
