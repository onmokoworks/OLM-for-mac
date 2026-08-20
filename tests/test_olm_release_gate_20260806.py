#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
from datetime import datetime, timedelta
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_olm_release_gate_20260806.py"
spec = importlib.util.spec_from_file_location("release_gate", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> int:
    manifest = json.loads(module.MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema"] == "olm.release-gate-manifest/2"
    assert manifest["current_identity_manifest"] == module.IDENTITY_MANIFEST.relative_to(module.ROOT).as_posix()
    assert manifest["current_host_smoke"] == module.CURRENT_HOST_SMOKE.relative_to(module.ROOT).as_posix()
    rows = module.validate_current_host_smoke(manifest)
    assert len(rows) == 10
    assert {row["plugin"] for row in rows} == {
        "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
        "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
        "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
    }
    assert not [row for row in rows if row["state"] == "invalid"]
    assert not [row for row in rows if row["state"] == "pending"]
    assert {row["evidence"] for row in rows} == {
        "refs/conformance/olm_all10_post_colorkeep_count9_fresh_ae_smoke_20260813.json"
    }
    install = module.installed_gate()
    assert install["state"] == "proven", install
    parameter_ui = module.parameter_ui_gate()
    assert parameter_ui["state"] == "proven", parameter_ui
    assert parameter_ui["counts"] == {"proven": 10, "pending": 0, "invalid": 0}
    print("PASS_OLM_RELEASE_GATE_AUDIT proven=10 pending=0 invalid=0 universal=10 parameter_ui=10")
    return 0


def fail_closed_binding_regression() -> None:
    manifest = json.loads(module.MANIFEST.read_text(encoding="utf-8"))
    identity = json.loads(module.IDENTITY_MANIFEST.read_text(encoding="utf-8"))
    accepted = {row["plugin"]: row["sha256"] for row in identity["plugins"]}
    identity_rows = {row["plugin"]: row for row in identity["plugins"]}
    identity_sha = hashlib.sha256(module.IDENTITY_MANIFEST.read_bytes()).hexdigest()
    accepted_at = datetime.fromisoformat(identity["accepted_at"])
    expectations = {row["plugin"]: row["host_smoke_expectation"] for row in manifest["plugins"]}
    base = {
        "schema": "olm.all10-current-install-fresh-ae-smoke/1",
        "status": "pass",
        "passed": True,
        "installed_identity_manifest": {
            "path": module.IDENTITY_MANIFEST.relative_to(module.ROOT).as_posix(),
            "sha256": identity_sha,
            "accepted_at": identity["accepted_at"],
        },
        "host": {
            "process_count": 1,
            "fresh_process": True,
            "started_after_identity_acceptance": True,
            "renderer": "SOFTWARE",
            "pid": 4242,
            "started_at": (accepted_at + timedelta(seconds=1)).isoformat(),
            "captured_at": (accepted_at + timedelta(seconds=2)).isoformat(),
        },
        "plugins": [
            {
                "plugin": plugin,
                "status": "pass",
                "loaded": True,
                "applied": True,
                "host_frame_render_succeeded": True,
                "render_succeeded": True,
                "host_smoke_expectation": expectations[plugin],
                "effect_enabled_host_frame_attempted": expectations[plugin] == "enabled_host_frame_render",
                "effect_enabled_host_frame_succeeded": expectations[plugin] == "enabled_host_frame_render",
                "numerical_render_expected": False,
                "numerical_render_supported": False,
                "effect_enabled_numerical_render_attempted": False,
                "numerical_render_succeeded": None,
                "effect_disabled_during_host_frame": expectations[plugin] == "disabled_host_frame_render",
                "installed_executable_sha256": sha,
                "loaded_module_path": str(
                    Path(identity_rows[plugin]["installed_bundle"]) / "Contents/MacOS" / plugin
                ),
                "loaded_module_count": 1,
                "ae_pid": 4242,
                "post_render_mapping_exact": True,
                "post_render_on_disk_sha256": sha,
            }
            for plugin, sha in accepted.items()
        ],
    }
    original = module.CURRENT_HOST_SMOKE
    original_raw = module.CURRENT_HOST_SMOKE_RAW
    original_runner = module.CURRENT_HOST_SMOKE_RUNNER
    with tempfile.TemporaryDirectory(dir=ROOT / "handoffs") as raw:
        directory = Path(raw)
        path = directory / "smoke.json"
        raw_report = directory / "raw.json"
        runner = directory / "runner.py"
        raw_payload = json.loads(json.dumps(base))
        raw_payload["schema"] = "olm.all10-current-install-fresh-ae-smoke-raw/1"
        raw_report.write_text(json.dumps(raw_payload), encoding="utf-8")
        runner.write_text(
            "def validate_persisted_summary(summary, raw, raw_path):\n"
            "    return (raw.get('status') == summary.get('status') and "
            "raw.get('passed') == summary.get('passed') and "
            "raw.get('installed_identity_manifest') == summary.get('installed_identity_manifest'))\n",
            encoding="utf-8",
        )
        base["raw_report"] = {
            "path": raw_report.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(raw_report.read_bytes()).hexdigest(),
        }
        base["runner"] = {
            "path": runner.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(runner.read_bytes()).hexdigest(),
        }
        # Artifact bindings are summary-only metadata; the raw authority keeps
        # the normalized semantic fields it observed.
        module.CURRENT_HOST_SMOKE = path
        module.CURRENT_HOST_SMOKE_RAW = raw_report
        module.CURRENT_HOST_SMOKE_RUNNER = runner
        synthetic_manifest = json.loads(json.dumps(manifest))
        synthetic_manifest["current_host_smoke"] = path.relative_to(ROOT).as_posix()
        try:
            path.write_text(json.dumps(base), encoding="utf-8")
            assert all(row["state"] == "proven" for row in module.validate_current_host_smoke(synthetic_manifest))
            tampered = json.loads(json.dumps(base))
            tampered["installed_identity_manifest"]["sha256"] = "0" * 64
            path.write_text(json.dumps(tampered), encoding="utf-8")
            assert all(row["state"] == "invalid" for row in module.validate_current_host_smoke(synthetic_manifest))
            tampered = json.loads(json.dumps(base))
            tampered["plugins"][0]["installed_executable_sha256"] = "f" * 64
            path.write_text(json.dumps(tampered), encoding="utf-8")
            rows = module.validate_current_host_smoke(synthetic_manifest)
            assert sum(row["state"] == "invalid" for row in rows) == 1
            tampered = json.loads(json.dumps(base))
            tampered["host"]["fresh_process"] = False
            path.write_text(json.dumps(tampered), encoding="utf-8")
            assert all(row["state"] == "invalid" for row in module.validate_current_host_smoke(synthetic_manifest))
            tampered = json.loads(json.dumps(base))
            tampered["host"]["started_at"] = (accepted_at - timedelta(seconds=1)).isoformat()
            path.write_text(json.dumps(tampered), encoding="utf-8")
            assert all(row["state"] == "invalid" for row in module.validate_current_host_smoke(synthetic_manifest))
            tampered = json.loads(json.dumps(base))
            tampered["plugins"].append(dict(tampered["plugins"][0]))
            path.write_text(json.dumps(tampered), encoding="utf-8")
            assert all(row["state"] == "invalid" for row in module.validate_current_host_smoke(synthetic_manifest))
            tampered = json.loads(json.dumps(base))
            tampered["plugins"][0]["loaded_module_count"] = 2
            path.write_text(json.dumps(tampered), encoding="utf-8")
            rows = module.validate_current_host_smoke(synthetic_manifest)
            assert sum(row["state"] == "invalid" for row in rows) == 1
            raw_report.write_text("tampered\n", encoding="utf-8")
            path.write_text(json.dumps(base), encoding="utf-8")
            assert all(row["state"] == "invalid" for row in module.validate_current_host_smoke(synthetic_manifest))
        finally:
            module.CURRENT_HOST_SMOKE = original
            module.CURRENT_HOST_SMOKE_RAW = original_raw
            module.CURRENT_HOST_SMOKE_RUNNER = original_runner


def windows_boundary_tamper_regression() -> None:
    payload = json.loads(module.WINDOWS_BOUNDARY_INTAKE.read_text(encoding="utf-8"))
    assert module.windows_boundary_gate()["accepted_rows"] == 7
    original = module.WINDOWS_BOUNDARY_INTAKE
    with tempfile.TemporaryDirectory(dir=ROOT / "handoffs") as raw:
        path = Path(raw) / "intake.json"
        module.WINDOWS_BOUNDARY_INTAKE = path
        try:
            duplicate = json.loads(json.dumps(payload))
            duplicate["rows"] = [dict(duplicate["rows"][0]) for _ in range(7)]
            path.write_text(json.dumps(duplicate), encoding="utf-8")
            try:
                module.windows_boundary_gate()
            except ValueError:
                pass
            else:
                raise AssertionError("duplicate Windows boundary rows were accepted")
            bad_hash = json.loads(json.dumps(payload))
            bad_hash["rows"][0]["effect_on_sha256"] = "0" * 63
            path.write_text(json.dumps(bad_hash), encoding="utf-8")
            try:
                module.windows_boundary_gate()
            except ValueError:
                pass
            else:
                raise AssertionError("invalid Windows boundary hash was accepted")
        finally:
            module.WINDOWS_BOUNDARY_INTAKE = original


def windows_boundary_is_release_critical() -> None:
    """The top-level GO predicate must fail when the Windows gate is invalid."""
    proven = {"state": "proven"}
    counts = {"proven": 10, "pending": 0, "invalid": 0}
    expected = {"state": "accepted_bounded_plugin_comparisons_complete", "accepted_rows": 7}
    invalid_state = {**expected, "state": "invalid"}
    invalid_count = {**expected, "accepted_rows": 6}
    assert module.release_predicate(proven, proven, proven, expected, counts)
    assert not module.release_predicate(proven, proven, proven, invalid_state, counts)
    assert not module.release_predicate(proven, proven, proven, invalid_count, counts)


if __name__ == "__main__":
    fail_closed_binding_regression()
    windows_boundary_tamper_regression()
    windows_boundary_is_release_critical()
    raise SystemExit(main())
