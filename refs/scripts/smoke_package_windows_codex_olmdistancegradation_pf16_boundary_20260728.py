#!/usr/bin/env python3
"""Local compile-only smoke for the DG PF16 Windows Codex batch child."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = (
    ROOT
    / "scripts"
    / "package_windows_codex_olmdistancegradation_pf16_boundary_20260728.py"
)
BATCH_PACKAGER = ROOT / "scripts" / "package_windows_codex_batch_handoff_20260728.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


builder = load(BUILDER, "olmdg_pf16_child")
batch = load(BATCH_PACKAGER, "windows_codex_batch")
runtime = load(ROOT / "tools" / "windows_witness" / "runtime.py", "witness_runtime")


def sample(field: str, constraint: dict[str, str] | None) -> str:
    if constraint and "equals" in constraint:
        return str(constraint["equals"])
    if field == "run_id":
        return "fixture-run"
    if field == "ae_pid":
        return "4242"
    if field == "module_base":
        return "0x180000000"
    if field == "aex_sha256":
        return builder.AEX_SHA256
    if field == "project_bpc":
        return "16"
    if field == "renderer":
        return "Software"
    if field.endswith("_addr"):
        return "0x180001000"
    if "f32_bits" in field:
        return "0x3f800000,0x3f000000,0x00000000,0x3e800000"
    if "f32" in field:
        return "1,0.5,0,0.25"
    if "words_agrb" in field:
        return "32768,1,2,3"
    if field == "direct_field_staging_word":
        return "1"
    return "1"


def fixture_trace(contract: dict) -> str:
    lines = []
    for event in contract["validation"]["events"]:
        constraints = event.get("field_constraints", {})
        fields = {
            field: sample(field, constraints.get(field))
            for field in event["required_fields"]
        }
        lines.append(
            event["prefix"] + " " +
            " ".join(f"{key}={value}" for key, value in fields.items())
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    subprocess.run([sys.executable, str(BUILDER), "--verify"], check=True)
    target = builder.TARGET
    manifest_path = target / "job_manifest.json"
    package_path = target / "package.zip"
    checksum_path = target / "package.zip.sha256"

    job, loaded_package, snapshot = batch.load_job(manifest_path, 1)
    assert job["job_id"] == builder.JOB_ID
    assert loaded_package == package_path.resolve()
    assert hashlib.sha256(snapshot).hexdigest() == job["package_sha256"]
    assert checksum_path.read_text(encoding="ascii") == (
        f"{job['package_sha256']}  package.zip\n"
    )

    with tempfile.TemporaryDirectory(prefix="olmdg_pf16_smoke_") as first:
        one = builder.build_bytes(Path(first))
    with tempfile.TemporaryDirectory(prefix="olmdg_pf16_smoke_") as second:
        two = builder.build_bytes(Path(second))
    assert one == two
    assert one == (
        package_path.read_bytes(),
        manifest_path.read_bytes(),
        checksum_path.read_bytes(),
    )

    with zipfile.ZipFile(package_path) as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert len(names) == len(set(name.casefold() for name in names))
        assert not any(name.lower().endswith(".zip") for name in names)
        assert "run.ps1" in names
        assert "witness-contract.json" in names
        assert "package-manifest.json" in names
        contract = json.loads(archive.read("witness-contract.json"))
        generated = json.loads(archive.read("package-manifest.json"))
        runner = archive.read("run.ps1").decode("ascii")
        probes = [
            archive.read(name).decode("ascii")
            for name in names if name.startswith("cdb/") and name.endswith(".cdb.in")
        ]
        assert len(probes) == 6
        assert all('.logopen /t "{{TRACE_PATH}}"' in probe for probe in probes)
        assert all("{{ADDRESS:field_read}}" in probe for probe in probes)
        assert "Stop-Process -Name AfterFX" not in runner
        assert "Get-Process -Name AfterFX" not in runner
        assert "PluginCache" not in runner
        assert "preferences" not in runner.lower()
        assert "modal" not in runner.lower()
        assert "DIRECT_BOUNDARY_RETURN.json" in runner
        assert "derived_values_reported_as_raw = $false" in runner
        assert "nearest_even_claimed = $false" in runner
        assert contract["request_id"] == builder.REQUEST_ID
        assert contract["plugin"]["aex_sha256"] == builder.AEX_SHA256
        assert [case["id"] for case in contract["cases"]] == [
            f"olmdistancegradation_extended__case_{row['code']}"
            for row in builder.CASES
        ]
        assert len(contract["validation"]["events"]) == 30
        assert generated["claim_boundary"] == builder.CLAIM_BOUNDARY
        assert generated["unresolved_boundary"] == builder.UNRESOLVED_BOUNDARY
        for entry in generated["files"]:
            data = archive.read(entry["path"])
            assert hashlib.sha256(data).hexdigest() == entry["sha256"]
            assert len(data) == entry["size_bytes"]

    identity = {
        "run_id": "fixture-run",
        "ae_pid": 4242,
        "module_base": "0x180000000",
    }
    validated = runtime.validate_trace(contract, fixture_trace(contract), identity)
    assert validated["status"] == "answered", validated
    assert len(validated["events"]) == 30

    source = builder.CDB_TEMPLATE
    for rva in ("1170480", "117057d", "11705f1", "11707f4", "117082b"):
        assert rva in source
    assert "direct_memory_read_not_derived" in source
    assert "direct_register_bits_before_pf16_scale" in source
    assert "direct_output_memory_after_four_stores" in source
    assert re.search(r"nearest.?even", source, re.I) is None

    print(json.dumps({
        "status": "ok",
        "job_id": builder.JOB_ID,
        "package_sha256": job["package_sha256"],
        "events": 30,
        "shared_load_job": "accepted",
        "windows_execution": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
