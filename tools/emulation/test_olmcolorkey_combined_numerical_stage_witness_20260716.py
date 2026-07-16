from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from probe_olmcolorkey_combined_numerical_stage_witness_20260716 import run  # noqa: E402


def test_combined_numerical_stage_witness() -> None:
    report = run()
    assert report["status"] == "pass", report.get("first_divergence")
    assert report["first_divergence"] is None
    assert all(report["acceptance_gates"].values())
    replacement = report["captures"]["replacement_output"]
    assert replacement[48:52] == [255, 0, 0, 255]
    assert replacement[:4] == [255, 0, 255, 0]
    assert len(report["captures"]["thin_boundary_seed_first_channel"]) == 25
    assert len(report["captures"]["type3_distance_first_channel_float32_words"]) == 25
    assert report["captures"]["blur_destination_before"] != report["captures"]["blur_destination_after"]
    assert all(value == "0x0" for value in report["execution"]["returns"].values())


def test_hash_mismatch_fails_closed() -> None:
    with tempfile.NamedTemporaryFile() as wrong_binary:
        wrong_binary.write(b"not the pinned OLMColorKey binary")
        wrong_binary.flush()
        report = run(Path(wrong_binary.name))
    assert report["status"] == "blocked"
    assert report["aex"]["sha256_match"] is False
    assert report["first_divergence"]["stage"] == "preflight"


if __name__ == "__main__":
    test_combined_numerical_stage_witness()
    test_hash_mismatch_fails_closed()
    print("PASS OLMColorKey combined numerical-stage witness")
