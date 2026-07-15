#!/usr/bin/env python3
"""Independent audit of the OLMSmoother2 case_0012 common-core witness."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = ROOT / "refs/windows_witness_specs/olmsmoother2_case0012_current_aex_20260713"
SPEC_PATH = SPEC_ROOT / "witness-spec.json"
GENERATOR = ROOT / "scripts/package_windows_witness_olmsmoother2_case0012_20260713.py"
COMPLETE_TRACE = SPEC_ROOT / "fixtures/complete_cdb_trace.txt"

sys.path.insert(0, str(ROOT))
from tools.windows_witness.runtime import bundle_return, validate_trace  # noqa: E402


def printf_parts(template: str, stage: str) -> tuple[list[str], list[str]]:
    line = next(line for line in template.splitlines() if f"stage={stage}" in line)
    match = re.search(r'\.printf \\\"(?P<format>.*?)\\\\n\\\",(?P<args>.*?)\} ;gc', line)
    assert match, stage
    conversions = re.findall(r'%(?!%)[-+#0 ]*(?:\d+|\*)?(?:\.\d+|\.\*)?[a-zA-Z]', match.group("format"))
    args = [item.strip() for item in match.group("args").split(",")]
    assert len(conversions) == len(args), (stage, conversions, args)
    return conversions, args


def test_cdb_arity_and_byte_offsets() -> None:
    template = (SPEC_ROOT / "probe.cdb.in").read_text(encoding="ascii")
    cce0_conversions, cce0_args = printf_parts(template, "cce0")
    assert len(cce0_conversions) == 9
    assert cce0_args[0] == "@$t6"
    assert [arg for arg in cce0_args if arg.startswith("by(")] == [
        "by(@$t6+0x00)", "by(@$t6+0x01)", "by(@$t6+0x02)",
        "by(@$t6+0x03)", "by(@$t6+0x04)", "by(@$t6+0x05)",
        "by(@$t6+0x06)", "by(@$t6+0x06)",
    ]

    c280_conversions, c280_args = printf_parts(template, "c280")
    assert len(c280_conversions) == 12
    assert "poi(@rsp+0x28)==@$t6" in next(line for line in template.splitlines() if "stage=c280" in line)
    assert c280_args[:2] == ["@$t6", "poi(@rsp+0x28)"]
    assert [arg for arg in c280_args if arg.startswith("by(")] == [
        f"by(poi(@rsp+0x28)+0x{offset:02x})" for offset in range(0x20, 0x28)
    ]


def test_pointer_provenance_and_seven_byte_capture() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    identity = {"run_id": "s2-audit", "ae_pid": 7312, "module_base": "0x7ff900000000"}
    complete = COMPLETE_TRACE.read_text(encoding="ascii")
    accepted = validate_trace(spec, complete.replace("run_id=s2-fixture", "run_id=s2-audit"), identity)
    assert accepted["status"] == "answered"
    cce0 = next(row["fields"] for row in accepted["events"] if row["prefix"] == "S2_CCE0")
    assert cce0["config_raw_bytes"] == "00,00,80,3f,04,00,03"
    assert len(cce0["config_raw_bytes"].split(",")) == 7

    drifted = complete.replace("pointer_identity=1", "pointer_identity=0", 1)
    rejected = validate_trace(spec, drifted.replace("run_id=s2-fixture", "run_id=s2-audit"), identity)
    assert rejected["status"] == "exact_bind_failure"
    assert any("pointer_identity" in field for field in rejected["failure"]["missing_fields"])


def test_failed_return_zip_contains_no_export() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    identity = {"run_id": "s2-audit", "ae_pid": 7312, "module_base": "0x7ff900000000"}
    complete = COMPLETE_TRACE.read_text(encoding="ascii").replace("run_id=s2-fixture", "run_id=s2-audit")
    status = validate_trace(spec, complete, identity)
    assert status["status"] == "answered"
    with tempfile.TemporaryDirectory(prefix="smoother2_common_core_audit_") as raw:
        work = Path(raw)
        package = work / "package"
        archive = work / "package.zip"
        subprocess.run(
            [sys.executable, str(GENERATOR), "--output-dir", str(package), "--zip", str(archive)],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )
        contract = json.loads((package / "witness-contract.json").read_text(encoding="utf-8"))
        failed, return_zip = bundle_return(contract, status, work / "missing-work")
        assert failed["status"] == "exact_bind_failure"
        assert failed["failure"]["stage"] == "artifact_collection"
        with zipfile.ZipFile(return_zip) as result:
            assert result.namelist() == [contract["return_bundle"]["json_name"]]
            manifest = json.loads(result.read(result.namelist()[0]))
            assert manifest["status"] == "exact_bind_failure"
            assert manifest["artifacts"] == []


if __name__ == "__main__":
    test_cdb_arity_and_byte_offsets()
    test_pointer_provenance_and_seven_byte_capture()
    test_failed_return_zip_contains_no_export()
    print("[OK] independent OLMSmoother2 case_0012 common-core audit")
