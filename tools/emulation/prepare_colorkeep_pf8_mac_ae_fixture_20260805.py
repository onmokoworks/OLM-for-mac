#!/usr/bin/env python3
"""Generate the ColorKeep Mac AE PF8 fixture with the actual Windows AEX worker."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
AEX_SHA256 = "6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86"
OUT = ROOT / "refs/mac_validation_fixtures/colorkeep_pf8_20260805"
REPORT = ROOT / "refs/conformance/colorkeep_pf8_mac_ae_fixture_actual_aex_20260805.json"
KEYS_RGBA = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (128, 128, 128, 255), (255, 255, 0, 255)]
PIXELS_RGBA = [
    KEYS_RGBA[0], (254, 0, 0, 255), KEYS_RGBA[1], (0, 254, 0, 255),
    KEYS_RGBA[2], (0, 0, 254, 255), KEYS_RGBA[3], (129, 128, 128, 255),
    KEYS_RGBA[4], (255, 254, 0, 255), (17, 29, 43, 255), KEYS_RGBA[0],
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    assert digest(AEX) == AEX_SHA256
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    refcon = loader.host_alloc(0x38 + len(KEYS_RGBA) * 16)
    loader.write_bytes(refcon + 0x24, struct.pack("<i", len(KEYS_RGBA)))
    for index, (r, g, b, a) in enumerate(KEYS_RGBA):
        loader.write_bytes(refcon + 0x28 + index * 16, struct.pack("<4f", a / 255, r / 255, g / 255, b / 255))
    output: list[tuple[int, int, int, int]] = []
    instruction_counts = []
    for rgba in PIXELS_RGBA:
        r, g, b, a = rgba
        src = loader.host_alloc(4); dst = loader.host_alloc(4)
        loader.write_bytes(src, bytes((a, r, g, b))); loader.write_bytes(dst, b"\xa5" * 4)
        result = loader.call_function(0x180001580, int_args=[refcon, 0, 0, src, dst], max_instructions=20_000)
        oa, or_, og, ob = loader.read_bytes(dst, 4)
        output.append((or_, og, ob, oa)); instruction_counts.append(result["instructions"])
    OUT.mkdir(parents=True, exist_ok=True)
    input_png = OUT / "colorkeep_pf8_input.png"
    expected_png = OUT / "colorkeep_pf8_expected_actual_aex.png"
    expected_raw = OUT / "colorkeep_pf8_expected_actual_aex.argb8"
    image = Image.new("RGBA", (4, 3)); image.putdata(PIXELS_RGBA); image.save(input_png)
    image = Image.new("RGBA", (4, 3)); image.putdata(output); image.save(expected_png)
    expected_raw.write_bytes(b"".join(bytes((a, r, g, b)) for r, g, b, a in output))
    report = {
        "status": "exact_actual_aex_fixture", "aex": str(AEX.relative_to(ROOT)), "aex_sha256": AEX_SHA256,
        "worker_entry": "0x180001580", "depth": "PF8", "dimensions": [4, 3], "enabled_color_count": len(KEYS_RGBA),
        "keys_rgba8": [list(v) for v in KEYS_RGBA], "input_pixels_rgba8": [list(v) for v in PIXELS_RGBA],
        "expected_pixels_rgba8": [list(v) for v in output], "worker_instruction_counts": instruction_counts,
        "artifacts": {p.name: {"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in (input_png, expected_png, expected_raw)},
        "not_proven": ["After Effects host dispatch", "After Effects PNG handling of hidden RGB at alpha zero", "installed Mac plug-in AE loading"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
