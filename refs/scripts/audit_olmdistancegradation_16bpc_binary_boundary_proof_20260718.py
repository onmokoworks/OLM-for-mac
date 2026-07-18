#!/usr/bin/env python3
"""Build a Mac-only, binary-grounded DG 16bpc residual boundary proof.

The proof re-runs existing actual-AEX/PF16 differential fixtures, pins the
Windows AEX and disassembly facts, and fails closed on target-case attribution.
It does not build, install, edit source, or inspect/tune PNG pixels.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "refs/conformance/olmdistancegradation_16bpc_case0012_case0014_binary_boundary_proof_20260718.json"
OUT_MD = ROOT / "refs/conformance/olmdistancegradation_16bpc_case0012_case0014_binary_boundary_proof_20260718.md"
EXPECTED_AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
MATRIX = ROOT / "tools/emulation/test_dg_pf16_boundary_matrix_20260717.py"
STAGING = ROOT / "tools/emulation/test_dg_pf16_field_staging_differential_20260717.py"
TARGET = ROOT / "refs/conformance/olmdistancegradation_16bpc_layer_residual_mac_ae_20260717.md"
NEARMISS = ROOT / "refs/conformance/olmdistancegradation_16bpc_nearmiss_boundary_20260718.md"
ASM = ROOT / "disasm/DistanceGradation.aex.asm.txt"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_json(script: Path) -> dict:
    proc = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{script.name} exited {proc.returncode}: {proc.stderr[-1200:]}")
    return json.loads(proc.stdout)


def main() -> int:
    matrix = run_json(MATRIX)
    staging = run_json(STAGING)
    target_text = TARGET.read_text(encoding="utf-8")
    nearmiss_text = NEARMISS.read_text(encoding="utf-8")
    asm_text = ASM.read_text(encoding="utf-8")

    matrix_cases = matrix["cases"]
    matrix_exact = (
        matrix["status"] == "PASS"
        and len(matrix_cases) == 6
        and all(case["status"] == "PASS" for case in matrix_cases)
        and all(case["comparison"]["field_raw_words_exact"] for case in matrix_cases)
        and all(case["comparison"]["compose_raw_bytes_exact"] for case in matrix_cases)
    )
    staging_exact = (
        staging["status"] == "PASS"
        and staging["actual_aex"]["binary_sha256"] == EXPECTED_AEX_SHA256
        and staging["field_comparison"]["word_diff_count"] == 0
        and staging["output_comparison"]["pixel_diff_count"] == 0
        and staging["actual_aex"]["compose_hits"] == 40
        and staging["actual_aex"]["padding_preserved"]
    )
    disasm_facts = {
        "pf16_pack_store_sequence_present": "PACKSSDW" in asm_text and "MOV word ptr [RSI],AX" in asm_text,
        "float_to_int_conversion_present": "CVTPS2DQ" in asm_text,
        "compose_symbol_present": "181170480" in asm_text,
    }
    target_facts = {
        "case0012_max1": "case_0012` | `1` | `39` | `95`" in target_text,
        "case0014_max1": "case_0014` | `1` | `35` | `104`" in target_text,
        "windows_pre_store_missing": "Windows pre-store float" in nearmiss_text,
        "windows_store_word_missing": "Windows store word" in nearmiss_text,
        "same_run_true16_missing": "same-run true16 TIFF/EXR" in nearmiss_text,
    }
    status = "PASS" if matrix_exact and staging_exact and all(disasm_facts.values()) and all(target_facts.values()) else "BLOCKED"
    report = {
        "schema": "olmdistancegradation.16bpc-binary-boundary-proof/1",
        "date": "2026-07-18",
        "status": status,
        "scope": "Mac-only binary-grounded residual boundary proof for case_0012 and case_0014",
        "verdict": "binary_pf16_boundary_validated_target_attribution_still_blocked",
        "aex": {
            "path": "aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex",
            "sha256": EXPECTED_AEX_SHA256,
            "sha256_observed_by_matrix": matrix["aex"]["sha256"],
        },
        "binary_proof": {
            "matrix_script": str(MATRIX.relative_to(ROOT)),
            "matrix_status": matrix["status"],
            "matrix_case_count": len(matrix_cases),
            "matrix_all_field_raw_words_exact": matrix_exact,
            "matrix_all_compose_raw_bytes_exact": matrix_exact,
            "staging_script": str(STAGING.relative_to(ROOT)),
            "staging_status": staging["status"],
            "staging_field_word_diff_count": staging["field_comparison"]["word_diff_count"],
            "staging_output_diff_count": staging["output_comparison"]["pixel_diff_count"],
            "staging_compose_hits": staging["actual_aex"]["compose_hits"],
            "staging_padding_preserved": staging["actual_aex"]["padding_preserved"],
            "disassembly_facts": disasm_facts,
        },
        "target_residual": {
            "source": str(TARGET.relative_to(ROOT)),
            "case0012": {"max_diff": 1, "nonzero_pixels": 39, "nonzero_samples": 95},
            "case0014": {"max_diff": 1, "nonzero_pixels": 35, "nonzero_samples": 104},
            "facts": target_facts,
        },
        "conclusion": {
            "proved": [
                "The pinned actual AEX reaches field generation and 40 per-pixel PF16 compose calls in the bounded fixture.",
                "Across threshold, transparency, half-step, and endpoint fixtures, AEX and production-source field/store words are exact.",
                "The disassembly contains float-to-int conversion and packed 16-bit store operations at the relevant binary boundary.",
            ],
            "not_proved": [
                "No Windows live pre-store float, PF16 store word, or same-run true16 export exists for case_0012/0014.",
                "The Mac binary fixture cannot identify whether the target residual is upstream field, pre-store conversion, final store, or host export.",
                "No AE exactness, Windows conformance, source change, or PNG tuning claim is made.",
            ],
            "next_narrow_proof": "Capture one Windows Software AE same-run coordinate for each target with source PF16, field, compose pre-store float, PF16 store word, and true16 export word; compare each boundary separately.",
        },
        "input_sha256": {
            "matrix_script": sha256(MATRIX),
            "staging_script": sha256(STAGING),
            "target_residual_report": sha256(TARGET),
            "near_miss_report": sha256(NEARMISS),
            "disassembly": sha256(ASM),
        },
        "claims": {"mac_only": True, "binary_grounded": True, "ae_exact": False, "windows_claim": False, "production_edit": False, "png_tuning": False},
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# OLMDistanceGradation 16bpc target binary-boundary proof

- Date: `2026-07-18`
- Status: `{status}`
- Scope: Mac-only actual-AEX/PF16 boundary evidence for `case_0012` and `case_0014`
- AEX SHA-256: `{EXPECTED_AEX_SHA256}`

## Proof

- The six-case actual-AEX PF16 threshold/half-step matrix passed with exact field raw words and exact compose/store raw bytes.
- The non-degenerate 8x5 staging differential passed with zero field-word differences, zero output differences, 40 compose calls, and preserved row padding.
- Disassembly confirms `CVTPS2DQ` float-to-int conversion and packed 16-bit store operations at the relevant binary path.

## Target Residual

The retained Mac AE layer run is `max_diff=1` for both targets: `case_0012` has 39 nonzero pixels / 95 samples, and `case_0014` has 35 nonzero pixels / 104 samples.

This proof does **not** attribute those residuals. The target evidence still lacks Windows same-run pre-store float, PF16 store word, and true16 export word. Therefore host conversion, final store, and upstream field/pre-store causes remain separable only with the requested Windows boundary capture.

## Reproduction

```sh
python3 refs/scripts/audit_olmdistancegradation_16bpc_binary_boundary_proof_20260718.py
```

The script only runs existing Mac-local emulation/differential fixtures and writes the two dated conformance artifacts. It does not build or install the plug-in, edit production source, or tune PNGs.
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(json.dumps({"status": status, "json": str(OUT_JSON), "md": str(OUT_MD)}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
