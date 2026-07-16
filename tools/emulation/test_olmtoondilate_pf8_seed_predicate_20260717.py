"""Tests for the bounded PF8 seed-predicate worker fixture."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from probe_olmtoondilate_pf8_seed_predicate_20260717 import run  # noqa: E402


def test_pf8_fixture_is_discriminating() -> None:
    payload = run()
    assert payload["status"] == "PASS_PF8_SEED_PREDICATE_DISCRIMINATED"
    assert all(payload["gates"].values())
    pair = payload["paired_runs"]
    assert pair[0]["x1_alpha"] == 254
    assert pair[1]["x1_alpha"] == 255
    assert pair[0]["matches_exact_equality_model"] is True
    assert pair[0]["matches_threshold_conversion_model"] is False
    assert pair[1]["matches_exact_equality_model"] is True
    assert pair[1]["matches_threshold_conversion_model"] is True


if __name__ == "__main__":
    test_pf8_fixture_is_discriminating()
    raise SystemExit(0)
