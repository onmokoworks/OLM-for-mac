#!/usr/bin/env python3
"""Prove Type 3 Layer size mismatch is rejected by actual AEX and production."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "tools/emulation/test_olmdirectionalblur_complete_pf8_compare_20260718.py"
ALPHA_PATH = ROOT / "tools/emulation/test_olmdirectionalblur_alpha_validity_pf8_production_20260805.py"
PRODUCTION_TEST = ROOT / "tools/emulation/test_dblur_mac_mode2_host_adapter_20260805.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_noise_type3_layer_size_contract_20260805.json"
NOTE = ROOT / "refs/conformance/olmdirectionalblur_noise_type3_layer_size_contract_20260805.md"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    base = load(BASE_PATH, "dblur_complete_pf8")
    source = load(ALPHA_PATH, "dblur_alpha_validity").build_input()
    settings = dict(front_strength=8, noise_variation=25.0, noise_type=3,
                    seed=1, noise_offset=0, thickness=10.0)
    cases = []
    for dimensions, relation in (((12, 12), "smaller"), ((20, 20), "larger")):
        _, metadata = base.capture_actual(
            0.0, source, **settings, noise_layer_row_padding=28,
            noise_layer_dimensions=dimensions, require_complete=False
        )
        callbacks = [call["callback"] for call in metadata["iterate_calls"]]
        rejected_before_processing = (
            metadata["natural_complete"] is False
            and metadata["output_complete"] is False
            and metadata["rotate_call_count"] == 0
            and callbacks == ["0x180006980"]
        )
        cases.append({
            "relation": relation,
            "source_dimensions": [16, 16],
            "layer_dimensions": list(dimensions),
            "callbacks": callbacks,
            "rotate_call_count": metadata["rotate_call_count"],
            "output_complete": metadata["output_complete"],
            "rejected_before_processing": rejected_before_processing,
        })
    production = subprocess.run(
        ["python3", str(PRODUCTION_TEST)], cwd=ROOT,
        capture_output=True, text=True, check=False,
    )
    if production.returncode:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: production dimension-mismatch gate test failed\n" + production.stderr)
    production_report = json.loads(production.stdout.splitlines()[-1])
    production_fail_closed = production_report["checks"]["dimension_mismatch_fail_closed"]
    exact_contract = all(case["rejected_before_processing"] for case in cases) and production_fail_closed
    result = {
        "schema": 1,
        "kind": "olmdirectionalblur_noise_type3_layer_size_contract_20260805",
        "status": "pass" if exact_contract else "mismatch",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "PF8 Type 3, 16x16 source, controlled top-left-crop 12x12 Layer and transparent-padded 20x20 Layer; equal origin; independent rowbytes",
        "actual_aex": {"cases": cases, "contract": "Layer width and height must equal render source width and height before rotate/field/rowdriver/output"},
        "production": {"dimension_mismatch_fail_closed": production_fail_closed, "test": str(PRODUCTION_TEST.relative_to(ROOT))},
        "comparison": {"rejection_contract_exact": exact_contract, "full_frame_available": False},
        "boundary": {"equal_dimension_layer_supported": True, "different_dimension_layer_supported": False, "crop_clamp_rule": "none; rejected before field construction", "mac_ae_exact_claim": False},
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    NOTE.write_text(
        "# OLMDirectionalBlur Type 3 Layer Size Contract\n\n"
        f"- Status: `{result['status']}`.\n"
        "- A 12x12 Layer and a 20x20 Layer were each checked out naturally against a 16x16 source.\n"
        "- Both actual-AEX runs stopped after the populate callback, with zero rotate calls and no complete output callback.\n"
        "- Production rejects the same dimension mismatch through its exact gate.\n"
        "- There is no crop/clamp/local-coordinate rule to port for unequal dimensions in this bounded PF8 path: the AEX rejects the geometry before field construction.\n"
        "- Consequently no actual-AEX full frame exists for unequal size; claiming pixel exactness would be fabricated. Mac AE behavior remains unclaimed.\n\n"
        "Reproduction: `python3 tools/emulation/test_olmdirectionalblur_noise_type3_layer_size_contract_20260805.py`\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "cases": cases, "production_fail_closed": production_fail_closed}))
    return 0 if exact_contract else 1


if __name__ == "__main__":
    raise SystemExit(main())
