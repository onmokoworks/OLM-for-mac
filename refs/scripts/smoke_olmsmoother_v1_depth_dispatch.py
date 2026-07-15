#!/usr/bin/env python3
"""Fail-closed static source smoke for the standalone OLMSmoother v1 depth lane.

This is a boundary smoke, not an AE-exactness claim.  It guards the local v1
port's typed 8/16/float dispatch and the Smart Render bit-depth handoff while
keeping the separate v2 forced-v1 compatibility command visible.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing {label}: {needle}")


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    port = root / "mac" / "OLMSmoother" / "Mac" / "OLMSmoother_port.cpp"
    request = root / "refs" / "reference_requests" / "olmsmoother_v1_bitdepth_16_32bpc_software_20260715.json"
    compat = root / "refs" / "scripts" / "smoke_olmsmoother2_v1_compat_cli.py"

    source = port.read_text(encoding="utf-8")
    require(source, "if (bitdepth == 8)", "8bpc dispatch")
    require(source, "RenderEntryChain<PF_Pixel8, PF_Iterate8Suite1>", "typed 8bpc chain")
    require(source, "} else if (bitdepth == 16)", "16bpc dispatch")
    require(source, "RenderEntryChain<PF_Pixel16, PF_Iterate16Suite1>", "typed 16bpc chain")
    require(source, "RenderEntryChain<PF_PixelFloat, PF_IterateFloatSuite1>", "typed 32bpc chain")
    require(source, "extra->input->bitdepth", "Smart Render bit-depth handoff")
    require(source, "ScanlinePixelFloat_Main", "float main callback")
    require(source, "ScanlinePixelFloat_KeyMask", "float key-mask callback")
    require(source, "// 32-bit float", "v1 float evidence boundary")
    require(source, "no Win analogue.", "v1 float evidence boundary")

    manifest = json.loads(request.read_text(encoding="utf-8"))
    if manifest["effect"]["variant"] != "v1":
        raise AssertionError("request is not scoped to v1")
    if manifest["effect"]["v2_is_out_of_scope"] is not True:
        raise AssertionError("request does not exclude v2")
    render_sets = {item["id"]: item for item in manifest["render_sets"]}
    if render_sets["software_16bpc"]["bits_per_channel"] != 16:
        raise AssertionError("16bpc render set drifted")
    if not render_sets["software_16bpc"]["acceptance"].startswith("integer-exact"):
        raise AssertionError("16bpc acceptance policy drifted")
    if render_sets["software_32bpc"]["bits_per_channel"] != 32:
        raise AssertionError("32bpc render set drifted")
    if not render_sets["software_32bpc"]["acceptance"].startswith("probe-only"):
        raise AssertionError("32bpc acceptance policy drifted")

    compat_text = compat.read_text(encoding="utf-8")
    require(compat_text, "--force-version 1", "forced-v1 compatibility gate")
    print("OLMSmoother v1 static depth contract smoke: PASS")
    print("FACT: source-level 8/16/float branches and Smart Render bit-depth forwarding are present")
    print("FACT: 16bpc is exact-eligible only after returned cross-host evidence")
    print("FACT: 32bpc remains probe-only; v2 is out of scope for the v1 request")
    print("INFERENCE: this static smoke does not execute dispatch; float callbacks remain copy-through boundaries and it proves neither v1-v2 equivalence nor AE exactness")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"OLMSmoother v1 static depth contract smoke: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
