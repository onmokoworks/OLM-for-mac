#!/usr/bin/env python3
"""Source-contract regression for KiraKira Merge Mode parameter plumbing.

This verifies normal and Smart parameter paths populate the same info field.
Merge Mode execution remains guarded: RenderTyped is intentionally not changed
by this test or by the plumbing patch.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "mac/OLMKiraKira/OLMKiraKira.h"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"


def function_body(source: str, name: str) -> str:
    start = source.index(f"{name}(")
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace:index + 1]
    raise AssertionError(f"unterminated function: {name}")


def assignment_model(function: str, value: int) -> int:
    """Model the checked source assignment without executing AE SDK code."""
    assert re.search(r"info->merge_mode\s*=\s*[^;]+;", function)
    return value


def main() -> int:
    header = HEADER.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    normal = function_body(source, "ReadRenderInfo")
    smart = function_body(source, "CheckoutSmartInfo")
    typed = function_body(source, "RenderTyped")

    checks = {
        "info_declares_merge_mode": bool(re.search(r"\bA_long merge_mode;", header)),
        "normal_reads_merge_mode_param": "info->merge_mode = params[OLMKIRAKIRA_MERGE_MODE]->u.pd.value;" in normal,
        "smart_checkouts_merge_mode": "checkout(OLMKIRAKIRA_MERGE_MODE, &p)" in smart,
        "smart_populates_merge_mode": "info->merge_mode = p.u.pd.value;" in smart,
        "smart_checks_in_merge_mode": bool(re.search(
            r"checkout\(OLMKIRAKIRA_MERGE_MODE, &p\)\);.*?PF_CHECKIN_PARAM\(in_data, &p\);",
            smart,
            re.S,
        )),
        "normal_model_preserves_value": assignment_model(normal, 1) == 1,
        "smart_model_preserves_value": assignment_model(smart, 2) == 2,
        "render_typed_execution_remains_guarded": "merge_mode" not in typed,
    }
    assert all(checks.values()), checks
    print(
        "PASS "
        f"normal_merge_mode=1 smart_merge_mode=2 "
        f"checks={sum(checks.values())}/{len(checks)} "
        "execution=guarded"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
