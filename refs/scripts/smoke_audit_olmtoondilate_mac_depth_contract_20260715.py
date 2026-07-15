#!/usr/bin/env python3
"""Audit the ToonDilate Mac depth callback boundary and evidence labels."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
MAC_PAIR = ROOT / "refs/conformance/olmtoondilate_32bpc_case0001_mac_pair_20260712.md"
AUDIT = ROOT / "refs/conformance/olmtoondilate_bitdepth_conformance_20260715.md"
PROBE_STATUS = ROOT / "refs/conformance/bitdepth_32bpc_probe_status_20260703.md"
OUT_JSON = ROOT / "refs/conformance/olmtoondilate_mac_depth_contract_20260715.json"
OUT_MD = ROOT / "refs/conformance/olmtoondilate_mac_depth_contract_20260715.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    mac_pair = MAC_PAIR.read_text(encoding="utf-8")
    audit = AUDIT.read_text(encoding="utf-8")
    probe_status = PROBE_STATUS.read_text(encoding="utf-8")

    render = re.search(r"static PF_Err\s+Render\(.*?\n}\n\ntypedef struct", source, re.S)
    smart_render = re.search(r"static PF_Err\s+SmartRender\(.*?\n}\n\nextern", source, re.S)
    require(render and smart_render, "could not isolate Mac render callbacks")
    render_text = render.group(0)
    smart_text = smart_render.group(0)

    require("PF_WORLD_IS_DEEP(output) ? 16 : 8" in render_text, "legacy callback depth boundary changed")
    require("RenderWorld(&params[OLMTOONDILATE_INPUT]->u.ld, output, info, bitdepth)" in render_text,
            "legacy callback no longer uses the typed renderer")
    require("extra->input->bitdepth" in smart_text, "Smart Render no longer supplies explicit depth")
    require("RenderWorld(input_world, output_world, info, extra->input->bitdepth)" in smart_text,
            "Smart Render no longer dispatches through the typed renderer")
    require("bitdepth == 32" in source and "RenderTyped<PF_PixelFloat>" in source,
            "float renderer branch missing")
    require("PF_OutFlag2_FLOAT_COLOR_AWARE" in source and "PF_OutFlag2_SUPPORTS_SMART_RENDER" in source,
            "float-aware Smart Render contract missing")

    require("blocked-by-host-input-conversion" in mac_pair, "Mac 32bpc pair is missing its host classification")
    require("CLASSIFICATION" in mac_pair and "AE exact" not in mac_pair,
            "Mac 32bpc pair must remain non-exact evidence")
    require("32bpc" in audit and "not\n  itself a cross-host `AE exact` result" in audit,
            "ToonDilate audit lost its 32bpc non-exact boundary")
    require("probe-only-png-return" in probe_status, "32bpc probe status lost its PNG-only classification")

    report = {
        "kind": "olmtoondilate_mac_depth_contract_audit",
        "schema": 1,
        "status": "pass",
        "facts": {
            "legacy_pf_cmd_render_depths": [8, 16],
            "smart_render_depth_source": "extra->input->bitdepth",
            "smart_render_float_branch": True,
            "float_color_aware": True,
            "mac_32bpc_pair_classification": "blocked-by-host-input-conversion",
            "mac_32bpc_ae_exact": False,
        },
        "inferences": [
            "Mac 32bpc execution is evidence-backed only on the advertised Smart Render path.",
            "The legacy PF_Cmd_RENDER callback must not be used as proof of 32bpc support.",
            "The current 32bpc float return remains a host/input probe, not AE exact evidence.",
        ],
    }
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "# OLMToonDilate Mac Depth Contract Audit - 2026-07-15\n\n"
        "## FACT\n\n"
        "- The legacy `PF_Cmd_RENDER` callback selects only 8/16bpc via `PF_WORLD_IS_DEEP(output)`.\n"
        "- The advertised Smart Render callback dispatches the explicit `extra->input->bitdepth`, including `PF_PixelFloat` for 32bpc.\n"
        "- The Mac 32bpc effect/control pair is classified `blocked-by-host-input-conversion`; it is not `AE exact`.\n"
        "- The existing 32bpc probe evidence is PNG-only/non-float-preserving and remains probe-only.\n\n"
        "## INFERENCE\n\n"
        "- Mac 32bpc support is evidenced only when AE invokes the float-aware Smart Render path.\n"
        "- The legacy callback boundary cannot promote a 32bpc probe to an exact claim.\n\n"
        "## Gate\n\n"
        "`python3 refs/scripts/smoke_audit_olmtoondilate_mac_depth_contract_20260715.py`\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    print("[OK] ToonDilate Mac depth callback and 32bpc evidence labels")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
