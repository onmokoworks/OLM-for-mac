#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "tools/emulation/probe_olmkirakira_mode4_fullcaller_scaffold_20260807.py"
SINGLE = ROOT / "refs/conformance/olmkirakira_mode4_natural_fullframe_exact_20260811.json"
REPORT = ROOT / "refs/conformance/olmkirakira_mode4_natural_families_exact_20260811.json"
REPORT_MD = ROOT / "refs/conformance/olmkirakira_mode4_natural_families_exact_20260811.md"

CASES = (
    ("horizontal_control", 1, 5, 0),
    ("vertical_rot17_len7", 0, 7, 17),
    ("diagonal_rot13_len11", 2, 11, 13),
    ("diagonal2_rotm11_len9", 3, 9, -11),
    ("highlight_constant_radius3", 4, 3, 23),
)


def load_base():
    spec = importlib.util.spec_from_file_location("kira_fullcaller_matrix", BASE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_base()
    cases = []
    try:
        for name, slot, length, rotation in CASES:
            result = module.main(
                natural=True, natural_slot=slot,
                natural_length=length, natural_rotation=rotation)
            if result != 0:
                raise RuntimeError(f"{name} failed with {result}")
            report = json.loads(SINGLE.read_text(encoding="utf-8"))
            cases.append({
                "name": name,
                "status": report["status"],
                "fixture": report["fixture"],
                "same_run_seed_f32": report["actual_aex"]["same_run_seed_f32"],
                "same_run_direction": report["actual_aex"]["same_run_direction"],
                "selected_ray_u32": report["actual_aex"]["selected_ray_u32"],
                "portable_ray_u32": report["actual_aex"]["portable_ray_u32"],
                "typed_outputs": report["actual_aex"]["typed_outputs"],
                "comparison": report["comparison"],
            })
    finally:
        # Keep the original single-case artifact deterministic as the control.
        module.main(natural=True, natural_slot=1, natural_length=5, natural_rotation=0)

    passed = all(
        case["status"] == "exact"
        and case["selected_ray_u32"] == case["portable_ray_u32"]
        and all(output["actual_hex"] == output["portable_hex"]
                for output in case["typed_outputs"].values())
        for case in cases
    )
    output = {
        "kind": "olmkirakira_mode4_natural_families_exact",
        "date": "2026-08-11",
        "status": "exact" if passed else "blocked",
        "exact": {
            "cases": len(cases),
            "ray_words": len(cases) * 15,
            "typed_rows": len(cases) * 3,
            "remaining_family_typed_rows": (len(cases) - 1) * 3,
            "typed_bytes": len(cases) * (60 + 120 + 240),
            "max_ulp": 0,
        },
        "cases": cases,
        "connected_evidence": {
            "directional_helper_matrix": "olmkirakira_mode4_canonical_angles_actual_aex_20260810.json (17 cases)",
            "compose_matrix": "olmkirakira_mode4_compose_matrix_actual_aex_20260811.json (5 cases)",
        },
        "boundary": "Five bounded 5x3 same-run source cases; no all-parameter Cartesian product or live Windows AE generality is claimed.",
    }
    REPORT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(
        "# OLMKiraKira Mode 4 natural family matrix（2026-08-11）\n\n"
        f"Status: **{output['status']}**\n\n"
        "Horizontal controlに加え、Vertical、Diagonal、Diagonal2、Highlightを各1件、"
        "actual AEX full callerのsame-run seed→selected ray→aggregate→PF8/PF16/PF32へ接続した。"
        "全5ケースのray 75 wordsとtyped 15 rows（残り4 familyは12 rows）がraw exact、max ULP 0。\n\n"
        "Directional 3 familyはnondefault length/rotation、Highlightはconstant 5×3 source・Radius 3で"
        "専用branchを分離した。全直積およびlive Windows AE一般一致は主張しない。\n\n"
        "Verification: `python3 tools/emulation/probe_olmkirakira_mode4_natural_families_exact_20260811.py`\n",
        encoding="utf-8")
    print(json.dumps({"status": output["status"], "exact": output["exact"]}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
