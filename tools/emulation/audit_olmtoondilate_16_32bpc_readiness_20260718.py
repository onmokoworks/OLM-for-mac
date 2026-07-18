#!/usr/bin/env python3
"""Bounded, read-only conformance audit for ToonDilate depth expansion."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
CLI = ROOT / "cli/OLMToonDilate/olmtoondilate_cli"
WIN_ROOT = ROOT / "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"
WIN_MANIFEST = WIN_ROOT / "reference_manifest.json"
EXACT16 = ROOT / "refs/conformance/bitdepth_16bpc_exact_manifest_20260703.md"
PACKAGE_SMOKE = ROOT / "refs/scripts/smoke_package_olmtoondilate_mac_32bpc_validation_20260715.py"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(command: list[str]) -> dict:
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }


def source_facts() -> dict:
    text = SOURCE.read_text(encoding="utf-8")
    rules = {
        "typed_pf8_dispatch": "PF_PixelFormat_ARGB32" in text and "RenderTyped<PF_Pixel8>" in text,
        "typed_pf16_dispatch": "PF_PixelFormat_ARGB64" in text and "RenderTyped<PF_Pixel16>" in text,
        "typed_pf32_dispatch": "PF_PixelFormat_ARGB128" in text and "RenderTyped<PF_PixelFloat>" in text,
        "pf8_opaque_seed": "p.alpha == PF_MAX_CHAN8" in text,
        "pf16_opaque_seed": "p.alpha == PF_MAX_CHAN16" in text,
        "pf32_opaque_seed": "p.alpha >= 1.0f" in text,
        "effective_radius_ceil": "std::ceil(info.search_radius" in text,
        "pre_render_comp_width": "in_result.ref_width" in text,
        "preserve_zero_alpha_rgb": "preserve_rgb_of_zero_alpha = TRUE" in text,
        "two_pass_neighbor_relaxation": "for (A_long y = 0; y < h; ++y)" in text and "for (A_long y = h - 1" in text,
    }
    return {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE), "rules": rules, "all_rules_present": all(rules.values())}


def exr_header_facts() -> dict:
    rows = []
    for path in sorted(WIN_ROOT.glob("*olmtoondilate*.exr")):
        header = path.read_bytes()[:8]
        rows.append({
            "name": path.name,
            "bytes": path.stat().st_size,
            "openexr_magic": header[:4] == b"\x76\x2f\x31\x01",
            "sha256": sha256(path),
        })
    return {"root": str(WIN_ROOT.relative_to(ROOT)), "count": len(rows), "files": rows}


def manifest_facts() -> dict:
    data = json.loads(WIN_MANIFEST.read_text(encoding="utf-8"))
    toon = [case for case in data.get("cases", []) if "toondilate" in str(case).lower()]
    return {
        "path": str(WIN_MANIFEST.relative_to(ROOT)),
        "project_bits_per_channel": data.get("project", {}).get("bits_per_channel"),
        "renderer": data.get("project", {}).get("project_gpu_accel_type", {}).get("current_name"),
        "ae_version": data.get("ae_version"),
        "output_capabilities": data.get("output_capabilities"),
        "toondilate_cases": len(toon),
        "toondilate_case_ids": [case.get("id") for case in toon],
        "toondilate_float_preserving": all(case.get("float_preserving") is True for case in toon),
        "toondilate_output_formats": sorted({case.get("output_format") for case in toon}),
        "toondilate_frames_exist": all((WIN_ROOT / case.get("frame", "")).is_file() for case in toon),
        "toondilate_before_frames_exist": all((WIN_ROOT / case.get("before_effects_frame", "")).is_file() for case in toon),
    }


def main() -> int:
    binary_candidates = sorted(ROOT.glob("mac/OLMToonDilate/Mac/build/**/Contents/MacOS/OLMToonDilate"))
    binary_facts = [{"path": str(path.relative_to(ROOT)), "sha256": sha256(path)} for path in binary_candidates]
    package_smoke = run(["python3", str(PACKAGE_SMOKE.relative_to(ROOT))])

    result = {
        "kind": "olmtoondilate_depth_readiness_audit",
        "schema": 1,
        "generated_at": "2026-07-18",
        "scope": {"plugin": "OLMToonDilate", "depths": [16, 32], "windows_renderer": "SOFTWARE"},
        "source": source_facts(),
        "windows_32bpc": {"manifest": manifest_facts(), "exr_headers": exr_header_facts()},
        "mac_candidate_binary": {"candidates": binary_facts,
                                  "package_hash_binding": "generated_from_current_binary_at_package_time",
                                  "package_smoke_returncode": package_smoke["returncode"],
                                  "hash_matches_package": package_smoke["returncode"] == 0},
        "existing_evidence": {
            "16bpc_declared_exact": "AE exact: 3" in EXACT16.read_text(encoding="utf-8"),
            "pf16_actual_aex_stage": "tools/emulation/test_olmtoondilate_pf16_actual_aex_cli_differential_20260716.py",
            "pf32_actual_aex_matrix": "tools/emulation/test_olmtoondilate_pf32_seed_propagation_matrix_20260717.py",
            "mac_32bpc_candidate_exr_count": len(list((ROOT / "refs/reports").rglob("*toondilate*.exr"))),
        },
        "reproducible_checks": [
            run(["python3", "refs/scripts/smoke_olmtoondilate_bitdepth_conformance.py"]),
            run(["python3", "tools/emulation/test_olmtoondilate_pf16_actual_aex_cli_differential_20260716.py"]),
            run(["python3", "tools/emulation/test_olmtoondilate_pf32_seed_propagation_matrix_20260717.py"]),
            run(["python3", "tools/emulation/test_olmtoondilate_mac_smartrender_adapter_20260717.py"]),
        ],
        "package_contract": {
            "package_smoke_path": str(PACKAGE_SMOKE.relative_to(ROOT)),
            "known_issue": "no Mac 32bpc candidate EXR or cross-host comparison exists; package provenance now binds the current binary SHA at generation time",
        },
        "classification": {
            "16bpc": "AE exact for the declared 3-case slice; broader coverage not claimed",
            "32bpc": "Windows float-preserving EXR evidence exists for 3 cases, but Mac candidate EXR and cross-host comparison are absent",
            "highest_value_mac_only_action": "build the current ToonDilate plugin, refresh the 32bpc validation package provenance, run its isolated AE fixture, and retain no-effect/effect FLOAT EXRs plus output-module settings",
            "forbidden_action": "do not change ToonDilate source or infer 32bpc AE exactness from PNG, CLI, PF16/PF32 worker fixtures, or a no-effect-only render",
        },
    }
    out_json = ROOT / "refs/conformance/olmtoondilate_16_32bpc_readiness_20260718.json"
    out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output": str(out_json), "classification": result["classification"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
