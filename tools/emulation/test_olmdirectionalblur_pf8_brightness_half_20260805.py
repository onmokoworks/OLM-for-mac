#!/usr/bin/env python3
"""PF8 255-scale/truncate writer gate for Brightness Gain 0.5."""

import hashlib
import tempfile
from pathlib import Path

from PIL import Image

import test_olmdirectionalblur_complete_pf8_compare_20260718 as base

EXPECTED = "20b63b4f408d7e865c1bcec9e48d4dffd21609e17280d3c656769cfc0d2ee10b"


def main() -> int:
    actual, actual_meta = base.capture_actual(brightness_gain=0.5)
    rgba = Image.open(base.SOURCE).convert("RGBA").crop((472, 262, 488, 278)).tobytes()
    argb = bytes(value for pixel in (rgba[i:i + 4] for i in range(0, len(rgba), 4))
                 for value in (pixel[3], pixel[0], pixel[1], pixel[2]))
    with tempfile.TemporaryDirectory(prefix="olm_dblur_pf8_gain_half_") as name:
        production, production_meta = base.capture_mac(argb, Path(name), brightness_gain=0.5)
    digest = hashlib.sha256(actual).hexdigest()
    if (actual_meta["natural_complete"] is not True or
            [call["callback"] for call in actual_meta["iterate_calls"]] !=
            ["0x180006980", "0x180006b30"] or
            len(actual) != 1024 or digest != EXPECTED or production != actual or
            actual_meta["input_rowbytes"] != 76 or production_meta["rowbytes"] != 76 or
            production_meta["exact"] != 1):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF8 Brightness Gain 0.5 exact gate failed")
    print({"status": "pass", "format": "ARGB8", "brightness_gain": 0.5,
           "bytes": len(actual), "rowbytes": 76, "sha256": digest,
           "callbacks": ["0x180006980", "0x180006b30"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
