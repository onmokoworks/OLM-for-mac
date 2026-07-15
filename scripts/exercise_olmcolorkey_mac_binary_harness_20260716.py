#!/usr/bin/env python3
"""Exercise the checked-in Mac OLMColorKey binary on a deterministic RGBA fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "cli" / "OLMColorKey" / "olmcolorkey_cli"
PLUGIN_BINARY = ROOT / "handoff" / "mac_plugin_backups" / "20260626_112301_OLMColorKey_force_lower_precision" / "OLMColorKey.plugin" / "Contents" / "MacOS" / "OLMColorKey"


def write_rgba_png(path: Path, width: int, height: int, pixels: bytes) -> None:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    rows = b"".join(b"\x00" + pixels[y * width * 4:(y + 1) * width * 4] for y in range(height))
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows, 9))
        + chunk(b"IEND", b"")
    )


def read_rgba_png(path: Path) -> tuple[int, int, bytes]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError("output is not PNG")
    pos = 8
    width = height = None
    compressed = bytearray()
    while pos < len(data):
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + size]
        pos += 12 + size
        if kind == b"IHDR":
            width, height, depth, color_type, *_ = struct.unpack(">IIBBBBB", payload)
            if (depth, color_type) != (8, 6):
                raise AssertionError("unexpected output PNG format")
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    if width is None or height is None:
        raise AssertionError("missing PNG header")
    raw = zlib.decompress(compressed)
    stride = width * 4
    rows = []
    for y in range(height):
        filter_type = raw[y * (stride + 1)]
        if filter_type != 0:
            raise AssertionError("harness only accepts filter-zero output")
        rows.append(raw[y * (stride + 1) + 1:y * (stride + 1) + 1 + stride])
    return width, height, b"".join(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command_output(command: list[str]) -> str:
    return subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def repo_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sanitize_repo_output(value: str) -> str:
    return value.replace(str(ROOT), ".")


def run(report_path: Path) -> dict:
    if platform.system() != "Darwin":
        raise RuntimeError("Mac-only harness: expected Darwin")
    if not BINARY.exists():
        raise RuntimeError(f"missing binary: {BINARY}")

    # Red and blue are exact key/non-key controls; the half-alpha green control
    # proves that a non-matching pixel is cleared without changing the input.
    pixels = bytes([
        255, 0, 0, 255,
        0, 255, 0, 128,
        0, 0, 255, 255,
        255, 0, 0, 64,
    ])
    expected = bytes([
        0, 255, 0, 255,
        0, 0, 0, 0,
        0, 0, 0, 0,
        0, 255, 0, 64,
    ])
    params = {
        "Color Keep": 1,
        "Threshold": 0,
        "Premultiplied Color": 0,
        "Color Space": 1,
        "Per Color": 0,
        "Per Component": 0,
        "Enable Replace": 1,
        "Number of Colors": 1,
        "Use Color 1": 1,
        "Color 1": [1, 0, 0],
        "Use Replace Color 1": 1,
        "Replace Color 1": [0, 1, 0],
    }

    with tempfile.TemporaryDirectory(prefix="olmcolorkey_mac_binary_20260716_") as raw:
        temp = Path(raw)
        input_path = temp / "input.png"
        params_path = temp / "params.json"
        output_path = temp / "output.png"
        write_rgba_png(input_path, 2, 2, pixels)
        params_path.write_text(json.dumps(params, sort_keys=True), encoding="utf-8")
        completed = subprocess.run(
            [str(BINARY), "--input", str(input_path), "--params", str(params_path), "--output", str(output_path)],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        width, height, actual = read_rgba_png(output_path)

    plugin_symbols = command_output(["nm", "-gU", str(PLUGIN_BINARY)]).splitlines()
    selected_symbols = [line for line in plugin_symbols if any(name in line for name in ("_EffectMain", "_PluginDataEntryFunction2"))]
    result = {
        "status": "pass_mac_binary_fixture",
        "classification": "Mac executable binary evidence only; not AE exact and not host execution",
        "platform": platform.platform(),
        "binary": repo_path(BINARY),
        "binary_sha256": sha256(BINARY),
        "binary_file": sanitize_repo_output(command_output(["file", str(BINARY)])),
        "command": [repo_path(BINARY), "--input", "<temp>/input.png", "--params", "<temp>/params.json", "--output", "<temp>/output.png"],
        "stdout": completed.stdout.strip(),
        "fixture": {"width": width, "height": height, "raw_rgba_bytes": len(actual)},
        "raw_output_sha256": hashlib.sha256(actual).hexdigest(),
        "raw_output_matches_expected": actual == expected,
        "plugin_boundary": {
            "binary": repo_path(PLUGIN_BINARY),
            "binary_file": sanitize_repo_output(command_output(["file", str(PLUGIN_BINARY)])),
            "exported_host_symbols": selected_symbols,
            "standalone_worker_export": False,
            "blocker": "EffectMain requires AE PF_InData/PF_OutData/PF_ParamDef/PF_EffectWorld and host suites; no standalone worker ABI is exported.",
            "minimal_next_harness": "Load the bundle with AE's host, or add a host-owned PF_EffectWorld/suite shim and call EffectMain(PF_Cmd_SMART_RENDER) with captured typed worlds.",
        },
    }
    if not result["raw_output_matches_expected"]:
        raise AssertionError("Mac binary output bytes differ from deterministic fixture expectation")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=ROOT / "refs" / "conformance" / "olmcolorkey_mac_binary_harness_20260716.json")
    args = parser.parse_args()
    result = run(args.report)
    print(f"[OK] {result['status']}: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
