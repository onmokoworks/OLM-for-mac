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
        spec.write_text(json.dumps({"scope": {"bit_depth": "32bpc"}, "effect": {"match_name": "OLM OLM Blur"}, "cases": [{"id": "case_0001", "source_case_id": "case_0001"}]}), encoding="utf-8")
        for directory in (win, effect, noop):
            (directory / "provenance.json").write_text(json.dumps({"plugin_aex_sha256": "a" * 64}), encoding="utf-8")
        make_exr(win / "case_0001.exr")
        make_exr(win / "case_0001_before_effects.exr")
        make_exr(effect / "case_0001.exr")
        make_exr(noop / "case_0001_before_effects.exr")
        report = root / "audit.json"
        passed = subprocess.run([sys.executable, str(AUDIT), "--focused-spec", str(spec), "--windows-reference-dir", str(win), "--mac-effect-result-root", str(effect), "--mac-no-op-result-root", str(noop), "--output", str(report)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert passed.returncode == 0, passed.stdout
        assert json.loads(report.read_text())["gates"]["ae_exact"] is True
        make_exr(effect / "case_0001.exr", red=2.0)
        failed = subprocess.run([sys.executable, str(AUDIT), "--focused-spec", str(spec), "--windows-reference-dir", str(win), "--mac-effect-result-root", str(effect), "--mac-no-op-result-root", str(noop), "--output", str(root / "mismatch.json")], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert failed.returncode == 1, failed.stdout
        mismatch = json.loads((root / "mismatch.json").read_text())
        assert mismatch["gates"]["ae_exact"] is False
        assert mismatch["cases"][0]["effect"]["mismatched_values_by_channel"]["R"] == 2
        (effect / "provenance.json").unlink()
        blocked = subprocess.run([sys.executable, str(AUDIT), "--focused-spec", str(spec), "--windows-reference-dir", str(win), "--mac-effect-result-root", str(effect), "--mac-no-op-result-root", str(noop), "--output", str(root / "blocked.json")], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert blocked.returncode == 1, blocked.stdout
        assert "AEX hash missing from provenance" in json.loads((root / "blocked.json").read_text())["gates"]["refusal_reasons"]
    print("[OK] OLMBlur 32bpc audit exact, mismatch, and provenance refusal paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
