#!/usr/bin/env python3
"""Smoke-test the strict DG same-run exact-address package and parser contract."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUEST = "olmdistancegradation_current_aex_same_run_exact_address_20260711"
SCHEMA = "olmdg_current_aex_same_run_exact_address_v1"
CASES = ("olmdistancegradation_extended__case_0010", "olmdistancegradation_extended__case_0011")
XY = ((6, 40), (901, 394))


def parse_trace(lines: list[str]) -> dict[str, object]:
    rows = [json.loads(line) for line in lines]
    if any(row.get("run_id") != rows[0].get("run_id") for row in rows):
        return {"status": "exact_bind_failure", "failure": {"stage": "run_identity", "reason": "mixed run_id"}}
    required = ("field_world", "rcx_field_addr", "rcx_field_word_at_plus_2", "rdx_source_addr", "rdx_source_word_at_plus_2", "output_addr", "output_store_word", "compose_scalar_bits", "final_writer")
    missing = [f"{row.get('case_id')}:{row.get('xy')}:{key}" for row in rows for key in required if row.get(key) in (None, {}, [])]
    expected = {(case, xy) for case in CASES for xy in XY}
    seen = {(row.get("case_id"), tuple(row.get("xy", []))) for row in rows}
    if missing or seen != expected:
        return {"status": "exact_bind_failure", "failure": {"stage": "typed_tuple", "reason": "missing live field or witness", "missing_fields": missing}}
    return {"status": "answered", "run_id": rows[0]["run_id"], "witnesses": rows}


def row(case: str, xy: tuple[int, int], run: str = "run-20260711-001") -> str:
    return json.dumps({
        "run_id": run, "case_id": case, "xy": list(xy),
        "field_world": {"base": "0x10000000", "header": "0x20000000", "rowbytes": 15360, "pixel_size": 8},
        "rcx_field_addr": "0x10000030", "rcx_field_word_at_plus_2": 29500,
        "rdx_source_addr": "0x30000030", "rdx_source_word_at_plus_2": 0,
        "output_addr": "0x40000030", "output_store_word": 3268,
        "compose_scalar_bits": {"xmm1": "0x3f666000", "xmm2": "0x3dcc8000"},
        "final_writer": {"site": "DistanceGradation+0x1170814", "xmm": "0x3dcc8000", "pf16_words": [3268, 0, 32768, 0]},
    })


def parse_marker_fixture(lines: list[str]) -> dict[str, object]:
    records = {}
    active_key = None
    active_kind = None
    for line in lines:
        raw = re.match(r"\s*xmm(?P<lane>[1245])=(?P<raw>[^\s]+)", line)
        if raw and active_key in records:
            if active_kind == "COMPOSE":
                records[active_key][f"compose_xmm{raw.group('lane')}_bits"] = raw.group("raw")
            elif active_kind == "WRITER" and raw.group("lane") == "1":
                records[active_key]["writer_final_writer_xmm_raw32"] = raw.group("raw")
            continue
        match = re.match(r"OLMDG_(FIELD|SOURCE|COMPOSE|WRITER)\s+(.*)$", line)
        if not match:
            continue
        kind, payload = match.groups()
        fields = dict(re.findall(r"([a-z0-9_]+)=([^\s]+)", payload))
        key = (fields["run_id"], fields.get("case_id"), fields.get("x"), fields.get("y"))
        records.setdefault(key, {}).update({f"{kind.lower()}_{k}": v for k, v in fields.items()})
        records[key].update({"run_id": key[0], "case_id": key[1], "x": key[2], "y": key[3]})
        active_key = key
        active_kind = kind
    records = list(records.values())
    expected = {("case_0010" if case.endswith("0010") else "case_0011", str(x), str(y)) for case in CASES for x, y in XY}
    seen = {(r.get("case_id"), r.get("x"), r.get("y")) for r in records}
    required = ("field_field_base", "field_field_header", "field_rcx", "field_rcx_plus2_word", "source_rdx", "source_rdx_plus2_word", "writer_output", "writer_output_store_word", "compose_xmm1_bits", "compose_xmm2_bits", "compose_xmm4_bits", "compose_xmm5_bits", "writer_final_writer_site", "writer_final_writer_xmm_raw32", "writer_word0", "writer_word1", "writer_word2", "writer_word3")
    missing = [key for r in records for key in required if not r.get(key)]
    if len(records) != 4 or seen != expected or len({r.get("run_id") for r in records}) != 1 or missing:
        return {"status": "exact_bind_failure", "missing": missing}
    return {"status": "answered", "records": records}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmdg_same_run_smoke_") as tmp:
        package = Path(tmp) / "request.zip"
        subprocess.run([sys.executable, "scripts/package_olmdistancegradation_current_aex_same_run_exact_address_20260711.py", "--output", str(package)], cwd=ROOT, check=True)
        with zipfile.ZipFile(package) as archive:
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
            names = set(archive.namelist())
            runner_name = "artifacts/run_olmdistancegradation_current_aex_same_run_exact_address_20260711.ps1"
            runner = archive.read(runner_name).decode("utf-8")
            queue = archive.read("scripts/ae_render_olmdistancegradation_current_aex_queue_20260711.jsx").decode("utf-8")
            complete_fixture = archive.read("fixtures/complete_cdb_stdout_20260711.txt").decode("utf-8").splitlines()
            missing_fixture = archive.read("fixtures/missing_cdb_stdout_20260711.txt").decode("utf-8").splitlines()
            dead_fixture = archive.read("fixtures/dead_cdb_stdout_20260711.txt").decode("utf-8").splitlines()
        assert manifest["kind"] == "olm_runtime_trace_request_package"
        assert manifest["request_id"] == REQUEST
        assert template["schema"] == SCHEMA
        assert runner_name in names
        for token in ("Start-Process", "cdb.exe", "AfterFX.exe", "ParseOnly", "Convert-TraceToReturn", "dwo(@rbx+0xb8)", "dwo(@rbx+0xbc)", "0xdead", "63", "82", "348", "case_id=case_0010", "case_id=case_0011", "OLMDG_FIELD", "OLMDG_SOURCE", "OLMDG_COMPOSE", "OLMDG_WRITER", "exact_bind_failure", "DistanceGradation+0x117057d", "DistanceGradation+0x11705f1", "DistanceGradation+0x1170814", "r xmm1", "poi(@rdi+2)"):
            assert token in runner, token
        for forbidden in ("Case0010ParamBlock", "Case0011ParamBlock", "poi(@rbx+0xb8)", "poi(@rbx+0xbc)", "OLMDG_RECORD", "QUEUE_CASE", "OLMDG_PHASE", "$.writeln", "writer_word1=0", "if ($index -lt 2)", "@$t0 == 0", "final_writer_words=3268", "phase.get", "case_id = if"):
            assert forbidden not in runner, forbidden
        for token in ("case_0010", "case_0011", "$.evalFile", "OLMDG_CASE_START"):
            assert token in queue, token
        for forbidden in ("OLMDG_PHASE", "$.writeln", "phase", "order"):
            assert forbidden not in queue.lower(), forbidden
        for line in complete_fixture:
            if line.startswith("OLMDG_") and not line.startswith("OLMDG_ENTRY ") and not line.startswith("OLMDG_FIELD ") and not line.startswith("OLMDG_SOURCE ") and not line.startswith("OLMDG_COMPOSE ") and not line.startswith("OLMDG_WRITER "):
                raise AssertionError(f"unexpected non-CDB marker: {line}")
            if line.startswith("OLMDG_") and "case_id=" not in line:
                raise AssertionError(f"marker lacks direct case id: {line}")
        assert parse_marker_fixture(complete_fixture)["status"] == "answered"
        assert parse_marker_fixture(missing_fixture)["status"] == "exact_bind_failure"
        assert parse_marker_fixture(dead_fixture)["status"] == "exact_bind_failure"
        shell = shutil.which("pwsh") or shutil.which("powershell")
        if shell:
            with tempfile.TemporaryDirectory(prefix="olmdg_ps_parser_") as parser_tmp:
                parser_root = Path(parser_tmp)
                archive.extract(runner_name, parser_root)
                archive.extract("fixtures/complete_cdb_stdout_20260711.txt", parser_root)
                proc = subprocess.run([shell, "-NoProfile", "-File", str(parser_root / runner_name), "-ParseOnly", "-TracePath", str(parser_root / "fixtures/complete_cdb_stdout_20260711.txt")], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
                assert proc.returncode == 0, proc.stdout
                assert json.loads(proc.stdout)["status"] == "answered"
        complete = [row(case, xy) for case in CASES for xy in XY]
        assert parse_trace(complete)["status"] == "answered"
        assert parse_trace(complete[:-1])["status"] == "exact_bind_failure"
        partial = json.loads(complete[0]); partial["rcx_field_word_at_plus_2"] = None
        result = parse_trace([json.dumps(partial)] + complete[1:])
        assert result["status"] == "exact_bind_failure"
        assert "answered_partial" not in result
    print("[OK] OLMDistanceGradation same-run exact-address package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
