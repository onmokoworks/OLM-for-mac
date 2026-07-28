#!/usr/bin/env python3
"""Static/adversarial smoke for the DirectionalBlur r3 batch child."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts/package_windows_codex_olmdirectionalblur_target_writer_20260728.py"
TARGET = ROOT / "refs/handoffs/windows_codex_batch_jobs_20260728/olmdirectionalblur_target_writer_20260728_r3"


def load_builder():
    spec = importlib.util.spec_from_file_location("dblur_r2", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_builder()
    package, manifest, checksum = module.expected()
    assert package == (TARGET / "package.zip").read_bytes()
    assert manifest == (TARGET / "job_manifest.json").read_bytes()
    assert checksum == (TARGET / "package.zip.sha256").read_bytes()
    with zipfile.ZipFile(Path(TARGET / "package.zip")) as zf:
        names = set(zf.namelist())
        assert "run.ps1" in names and not any(name.endswith(".zip") for name in names)
        wrapper = zf.read("run.ps1").decode()
        inner = zf.read("artifacts/run_witness.ps1").decode()
        readme = zf.read("README.md").decode()
        package_manifest = json.loads(zf.read("package-manifest.json"))
        flattener = zf.read("scripts/flatten_return.py")
    assert package_manifest["entrypoint"] == "run.ps1"
    assert package_manifest["inner_runner_role"] == "internal_not_entrypoint"
    assert "Run only `run.ps1`" in readme
    assert ".\\artifacts\\run_witness.ps1" not in readme
    for token in ("} finally {", "cleanup_unresolved", "RETURN*.zip", "expanded_return", "Write-Status 'exact_bind_failure'",
                  "$exitCode = 2", "Remove-Item -LiteralPath $status"):
        assert token in wrapper
    for token in ("PRELAUNCH_AFTERFX_BASELINE.json", "OWNED_AFTERFX_IDENTITY.json", "OWNED_CDB_IDENTITY.json",
                  "CreationDate", "PID identity recycled or ambiguous", "user_pid_touched=$false"):
        assert token in inner
    assert "foreach ($state in @(Get-AfterFxState))" not in inner
    assert inner.count("Stop-Process") == 1
    assert "function Stop-ExactOwnedProcess" in inner
    assert "Stop-Process -Id ([int]$owned.pid)" in inner
    assert "Stop-Process -Id $launch.Id" not in inner
    assert "Stop-Process -Id $retry.Id" not in inner
    assert "Stop-Process -Id $fridaProcess.Id" not in inner
    assert "owned PID appears in prelaunch baseline" in inner
    assert "request-bound queue marker mismatch" in inner

    def finalize_model(cleanup_fails: bool, status_write_fails: bool) -> tuple[int, bool]:
        exit_code, answered_exists = 0, True
        if cleanup_fails:
            exit_code = 2
            answered_exists = False
            if not status_write_fails:
                answered_exists = True  # exact_bind_failure status, never answered
        return exit_code, answered_exists

    assert finalize_model(True, False)[0] != 0
    assert finalize_model(True, True) == (2, False)

    with tempfile.TemporaryDirectory(prefix="dblur_r2_flatten_") as tmp:
        root = Path(tmp)
        run = root / "run"
        evidence = root / "evidence"
        run.mkdir()
        argb = b"\xff\xa4\x00\x00"
        png = b"\x89PNG\r\n\x1a\npresence-only"
        trace = (
            "DBR_TARGET_STORE run_id=r1 ae_pid=44 module_base=0x180000000 "
            "aex_sha256=d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e "
            "renderer=Software case_id=db_angle0_alpha_fade_hard_edges\n"
        ).encode()
        records = [
            ("return/writer_pf_argb8.bin", argb),
            ("return/rendered_db_angle0_alpha_fade_hard_edges.png", png),
        ]
        payload = {
            "status": "answered", "request_id": "olmdirectionalblur_writer_entry_20260716",
            "artifacts": [{"archive_path": name, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)} for name, data in records],
            "logs": [{"archive_path": "logs/combined_cdb_trace.txt", "sha256": hashlib.sha256(trace).hexdigest(), "size_bytes": len(trace)}],
        }
        (run / "RETURN_OLMDIRECTIONALBLUR_WRITER_ENTRY.json").write_text(json.dumps(payload))
        with zipfile.ZipFile(run / "RETURN_OLMDIRECTIONALBLUR_WRITER_ENTRY.zip", "w") as zf:
            for name, data in records:
                zf.writestr(name, data)
            zf.writestr("logs/combined_cdb_trace.txt", trace)
        helper = root / "flatten_return.py"
        helper.write_bytes(flattener)
        subprocess.run(["python3", str(helper), "--run-root", str(run), "--evidence-root", str(evidence)], check=True)
        direct = json.loads((evidence / "DIRECT_EVIDENCE_MANIFEST.json").read_text())
        assert direct["aex_sha256"].startswith("d3e5e407")
        assert direct["direct_evidence"][1]["role"] == "rendered_output_presence_only_not_exact"
        payload["artifacts"][0]["sha256"] = "0" * 64
        (run / "RETURN_OLMDIRECTIONALBLUR_WRITER_ENTRY.json").write_text(json.dumps(payload))
        failed = subprocess.run(["python3", str(helper), "--run-root", str(run), "--evidence-root", str(root / "bad")])
        assert failed.returncode != 0
    print("[OK] DirectionalBlur r3 batch child smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
