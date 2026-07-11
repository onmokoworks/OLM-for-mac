#!/usr/bin/env python3
"""Smoke-test the 32bpc float return verifier with synthetic EXR files in /tmp."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFY = ROOT / "scripts/verify_32bpc_float_return.py"


def attr(name: str, typ: str, value: bytes) -> bytes:
    return name.encode() + b"\0" + typ.encode() + b"\0" + struct.pack("<I", len(value)) + value


def make_exr(
    path: Path,
    half: bool = False,
    channels: list[str] | None = None,
    ys: list[int] | None = None,
) -> None:
    channels = channels or ["R", "G", "B", "A"]
    entries = b"".join(name.encode() + b"\0" + struct.pack("<iB3xii", 1 if half else 2, 0, 1, 1) for name in channels) + b"\0"
    header = b"".join([
        attr("channels", "chlist", entries), attr("compression", "compression", b"\0"),
        attr("dataWindow", "box2i", struct.pack("<4i", 0, 0, 1, 1)),
        attr("displayWindow", "box2i", struct.pack("<4i", 0, 0, 1, 1)),
        attr("lineOrder", "lineOrder", b"\0"), attr("pixelAspectRatio", "float", struct.pack("<f", 1.0)),
        attr("screenWindowCenter", "v2f", struct.pack("<2f", 0.0, 0.0)), attr("screenWindowWidth", "float", struct.pack("<f", 1.0)),
        attr("color_space", "string", b"sRGB"), attr("alpha_mode", "string", b"straight"),
    ]) + b"\0"
    values = [0.0, 1.0, math.nan, math.inf, -math.inf, 0.5, 0.25, 1.0] if not half else [0.0] * 8
    payload = struct.pack("<8f", *values) if not half else b"\0" * (2 * len(channels) * 4)
    ys = ys or [0, 1]
    chunks = [struct.pack("<iI", y, len(payload)) + payload for y in ys]
    header_blob = struct.pack("<II", 20000630, 2) + header
    first_chunk = len(header_blob) + 8 * len(chunks)
    offsets = []
    cursor = first_chunk
    for chunk in chunks:
        offsets.append(cursor)
        cursor += len(chunk)
    path.write_bytes(
        header_blob
        + struct.pack("<" + "Q" * len(offsets), *offsets)
        + b"".join(chunks)
    )


def run(manifest: Path, request: Path, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(VERIFY), str(manifest), "--request", str(request), "--artifact-root", str(root), "--json"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def run_candidate_index(index: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(VERIFY), "--mac-candidate-index", str(index), "--json"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="verify_32bpc_float_return_") as tmp:
        root = Path(tmp)
        artifact = root / "output.exr"
        make_exr(artifact)
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        request = root / "request.json"
        request.write_text(json.dumps({"request_id": "synthetic", "scope": {"bit_depth": "32bpc"}, "render_sets": [{"id": "software_32bpc", "bit_depth": "32bpc", "bits_per_channel": 32}], "cases": [{"id": "case_0001", "params": {"strength": 1}}]}), encoding="utf-8")
        manifest = root / "manifest.json"
        manifest.write_text(json.dumps({"request_id": "synthetic", "ae_version": "26.2x49", "cases": [{"id": "case_0001", "render_set_id": "software_32bpc", "output_format": "exr", "float_preserving": True, "artifact": "output.exr", "sha256": digest, "channel_order": ["R", "G", "B", "A"], "color_space": "sRGB", "alpha_mode": "straight", "project_gpu_accel_type": {"current_name": "SOFTWARE"}, "comp": {"width": 2, "height": 2}, "effects": [{"params": {"strength": 1}}]}]}), encoding="utf-8")
        passed = run(manifest, request, root)
        assert passed.returncode == 0, passed.stdout
        assert '"nan": 2' in passed.stdout and '"+inf": 2' in passed.stdout and '"-inf": 2' in passed.stdout
        make_exr(artifact, half=True)
        half_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        half_manifest["cases"][0]["sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(half_manifest), encoding="utf-8")
        failed_half = run(manifest, request, root)
        assert failed_half.returncode != 0 and "HALF/non-FLOAT" in failed_half.stdout, failed_half.stdout
        manifest.write_text(manifest.read_text(encoding="utf-8").replace('"output_format": "exr"', '"output_format": "png"'), encoding="utf-8")
        failed_png = run(manifest, request, root)
        assert failed_png.returncode != 0 and "PNG-only" in failed_png.stdout, failed_png.stdout
        make_exr(artifact, ys=[2, 3])
        malformed_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        malformed_manifest["cases"][0]["output_format"] = "exr"
        malformed_manifest["cases"][0]["sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(malformed_manifest), encoding="utf-8")
        failed_y = run(manifest, request, root)
        assert failed_y.returncode != 0 and "out-of-range scanline" in failed_y.stdout, failed_y.stdout
        make_exr(artifact)
        params = [{"name": "Search Radius", "value": 13}]
        params_hash = hashlib.sha256(json.dumps(params, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        candidate_index = root / "candidate_index.json"
        candidate_index.write_text(json.dumps({
            "kind": "olm_mac_ae_32bpc_candidate_index",
            "ae_exact_claim": False,
            "candidates": [{
                "request_id": "synthetic_mac",
                "case_id": "toondilate__case_0001",
                "state": "rendered",
                "bit_depth": "32bpc",
                "bits_per_channel": 32,
                "params_sha256": params_hash,
                "case": {"id": "toondilate__case_0001", "params_full": params},
                "exr": {"path": str(artifact), "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()},
            }],
        }), encoding="utf-8")
        candidate_passed = run_candidate_index(candidate_index)
        assert candidate_passed.returncode == 0 and '"rendered": 1' in candidate_passed.stdout, candidate_passed.stdout
        broken_index = json.loads(candidate_index.read_text())
        broken_index["candidates"][0]["params_sha256"] = "0" * 64
        candidate_index.write_text(json.dumps(broken_index), encoding="utf-8")
        candidate_failed = run_candidate_index(candidate_index)
        assert candidate_failed.returncode != 0 and "params_sha256 mismatch" in candidate_failed.stdout, candidate_failed.stdout
        print("[OK] synthetic EXR pass, HALF/PNG rejection, and malformed scanline rejection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
