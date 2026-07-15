#!/usr/bin/env python3
"""Run one fail-closed Mac AE OLMBlur case_0006 observation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST_DIR = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625"
MAC_REQUEST = ROOT / "refs/mac_validation_requests/olmblur_case0006_mac_observation_20260715.json"
CASE_ID = "olmblur__case_0006"
REQUEST_ID = "olmblur_case0006_mac_observation_20260715"
PLUGIN_SHA256 = "c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206"
DEFAULT_PLUGIN_PATH = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMBlur.plugin"
MARKER = "OLMBLUR_OBSERVE_STORE16"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def png_header(path: Path) -> dict[str, int]:
    import struct

    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("output is not a PNG")
    if len(data) < 33 or data[12:16] != b"IHDR":
        raise ValueError("PNG IHDR is missing")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", data[16:29]
    )
    return {
        "width": width,
        "height": height,
        "bit_depth": depth,
        "color_type": color,
        "compression": compression,
        "filter_method": filtering,
        "interlace": interlace,
    }


def parse_observation(log_path: Path) -> dict[str, object]:
    lines = [line.strip() for line in log_path.read_text(encoding="utf-8").splitlines() if line.startswith(MARKER + " ")]
    if len(lines) != 1:
        raise ValueError(f"expected exactly one {MARKER} record, found {len(lines)}")
    fields = dict(re.findall(r"([a-z0-9_]+)=([^ ]+)", lines[0]))
    required = {
        "plugin", "effect", "case_id", "request_id", "render_id", "plugin_sha256",
        "project_bpc", "renderer", "x", "y", "w", "h", "blur_amount",
        "blur_smoothness", "repeat", "bias_dir", "legacy", "pre_store",
        "pre_store_hex", "stored",
    }
    missing = sorted(required - fields.keys())
    if missing:
        raise ValueError("diagnostic record missing fields: " + ", ".join(missing))
    expected = {
        "plugin": "OLMBlur", "effect": "OLM_Blur", "case_id": CASE_ID,
        "request_id": REQUEST_ID, "plugin_sha256": PLUGIN_SHA256, "project_bpc": "16",
        "renderer": "Software", "x": "601", "y": "598", "w": "1920",
        "h": "1080", "blur_amount": "5", "blur_smoothness": "100",
        "repeat": "10", "bias_dir": "1", "legacy": "0",
    }
    for key, value in expected.items():
        if fields[key] != value:
            raise ValueError(f"diagnostic {key}={fields[key]!r}, expected {value!r}")
    if fields["render_id"] == "":
        raise ValueError("diagnostic render_id is empty")
    def tuple_parts(key: str, count: int) -> list[str]:
        value = fields[key]
        if not (value.startswith("(") and value.endswith(")")):
            raise ValueError(f"diagnostic {key} must be parenthesized")
        parts = value[1:-1].split(",")
        if len(parts) != count or any(not part for part in parts):
            raise ValueError(f"diagnostic {key} must contain {count} values")
        return parts

    try:
        pre_store = [float(value) for value in tuple_parts("pre_store", 3)]
        pre_store_hex = [float.fromhex(value) for value in tuple_parts("pre_store_hex", 3)]
        stored = [int(value, 10) for value in tuple_parts("stored", 4)]
    except ValueError as error:
        raise ValueError("diagnostic numeric tuple is invalid") from error
    if any(not math.isfinite(value) for value in pre_store + pre_store_hex):
        raise ValueError("diagnostic pre_store values must be finite")
    for decimal, hexadecimal in zip(pre_store, pre_store_hex):
        if struct.pack("<f", decimal) != struct.pack("<f", hexadecimal):
            raise ValueError("diagnostic pre_store decimal/hex values disagree")
    if any(value < 0 or value > 32768 for value in stored):
        raise ValueError("diagnostic stored words are outside 0..32768")
    return {"marker": MARKER, "fields": fields, "raw": lines[0]}


def validate_artifacts(output_dir: Path, render_id: str) -> dict[str, object]:
    result_path = output_dir / "AE_SINGLE_CASE_RESULT.json"
    log_path = output_dir / "OLMBLUR_CASE0006_DIAGNOSTIC.log"
    if not result_path.is_file():
        raise ValueError("missing AE_SINGLE_CASE_RESULT.json")
    if not log_path.is_file():
        raise ValueError("missing OLMBlur diagnostic log")
    result = json.loads(result_path.read_text(encoding="utf-8-sig"))
    if result.get("status") != "ok" or result.get("case_id") != CASE_ID:
        raise ValueError("AE result is not a successful case_0006 render")
    if result.get("project_bits_per_channel") != 16:
        raise ValueError("AE result is not 16bpc")
    output_png = Path(str(result.get("output_png", ""))).resolve()
    if output_png.parent != output_dir.resolve() or not output_png.is_file():
        raise ValueError("AE result output_png is missing or outside output directory")
    header = png_header(output_png)
    if header != {
        "width": 1920, "height": 1080, "bit_depth": 16, "color_type": 6,
        "compression": 0, "filter_method": 0, "interlace": 0,
    }:
        raise ValueError(f"output PNG contract mismatch: {header}")
    observation = parse_observation(log_path)
    if observation["fields"]["render_id"] != render_id:
        raise ValueError("diagnostic render_id does not match requested run")
    report = {
        "schema": "olmblur-case0006-mac-observation-v1",
        "status": "answered_observation",
        "claim": "observation_only_not_exact",
        "case_id": CASE_ID,
        "request_id": REQUEST_ID,
        "render_id": render_id,
        "mac_plugin_binary_sha256": PLUGIN_SHA256,
        "point": [601, 598],
        "output": {"path": output_png.name, "sha256": sha256(output_png), "png": header},
        "diagnostic_log": {"path": log_path.name, "sha256": sha256(log_path), "record": observation},
        "ae_result": {"ae_version": result.get("ae_version"), "project_bits_per_channel": 16},
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--request-dir", type=Path, default=REQUEST_DIR)
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument("--plugin-path", type=Path, default=DEFAULT_PLUGIN_PATH)
    parser.add_argument("--render-id", default="olmblur-case0006-mac-observation-20260715")
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def ae_is_running(app_name: str) -> bool:
    script = (
        'tell application "System Events" to '
        f'(name of processes) contains {json.dumps(app_name)}'
    )
    probe = subprocess.run(
        ["osascript", "-e", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return probe.returncode == 0 and probe.stdout.strip().lower() == "true"


def resolve_plugin_binary(plugin_path: Path) -> Path:
    path = plugin_path.expanduser().resolve()
    if path.suffix == ".plugin":
        path = path / "Contents/MacOS/OLMBlur"
    return path


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    plugin_binary = resolve_plugin_binary(args.plugin_path)
    if not plugin_binary.is_file():
        print(f"FAIL-CLOSED: Mac OLMBlur binary is missing: {plugin_binary}", file=sys.stderr)
        return 2
    installed_sha256 = sha256(plugin_binary)
    if installed_sha256 != PLUGIN_SHA256:
        print(
            "FAIL-CLOSED: installed Mac OLMBlur binary identity mismatch: "
            f"{installed_sha256} != {PLUGIN_SHA256} ({plugin_binary})",
            file=sys.stderr,
        )
        return 2
    if args.validate_only:
        try:
            report = validate_artifacts(output_dir, args.render_id)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"FAIL-CLOSED: {error}", file=sys.stderr)
            return 2
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if output_dir.exists() and any(output_dir.iterdir()):
        print("FAIL-CLOSED: output directory must be new and empty", file=sys.stderr)
        return 2
    if not args.request_dir.is_dir():
        print(f"FAIL-CLOSED: request directory is missing: {args.request_dir}", file=sys.stderr)
        return 2
    if not MAC_REQUEST.is_file():
        print(f"FAIL-CLOSED: Mac request contract is missing: {MAC_REQUEST}", file=sys.stderr)
        return 2
    if shutil.which("osascript") is None:
        print("FAIL-CLOSED: osascript is unavailable; AE was not launched", file=sys.stderr)
        return 2
    if not ae_is_running(args.app_name):
        print(f"FAIL-CLOSED: {args.app_name!r} is not already running; AE was not launched", file=sys.stderr)
        return 2
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable, str(ROOT / "scripts/run_ae_single_case.py"),
        "--request-dir", str(args.request_dir.resolve()), "--case-id", CASE_ID,
        "--output-dir", str(output_dir), "--app-name", args.app_name,
        "--timeout", str(args.timeout), "--keep-open",
    ]
    env_args = {
        "OLM_AE_FORCE_NEW_PROJECT": "1", "OLM_AE_FORCE_SOFTWARE": "1",
        "OLMBLUR_OBSERVE_CASE0006_PIXEL": "1",
        "OLMBLUR_OBSERVE_DUMP_PATH": str(output_dir / "OLMBLUR_CASE0006_DIAGNOSTIC.log"),
        "OLMBLUR_OBSERVE_CASE_ID": CASE_ID, "OLMBLUR_OBSERVE_REQUEST_ID": REQUEST_ID,
        "OLMBLUR_OBSERVE_RENDER_ID": args.render_id,
        "OLMBLUR_OBSERVE_PLUGIN_SHA256": installed_sha256,
        "OLMBLUR_OBSERVE_PROJECT_BPC": "16", "OLMBLUR_OBSERVE_RENDERER": "Software",
    }
    for key, value in env_args.items():
        command.extend(["--ae-env", f"{key}={value}"])
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        print("FAIL-CLOSED: AE observation command failed", file=sys.stderr)
        return completed.returncode or 2
    try:
        report = validate_artifacts(output_dir, args.render_id)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL-CLOSED: {error}", file=sys.stderr)
        return 2
    report_path = output_dir / "OLMBLUR_CASE0006_OBSERVATION_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[OK] OLMBlur observation captured: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
