#!/usr/bin/env python3
"""Smoke-test the OLMBlur 32bpc candidate audit with local synthetic EXRs."""

from __future__ import annotations

import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "scripts" / "audit_olmblur_32bpc_mac_candidates.py"


def attr(name: str, typ: str, value: bytes) -> bytes:
    return name.encode() + b"\0" + typ.encode() + b"\0" + struct.pack("<I", len(value)) + value


def make_exr(path: Path, red: float = 1.0) -> None:
    entries = b"".join(name.encode() + b"\0" + struct.pack("<iB3xii", 2, 0, 1, 1) for name in ("R", "G", "B", "A")) + b"\0"
    header = b"".join([
        attr("channels", "chlist", entries), attr("compression", "compression", b"\0"),
        attr("dataWindow", "box2i", struct.pack("<4i", 0, 0, 1, 0)),
        attr("displayWindow", "box2i", struct.pack("<4i", 0, 0, 1, 0)),
        attr("lineOrder", "lineOrder", b"\0"), attr("pixelAspectRatio", "float", struct.pack("<f", 1.0)),
        attr("screenWindowCenter", "v2f", struct.pack("<2f", 0.0, 0.0)), attr("screenWindowWidth", "float", struct.pack("<f", 1.0)),
    ]) + b"\0"
    payload = struct.pack("<8f", red, red, 0.25, 0.25, 0.5, 0.5, 1.0, 1.0)
    blob = struct.pack("<II", 20000630, 2) + header
    offset = len(blob) + 8
    path.write_bytes(blob + struct.pack("<Q", offset) + struct.pack("<iI", 0, len(payload)) + payload)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix=".olmblur_32bpc_audit_smoke_", dir=ROOT / "refs" / "scripts") as tmp:
        root = Path(tmp)
        win, effect, noop = (root / name for name in ("windows", "mac_effect", "mac_noop"))
        for directory in (win, effect, noop):
            directory.mkdir()
        spec = root / "focused.json"
        param = {"name": "Number of Repeat", "match_name": "OLM OLM Blur-0003", "value": 2}
        spec.write_text(json.dumps({"scope": {"bit_depth": "32bpc"}, "effect": {"match_name": "OLM OLM Blur"}, "cases": [{"id": "olmblur__case_0001", "source_case_id": "case_0001", "params_full": [param]}]}), encoding="utf-8")
        (win / "provenance.json").write_text(json.dumps({"plugin_aex_sha256": "a" * 64}), encoding="utf-8")
        (win / "reference_manifest.json").write_text(json.dumps({"ae_version": "26.3x87", "project": {"bits_per_channel": 32, "working_space": "", "linearize_working_space": False, "blend_colors_using_1_0_gamma": False, "project_gpu_accel_type": {"current_name": "SOFTWARE", "raw": 1816}}, "output_capabilities": {"output_format": "exr", "float_preserving": True, "output_template": "OLM EXR 32 Float", "output_module_readback_verified": True}, "cases": [{"id": "olmblur__case_0001", "effects": [{"params": [param]}]}]}), encoding="utf-8")
        (noop / "provenance.json").write_text(json.dumps({"loaded_plugin": {"sha256": "a" * 64}}), encoding="utf-8")
        settings = {"sha256": "d" * 64, "serialization": "same"}
        mac_return = {"kind": "olmblur_32bpc_mac_validation_return", "ae_version": "26.3x87", "project": {"bits_per_channel": 32, "renderer": "SOFTWARE", "working_space": "None", "linear_blending": False}, "output_module": {"template_name": "OLM EXR 32 Float", "intent": {"channels": ["A", "B", "G", "R"], "compression": "none", "sample_type": "FLOAT"}}, "loaded_plugin": {"path": "/synthetic/OLMBlur", "sha256": "a" * 64}, "loaded_plugin_proof": {"method": "vmmap_exact_path", "pid": 123, "module_path": "/synthetic/OLMBlur", "module_sha256": "a" * 64, "binary_predates_process_start": True}, "cases": [{"id": "olmblur__case_0001", "input": {"sha256": "c" * 64}, "params": [param], "outputs": {"no_effect": {"output_module_settings": settings}, "effect_on": {"output_module_settings": settings}}}]}
        (effect / "mac_validation_return.json").write_text(json.dumps(mac_return), encoding="utf-8")
        make_exr(win / "olmblur__case_0001.exr")
        make_exr(win / "olmblur__case_0001_before_effects.exr")
        make_exr(win / "olmcolorkey__case_0001.exr")
        make_exr(win / "olmcolorkey__case_0001_before_effects.exr")
        make_exr(win / "olmblur__case_00010.exr")
        make_exr(win / "olmblur__case_0001__garbage.exr")
        make_exr(effect / "olmblur__case_0001__effect_on.exr")
        make_exr(noop / "olmblur__case_0001__no_effect.exr")
        report = root / "audit.json"
        passed = subprocess.run([sys.executable, str(AUDIT), "--focused-spec", str(spec), "--windows-reference-dir", str(win), "--mac-effect-result-root", str(effect), "--mac-no-op-result-root", str(noop), "--output", str(report)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert passed.returncode == 0, passed.stdout
        exact = json.loads(report.read_text())
        assert exact["gates"]["ae_exact"] is True
        assert exact["cases"][0]["mac"]["no_op"]["path"] == "olmblur__case_0001__no_effect.exr"
        assert exact["cases"][0]["parameter_identity"]["match"] is True
        assert exact["gates"]["mac_loaded_module_bound"] is True
        assert exact["gates"]["environment_identity"] is True
        assert str(root) not in report.read_text()
        (effect / "conflicting_provenance.json").write_text(json.dumps({"loaded_plugin": {"sha256": "b" * 64}}), encoding="utf-8")
        conflict = subprocess.run([sys.executable, str(AUDIT), "--focused-spec", str(spec), "--windows-reference-dir", str(win), "--mac-effect-result-root", str(effect), "--mac-no-op-result-root", str(noop), "--output", str(root / "conflict.json")], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert conflict.returncode == 2 and "conflicting explicit plug-in SHA-256" in conflict.stdout, conflict.stdout
        (effect / "conflicting_provenance.json").unlink()
        win_manifest = json.loads((win / "reference_manifest.json").read_text())
        win_manifest["cases"][0]["effects"][0]["params"][0]["value"] = 1
        (win / "reference_manifest.json").write_text(json.dumps(win_manifest), encoding="utf-8")
        param_mismatch = subprocess.run([sys.executable, str(AUDIT), "--focused-spec", str(spec), "--windows-reference-dir", str(win), "--mac-effect-result-root", str(effect), "--mac-no-op-result-root", str(noop), "--output", str(root / "param_mismatch.json")], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert param_mismatch.returncode == 1, param_mismatch.stdout
        mismatch_report = json.loads((root / "param_mismatch.json").read_text())
        assert mismatch_report["gates"]["parameter_identity"] is False
        assert mismatch_report["cases"][0]["effect_result_classification"] == "invalid_parameter_or_control_identity"
        assert mismatch_report["cases"][0]["parameter_identity"]["windows_differences"] == [{"match_name": "OLM OLM Blur-0003", "expected": 2, "actual": 1, "reason": "value_mismatch"}]
        win_manifest["cases"][0]["effects"][0]["params"][0]["value"] = 2
        (win / "reference_manifest.json").write_text(json.dumps(win_manifest), encoding="utf-8")
        make_exr(effect / "olmblur__case_0001__effect_on.exr", red=2.0)
        failed = subprocess.run([sys.executable, str(AUDIT), "--focused-spec", str(spec), "--windows-reference-dir", str(win), "--mac-effect-result-root", str(effect), "--mac-no-op-result-root", str(noop), "--output", str(root / "mismatch.json")], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert failed.returncode == 1, failed.stdout
        mismatch = json.loads((root / "mismatch.json").read_text())
        assert mismatch["gates"]["ae_exact"] is False
        assert mismatch["cases"][0]["effect"]["mismatched_values"] == 2
        assert mismatch["cases"][0]["effect"]["mismatched_values_by_channel"]["R"] == 2
        win_manifest["project"]["working_space"] = None
        (win / "reference_manifest.json").write_text(json.dumps(win_manifest), encoding="utf-8")
        environment_failed = subprocess.run([sys.executable, str(AUDIT), "--focused-spec", str(spec), "--windows-reference-dir", str(win), "--mac-effect-result-root", str(effect), "--mac-no-op-result-root", str(noop), "--output", str(root / "environment_failed.json")], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert environment_failed.returncode == 1, environment_failed.stdout
        environment_report = json.loads((root / "environment_failed.json").read_text())
        assert environment_report["gates"]["environment_identity"] is False
        assert environment_report["cases"][0]["effect_result_classification"] == "invalid_environment_or_provenance_identity"
        win_manifest["project"]["working_space"] = ""
        (win / "reference_manifest.json").write_text(json.dumps(win_manifest), encoding="utf-8")
        (win / "provenance.json").unlink()
        blocked = subprocess.run([sys.executable, str(AUDIT), "--focused-spec", str(spec), "--windows-reference-dir", str(win), "--mac-effect-result-root", str(effect), "--mac-no-op-result-root", str(noop), "--output", str(root / "blocked.json")], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert blocked.returncode == 1, blocked.stdout
        assert "Windows AEX hash missing from provenance" in json.loads((root / "blocked.json").read_text())["gates"]["refusal_reasons"]
    print("[OK] OLMBlur 32bpc audit exact, mismatch, and provenance refusal paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
