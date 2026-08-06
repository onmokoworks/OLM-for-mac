#!/usr/bin/env python3
"""Guard the PF16 classifier's forward direction comparison.

The Windows FUN_180006a90 and its byte twin FUN_180008060 compare the
selected direction pixel with the reverse-table-2 pixel.  An earlier port
overwrote the latter pointer and compared one slot with itself; at non-zero
tolerance this forced the forward-strong-match branch and removed most of the
native PF16 interpolation visible in the canonical Windows AE boundary row.
"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMSmoother/Mac/OLMSmoother_port.cpp"


def _function(name: str) -> str:
    source = SOURCE.read_text(encoding="utf-8")
    start = source.index(f"\n{name}(")
    next_marker = source.index("\n// ====", start)
    return source[start:next_marker]


def test_pf16_forward_pair_matches_the_pf8_twin() -> None:
    classifier16 = _function("Classifier16")
    classifier8 = _function("Classifier8")

    expected16 = re.compile(
        r"direction_pix\s*=\s*\(const uint16_t\*\)param_4\[param_5\];"
        r"\s*if \(cmp_le\(direction_pix, puVar12\)\)",
        re.S,
    )
    expected8 = re.compile(
        r"direction_pix\s*=\s*\(const uint8_t\*\)param_4\[param_5\];"
        r"\s*if \(cmp_le_8\(direction_pix, puVar12\)\)",
        re.S,
    )
    assert expected16.search(classifier16)
    assert expected8.search(classifier8)


def test_pf16_forward_pair_cannot_alias_reverse_table_operand() -> None:
    classifier16 = _function("Classifier16")
    forward = classifier16[
        classifier16.index("if (iVar23 != 0)") : classifier16.index(
            "// LAB_1800073cf", classifier16.index("if (iVar23 != 0)")
        )
    ]
    assert "puVar18 = (const uint16_t*)param_4[iVar8]" not in forward
    assert "cmp_le(puVar12, puVar18)" not in forward


def test_pf16_rgba8_shadow_changes_only_subhandler_geometry() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "if (state->byte_shadow_world != nullptr)" in source
    assert "SubHandler8(&byte_state, byte_neigh, x, y, dir," in source
    assert "Widen8To16((uint8_t)narrowed) != src[x]" in source
    assert "state->byte_shadow_world = &byte_shadow_world;" in source
    assert "free(byte_shadow_data);" in source
    classifier16 = _function("Classifier16")
    assert "byte_shadow_world" not in classifier16


def test_rgba8_derived_pf16_uses_exact_subhandler_geometry() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    subhandler16 = _function("SubHandler16")
    assert "state->byte_shadow_world != nullptr" in subhandler16
    assert "SubHandler8(&byte_state, byte_neigh" in subhandler16
    assert "state->byte_shadow_world = &byte_shadow_world;" in source
    assert "Widen8To16((uint8_t)narrowed) != src[x]" in source
    assert "MainInterpKernel16(state, neigh" in source
