#!/usr/bin/env python3
"""Audit three KiraKira parameters from AE surface to binary and Mac wiring."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
HEADER = ROOT / "mac/OLMKiraKira/OLMKiraKira.h"
DEFAULTS = ROOT / "refs/win_references/olm_fresh_instance_defaults_20260629/OLMmulti-effectdefaultcapture/reference_manifest.json"
RANGES = ROOT / "refs/win_references/olm_fresh_instance_ranges_20260629/OLMmulti-effectrangecapture/reference_manifest.json"
REPORT_JSON = ROOT / "refs/conformance/olmkirakira_unconsumed_parameters_20260718.json"
REPORT_MD = ROOT / "refs/conformance/olmkirakira_unconsumed_parameters_20260718.md"
TARGETS = ("Approximated Input", "Fade Out", "Highlight Radius")


def find_params(value: object) -> dict[str, dict[str, object]]:
    found: dict[str, dict[str, object]] = {}
    if isinstance(value, dict):
        name = value.get("name")
        path = value.get("path")
        if name in TARGETS and isinstance(path, list) and path[:1] == ["OLM Kira Kira"]:
            found[str(name)] = value
        for child in value.values():
            found.update(find_params(child))
    elif isinstance(value, list):
        for child in value:
            found.update(find_params(child))
    return found


def require(text: str, needles: list[str], label: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{label}: missing {missing}")


def main() -> int:
    decomp = DECOMP.read_text(encoding="utf-8")
    asm = ASM.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    header = HEADER.read_text(encoding="utf-8")
    defaults = find_params(json.loads(DEFAULTS.read_text(encoding="utf-8")))
    ranges = find_params(json.loads(RANGES.read_text(encoding="utf-8")))
    if set(defaults) != set(TARGETS) or set(ranges) != set(TARGETS):
        raise AssertionError("fresh manifests do not contain exactly the three KiraKira targets")

    expected_surface = {
        "Approximated Input": ("OLM OLM Kira Kira-0010", 4, 0, 0, 1),
        "Fade Out": ("OLM OLM Kira Kira-0027", 7, 0, 0, 1),
        "Highlight Radius": ("OLM OLM Kira Kira-0006", 34, 0, 0, 500),
    }
    surface: dict[str, object] = {}
    for name, expected in expected_surface.items():
        item = defaults[name]
        ranged = ranges[name]
        actual = (
            item.get("match_name"), item.get("property_index"), item.get("value"),
            ranged.get("range_metadata", {}).get("minValue"),
            ranged.get("range_metadata", {}).get("maxValue"),
        )
        if actual != expected:
            raise AssertionError(f"{name}: surface {actual!r} != {expected!r}")
        surface[name] = {
            "match_name": actual[0], "property_index": actual[1], "default": actual[2],
            "min": actual[3], "max": actual[4],
        }

    require(decomp, [
        "FUN_181154010(uVar2,param_1,0x1b,local_res18);",
        "*(float *)(lVar1 + 0xc) = local_res18[0] * _DAT_181486c18;",
        "FUN_181153e50(uVar2,param_1,6,lVar1 + 0x30);",
        "FUN_181153d70(uVar2,param_1,10,lVar1 + 0x50);",
        "if ((char)param_5[0x14] != '\\0') {",
        "param_5[0xc] = (int)((float)iVar4 * fVar11);",
        "local_78 = param_5[0xc];",
        "iVar6 = iVar6 * 2 + 1;",
        "if (param_4 < param_2) {",
        "fVar1 = powf(param_2 / param_4,param_5 + DAT_181486c20);",
    ], "AEX decomp contract")
    require(asm, [
        "18114e8db  MOV R8D,0x1b",
        "18114e903  MULSS XMM0,dword ptr [0x181486c18]",
        "18114eaa8  MOV R8D,0x6",
        "18114ebac  MOV R8D,0xa",
        "18114dc23  CMP byte ptr [RDI + 0x50],0x0",
        "18114f964  LEA EDX,[0x1 + RDX*0x2]",
    ], "AEX asm contract")

    loader = AexLoader(str(AEX), verbose=False, fast=True)
    fade_scale = struct.unpack("<f", loader.read_bytes(0x181486C18, 4))[0]
    approx_scale = struct.unpack("<f", loader.read_bytes(0x181486C1C, 4))[0]
    if fade_scale != struct.unpack("<f", struct.pack("<f", 0.2))[0] or approx_scale != 0.5:
        raise AssertionError((fade_scale, approx_scale))

    require(header, [
        "PF_FpLong fade_out;", "A_long highlight_radius;", "PF_Boolean approximated_input;",
    ], "Mac render info")
    require(source, [
        "params[OLMKIRAKIRA_FADE_OUT]->u.fs_d.value * 0.2",
        "checkout(OLMKIRAKIRA_FADE_OUT, &p)",
        "params[OLMKIRAKIRA_HIGHLIGHT_RADIUS]->u.sd.value",
        "checkout(OLMKIRAKIRA_HIGHLIGHT_RADIUS, &p)",
        "params[OLMKIRAKIRA_APPROX_INPUT]->u.bd.value",
        "checkout(OLMKIRAKIRA_APPROX_INPUT, &p)",
        "if (fade_threshold < value)",
        "highlight_radius * 2 + 1",
        "AddColoredUnion(glow, highlight, info.highlight_color, scale);",
        "PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_FadeOut_Param_Name)",
    ], "Mac binary-grounded wiring")

    fade_samples = []
    for value, exponent, control in ((0.1, 1.0, 1.0), (0.2, 2.0, 1.0), (0.8, 2.0, 1.0)):
        threshold = struct.unpack("<f", struct.pack("<f", control * fade_scale))[0]
        if value == 0.0:
            output = 0.0
            branch = "zero"
        elif threshold < value:
            output = value ** exponent
            branch = "pow"
        else:
            output = (value / threshold) ** 2.0 * threshold ** exponent
            branch = "knee"
        fade_samples.append({"value": value, "exponent": exponent, "control": control,
                             "threshold": threshold, "branch": branch, "output": output})

    report = {
        "schema": 1,
        "kind": "olmkirakira_unconsumed_parameter_binary_audit",
        "date": "2026-07-18",
        "status": "pass_binary_grounded_partial_wiring",
        "ae_exact_claim": False,
        "binary": str(AEX.relative_to(ROOT)),
        "binary_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "surface": surface,
        "parameters": {
            "Fade Out": {
                "disk_id": 27, "reader": "FUN_181154010 float -> state+0x0c",
                "normalization": {"constant_address": "0x181486c18", "value": fade_scale},
                "semantics": "Channel 2/4 seed knee; below-or-equal threshold uses (v/t)^2 * t^strength; above uses v^strength; Channel 1/3 ignore it",
                "mac": "wired in standard and smart reads and Channel 2/4 seed generation",
                "samples": fade_samples,
            },
            "Highlight Radius": {
                "disk_id": 6, "reader": "FUN_181153e50 int32 -> state+0x30",
                "semantics": "fifth layer; radius r becomes square kernel (2r+1,2r+1); Mode 1 one box pass, Mode 2 three box passes",
                "mac": "wired for binary-grounded Mode 1/2 paths; Mode 3/4 remain outside this change",
            },
            "Approximated Input": {
                "disk_id": 10, "reader": "FUN_181153d70 boolean -> state+0x50",
                "semantics": "when render scale is above 0.5, halves working dimensions and lengths, linearly resizes before processing, then resizes back; disabled at scale <= 0.5",
                "mac": "checked out and retained in render info; non-identity OpenCV resize remains deliberately unwired",
                "blocked_boundary": "no local independent oracle for non-identity FUN_1812639f0 resize/writeback",
            },
        },
        "fact": [
            "Fresh Windows manifests fix the three match names, property indices, defaults, and ranges.",
            "FUN_18114e860 reads all three controls and stores them at state offsets +0x0c, +0x30, and +0x50.",
            "Fade Out is a float slider and is multiplied by binary float 0.2 before seed generation.",
            "Highlight Radius is the fifth isotropic layer and forms an odd square kernel.",
            "Approximated Input owns a half-resolution pre/post resize branch, not a seed or gain toggle.",
        ],
        "inference": [
            "The Mac Mode 1/2 highlight primitive uses the existing portable box scaffold; this wiring does not claim OpenCV byte equivalence.",
            "Approximated Input cannot be completed safely until non-identity resize semantics have an independent local or Windows oracle.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(f"""# OLMKiraKira previously-unconsumed parameter audit (2026-07-18)

Status: **binary-grounded partial wiring**
AE exact: **false**

## Result

| Parameter | Windows binary semantics | Mac result |
| --- | --- | --- |
| Fade Out | Disk 27 is a float. `FUN_18114e860` multiplies it by `{fade_scale:.9g}` and Channel 2/4 use it as the knee threshold in `FUN_1811501b0`. | Standard and Smart reads plus the proven Channel 2/4 seed branches are wired. |
| Highlight Radius | Disk 6 is an integer fifth layer. Radius `r` becomes `(2r+1) x (2r+1)`; Mode 1 uses one box pass and Mode 2 uses three. | Mode 1/2 are wired to the existing portable isotropic box scaffold and Highlight Color. Mode 3/4 remain unresolved. |
| Approximated Input | Disk 10 controls a half-resolution pre/post-resize branch when render scale is above `{approx_scale}`. | Standard and Smart reads retain the flag, but non-identity resize is deliberately not implemented without an independent oracle. |

## Evidence boundary

The manifest facts come from the 2026-06-29 fresh Windows defaults/ranges captures. Reader offsets and branches are grounded in `FUN_18114e860`, the three typed owners, `FUN_18114f4a0`, and their checked-in assembly. This change does not use PNG tuning and does not claim AE exactness.

`Approximated Input` remains the sole blocked implementation boundary in this three-parameter task: the repository only has a same-shape resize detour, while this path requires non-identity OpenCV resize plus writeback.

## Re-run

`python3 tools/emulation/audit_olmkirakira_unconsumed_parameters_20260718.py`
""", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_UNCONSUMED_PARAMETER_BINARY_AUDIT")
    print(json.dumps({"status": report["status"], "ae_exact": False,
                      "wired": ["Fade Out", "Highlight Radius"],
                      "blocked": ["Approximated Input"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
