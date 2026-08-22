import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "refs/conformance/olm_public_beta_rc_native_ae_quick_20260822.json"
IDENTITY = ROOT / "refs/conformance/olm_public_beta_rc_identity_20260822.json"


def test_current_rc_native_ae_quick_report_is_exact_and_bounded() -> None:
    report = json.loads(REPORT.read_text())
    identity = json.loads(IDENTITY.read_text())
    assert report["schema"] == "olm.public-beta-rc-native-ae-quick/1"
    assert report["status"] == "accepted_exact"
    assert report["package"]["sha256"] == "74dd05284203287a61205a9f937e25c62731d4a07bbe6fbcecb3d951f523f80d"
    assert report["host"] == {
        "ae_versions": ["26.3x87"],
        "application": "Adobe After Effects 2026",
        "renderer": "SOFTWARE",
    }
    assert "not the full depth/route/parameter matrix" in report["scope"]
    cases = report["accepted_cases"]
    assert len(cases) == 10
    expected = {row["plugin"]: row["sha256"] for row in identity["plugins"]}
    assert {row["plugin"]: row["plugin_sha256"] for row in cases} == expected
    assert all((row["width"], row["height"], row["depth"]) == (1920, 1080, 8) for row in cases)
    assert all(len(row["commit_sha256"]) == 64 for row in cases)
    assert all(len(row["validated_output_sha256"]) == 64 for row in cases)
    assert all(row["validated_output_size_bytes"] > 0 for row in cases)


if __name__ == "__main__":
    test_current_rc_native_ae_quick_report_is_exact_and_bounded()
    print("PUBLIC_BETA_RC_NATIVE_AE pass=1 plugins=10 profile=quick")
