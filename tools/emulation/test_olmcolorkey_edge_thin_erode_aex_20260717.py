from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_olmcolorkey_edge_thin_erode_aex_20260717 import run  # noqa: E402


def test_hash_pinned_erode_leaf_capture() -> None:
    report = run(ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex")
    assert report["status"] == "pass"
    assert report["provenance"]["function"] == "FUN_180008320"
    assert report["provenance"]["aex_sha256"] == "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
    assert report["schema"] == 2
    assert report["search"]["tested_cases"] == (32 + 512) * 4
    assert report["search"]["discriminating_cases"] == 274
    assert report["search"]["candidate_a_matches"] == 0
    assert report["search"]["candidate_b_matches"] == 0
    assert report["search"]["neither_matches"] == report["search"]["discriminating_cases"]
    assert report["search"]["first_boundary_disagreement"]
    assert "CVTTSS2SI truncates toward zero" in report["boundary_rule_comparison"]["rounding"]
    assert len(report["search"]["exact_fixtures"]) == 6
    assert report["search"]["independent_oracle"].startswith("raw x*2 word load/store")


if __name__ == "__main__":
    test_hash_pinned_erode_leaf_capture()
    print("[OK] OLMColorKey erode leaf: 2176 calls and 6 terminal-loop fixtures")
