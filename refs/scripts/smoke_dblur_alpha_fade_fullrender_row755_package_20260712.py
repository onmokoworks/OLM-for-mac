#!/usr/bin/env python3
"""Fail-closed smoke/verifier for the DirectionalBlur row-755 trace package."""

from __future__ import annotations

import json
import hashlib
import math
import re
import struct
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "runtime_trace_packages" / "olmdirectionalblur_alpha_fade_fullrender_row755_20260712"
ZIP = ROOT / "runtime_trace_packages" / "olmdirectionalblur_alpha_fade_fullrender_row755_20260712.zip"
REQUEST = "olmdirectionalblur_alpha_fade_fullrender_row755_20260712"
HASH = "d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e"


def fail(reason: str) -> None:
    raise AssertionError("exact_bind_failure: " + reason)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_return(value: dict, root: Path) -> None:
    if value.get("request_id") != REQUEST or value.get("status") != "answered":
        fail("partial or wrong request status accepted")
    if not re.fullmatch(r"[0-9a-f-]{36}", value.get("run_id", "")):
        fail("run_id is absent or not UUID-shaped")
    if not isinstance(value.get("pid"), int) or value["pid"] <= 0:
        fail("single AE PID missing")
    aex = value.get("aex", {})
    if aex.get("sha256") != HASH or aex.get("size") != 56832:
        fail("AEX identity mismatch")
    schedule = value.get("call_schedule", {})
    if (schedule.get("worker_entry"), schedule.get("rowdriver_entry")) != ("0x4d84", "0x38d0"):
        fail("call identity mismatch")
    if schedule.get("rowdriver_calls", 0) <= 0:
        fail("worker schedule was not observed")
    stage = value.get("stage", {})
    if (stage.get("offset"), stage.get("before_normalization")) != ("0x5554", True):
        fail("stage is not the exact pre-normalization boundary")
    provenance = value.get("address_provenance", {})
    if not provenance.get("params"):
        fail("params binding absent")
    for name, source in (("destination", "params+0x8090"), ("denominator", "params+0x8080"), ("alpha_valid", "params+0x8088")):
        item = provenance.get(name, {})
        if item.get("source") != source or item.get("row") != 755 or item.get("x_start") != 747 or item.get("x_end") != 1080:
            fail(f"{name} address/row provenance mismatch")
        if item.get("base") in (None, "", "0x0", "0"):
            fail(f"{name} base address absent")
    if not all(provenance[name].get("base") for name in ("destination", "denominator", "alpha_valid")):
        fail("plane base binding absent")
    expected = {
        "row755_destination_rgba_f32_le.bin": 334 * 4 * 4,
        "row755_denominator_f32_le.bin": 334 * 4,
        "row755_alpha_valid_f32_le.bin": 334 * 4,
    }
    for name, size in expected.items():
        path = root / name
        if not path.is_file() or path.stat().st_size != size:
            fail(f"typed artifact missing or wrong size: {name}")
        if not any(math.isfinite(v) for v in struct.unpack("<" + "f" * (size // 4), path.read_bytes())):
            fail(f"typed artifact has no finite words: {name}")


def valid_return(tmp: Path) -> dict:
    for name, words in (("row755_destination_rgba_f32_le.bin", 1336), ("row755_denominator_f32_le.bin", 334), ("row755_alpha_valid_f32_le.bin", 334)):
        (tmp / name).write_bytes(struct.pack("<" + "f" * words, *([0.0] * words)))
    return {
        "request_id": REQUEST, "status": "answered", "run_id": "12345678-1234-1234-1234-123456789abc", "pid": 4242,
        "aex": {"sha256": HASH, "size": 56832},
        "call_schedule": {"worker_entry": "0x4d84", "rowdriver_entry": "0x38d0", "params": "0x1000", "row_start": 0, "row_end": 2206, "rowdriver_calls": 2206},
        "stage": {"offset": "0x5554", "before_normalization": True},
        "address_provenance": {"params": "0x1000", "destination": {"base": "0x2000", "source": "params+0x8090", "row": 755, "x_start": 747, "x_end": 1080}, "denominator": {"base": "0x3000", "source": "params+0x8080", "row": 755, "x_start": 747, "x_end": 1080}, "alpha_valid": {"base": "0x4000", "source": "params+0x8088", "row": 755, "x_start": 747, "x_end": 1080}},
    }


def main() -> int:
    manifest = json.loads((PACKAGE / "runtime_trace_package_manifest.json").read_text())
    assert manifest["request_id"] == REQUEST and manifest["aex"]["sha256"] == HASH
    assert "absolute-base CDB attach" in manifest["binding"]["runner"]
    assert "module-name breakpoint expressions" in manifest["runtime_actions"][0]["forbidden"]
    for path in PACKAGE.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".md", ".ps1", ".in"}:
            text = path.read_text(errors="replace")
            assert "/Users/" not in text and "\\Users\\onmk" not in text
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        required = {"runtime_trace_package_manifest.json", "RETURN_RUNTIME_TRACE_TEMPLATE.json", "README.md", "row755_capture.cdb.in", "run_alpha_fade_row755.ps1", "case/ae_render_single_case.jsx"}
        assert all(any(item.endswith("/" + wanted) or item == wanted for item in names) for wanted in required), sorted(names)
        readme_name = next(item for item in names if item.endswith("/README.md") or item == "README.md")
        assert "Run that script exactly as supplied" in archive.read(readme_name).decode("utf-8")
        runner_name = next(item for item in names if item.endswith("/run_alpha_fade_row755.ps1") or item == "run_alpha_fade_row755.ps1")
        runner = archive.read(runner_name).decode("utf-8")
        assert "OLM_AE_PAUSE_BEFORE_RENDER='1'" in runner
        assert ".Modules | Where-Object" in runner
        assert ".Replace('__BASE__',$base)" in runner
        cdb_name = next(item for item in names if item.endswith("/row755_capture.cdb.in") or item == "row755_capture.cdb.in")
        cdb = archive.read(cdb_name).decode("utf-8")
        assert "r @$t0=__BASE__" in cdb
        assert "OLMDirectionalBlur+" not in cdb
        assert "@$tA" not in cdb and "@$tB" not in cdb
        assert "755-dwo(@$t6+0x8098)" in cdb
        assert "747-dwo(@$t6+0x809c)" in cdb
        jsx_name = next(item for item in names if item.endswith("/case/ae_render_single_case.jsx") or item == "case/ae_render_single_case.jsx")
        jsx = archive.read(jsx_name).decode("utf-8")
        assert 'getenv("OLM_AE_PAUSE_BEFORE_RENDER") === "1"' in jsx
        assert "writeText(\n                readyMarkerPath" in jsx
        assert "while (!continueMarker.exists" in jsx
        assert "pause handshake timed out" in jsx
    with tempfile.TemporaryDirectory(prefix="dblur_row755_verify_") as name:
        tmp = Path(name)
        good = valid_return(tmp)
        verify_return(good, tmp)
        partial = dict(good, status="answered_partial")
        try:
            verify_return(partial, tmp)
        except AssertionError as exc:
            assert str(exc).startswith("exact_bind_failure:")
        else:
            fail("answered_partial fixture was accepted")
        wrong_row = json.loads(json.dumps(good))
        wrong_row["address_provenance"]["destination"]["row"] = 754
        try:
            verify_return(wrong_row, tmp)
        except AssertionError as exc:
            assert str(exc).startswith("exact_bind_failure:")
        else:
            fail("wrong-row fixture was accepted")
    print("[OK] DirectionalBlur Alpha Fade row-755 package integrity and fail-closed fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
