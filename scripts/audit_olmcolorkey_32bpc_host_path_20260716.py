#!/usr/bin/env python3
"""Audit the bounded OLMColorKey Mac 32bpc source/evidence contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
PAIR = ROOT / "refs/conformance/olmcolorkey_32bpc_case0002_mac_pair_20260712.md"
EVIDENCE = ROOT / "refs/conformance/olmcolorkey_bitdepth_evidence_audit_20260715.md"
EVIDENCE_JSON = ROOT / "refs/conformance/olmcolorkey_bitdepth_evidence_audit_20260715.json"
OUT_JSON = ROOT / "refs/conformance/olmcolorkey_32bpc_host_path_proof_20260716.json"
OUT_MD = ROOT / "refs/conformance/olmcolorkey_32bpc_host_path_proof_20260716.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def isolate(text: str, name: str, next_name: str) -> str:
    if next_name == "extern":
        pattern = rf"static PF_Err\s+{name}\(.*?(?=\nextern \"C\")"
    else:
        pattern = rf"static PF_Err\s+{name}\(.*?\n\}}\n\n(?:static PF_Err\s+)?{next_name}\("
    match = re.search(pattern, text, re.S)
    if not match:
        raise AssertionError(f"could not isolate {name}")
    return match.group(0)


def build_report(root: Path = ROOT) -> dict:
    source = (root / SOURCE.relative_to(ROOT)).read_text(encoding="utf-8")
    pair = (root / PAIR.relative_to(ROOT)).read_text(encoding="utf-8")
    evidence = (root / EVIDENCE.relative_to(ROOT)).read_text(encoding="utf-8")
    evidence_json = json.loads((root / EVIDENCE_JSON.relative_to(ROOT)).read_text(encoding="utf-8"))

    smart = isolate(source, "SmartRender", "extern")
    render_world = re.search(r"static PF_Err\s+RenderWorld\(.*?\n\}\n\nstatic PF_Err", source, re.S)
    if not render_world:
        raise AssertionError("could not isolate RenderWorld")
    render_world_text = render_world.group(0)

    facts = {
        "smart_render_reads_explicit_bitdepth": "extra->input->bitdepth" in smart,
        "smart_render_captures_float_entry_at_bitdepth_32": "CapturePixelFloatEntryIfRequested(input_world, extra->input->bitdepth)" in smart,
        "smart_render_dispatches_explicit_bitdepth": "RenderWorld(input_world, output_world, info, extra->input->bitdepth)" in smart,
        "render_world_has_float_branch": "bitdepth == 32" in render_world_text and "RenderTyped<PF_PixelFloat>" in render_world_text,
        "float_pixel_traits_are_native_float": all(token in source for token in (
            "struct OLMCKPixelTraits<PF_PixelFloat>",
            "static float r(const PF_PixelFloat &p) { return p.red; }",
            "static float a(const PF_PixelFloat &p) { return p.alpha; }",
        )),
        "float_color_aware_declared": "PF_OutFlag2_FLOAT_COLOR_AWARE" in source,
        "smart_render_declared": "PF_OutFlag2_SUPPORTS_SMART_RENDER" in source,
        "mac_pair_is_host_conversion_blocked": "blocked-by-host-input-conversion" in pair,
        "mac_pair_not_ae_exact": "not 32bpc AE exact evidence" in pair,
        "existing_gate_remains_closed": evidence_json["mac_float_gate"]["ae_exact_claim_allowed"] is False and "forbidden from `AE exact`" in evidence,
    }
    missing = [name for name, value in facts.items() if not value]
    if missing:
        raise AssertionError(f"contract failed: {missing}")

    return {
        "kind": "olmcolorkey_32bpc_mac_host_path_static_audit",
        "schema": 1,
        "status": "pass_static_contract",
        "date": "2026-07-16",
        "scope": "Mac OLMColorKey source and conformance evidence only",
        "facts": facts,
        "source_sha256": sha256(root / SOURCE.relative_to(ROOT)),
        "evidence_inputs": [str(PAIR.relative_to(ROOT)), str(EVIDENCE.relative_to(ROOT))],
        "inferences": [
            "A 32bpc Mac execution is type-safe only when AE invokes SmartRender and supplies extra->input->bitdepth=32.",
            "The legacy PF_Cmd_RENDER callback remains an 8/16bpc boundary and cannot promote a 32bpc result to exact evidence.",
            "The current Mac pair remains blocked by host/input conversion, so no ColorKey algorithm change is justified from that residual.",
        ],
    }


def write_report(report: dict, root: Path = ROOT) -> None:
    (root / OUT_JSON.relative_to(ROOT)).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    facts = report["facts"]
    lines = [
        "# OLMColorKey 32bpc Mac Host-Path Static Audit - 2026-07-16",
        "",
        "## FACT",
        "",
        "- `SmartRender` reads `extra->input->bitdepth`, captures the float entry only at bit depth 32, and dispatches that explicit depth to `RenderWorld`.",
        "- `RenderWorld` has a `bitdepth == 32` branch using `RenderTyped<PF_PixelFloat>`; the float traits read native float channels.",
        "- The plug-in declares both `PF_OutFlag2_SUPPORTS_SMART_RENDER` and `PF_OutFlag2_FLOAT_COLOR_AWARE`.",
        "- The 2026-07-12 Mac case `0002` pair is classified `blocked-by-host-input-conversion`, and is not `AE exact`.",
        "- The existing 32bpc exactness gate remains closed pending a raw-float Mac/Windows comparison.",
        "",
        "## INFERENCE",
        "",
        "- The supported Mac 32bpc contract is the Smart Render path with an explicit float depth; the legacy callback cannot establish 32bpc conformance.",
        "- The current pair does not justify changing ColorKey comparison, Edge Thin, Edge Blur, or PNG handling.",
        "",
        "## Audit Boundary",
        "",
        f"- Source SHA-256: `{report['source_sha256']}`",
        "- Static audit: `python3 scripts/audit_olmcolorkey_32bpc_host_path_20260716.py`",
        "- Contract smoke: `python3 refs/scripts/smoke_audit_olmcolorkey_32bpc_host_path_20260716.py`",
        "- This checks source structure and retained evidence labels; it does not execute Smart Render or revalidate the raw EXR pair.",
        "",
    ]
    (root / OUT_MD.relative_to(ROOT)).write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.write:
        write_report(report)
    print(json.dumps(report, sort_keys=True))
    print("[OK] OLMColorKey 32bpc Mac host-path static audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
