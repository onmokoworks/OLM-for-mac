from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from probe_olmcolorkey_boundary_to_distance_actual_aex_20260716 import run  # noqa: E402


def test_checked_in_aex_boundary_to_distance_contract() -> None:
    report = run(ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex")
    assert report["classification"].endswith("not AE-exact output")
    assert report["facts"]["seed_first_channel"][1] == [255, 255, 0, 255, 255]
    assert report["facts"]["distance_type_3_next_blocker"].startswith("FUN_180007ec0")
    for leaf in report["facts"]["distance"].values():
        assert leaf["rax"] == "0x0"
        assert leaf["imports"] == []
        assert any(value != 0.0 for row in leaf["first_float_grid"] for value in row)


def test_report_is_json_when_present() -> None:
    path = ROOT / "refs/conformance/olmcolorkey_boundary_to_distance_actual_aex_20260716.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["kind"].endswith("20260716")
