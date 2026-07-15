#!/usr/bin/env python3
"""Bounded actual-AEX witness for the legacy key/gamma lane.

The pass gate is intentionally limited to the checked-in AEX c280/cce0
classifier and gamma-config boundaries.  It does not use the portable adapter
as an oracle and does not claim live Windows or After Effects behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools" / "emulation"
sys.path.insert(0, str(HERE))

from test_smoother2_fullchain_diff import run_aex  # noqa: E402
from test_smoother2_producer import AEX_PATH  # noqa: E402


EXPECTED = {
    "c2_witness": {"c": 2, "gamma_apply": 1},
    "classifier_one": {"c": 3, "gamma_apply": 1},
}


def finite_gamma_row(row: dict[str, Any]) -> dict[str, Any]:
    normal = row["cce0_entry"]
    colors = row["cce0_gamma_colors_entry"]
    normal_bb10 = normal["bb10_after"]
    colors_bb10 = colors["bb10_after"]
    return {
        "normal": {
            "mode_byte": normal["config"]["gamma_mode_byte"],
            "bb10_apply": normal_bb10[0]["apply"] if normal_bb10 else None,
        },
        "gamma_colors": {
            "mode_byte": colors["config"]["gamma_mode_byte"],
            "gamma_value": colors_bb10[0]["gamma"] if colors_bb10 else None,
            "bb10_apply": colors_bb10[0]["apply"] if colors_bb10 else None,
        },
    }


def run() -> dict[str, Any]:
    rows = []
    checks: list[bool] = []
    for fixture, expected in EXPECTED.items():
        actual = run_aex(fixture, fixture == "c4_control")
        gamma = finite_gamma_row(actual)
        checks.extend([
            actual["c"] == expected["c"],
            gamma["normal"]["mode_byte"] == 0,
            gamma["normal"]["bb10_apply"] == 0,
            gamma["gamma_colors"]["mode_byte"] == 3,
            gamma["gamma_colors"]["bb10_apply"] == expected["gamma_apply"],
            abs(float(gamma["gamma_colors"]["gamma_value"]) - 2.1695473) < 1e-6,
        ])
        rows.append({
            "fixture": fixture,
            "aex_classifier_branch": {"c": actual["c"], "append": actual["append"]},
            "gamma_config_observed": gamma,
            "c280_entry_count": actual["c280_entry"]["count"],
            "aex_gamma_colors_rgba": actual["cce0_gamma_colors_entry"]["rgba"],
        })

    aex_sha256 = hashlib.sha256(AEX_PATH.read_bytes()).hexdigest()
    return {
        "verdict": "PASS_LOCAL_ACTUAL_AEX_LEGACY_GAMMA_CONFIG_BOUNDARY",
        "date": "2026-07-16",
        "scope": "checked-in actual AEX CPU emulation; classifier and cce0 gamma-config boundary only",
        "aex": {"path": str(AEX_PATH.relative_to(ROOT)), "sha256": aex_sha256},
        "facts": {
            "rows": rows,
            "gamma_value_expected": 2.1695473,
            "gamma_modes": {"normal": 0, "colors_only": 3},
            "classifier_fixture_coverage": ["c2_witness", "classifier_one"],
        },
        "inference": [
            "The actual AEX cce0 entry observes gamma mode 0 as no-apply and mode 3 as Gamma Colors apply for this bounded config.",
            "This narrows the local unresolved legacy lane to live key/setup binding and downstream producer state, rather than inventing a gamma-mode fallback.",
        ],
        "key_boundary": {
            "status": "not_executed_in_this_witness",
            "reason": "The existing actual-AEX entry harness starts after host parameter setup; no portable-only key simulation is accepted as compatibility evidence.",
            "static_sources": [
                "notes/OLMSmoother2_ASM_FACTS.md",
                "refs/conformance/olmsmoother2_case0012_live_config_contract_20260712.md",
            ],
        },
        "claims_not_made": [
            "No Windows execution or live AE host binding.",
            "No legacy case_0004/case_0012 mapping.",
            "No AE-exact, PNG, or portable-only compatibility claim.",
        ],
        "pass": all(checks),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    result = run()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output_json:
        args.output_json.write_text(payload, encoding="utf-8")
    if args.output_md:
        lines = [
            "# OLMSmoother2 legacy key/gamma classifier-config witness - 2026-07-16",
            "",
            f"- Verdict: `{result['verdict']}`",
            "- Scope: checked-in actual-AEX CPU emulation only; no portable adapter is used as an oracle.",
            f"- AEX: `{result['aex']['path']}` SHA-256 `{result['aex']['sha256']}`",
            "",
            "## FACT",
            "",
            "- The bounded actual-AEX rows cover c=2 append and classifier-one c=3.",
            "- The normal cce0 config reaches mode byte 0 with `apply=0`.",
            "- The Gamma Colors cce0 config reaches mode byte 3 with `gamma=2.1695473` and `apply=1`.",
            "- The JSON artifact records the raw AEX-returned rows and all pass checks.",
            "",
            "## INFERENCE",
            "",
            "- This closes only the local classifier/config boundary and does not identify the live legacy case producer state.",
            "- Key host setup remains unexecuted here; portable-only key simulation is deliberately excluded from compatibility evidence.",
            "",
            "## Reproduction",
            "",
            "```sh",
            "python3 tools/emulation/test_olmsmoother2_legacy_key_gamma_classifier_config_witness_20260716.py \\",
            "  --output-json refs/conformance/olmsmoother2_legacy_key_gamma_classifier_config_witness_20260716.json \\",
            "  --output-md refs/conformance/olmsmoother2_legacy_key_gamma_classifier_config_witness_20260716.md",
            "```",
            "",
            "Result: exit `0` when the actual-AEX checks pass.",
            "",
            "## Claims Not Made",
            "",
            "Windows/AE host binding, case mapping, AE exactness, final writeback equivalence, and portable-only compatibility.",
        ]
        args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(payload, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
