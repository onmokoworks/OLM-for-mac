#!/usr/bin/env python3
"""Keep release-facing claims synchronized with retained evidence."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    typed = json.loads(
        (ROOT / "refs/conformance/olmradialblur_rotation_typed_inner_geometry_20260807.json").read_text()
    )
    practical = json.loads(
        (ROOT / "refs/conformance/olmradialblur_rotation_pf16_inner_640x360_20260807.json").read_text()
    )
    matrix = (ROOT / "refs/conformance/olm_release_completion_matrix_20260806.md").read_text()
    limitations = (ROOT / "KNOWN_LIMITATIONS.md").read_text()
    kira_ui = json.loads(
        (ROOT / "refs/conformance/olmkirakira_ui_setup_actual_aex_20260806.json").read_text()
    )
    kira_current = (
        ROOT / "refs/conformance/olmkirakira_parameter_surface_current_20260810.md"
    ).read_text()
    kira_old = (
        ROOT / "refs/conformance/olmkirakira_parameter_surface_contract_20260717.md"
    ).read_text()

    assert typed["status"] == "exact"
    observed = {
        (case["bit_depth"], case["geometry"]["width"], case["geometry"]["height"])
        for case in typed["cases"]
        if case["status"] == "exact"
    }
    assert (16, 64, 36) in observed
    assert (32, 64, 36) in observed
    assert practical["status"] == "exact"
    practical_cases = practical["cases"]
    assert any(
        case["status"] == "exact"
        and case["bit_depth"] == 16
        and case["geometry"]["width"] == 640
        and case["geometry"]["height"] == 360
        for case in practical_cases
    )

    assert "PF16/PF32 Inner remain 9x7 guarded" not in matrix
    assert "PF16 at 9x7, 64x36 and 640x360" in matrix
    assert "PF32 at 9x7 and 64x36" in matrix
    assert "PF8/PF16が640×360、PF32が" in limitations
    assert "64×36" in limitations
    assert kira_ui["status"] == "exact"
    assert kira_ui["params_setup"]["num_params_including_input"] == 41
    ramp_rows = [
        row for row in kira_ui["params_setup"]["rows"]
        if row.get("param_type") == 11 and row.get("name") == "Ramp"
    ]
    assert len(ramp_rows) == 5
    assert all(row["arbitrary"]["default_size"] == 608 for row in ramp_rows)
    assert "registration exact; native-host interaction bounded" in kira_current
    assert "Historical snapshot / superseded" in kira_old
    print("PASS_RELEASE_CLAIM_CONSISTENCY radial_typed_geometry=1 kira_surface=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
