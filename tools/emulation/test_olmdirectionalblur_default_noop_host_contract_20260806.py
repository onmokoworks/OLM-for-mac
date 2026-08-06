#!/usr/bin/env python3
"""Pin the actual-AEX default tuple and its Windows/Mac AE no-op host route."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = ROOT / "refs/win_references/olm_fresh_instance_ranges_20260629/OLMmulti-effectrangecapture"
MANIFEST = REFERENCE_DIR / "reference_manifest.json"
UI_SETUP = ROOT / "refs/conformance/olmdirectionalblur_ui_setup_actual_aex_20260806.json"
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
EXPECTED_PNG_SHA256 = "e1597b6557a3018b78a21ea6cc8436ed93f1b19d25115ef747b051cf8086e4c7"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    case = next(c for c in manifest["cases"] if c["id"] == "range_default_olmdirectionalblur")
    effect = next(e for e in case["effects"] if e["name"] == "OLM DirectionalBlur")
    params = effect["params"]

    def values(name: str) -> list[object]:
        return [p.get("value") for p in params if p["name"] == name]

    assert values("Angle") == [0]
    assert values("Brightness Gain") == [1]
    assert values("Size Variation") == [0]
    assert values("Blur Strength") == [0, 0]
    assert values("Alpha Fade") == [0, 0]
    assert values("Noise Variation") == [0]
    assert values("Noise Type") == [1]
    assert values("Noise Layer") == [0]
    assert values("Seed") == [1]
    assert values("Offset") == [0]

    effect_png = REFERENCE_DIR / case["frame"]
    before_png = REFERENCE_DIR / case["before_effects_frame"]
    assert sha256(effect_png) == EXPECTED_PNG_SHA256
    assert sha256(before_png) == EXPECTED_PNG_SHA256
    assert effect_png.read_bytes() == before_png.read_bytes()

    setup = json.loads(UI_SETUP.read_text(encoding="utf-8"))
    rows = {row["disk_id"]: row for row in setup["params_setup"]["rows"]}
    assert rows[1]["angle_fixed"] == [0, 0, 0, 0]
    assert rows[2]["value_f64_bits"] == 0x3FF0000000000000
    assert rows[3]["values_fixed"][0] == 0
    assert rows[5]["values_i32"][0] == 0
    assert rows[10]["values_i32"][0] == 0
    assert rows[15]["values_fixed"][0] == 0
    assert rows[16]["popup"] == [1, 2, 1]
    assert rows[17]["layer_default"] == 0
    assert rows[18]["values_i32"][0] == 1
    assert rows[19]["angle_fixed"] == [0, 0, 0, 0]
    assert rows[20]["value_f64_bits"] == 0x4024000000000000

    source = SOURCE.read_text(encoding="utf-8")
    assert "const bool default_no_op" in source
    assert "case 16: CopyWorld<PF_Pixel16>" in source
    assert "case 32: CopyWorld<PF_PixelFloat>" in source
    assert "noise_checked_out = noise_err == PF_Err_NONE" in source

    print(json.dumps({
        "status": "pass",
        "actual_aex_default_tuple": "pinned from raw PARAMS_SETUP",
        "windows_ae_default_output": "byte-identical to before-effects PNG",
        "windows_png_sha256": EXPECTED_PNG_SHA256,
        "production_default_route": "row-wise identity PF8/PF16/PF32",
        "optional_noise_layer_none": "checkout failure is non-fatal until a consuming mode requires it",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
