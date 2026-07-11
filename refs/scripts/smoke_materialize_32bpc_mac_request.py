#!/usr/bin/env python3
"""Smoke test the 32bpc Mac AE request bridge materializer."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "materialize_32bpc_mac_request.py"
SPEC = ROOT / "refs" / "reference_requests" / "olm_bitdepth_32bpc_colorkey_float_20260710.json"
SOURCE = ROOT / "refs" / "reports" / "ae_host_validation_20260618_232926" / "normalized_refs" / "OLMColorKey"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_32bpc_bridge_") as tmp:
        output = Path(tmp) / "bridge"
        subprocess.run([
            sys.executable, str(SCRIPT), "--spec", str(SPEC), "--source-reference", str(SOURCE),
            "--output", str(output), "--case-id", "olmcolorkey__case_0001",
        ], check=True)
        request = json.loads((output / "request_manifest.json").read_text(encoding="utf-8"))
        reference = json.loads((output / "reference_manifest.json").read_text(encoding="utf-8"))
        result = json.loads((output / "AE_32BPC_RESULT.template.json").read_text(encoding="utf-8"))
        assert request["render_set"]["bits_per_channel"] == 32
        assert request["cases"][0]["frame"].endswith(".exr")
        assert reference["project"]["bits_per_channel"] == 32
        assert reference["comp"]["width"] == 1920
        assert reference["comp"]["height"] == 1080
        assert len(reference["cases"][0]["effects"][0]["params"]) == 219
        assert result["cases"][0]["output_format"] == "exr"
        assert (output / "raw_32bpc_request.json").is_file()
        assert list((output / "input").glob("*.png"))
    print("[OK] 32bpc Mac AE bridge materialization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
