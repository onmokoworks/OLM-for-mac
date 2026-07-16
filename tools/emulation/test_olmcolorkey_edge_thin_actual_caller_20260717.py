from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_olmcolorkey_edge_thin_actual_caller_20260717 import run  # noqa: E402


def test_actual_caller_type2_chain() -> None:
    report = run(ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex")
    checked_in = json.loads(
        (ROOT / "refs/conformance/olmcolorkey_edge_thin_actual_caller_20260717.json").read_text(
            encoding="utf-8"
        )
    )
    assert report == checked_in
    assert report["status"] == "pass"
    assert report["schema"] == 2
    assert report["provenance"]["aex_sha256"] == "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
    assert report["fixture"]["dimensions"] == [5, 1]
    assert report["chain"] == ["0x180008ad0", "0x1800058a0", "0x180008320"]
    for row in report["runs"]:
        assert row["status"] == "pass"
        assert row["hits"] == {"caller_callsite": 1, "boundary": 1, "distance": 1, "erode": 1}
        assert row["observations"]["distance"]["XMM3"] == 4000.0
        raw = row["observations"]["erode"]["raw"]
        repaired = row["observations"]["erode"]["repaired"]
        assert raw["RDX_after_callsite_binding"] == raw["stack5_native"]
        assert raw["R9_native"] == repaired["stack5"]
        assert raw["stack7_native"] == repaired["R9"]
        assert raw["stack6_native"] == repaired["stack6"]
        assert raw["R8D_native"] == 2
        assert raw["XMM1_native"] == row["amount"]
        assert raw != repaired
        assert row["distance_identity_preserved"]
        assert row["destination_sentinel_integrity"]
        assert row["repaired_leaf_observation"]["sentinel_integrity"]
        assert row["destination_actual_hex"] == ("ff7f" + "cc" * 6) * 5
        assert all(row["invariants"].values())
    assert report["paired_amount_forwarding"]["exact_forwarding"]
    assert "untouched full caller-to-leaf execution" in report["claim_boundary"]
    assert "semantic oracle" in report["runs"][0]["repaired_leaf_observation"]["classification"]
    assert "terminal_oracle" not in str(report)


if __name__ == "__main__":
    test_actual_caller_type2_chain()
    print("[OK] OLMColorKey actual FUN_180009000 type2 caller chain")
