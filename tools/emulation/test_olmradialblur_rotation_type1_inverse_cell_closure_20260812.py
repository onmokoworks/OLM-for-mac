#!/usr/bin/env python3
"""Validate/materialize the fixed-32x18 Rotation Type-1 inverse-cell closure.

Normal execution is read-only.  ``--write`` is required to replace the checked-in
JSON and Markdown.  The 98 rows are a deterministic projection of the pinned
actual-AEX/direct-owner reports; this script does not install a plug-in or launch AE.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
NOISE_HEADER = ROOT / "core/dblur_noise.h"
REPORT = ROOT / "refs/conformance/olmradialblur_rotation_type1_inverse_cell_closure_20260812.json"
DOC = REPORT.with_suffix(".md")
AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
PRODUCTION_SOURCE_SHA256 = "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1"
CORE_SAMPLER_SOURCE_SHA256 = "f0600bb4bb208ed8fba92cc6586eb66ac8f767299c8928ec88fc4635c1cfb591"
SCHEMA = "olm.radialblur-rotation-type1-inverse-cell-closure/1"

EVIDENCE = {
    "pairwise_pf8": "refs/conformance/olmradialblur_noise_type1_pf8_combo_actual_aex_20260811.json",
    "pairwise_pf16": "refs/conformance/olmradialblur_noise_type1_pf16_pairwise_actual_aex_20260811.json",
    "dual_strength": "refs/conformance/olmradialblur_dual_strength_noise_32x18_actual_aex_20260811.json",
    "dual_strength_component": "refs/conformance/olmradialblur_dual_strength_size_noise_components_actual_aex_20260812.json",
    "edge_noise": "refs/conformance/olmradialblur_edge_noise_endpoints_32x18_actual_aex_20260811.json",
    "outer_size_edge": "refs/conformance/olmradialblur_size_edge_noise_components_actual_aex_20260811.json",
    "inner_size_edge": "refs/conformance/olmradialblur_inner_size_edge_noise_components_actual_aex_20260811.json",
    "size_noise": "refs/conformance/olmradialblur_rotation_size_noise_components_actual_aex_20260811.json",
    "brightness": "refs/conformance/olmradialblur_brightness_size_noise_components_actual_aex_20260811.json",
}

FLAGS = {
    "pairwise": "use_aex_typed_noise_type1_pairwise",
    "dual_strength": "use_aex_typed_rotation_dual_strength_32x18",
    "edge_noise": "use_aex_typed_rotation_edge_noise_32x18",
    "any_size_edge_noise": "use_aex_typed_rotation_any_size_edge_noise_components_32x18",
    "size_noise": "use_aex_typed_rotation_size_noise_components_32x18",
}
EXPECTED_COUNTS = {
    "pairwise": 8,
    "dual_strength": 18,
    "edge_noise": 24,
    "any_size_edge_noise": 12,
    "size_noise": 36,
}

SUPERSEDES = [
    "refs/conformance/olmradialblur_noise_type1_pf8_combo_actual_aex_20260811.json",
    "refs/conformance/olmradialblur_noise_type1_pf16_pairwise_actual_aex_20260811.json",
    "refs/conformance/olmradialblur_dual_strength_noise_32x18_actual_aex_20260811.json",
    "refs/conformance/olmradialblur_dual_strength_size_noise_components_actual_aex_20260812.json",
    "refs/conformance/olmradialblur_edge_noise_endpoints_32x18_actual_aex_20260811.json",
    "refs/conformance/olmradialblur_size_edge_noise_components_actual_aex_20260811.json",
    "refs/conformance/olmradialblur_inner_size_edge_noise_components_actual_aex_20260811.json",
    "refs/conformance/olmradialblur_brightness_size_noise_components_actual_aex_20260811.json",
]

EXPECTED_SELECTOR_COMPACT = (
    "constbooluse_aex_rotation_type1_inverse_cell_32x18=info.noise_type==1&&"
    "((use_aex_typed_noise_type1_pairwise&&w==32&&h==18)||"
    "(use_aex_typed_rotation_dual_strength_32x18&&info.noise_variation!=0.0)||"
    "use_aex_typed_rotation_edge_noise_32x18||"
    "use_aex_typed_rotation_any_size_edge_noise_components_32x18||"
    "use_aex_typed_rotation_size_noise_components_32x18);"
)

# Materialized from the completed read-only /tmp actual-owner vs integrated-
# candidate campaign.  These are the new integration results; EVIDENCE above is
# retained as historical/downstream context and is not used as a substitute for
# fresh source-scalar equality.  /tmp artifacts are intentionally diagnostic and
# are not required to survive for --validate-only.
FRESH_INTEGRATION_VERIFICATION = {
    "campaign": "fresh actual-AEX direct-owner versus temporary integrated production copies",
    "tracked_source_edited_by_campaign": False,
    "total_cells": 98,
    "exact_cells": 98,
    "different_bytes": 0,
    "all_family_required_available_planes_exact": True,
    "available_plane_union": [
        "source_span", "source_scalar", "polar", "prepass_alpha", "accum",
        "max_alpha", "final_rgba", "coordinates", "padded_output"],
    "per_family": {
        "pairwise": {"cells": 8, "exact": 8, "raw_exact_planes": [
            "source_span", "source_scalar", "polar", "accum", "max_alpha",
            "final_rgba", "coordinates", "padded_output"]},
        "dual_strength": {"cells": 18, "exact": 18, "raw_exact_planes": [
            "source_span", "source_scalar", "polar", "accum", "max_alpha",
            "final_rgba", "coordinates", "padded_output"]},
        "edge_noise": {"cells": 24, "exact": 24, "raw_exact_planes": [
            "source_span", "source_scalar", "polar", "prepass_alpha", "accum",
            "max_alpha", "final_rgba", "coordinates", "padded_output"]},
        "any_size_edge_noise": {"cells": 12, "exact": 12, "raw_exact_planes": [
            "source_span", "source_scalar", "polar", "prepass_alpha", "accum",
            "max_alpha", "final_rgba", "coordinates", "padded_output"]},
        "size_noise": {"cells": 36, "exact": 36, "raw_exact_planes": [
            "source_span", "source_scalar", "polar", "accum", "max_alpha",
            "final_rgba", "coordinates", "padded_output"]},
    },
    "pf8_source_span_capture": {
        "hook": "Rotation owner return; owner work pointer + 0x90",
        "purpose": "closes the PF8 fixture gap where source_span was not in the ordinary returned plane map",
        "exact": True,
        "different_float_words": 0,
    },
    "size_noise_aggregate": {
        "cells": 36,
        "compared_bytes": 55_214_784,
        "different_bytes": 0,
        "planes": ["source_span", "source_scalar", "polar", "accum", "max_alpha",
                   "final_rgba", "coordinates", "padded_output"],
    },
    "strength290_diagnostic": {
        "role": "post-fix direct-owner counterexample replay only",
        "different_bytes": 0,
        "all_named_planes_exact": True,
        "planes": ["source_span", "source_scalar", "polar", "accum", "max_alpha",
                   "final_rgba", "coordinates", "padded_output"],
        "public_effectmain": "PF_Err_BAD_CALLBACK_PARAM; still not admitted",
    },
    "controls": {
        "type2_actual": {"cases": 12, "exact": 12, "different_bytes": 0,
                         "selector_branch": "unchanged block sampler"},
        "type3_rotation_fail_close": {"cases": 9, "fail_closed": 9,
                                      "pixel_iteration": 0, "output_unchanged": True},
    },
    "isolated_universal_build": {
        "provenance": "durable hostless Type1 pairwise, dual-strength, and edge/noise source-guard batch candidate; the closure generator does not rerun xcodebuild",
        "command": [
            "xcodebuild", "-project", "mac/OLMRadialBlur/Mac/OLMRadialBlur.xcodeproj",
            "-scheme", "OLMRadialBlur", "-configuration", "Debug",
            "ARCHS=arm64 x86_64", "ONLY_ACTIVE_ARCH=NO", "MACOSX_DEPLOYMENT_TARGET=11.0",
            "CODE_SIGNING_ALLOWED=NO", "build",
        ],
        "architectures": ["x86_64", "arm64"],
        "universal_binary_sha256": "2934d1367a5fd9d1fead35894271d9adf58ca1e008cab436e0a7d6bbb6f13083",
        "arm64_slice_sha256": "0f047d076e5561a7f402b10f0a9a90459fc1d09f9b85ef1ce35b130e1fa7721d",
        "x86_64_slice_sha256": "14e90c512aefd7e86758b73d7666ea0de774acd3c63460e72bc52145e4676499",
        "required_exports": ["EffectMain", "PluginData"],
        "required_exports_present": True,
        "codesign": {
            "enabled_during_build": False,
            "whole_bundle_signed": True,
            "strict_deep_valid": True,
            "type": "ad-hoc",
            "claim": "the durable hostless bundle was ad-hoc signed after the isolated build; no Developer ID or notarization claim",
        },
        "install_or_ae_launch": False,
    },
    "diagnostic_tmp_provenance": [
        {"command": "python3 /tmp/verify_radial_dual_type1_inverse.py",
         "role": "dual-strength 18-cell direct-owner plane comparison",
         "script_sha256": "89cbbd0f4e1a1f03f4cd2b55b06fb5316d400492b840969e509d3611337feadf"},
        {"command": "python3 /tmp/verify_radial_pf8_dual_type1_source_span.py",
         "role": "PF8 owner+0x90 dual-strength source-span capture",
         "script_sha256": "ffec1154a4a39dddc7cd829d0475cfca5d2f4ad0e8a69e3615d175648768750e"},
        {"command": "temporary Python matrix -> /tmp/olmradialblur_type1_edge_noise_inverse_selector_verify_20260812.json",
         "role": "24 edge/noise cells",
         "artifact_sha256": "220625cce8823a2968aef40b7276df395629d43806823c0b275a8e5261512853"},
        {"command": "temporary PF8 owner hook -> /tmp/olmradialblur_pf8_type1_edge_noise_owner_span_verify_20260812.json",
         "role": "PF8 edge/noise owner+0x90 source span",
         "artifact_sha256": "c46ae28358f1c03634d8ee07e9bfbf972610c9f5a625b39dd73c5e49c423e362"},
        {"command": "temporary matrix -> /tmp/radial_type1_verify.WsJDg0/candidate_report.json",
         "role": "12 size+edge+noise cells",
         "artifact_sha256": "1e6a31f3a67d3783b364f47fc56d0cd241eaf7d24b6370404fefc3735742122b"},
        {"command": "python3 /tmp/verify_pf8_type1_size_noise_span.py",
         "role": "PF8 size/noise owner+0x90 source-span matrix",
         "script_sha256": "4c9ac0d76caf3a14a20b6b5ef14bd26cdfdbb7e12b0faf5d9d083b0921aae626"},
        {"command": "python3 /tmp/verify_olmradialblur_type1_size_noise_pf16.py",
         "role": "PF16 size/noise all-plane matrix",
         "script_sha256": "9f0941b6bf73fd3ac39786718792073d9dff24c493f6fa50cd91742bda903060"},
        {"command": "python3 /tmp/verify_olmradialblur_type1_size_noise_pf32.py",
         "role": "PF32 size/noise all-plane matrix",
         "script_sha256": "22a8f1f19dec9172d7218a6dae19f8114cf70ddfa60dda5e0c334cbdae1f833e"},
        {"command": "temporary control matrix -> /tmp/olmradialblur_type1_candidate_type2_nonregression_20260812.json",
         "role": "Type2 actual/control non-regression",
         "artifact_sha256": "b64cae8e45ca0ecdc935a221cc39a442cd05801cb8110ede08461f26818c295a"},
        {"command": "ephemeral /tmp Strength290 direct-owner replay",
         "role": "post-fix minimum-boundary diagnostic; all named planes zero-diff"},
        {"command": "ephemeral /tmp Rotation-Type3 public fail-close probe",
         "role": "nine one-away Type3 controls rejected before iteration"},
    ],
    "provenance_boundary": "commands and hashes describe completed ephemeral /tmp diagnostics; the generator deliberately does not rerun that expensive campaign, and validation pins this materialized result without inferring it from the older checked-in reports",
}

CORE_SAMPLER_TOKENS = (
    "inline float sample_radial_noise_plane(const NoisePlaneView& plane, int x, int y,",
    "const float inverse_cell_size = 1.0f / plane.cell_size;",
    "const float sample_x = static_cast<float>(x) * inverse_cell_size;",
    "const float sample_y = static_cast<float>(y) * inverse_cell_size;",
)


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_path(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def compact_cpp(value: str) -> str:
    return re.sub(r"\s+", "", value)


def selector_contract() -> dict[str, Any]:
    if sha_path(SOURCE) != PRODUCTION_SOURCE_SHA256:
        raise RuntimeError("production source identity drift (Type1/Type3 integrated source expected)")
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(
        r"const bool use_aex_rotation_type1_inverse_cell_32x18\s*=.*?;",
        source,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError("Type-1 inverse-cell selector marker missing")
    compact = compact_cpp(match.group(0))
    if compact != EXPECTED_SELECTOR_COMPACT:
        raise RuntimeError("Type-1 inverse-cell selector is not the canonical exact five-flag selector")
    loop = source[match.end():match.end() + 2300]
    selection = re.search(r"const float noise\s*=.*?;", loop, re.DOTALL)
    if not selection:
        raise RuntimeError("Rotation noise sample selection marker missing")
    selected = compact_cpp(selection.group(0))
    required = (
        "use_aex_rotation_type1_inverse_cell_32x18)",
        "olm::dblur::sample_radial_noise_plane(noise_view,x,y,info.noise_type==1)",
        ":(use_aex_typed_noise_type2_small",
    )
    if any(token not in selected for token in required):
        raise RuntimeError("inverse-cell selector is not connected to the common sampler before Type-2")
    return {
        "name": "use_aex_rotation_type1_inverse_cell_32x18",
        "canonical_compact_sha256": sha_bytes(compact.encode()),
        "flags_in_exact_order": list(FLAGS.values()),
        "sampler": "olm::dblur::sample_radial_noise_plane",
        "coordinate_rule": "inverse_cell_size = 1.0f / cell_size; x/y * inverse_cell_size",
        "type2_branch_unchanged": True,
    }


def core_sampler_contract() -> dict[str, Any]:
    if sha_path(NOISE_HEADER) != CORE_SAMPLER_SOURCE_SHA256:
        raise RuntimeError("core radial-noise sampler header identity drift")
    source = NOISE_HEADER.read_text(encoding="utf-8")
    if any(token not in source for token in CORE_SAMPLER_TOKENS):
        raise RuntimeError("core inverse-cell sampler token drift")
    return {
        "path": str(NOISE_HEADER.relative_to(ROOT)),
        "sha256": CORE_SAMPLER_SOURCE_SHA256,
        "required_inverse_cell_tokens": list(CORE_SAMPLER_TOKENS),
    }


def evidence() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    identities, loaded = {}, {}
    for name, relative in EVIDENCE.items():
        path = ROOT / relative
        loaded[name] = json.loads(path.read_text(encoding="utf-8"))
        identities[name] = {"path": relative, "sha256": sha_path(path)}
    return identities, loaded


def rows_where(data: dict[str, Any], predicate: Callable[[dict[str, Any]], bool]) -> list[dict[str, Any]]:
    rows = data.get("cases")
    if not isinstance(rows, list):
        raise RuntimeError("evidence report has no cases list")
    result = [row for row in rows if predicate(row)]
    if not all(row.get("exact") is True for row in result):
        raise RuntimeError("selected prior consumed-path evidence is not exact")
    return result


def evidence_ref(name: str, row: dict[str, Any]) -> dict[str, str]:
    return {"report": EVIDENCE[name], "case_sha256": sha_bytes(canonical(row))}


def base_cell(category: str, identifier: str, refs: list[dict[str, str]], **params: Any) -> dict[str, Any]:
    planes = FRESH_INTEGRATION_VERIFICATION["per_family"][category]["raw_exact_planes"]
    return {
        "id": identifier,
        "flag": FLAGS[category],
        "category": category,
        "params": params,
        "evidence": refs,
        "prior_consumed_planes_and_typed_output_exact": True,
        "fresh_integration": {"raw_exact": True, "available_planes": planes},
        "exact": True,
    }


def build_cells(data: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []

    # 8: PF8/PF16, fixed 32x18, four pairwise seed/offset/thickness tuples.
    p8 = rows_where(data["pairwise_pf8"], lambda r: r["mode"] == "rotation" and r["width"] == 32 and r["height"] == 18)
    p16 = rows_where(data["pairwise_pf16"], lambda r: r["mode"] == "rotation" and r["geometry"][:2] == [32, 18])
    for depth, name, rows in ((8, "pairwise_pf8", p8), (16, "pairwise_pf16", p16)):
        for row in rows:
            params = {k: row[k] for k in ("noise_variation", "seed", "thickness")}
            params["noise_offset"] = row.get("noise_offset", row.get("offset"))
            ident = f"pairwise-pf{depth}-nv{params['noise_variation']:g}-s{params['seed']}-o{params['noise_offset']:g}-t{params['thickness']:g}"
            cells.append(base_cell("pairwise", ident, [evidence_ref(name, row)], depth=depth, **params))

    # 18: 12 SV0 Type1 cells plus 6 SV25/NV25 component cells.
    plain = rows_where(data["dual_strength"], lambda r: r["mode"] == "rotation" and r["noise_type"] == 1)
    component = rows_where(data["dual_strength_component"], lambda r: r["mode"] == "rotation" and r["noise_type"] == 1)
    for name, rows in (("dual_strength", plain), ("dual_strength_component", component)):
        for row in rows:
            sv = row.get("size_variation", 0.0)
            ident = f"dual-pf{row['depth']}-i{row['inner_strength']}-sv{sv:g}-nv{row['noise_variation']:g}"
            cells.append(base_cell("dual_strength", ident, [evidence_ref(name, row)],
                                   depth=row["depth"], outer_strength=4,
                                   inner_strength=row["inner_strength"], size_variation=sv,
                                   noise_variation=row["noise_variation"], noise_type=1))

    # 24: SV0, both sides, both fade endpoints, both Type1 NV endpoints.
    edge = rows_where(data["edge_noise"], lambda r: r["owner"] == "rotation" and r["noise_type"] == 1)
    for row in edge:
        ident = f"edge-pf{row['depth']}-{row['side']}-f{row['edge_fade']}-nv{row['noise_variation']:g}"
        cells.append(base_cell("edge_noise", ident, [evidence_ref("edge_noise", row)],
                               depth=row["depth"], side=row["side"], size_variation=0.0,
                               edge_fade=row["edge_fade"], noise_variation=row["noise_variation"], noise_type=1))

    # 12: both sides x all depths x the two admitted SV25 Type1 tuples.
    for name in ("outer_size_edge", "inner_size_edge"):
        selected = rows_where(data[name], lambda r: r["mode"] == "rotation" and r["noise_type"] == 1 and
                              r["size_variation"] == 25.0 and
                              (r["edge_fade"], r["noise_variation"]) in ((50, 25.0), (100, 100.0)))
        for row in selected:
            ident = f"size-edge-pf{row['depth']}-{row['side']}-f{row['edge_fade']}-nv{row['noise_variation']:g}"
            cells.append(base_cell("any_size_edge_noise", ident, [evidence_ref(name, row)],
                                   depth=row["depth"], side=row["side"], size_variation=25.0,
                                   edge_fade=row["edge_fade"], noise_variation=row["noise_variation"], noise_type=1))

    # 36: gain1 direct matrix plus gain .5/2 factorized from that direct matrix
    # and the pinned actual-AEX gain-invariance/output-writer witnesses.
    direct = rows_where(data["size_noise"], lambda r: r["noise_type"] == 1)
    brightness = rows_where(data["brightness"], lambda r: r["mode"] == "rotation" and r["noise_type"] == 1)
    direct_map = {(r["depth"], r["size_variation"], r["noise_variation"]): r for r in direct}
    gain_witness = {(r["depth"], r["brightness_gain"]): r for r in brightness}
    for depth in (8, 16, 32):
        for gain in (.5, 1.0, 2.0):
            for sv in (25.0, 100.0):
                for nv in (25.0, 100.0):
                    row = direct_map[(depth, sv, nv)]
                    refs = [evidence_ref("size_noise", row)]
                    proof = "fresh direct-owner integration row; older gain1 report retained as context"
                    if gain != 1.0:
                        refs.append(evidence_ref("brightness", gain_witness[(depth, gain)]))
                        proof = "fresh direct-owner integration row; older factorized reports retained as context"
                    ident = f"size-noise-pf{depth}-g{gain:g}-sv{sv:g}-nv{nv:g}"
                    cell = base_cell("size_noise", ident, refs, depth=depth, brightness_gain=gain,
                                     size_variation=sv, noise_variation=nv, noise_type=1)
                    cell["proof_composition"] = proof
                    cells.append(cell)

    cells.sort(key=lambda row: (list(FLAGS).index(row["category"]), row["id"]))
    return cells


def control_contract(data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    type2 = {
        "pairwise": "selector is Type1-only; the existing Type2 block route is not selected",
        "dual_strength": "12 Rotation Type2 rows in the dual-strength evidence remain exact",
        "edge_noise": "24 Rotation Type2 rows in the edge endpoint evidence remain exact",
        "any_size_edge_noise": "Type2 rows remain on SampleRadialBlockNoisePlaneAEX",
        "size_noise": "12 gain1 Rotation Type2 rows remain on SampleRadialBlockNoisePlaneAEX",
    }
    if len(rows_where(data["dual_strength"], lambda r: r["mode"] == "rotation" and r["noise_type"] == 2)) != 12:
        raise RuntimeError("dual-strength Type2 control drift")
    if len(rows_where(data["edge_noise"], lambda r: r["owner"] == "rotation" and r["noise_type"] == 2)) != 24:
        raise RuntimeError("edge Type2 control drift")
    if len(rows_where(data["size_noise"], lambda r: r["noise_type"] == 2)) != 12:
        raise RuntimeError("size/noise Type2 control drift")
    return {
        "type2": type2,
        "type3_rotation": "fail-closed at RenderWorld: Type3 requires a Layer and only PF32 Zoom has one bounded admission; Rotation is rejected",
        "strength290": "excluded; diagnostic direct-owner counterexample only, never a public admission or closure row",
    }


DOC_TEXT = """# OLM RadialBlur Rotation Type-1 inverse-cell closure — 2026-08-12

Status: **98/98 bounded cells exact after inverse-cell integration**.

The fixed 32×18 Rotation Type-1 source-scalar seam is closed for exactly five
existing admission flags: pairwise (8 cells), dual strength (18), edge/noise
(24), size+edge+noise (12), and size+noise/brightness (36).  The common sampler
uses a float inverse-cell multiply, matching the pinned Windows AEX arithmetic.
Fresh read-only direct-owner integration runs pin every required available plane
across all 98 cells.  Pairwise, dual-strength, and size/noise do not make a
98-wide prepass claim; edge families additionally captured exact prepass alpha.
The size/noise family alone compared 55,214,784 bytes with zero differences.
PF8 source span was captured explicitly at owner work `+0x90`.
Older reports remain contextual evidence; source-scalar exactness is not inferred
from their stale inactive-only classification.

The Windows evidence is direct internal-owner execution under the repository's
x86_64 emulation fixture, not a natural exported public AEX call.  The Mac
numerical evidence likewise reuses direct typed-owner fixtures; the natural
classic `EffectMain` public admission is bounded by the same five flags, but this
document does not relabel all 98 rows as fresh natural-owner executions.

Type 2 stays on its prior block sampler and Type 3 Rotation remains fail-closed.
Fresh Type2 actual controls are exact and all nine Type3 Rotation controls reject
before iteration.  Strength 290 is excluded: its post-fix direct-owner replay is
zero-diff on all named planes, while public `EffectMain` still rejects it.  No
install, native AE render, arbitrary geometry, or general-strength claim is made.

An isolated Debug `xcodebuild` also completed for `arm64` and `x86_64`; the
Universal binary and both slices are hash-bound in the JSON, and `EffectMain`
and `PluginData` were exported.  The durable bundle is strict/deep-valid ad-hoc
signed.  It is not Developer ID/notarized, installed, or AE-load evidence.

This closure supersedes the older “inactive/unreferenced source-scalar only”
wording in the listed 2026-08-11 reports.  Some differing cells were consumable;
they happened not to cross the fixed small-strength integer-span boundary.
"""


def generate_report() -> dict[str, Any]:
    identities, loaded = evidence()
    selector = selector_contract()
    cells = build_cells(loaded)
    counts = {name: sum(row["category"] == name for row in cells) for name in FLAGS}
    if counts != EXPECTED_COUNTS or len(cells) != 98 or len({row["id"] for row in cells}) != 98:
        raise RuntimeError(f"98-cell projection drift: {counts}")
    controls = control_contract(loaded)
    if any(row["params"].get("outer_strength") == 290 or
           row["params"].get("inner_strength") == 290 for row in cells):
        raise RuntimeError("Strength290 leaked into the public closure matrix")
    return {
        "schema": SCHEMA,
        "status": "exact_bounded_98_cells_inverse_cell_integrated",
        "aex_sha256": AEX_SHA256,
        "production_source_sha256": PRODUCTION_SOURCE_SHA256,
        "core_sampler_source": core_sampler_contract(),
        "scope": "Rotation; fixed 32x18 component/pairwise fixtures; Type1; exactly five existing admission flags and 98 enumerated cells",
        "selector_contract": selector,
        "flag_counts": counts,
        "total_cells": len(cells),
        "cells": cells,
        "fresh_integration_verification": FRESH_INTEGRATION_VERIFICATION,
        "controls": controls,
        "owner_provenance": {
            "windows_actual": "direct internal AEX owner through the repository x86_64 emulation fixtures; not natural exported-public execution",
            "mac_numeric": "direct typed-owner fixture evidence plus the canonical common-sampler selector integration",
            "mac_public": "natural classic EffectMain admission is bounded by the same flags; no claim that these are 98 fresh natural-owner captures",
        },
        "evidence_reports": identities,
        "supersedes_stale_inactive_only_wording": SUPERSEDES,
        "claims_not_made": [
            "Strength290 public admission", "arbitrary strength, geometry, seed, offset, thickness, fade, size, or brightness",
            "Rotation Type3 numerical admission", "native After Effects render", "installed plug-in identity",
            "natural exported-public Windows AEX execution for all 98 rows",
        ],
    }


def validate_report() -> None:
    checked = json.loads(REPORT.read_text(encoding="utf-8"))
    expected = generate_report()
    if checked != expected:
        raise RuntimeError("checked-in inverse-cell closure report drift")
    if DOC.read_text(encoding="utf-8") != DOC_TEXT:
        raise RuntimeError("checked-in inverse-cell closure Markdown drift")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--validate-only", action="store_true", help="validate checked-in artifacts (default)")
    mode.add_argument("--write", action="store_true", help="explicitly replace checked-in JSON and Markdown")
    args = parser.parse_args()
    if args.write:
        report = generate_report()
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        DOC.write_text(DOC_TEXT, encoding="utf-8")
    validate_report()
    print(json.dumps({"status": "pass", "cells": 98, "mode": "write" if args.write else "validate-only"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
