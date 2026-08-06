#!/usr/bin/env python3
"""Static acceptance skeleton for the external AEXCompat implementation."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "refs/requests/olmsmoother_v1_pf16_macos_aexcompat_session_20260805.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_contract_and_run5_identities_are_pinned() -> None:
    spec = json.loads(CONTRACT.read_text())
    assert spec["schema_version"] == 1
    assert spec["transport_invariants"]["pixel_format"] == "argb16"
    assert spec["transport_invariants"]["render_path"] == "classic"
    assert spec["transport_invariants"]["output_hash_domain"] == "raw rowbytes*height typed world including padding"
    assert "exact RGBA" in spec["required_api"]["color_parameter_requirement"]
    for record in spec["run5_identity"].values():
        if isinstance(record, dict) and "path" in record:
            assert sha(ROOT / record["path"]) == record["sha256"]


def test_external_report_when_supplied(tmp_path: Path) -> None:
    """AEXCompat can copy its report here in CI; absence is not an exact pass."""
    report_path = ROOT / "refs/returns/olmsmoother_v1_pf16_macos_aexcompat_session_20260805.json"
    if not report_path.exists():
        return
    spec = json.loads(CONTRACT.read_text())
    report = json.loads(report_path.read_text())
    required = set(spec["required_api"]["report_required_fields"])
    assert required <= set(report)
    assert report["plugin_sha256"] == spec["run5_identity"]["plugin"]["sha256"]
    assert report["pixel_format"] == "argb16"
    assert report["render_path"] == "classic"
    assert report["input_immutable"] is True
    assert report["guard_bytes_intact"] is True
    assert report["session_frame_count"] == 1
    assert report["parameters_readback"] == [
        {"slot": 1, "value": 1},
        {"slot": 2, "value": [0.79379999637604, 0.7335000038147, 0.90140002965927, 1]},
        {"slot": 3, "value": 33},
    ]
