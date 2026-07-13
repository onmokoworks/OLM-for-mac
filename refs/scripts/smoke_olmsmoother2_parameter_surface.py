#!/usr/bin/env python3
"""Pin the Windows-visible OLMSmoother2 parameter ranges and defaults."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

text = SOURCE.read_text(encoding="utf-8")
required = [
    "0, 100, 0, 100, 100,\n\t              SMOOTHNESS_DISK_ID",
    "0, 100, 0, 100, 0,\n\t              EXTRA_SMOOTH_DISK_ID",
    "0, 255, 0, 255, 2,\n\t              SMOOTH_RANGE_DISK_ID",
    "1.0, 2.4, 1.0, 2.4, 2.4,",
]
for needle in required:
    assert needle in text, needle

manifest = ROOT / "refs/win_references/20260629_202911__olm_fresh_instance_defaults_20260629_windows_return/OLMmulti-effectdefaultcapture/reference_manifest.json"
assert manifest.is_file()
print("PASS OLMSmoother2 Windows parameter surface")
