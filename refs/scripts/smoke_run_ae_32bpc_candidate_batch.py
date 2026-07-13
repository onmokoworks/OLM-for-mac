#!/usr/bin/env python3
"""Smoke-test dual-artifact 32bpc candidate batching without launching After Effects."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / "scripts/run_ae_32bpc_candidate_batch.py"


def load_batch_module():
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("run_ae_32bpc_candidate_batch", BATCH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def attr(name: str, typ: str, value: bytes) -> bytes:
    return name.encode() + b"\0" + typ.encode() + b"\0" + struct.pack("<I", len(value)) + value


def make_exr(path: Path, delta: int) -> None:
    channels = ["A", "B", "G", "R"]
    entries = b"".join(name.encode() + b"\0" + struct.pack("<iB3xii", 2, 0, 1, 1) for name in channels) + b"\0"
    header = b"".join([
        attr("channels", "chlist", entries),
        attr("compression", "compression", b"\0"),
        attr("dataWindow", "box2i", struct.pack("<4i", 0, 0, 1, 0)),
        attr("displayWindow", "box2i", struct.pack("<4i", 0, 0, 1, 0)),
        attr("lineOrder", "lineOrder", b"\0"),
        attr("pixelAspectRatio", "float", struct.pack("<f", 1.0)),
        attr("screenWindowCenter", "v2f", struct.pack("<2f", 0.0, 0.0)),
        attr("screenWindowWidth", "float", struct.pack("<f", 1.0)),
    ]) + b"\0"
    header_blob = struct.pack("<II", 20000630, 2) + header
    payload = struct.pack(
        "<8I",
        0x3f800000,
        0x3f000000,
        0x3e800000,
        0x00000000,
        0x3f800000,
        0x3f000000,
        0x3e800000,
        delta,
    )
    chunk = struct.pack("<iI", 0, len(payload)) + payload
    offset = len(header_blob) + 8
    path.write_bytes(header_blob + struct.pack("<Q", offset) + chunk)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_flag(command: list[str], name: str) -> str:
    return command[command.index(name) + 1]


def parse_ae_env(command: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for index, token in enumerate(command):
        if token == "--ae-env":
            key, value = command[index + 1].split("=", 1)
            values[key] = value
    return values


def run_batch(module, argv: list[str]) -> int:
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(BATCH), *argv]
        return module.main()
    finally:
        sys.argv = old_argv


def main() -> int:
    module = load_batch_module()
    with tempfile.TemporaryDirectory(prefix="olm_32bpc_candidate_batch_") as tmp:
        work = Path(tmp) / "work"
        dry_work = Path(tmp) / "dry_work"
        plugin_dir = Path(tmp) / "plugins"
        plugin_dir.mkdir()
        color_key_plugin = plugin_dir / "OLMColorKey.plugin"
        toon_dilate_plugin = plugin_dir / "OLMToonDilate.plugin"
        color_key_plugin.write_bytes(b"olmcolorkey-plugin-binary\n")
        toon_dilate_plugin.write_bytes(b"olmtoondilate-plugin-binary\n")
        plugin_hashes = {
            "OLM Color Key": digest(color_key_plugin),
            "ADBE OLMToonDilate": digest(toon_dilate_plugin),
        }
        plugin_args = [
            "--plugin-binary", f"OLM Color Key={color_key_plugin}",
            "--plugin-binary", f"ADBE OLMToonDilate={toon_dilate_plugin}",
        ]
        calls: list[dict[str, object]] = []
        original_run = module.subprocess.run
        original_platform_system = module.platform.system

        def fake_run(command, cwd=None, text=None, stdout=None, stderr=None, **kwargs):
            assert isinstance(command, list)
            command_text = [str(item) for item in command]
            if command_text[:2] == ["pgrep", "-x"]:
                return subprocess.CompletedProcess(command_text, 1, stdout="")
            output_dir = Path(parse_flag(command_text, "--output-dir"))
            case_id = parse_flag(command_text, "--case-id")
            ae_env = parse_ae_env(command_text)
            effect_disabled = ae_env.get("OLM_AE_DISABLE_EFFECT") == "1"
            output_dir.mkdir(parents=True, exist_ok=True)
            exr_path = output_dir / f"{case_id}.exr"
            make_exr(exr_path, 17 if effect_disabled else 9)
            result = {
                "kind": "olm_ae_single_case_result",
                "ae_version": "26.3-test",
                "request_dir": parse_flag(command_text, "--request-dir"),
                "case_id": case_id,
                "output_dir": str(output_dir),
                "output_png": "",
                "output_exr": str(exr_path),
                "project_bits_per_channel": 32,
                "project_working_space": "",
                "project_linear_blending": False,
                "input_alpha_mode": "default",
                "effect_disabled": effect_disabled,
                "status": "ok",
                "error": "",
                "warnings": [],
            }
            (output_dir / "AE_SINGLE_CASE_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            calls.append({
                "case_id": case_id,
                "output_dir": str(output_dir),
                "ae_env": ae_env,
                "cwd": str(cwd),
            })
            return subprocess.CompletedProcess(command_text, 0, stdout=f"fake runner {case_id} effect_disabled={int(effect_disabled)}\n")

        try:
            module.subprocess.run = fake_run
            module.platform.system = lambda: "Darwin"
            failed_calls_before = len(calls)
            assert run_batch(module, ["--work-dir", str(work)]) == 1
            assert len(calls) == failed_calls_before

            assert run_batch(module, ["--work-dir", str(work), *plugin_args]) == 0
            index = json.loads((work / "MAC_32BPC_CANDIDATE_INDEX.json").read_text())
            rows = index["candidates"]
            assert len(rows) == 12
            assert len(calls) == 24
            assert all(row["state"] == "rendered" for row in rows)
            assert all(row["readiness"]["executed"] is True and row["readiness"]["validated"] is True for row in rows)
            for row in rows:
                assert Path(row["bridge_dir"]).is_dir()
                assert row["candidate_contract"] == "mac-float-rgba-exr-v1"
                assert row["bit_depth"] == "32bpc" and row["bits_per_channel"] == 32
                assert len(row["params_sha256"]) == 64
                binding = row["mac_plugin_binding"]
                match_name = row["case"]["effect"]["match_name"]
                assert binding["match_name"] == match_name
                assert binding["state"] == "bound"
                assert binding["required_for_actual_run"] is True
                assert binding["sha256"] == plugin_hashes[match_name]
                artifacts = row["artifacts"]
                assert set(artifacts) == {"effect_on", "no_effect"}
                assert row["exr"]["sha256"] == artifacts["effect_on"]["sha256"]
                assert row["result"]["effect_disabled"] is False
                assert "loaded_plugin_sha256" not in row["result"]
                assert artifacts["effect_on"]["state"] == "rendered"
                assert artifacts["effect_on"]["effect_disabled"] is False
                assert artifacts["effect_on"]["bound_plugin_sha256"] == plugin_hashes[match_name]
                assert artifacts["effect_on"]["result"]["effect_disabled"] is False
                assert "loaded_plugin_sha256" not in artifacts["effect_on"]["result"]
                assert artifacts["effect_on"]["sha256"] == artifacts["effect_on"]["exr"]["sha256"]
                assert artifacts["no_effect"]["state"] == "rendered"
                assert artifacts["no_effect"]["effect_disabled"] is True
                assert artifacts["effect_on"]["ae_env"] == {"OLM_AE_FORCE_NEW_PROJECT": "1"}
                assert artifacts["no_effect"]["ae_env"] == {
                    "OLM_AE_DISABLE_EFFECT": "1",
                    "OLM_AE_FORCE_NEW_PROJECT": "1",
                }
                assert artifacts["no_effect"]["result"]["effect_disabled"] is True
                assert "loaded_plugin_sha256" not in artifacts["no_effect"]["result"]
                assert artifacts["no_effect"]["sha256"] == artifacts["no_effect"]["exr"]["sha256"]
                assert artifacts["effect_on"]["sha256"] != artifacts["no_effect"]["sha256"]
            by_case: dict[str, list[dict[str, object]]] = {}
            for call in calls:
                by_case.setdefault(str(call["case_id"]), []).append(call)
            assert all(len(case_calls) == 2 for case_calls in by_case.values())
            assert all(any(call["ae_env"] == {"OLM_AE_FORCE_NEW_PROJECT": "1"} for call in case_calls) for case_calls in by_case.values())
            assert all(any(call["ae_env"] == {
                "OLM_AE_DISABLE_EFFECT": "1",
                "OLM_AE_FORCE_NEW_PROJECT": "1",
            } for call in case_calls) for case_calls in by_case.values())

            calls_before_dry_run = len(calls)
            assert run_batch(module, ["--dry-run", "--work-dir", str(dry_work), *plugin_args]) == 0
        finally:
            module.subprocess.run = original_run
            module.platform.system = original_platform_system

        dry_index = json.loads((dry_work / "MAC_32BPC_CANDIDATE_INDEX.json").read_text())
        dry_rows = dry_index["candidates"]
        assert len(calls) == calls_before_dry_run
        assert len(dry_rows) == 12
        assert all(row["state"] == "planned" for row in dry_rows)
        assert all(Path(row["bridge_dir"]).is_dir() for row in dry_rows)
        assert all(set(row["artifacts"]) == {"effect_on", "no_effect"} for row in dry_rows)
        assert all(row["mac_plugin_binding"]["state"] == "planned" for row in dry_rows)
        assert all("sha256" not in row["mac_plugin_binding"] for row in dry_rows)
        assert all(row["artifacts"]["effect_on"]["state"] == "planned" for row in dry_rows)
        assert all(row["artifacts"]["effect_on"]["ae_env"] == {
            "OLM_AE_FORCE_NEW_PROJECT": "1",
        } for row in dry_rows)
        assert all(row["artifacts"]["no_effect"]["state"] == "planned" for row in dry_rows)
        assert all(row["artifacts"]["no_effect"]["ae_env"] == {
            "OLM_AE_DISABLE_EFFECT": "1",
            "OLM_AE_FORCE_NEW_PROJECT": "1",
        } for row in dry_rows)
        assert (dry_work / "MAC_32BPC_READINESS.json").is_file()
        readiness = json.loads((dry_work / "MAC_32BPC_READINESS.json").read_text())
        assert readiness["status"] == "ready_for_mac_ae_gui"
        validator = subprocess.run(
            [
                "python3", "scripts/verify_32bpc_float_return.py",
                "--mac-candidate-index", str(dry_work / "MAC_32BPC_CANDIDATE_INDEX.json"),
                "--allow-unrendered", "--json",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )
        assert '"pending": 12' in validator.stdout
    if platform.system() == "Darwin":
        print("[OK] 32bpc Mac candidate batch smoke passed with effect-on/no-effect EXR coverage")
    else:
        print("[OK] 32bpc Mac candidate batch smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
