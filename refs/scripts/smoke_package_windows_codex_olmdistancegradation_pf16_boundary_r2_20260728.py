#!/usr/bin/env python3
"""Local compile-only/adversarial smoke for the DG PF16 r2 child."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = (
    ROOT
    / "scripts"
    / "package_windows_codex_olmdistancegradation_pf16_boundary_r2_20260728.py"
)
BATCH = ROOT / "scripts" / "package_windows_codex_batch_handoff_20260728.py"
RUNTIME = ROOT / "tools" / "windows_witness" / "runtime.py"


def load(path: Path, name: str):
    module_spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(module_spec)
    assert module_spec.loader
    module_spec.loader.exec_module(module)
    return module


builder = load(BUILDER, "olmdg_pf16_r2")
batch = load(BATCH, "windows_batch")
runtime = load(RUNTIME, "windows_witness_runtime")


def sample(field, constraint):
    if constraint and "equals" in constraint:
        return str(constraint["equals"])
    values = {
        "run_id": "fixture-run",
        "ae_pid": "4242",
        "module_base": "0x180000000",
        "aex_sha256": builder.AEX_SHA256,
        "project_bpc": "16",
        "renderer": "Software",
        "pre_store_argb_f32_bits": (
            "0x3f800000,0x3f000000,0x00000000,0x3e800000"
        ),
        "pre_store_argb_f32": "1,0.5,0,0.25",
        "direct_field_staging_word": "1",
    }
    if field in values:
        return values[field]
    if field.endswith("_addr"):
        return "0x180001000"
    if "words_agrb" in field:
        return "32768,1,2,3"
    return "1"


def fixture_trace(contract):
    lines = []
    for event in contract["validation"]["events"]:
        constraints = event.get("field_constraints", {})
        fields = {
            field: sample(field, constraints.get(field))
            for field in event["required_fields"]
        }
        lines.append(
            event["prefix"]
            + " "
            + " ".join(f"{key}={value}" for key, value in fields.items())
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    subprocess.run([sys.executable, str(BUILDER), "--verify"], check=True)
    target = builder.TARGET
    job, package, snapshot = batch.load_job(target / "job_manifest.json", 1)
    assert package == (target / "package.zip").resolve()
    assert hashlib.sha256(snapshot).hexdigest() == job["package_sha256"]

    with tempfile.TemporaryDirectory(prefix="dg_r2_a_") as first:
        one = builder.build_bytes(Path(first))
    with tempfile.TemporaryDirectory(prefix="dg_r2_b_") as second:
        two = builder.build_bytes(Path(second))
    assert one == two
    assert one == tuple(
        (target / name).read_bytes()
        for name in ("package.zip", "job_manifest.json", "package.zip.sha256")
    )

    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert len(names) == len(set(name.casefold() for name in names))
        required = {
            "run.ps1",
            "README.md",
            "package-manifest.json",
            "witness-contract.json",
            "scripts/validate_direct_boundary.py",
            "anchors/entry_1170480.json",
        }
        assert required <= set(names)
        contract = json.loads(archive.read("witness-contract.json"))
        manifest = json.loads(archive.read("package-manifest.json"))
        readme = archive.read("README.md").decode("ascii")
        root_runner = archive.read("run.ps1").decode("ascii")
        inner = archive.read("artifacts/run_witness.ps1").decode("utf-8")
        validator_path = Path(tempfile.mkdtemp()) / "typed.py"
        validator_path.write_bytes(
            archive.read("scripts/validate_direct_boundary.py")
        )
        typed = load(validator_path, "typed_validator")
        assert manifest["entrypoint"] == "run.ps1"
        assert manifest["internal_runner"]["role"] == "internal_not_entrypoint"
        assert manifest["runtime_binary_exact"] is False
        assert "only supported entrypoint" in readme
        assert "Do not invoke" in readme
        assert "foreach ($state in @(Get-AfterFxState))" not in inner
        for marker in (
            "launch_ownership_context.json",
            "owned_afterfx_process.json",
            "owned_cdb_process.json",
            "creation_time_utc",
            "executable_sha256",
            "cleanup_unresolved",
        ):
            assert marker in inner
        assert "OWNERSHIP_CLEANUP.json" in root_runner
        assert "DIRECT_TYPED_VALIDATION.json" in root_runner
        assert "runtime_binary_exact = $false" in root_runner
        assert "observed_not_pinned" in root_runner
        probes = [
            archive.read(name).decode("ascii")
            for name in names
            if name.startswith("cdb/") and name.endswith(".cdb.in")
        ]
        assert len(probes) == 6
        for probe in probes:
            builder.validate_entry_cdb_source(probe)
            entry = next(
                line
                for line in probe.splitlines()
                if line.startswith("bp {{ADDRESS:entry}}")
            )
            assert "@rbx" not in entry.lower()
            assert "@rcx+0x94" in entry
            assert "poi(@rsp+0x28)" in entry
            assert "(@xmm6&0xffffffff)" in probe

        anchor = json.loads(archive.read("anchors/entry_1170480.json"))
        assert anchor["source_sha256"] == builder.DISASSEMBLY_SHA256
        assert anchor["register_contract"]["forbidden_entry_alias"] == "RBX"
        assert len(contract["validation"]["events"]) == 30
        validated = runtime.validate_trace(
            contract,
            fixture_trace(contract),
            {"run_id": "fixture-run", "ae_pid": 4242, "module_base": "0x180000000"},
        )
        assert validated["status"] == "answered", validated
        accepted = typed.validate_document(validated)
        assert accepted["pf16_word_scalar_count"] == 78
        assert accepted["float32_lane_count"] == 24

        adversarial = []
        over = copy.deepcopy(validated)
        next(
            row for row in over["events"]
            if "stored_pf16_words_agrb" in row["fields"]
        )["fields"]["stored_pf16_words_agrb"] = "32769,0,0,0"
        adversarial.append(over)
        malformed = copy.deepcopy(validated)
        next(
            row for row in malformed["events"]
            if "field_words_agrb" in row["fields"]
        )["fields"]["field_words_agrb"] = "+1,0,0,0"
        adversarial.append(malformed)
        bad_bits = copy.deepcopy(validated)
        next(
            row for row in bad_bits["events"]
            if "pre_store_argb_f32_bits" in row["fields"]
        )["fields"]["pre_store_argb_f32_bits"] = (
            "0x3f80000,0x3f000000,0x00000000,0x3e800000"
        )
        adversarial.append(bad_bits)
        mismatch = copy.deepcopy(validated)
        next(
            row for row in mismatch["events"]
            if "pre_store_argb_f32" in row["fields"]
        )["fields"]["pre_store_argb_f32"] = "2,0.5,0,0.25"
        adversarial.append(mismatch)
        nan = copy.deepcopy(validated)
        float_row = next(
            row for row in nan["events"]
            if "pre_store_argb_f32_bits" in row["fields"]
        )
        float_row["fields"]["pre_store_argb_f32_bits"] = (
            "0x7fc00000,0x3f000000,0x00000000,0x3e800000"
        )
        float_row["fields"]["pre_store_argb_f32"] = "nan,0.5,0,0.25"
        adversarial.append(nan)
        for document in adversarial:
            try:
                typed.validate_document(document)
            except ValueError:
                pass
            else:
                raise AssertionError("typed validator accepted adversarial evidence")

    poisoned = builder.CDB_TEMPLATE.replace("@rcx+0x94", "@rbx+0x94", 1)
    try:
        builder.validate_entry_cdb_source(poisoned)
    except ValueError:
        pass
    else:
        raise AssertionError("entry validator accepted RBX at function entry")

    print(
        json.dumps(
            {
                "status": "ok",
                "job_id": builder.JOB_ID,
                "package_sha256": job["package_sha256"],
                "events": 30,
                "typed_adversarial_rejections": 5,
                "entry_rbx_rejected": True,
                "shared_load_job": "accepted",
                "windows_execution": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
