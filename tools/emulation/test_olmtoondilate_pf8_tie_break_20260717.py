"""Direct executable assertions for the PF8 worker tie-break fixture."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from probe_olmtoondilate_pf8_tie_break_20260717 import run  # noqa: E402


def test_pf8_worker_tie_break() -> None:
    payload = run()
    assert payload["status"] == "PASS_PF8_WORKER_TIE_BREAK"
    assert all(payload["gates"].values())
    assert payload["paired_runs"][0]["output_pixels"][1] == [255, 10, 20, 30]
    assert payload["paired_runs"][1]["output_pixels"][1] == [255, 90, 80, 70]


if __name__ == "__main__":
    test_pf8_worker_tie_break()
    print("PASS OLMToonDilate PF8 worker tie-break")
