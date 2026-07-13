#!/usr/bin/env python3
"""Smoke-test scripts/analyze_dblur_ucrt_expf_return.py."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


REQUEST_ID = "olm_runtime_trace_olmdirectionalblur_ucrt_expf_gaussian_tables_20260711"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(cmd), flush=True)
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    return proc


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def u32_from_f32(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def u64_from_f64(value: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", float(value)))[0]


def fmt_u32(bits: int) -> str:
    return f"0x{bits:08X}"


def fmt_u64(bits: int) -> str:
    return f"0x{bits:016X}"


def sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    host = {
        "os_description": "Microsoft Windows 11 Pro",
        "os_architecture": "X64",
        "process_architecture": "X64",
        "process_bitness": 64,
        "framework_description": ".NET 8.0.0",
        "clr_version": "8.0.0",
        "powershell_edition": "Desktop",
        "powershell_version": "7.4.0",
    }
    ucrt = {
        "path": r"C:\Windows\System32\ucrtbase.dll",
        "file_version": "10.0.26100.1",
        "product_version": "10.0.26100.1",
        "sha256": "1" * 64,
    }
    for n in (96, 240):
        for i in range(n):
            numerator_int = -(i * i)
            numerator_f32 = f32(float(numerator_int))
            ratio = f32(float(n) / f32(3.0))
            ratio_square = f32(ratio * ratio)
            denominator_double = float(ratio_square)
            denominator_double = denominator_double + denominator_double + 1.0e-5
            denominator_f32 = f32(denominator_double)
            arg = f32(numerator_f32 / denominator_f32)
            result = f32(math.exp(float(arg)))
            rows.append(
                {
                    "request_id": REQUEST_ID,
                    "n": n,
                    "i": i,
                    "numerator_int": numerator_int,
                    "numerator_f32": repr(numerator_f32),
                    "numerator_f32_hex": fmt_u32(u32_from_f32(numerator_f32)),
                    "ratio_f32": repr(ratio),
                    "ratio_f32_hex": fmt_u32(u32_from_f32(ratio)),
                    "ratio_square_f32": repr(ratio_square),
                    "ratio_square_f32_hex": fmt_u32(u32_from_f32(ratio_square)),
                    "denominator_f64": repr(denominator_double),
                    "denominator_f64_hex": fmt_u64(u64_from_f64(denominator_double)),
                    "denominator_f32": repr(denominator_f32),
                    "denominator_f32_hex": fmt_u32(u32_from_f32(denominator_f32)),
                    "arg_f32": repr(arg),
                    "arg_f32_hex": fmt_u32(u32_from_f32(arg)),
                    "expf_result_f32": repr(result),
                    "expf_result_f32_hex": fmt_u32(u32_from_f32(result)),
                    "os_description": host["os_description"],
                    "os_architecture": host["os_architecture"],
                    "process_architecture": host["process_architecture"],
                    "process_bitness": host["process_bitness"],
                    "framework_description": host["framework_description"],
                    "clr_version": host["clr_version"],
                    "powershell_edition": host["powershell_edition"],
                    "powershell_version": host["powershell_version"],
                    "ucrtbase_path": ucrt["path"],
                    "ucrtbase_file_version": ucrt["file_version"],
                    "ucrtbase_product_version": ucrt["product_version"],
                    "ucrtbase_sha256": ucrt["sha256"],
                }
            )
    return rows


def write_fixture(base: Path, *, mutate: str | None = None) -> tuple[Path, Path]:
    run_dir = base / "nested" / REQUEST_ID
    run_dir.mkdir(parents=True, exist_ok=True)

    host = {
        "os_description": "Microsoft Windows 11 Pro",
        "os_architecture": "X64",
        "process_architecture": "X64",
        "process_bitness": 64,
        "framework_description": ".NET 8.0.0",
        "clr_version": "8.0.0",
        "powershell_edition": "Desktop",
        "powershell_version": "7.4.0",
    }
    ucrt = {
        "path": r"C:\Windows\System32\ucrtbase.dll",
        "file_version": "10.0.26100.1",
        "product_version": "10.0.26100.1",
        "sha256": "1" * 64,
    }
    rows = build_rows()
    if mutate == "missing_row":
        rows = rows[:-1]
    if mutate == "bad_arg_bits":
        rows = copy.deepcopy(rows)
        rows[1]["arg_f32_hex"] = "0x00000000"

    rows_doc = {
        "request_id": REQUEST_ID,
        "status": "answered",
        "run_id": "smoke-run-id",
        "created_at_utc": "2026-07-11T00:00:00Z",
        "host": host,
        "ucrtbase": ucrt,
        "formula": {
            "ratio": "float(n) / 3.0f",
            "ratio_square": "ratio * ratio (float)",
            "denominator_double": "double(ratio_square); d = d + d + 1e-5",
            "denominator_float": "float(d)",
            "arg": "float(-i*i) / denominator_float",
            "result": "ucrtbase.dll!expf(arg)",
        },
        "lengths": [
            {"n": 96, "i_start": 0, "i_end": 95, "row_count": 96},
            {"n": 240, "i_start": 0, "i_end": 239, "row_count": 240},
        ],
        "total_rows": 336,
        "rows": rows,
    }
    rows_json = run_dir / "gaussian_rows.json"
    rows_csv = run_dir / "gaussian_rows.csv"
    rows_json.write_text(json.dumps(rows_doc, indent=2) + "\n", encoding="utf-8")
    rows_csv.write_text("request_id,n,i\n" + "\n".join(f"{REQUEST_ID},{row['n']},{row['i']}" for row in rows) + "\n", encoding="utf-8")

    artifacts = [
        {
            "path": rf"C:\return\{rows_json.name}",
            "size_bytes": rows_json.stat().st_size,
            "sha256": sha256_hex(rows_json),
        },
        {
            "path": rf"C:\return\{rows_csv.name}",
            "size_bytes": rows_csv.stat().st_size,
            "sha256": sha256_hex(rows_csv),
        },
    ]
    if mutate == "bad_artifact_hash":
        artifacts = copy.deepcopy(artifacts)
        artifacts[0]["sha256"] = "0" * 64

    if mutate == "invalid_arch":
        host = copy.deepcopy(host)
        host["process_architecture"] = "ARM64"

    summary = {
        "request_id": REQUEST_ID,
        "status": "answered",
        "run_id": "smoke-run-id",
        "created_at_utc": "2026-07-11T00:00:00Z",
        "return_zip": str(base / f"{REQUEST_ID}_return_windows.zip"),
        "host": host,
        "ucrtbase": ucrt,
        "lengths": [
            {"n": 96, "row_count": 96},
            {"n": 240, "row_count": 240},
        ],
        "total_rows": 336,
        "artifacts": artifacts,
        "failure": None,
    }
    (run_dir / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (run_dir / "RETURN_RUNTIME_TRACE.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    zip_path = base / f"{REQUEST_ID}_return_windows.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(run_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(base))
    return run_dir, zip_path


def expect_ok(proc: subprocess.CompletedProcess[str], label: str) -> None:
    if proc.returncode != 0:
        raise AssertionError(f"{label} unexpectedly failed")


def expect_fail(proc: subprocess.CompletedProcess[str], label: str, needle: str) -> None:
    if proc.returncode == 0:
        raise AssertionError(f"{label} unexpectedly succeeded")
    if needle not in proc.stdout:
        raise AssertionError(f"{label} output missing {needle!r}")


def normalize_table_export(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(payload)
    normalized.pop("generated_at_utc", None)
    for artifact in normalized.get("artifacts", []):
        artifact.pop("actual_path", None)
    return normalized


def main() -> int:
    root = repo_root()
    py = sys.executable
    script = root / "scripts" / "analyze_dblur_ucrt_expf_return.py"
    with tempfile.TemporaryDirectory(prefix="smoke_analyze_dblur_ucrt_expf_return_") as td:
        tmp = Path(td)

        valid_dir, valid_zip = write_fixture(tmp / "valid")
        out_dir_json = tmp / "valid_dir.json"
        out_dir_md = tmp / "valid_dir.md"
        out_dir_table = tmp / "valid_dir_table.json"
        valid_dir_proc = run(
            [
                py,
                str(script),
                str(valid_dir),
                "--output-json",
                str(out_dir_json),
                "--output-md",
                str(out_dir_md),
                "--emit-table-json",
                str(out_dir_table),
            ],
            root,
        )
        expect_ok(valid_dir_proc, "valid dir")

        out_zip_json = tmp / "valid_zip.json"
        out_zip_md = tmp / "valid_zip.md"
        out_zip_table = tmp / "valid_zip_table.json"
        valid_zip_proc = run(
            [
                py,
                str(script),
                str(valid_zip),
                "--output-json",
                str(out_zip_json),
                "--output-md",
                str(out_zip_md),
                "--emit-table-json",
                str(out_zip_table),
            ],
            root,
        )
        expect_ok(valid_zip_proc, "valid zip")

        dir_payload = json.loads(out_dir_json.read_text(encoding="utf-8"))
        zip_payload = json.loads(out_zip_json.read_text(encoding="utf-8"))
        assert dir_payload["kind"] == "olmdirectionalblur_ucrt_expf_return_analysis"
        assert zip_payload["kind"] == "olmdirectionalblur_ucrt_expf_return_analysis"
        assert [table["n"] for table in dir_payload["tables"]] == [96, 240]
        assert [table["row_count"] for table in dir_payload["tables"]] == [96, 240]
        assert "does not claim Windows exactness" in out_dir_md.read_text(encoding="utf-8")

        dir_table = normalize_table_export(json.loads(out_dir_table.read_text(encoding="utf-8")))
        zip_table = normalize_table_export(json.loads(out_zip_table.read_text(encoding="utf-8")))
        if dir_table != zip_table:
            raise AssertionError("zip and directory validated table exports differ")
        print("[OK] zip vs directory validated table export matched")

        invalid_arch_dir, _ = write_fixture(tmp / "invalid_arch", mutate="invalid_arch")
        invalid_arch_proc = run(
            [
                py,
                str(script),
                str(invalid_arch_dir),
                "--output-json",
                str(tmp / "invalid_arch.json"),
                "--output-md",
                str(tmp / "invalid_arch.md"),
            ],
            root,
        )
        expect_fail(invalid_arch_proc, "invalid arch", "process_architecture must be X64")

        missing_row_dir, _ = write_fixture(tmp / "missing_row", mutate="missing_row")
        missing_row_proc = run(
            [
                py,
                str(script),
                str(missing_row_dir),
                "--output-json",
                str(tmp / "missing_row.json"),
                "--output-md",
                str(tmp / "missing_row.md"),
            ],
            root,
        )
        expect_fail(missing_row_proc, "missing row", "rows length must be 336")

        bad_arg_dir, _ = write_fixture(tmp / "bad_arg_bits", mutate="bad_arg_bits")
        bad_arg_proc = run(
            [
                py,
                str(script),
                str(bad_arg_dir),
                "--output-json",
                str(tmp / "bad_arg_bits.json"),
                "--output-md",
                str(tmp / "bad_arg_bits.md"),
            ],
            root,
        )
        expect_fail(bad_arg_proc, "bad arg bits", "arg_f32 bits mismatch")

        bad_hash_dir, _ = write_fixture(tmp / "bad_artifact_hash", mutate="bad_artifact_hash")
        bad_hash_proc = run(
            [
                py,
                str(script),
                str(bad_hash_dir),
                "--output-json",
                str(tmp / "bad_artifact_hash.json"),
                "--output-md",
                str(tmp / "bad_artifact_hash.md"),
            ],
            root,
        )
        expect_fail(bad_hash_proc, "bad artifact hash", "artifact sha256 mismatch")

    print("[OK] analyze_dblur_ucrt_expf_return smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
