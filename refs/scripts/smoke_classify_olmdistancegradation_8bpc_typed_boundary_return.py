#!/usr/bin/env python3
"""Smoke-test the DG 8bpc typed-boundary v4 return classifier."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLASSIFIER = ROOT / "scripts/classify_olmdistancegradation_8bpc_typed_boundary_return.py"
TRACE_MEMBER = "return/combined_cdb_trace.txt"


def load_classifier():
    spec = importlib.util.spec_from_file_location("dg_typed_classifier", CLASSIFIER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stage_row(module, case: str, stage: str) -> dict[str, object]:
    row: dict[str, object] = {
        "run_id": "dg8typed-smoke",
        "ae_pid": "4242",
        "module_base": "0x7fffcd660000",
        "aex_sha256": module.AEX_SHA256,
        "project_bpc": "8",
        "case_id": case,
        "x": "397",
        "y": "281",
        "output_addr": "0x1000",
        "typed_rgba": "01,02,03,ff",
    }
    if stage in ("FIELD_IN", "FIELD_OUT"):
        row.update(
            field_base="0x2000",
            field_rowbytes="1e00",
            field_addr="0x3000",
            pixel_size="4",
            address_formula="base+y*rowbytes+x*4",
        )
    elif stage == "COMPOSE_IN":
        row.update(
            source_base="0x4000",
            source_rowbytes="1e00",
            source_addr="0x5000",
            field_green="02",
            x_before_invert="0.007843",
            x_after_invert="0.992157",
            typed_rgba="10,20,30,ff",
        )
    elif stage == "COMPOSE_OUT":
        row.update(
            pre_store_rgba_float="1.0,2.0,3.0,255.0",
            typed_rgba="1.0,2.0,3.0,255.0",
        )
    return row


def marker_line(stage: str, row: dict[str, object]) -> str:
    return f"DG8_{stage} " + " ".join(f"{key}={value}" for key, value in row.items())


def build_trace(module, cases: list[dict[str, object]]) -> str:
    lines: list[str] = []
    for case_row in cases:
        case = str(case_row["case_id"])
        stages = case_row["stages"]
        assert isinstance(stages, dict)
        for stage in module.STAGES:
            item = stages[stage]
            assert isinstance(item, dict)
            lines.append(marker_line(stage, item))
        common = (
            f"run_id=dg8typed-smoke ae_pid=4242 module_base=0x7fffcd660000 "
            f"aex_sha256={module.AEX_SHA256} project_bpc=8 case_id={case}"
        )
        lines.append(f"DG8_DEPTH_SUMMARY {common} rva=1170870 hit_count=1")
        lines.append(f"DG8_DEPTH_SUMMARY {common} rva=1170c90 hit_count=0")
    return "\n".join(lines) + "\n"


def valid_return(module) -> tuple[dict, dict[str, bytes]]:
    cases = []
    for case in module.CASES:
        stages = {stage: stage_row(module, case, stage) for stage in module.STAGES}
        cases.append({"case_id": case, "xy": [397, 281], "output_addr": "0x1000", "stages": stages})
    trace = build_trace(module, cases)
    raw_values: dict[str, str] = {
        "launcher_stdout": "launcher\n",
        "launcher_stderr": "",
        "queue_log": "queue\n",
        "combined_cdb_trace": trace,
    }
    raw_cases = []
    for case in module.CASES:
        logs = {
            "ready_marker": f"{case}-ready\n",
            "cdb_trace": f"{case}-cdb-trace\n",
            "cdb_stdout": f"{case}-cdb-stdout\n",
            "cdb_stderr": "",
            "ae_log": f"{case}-ae-log\n",
            "ae_result": f'{{"case_id":"{case}","status":"ok"}}\n',
        }
        raw_cases.append({"case_id": case, **logs})
        raw_values.update({f"{case}.{name}": value for name, value in logs.items()})
    payload = {
        "schema": module.SCHEMA,
        "request_id": module.REQUEST_ID,
        "status": "answered",
        "kind": "typed_boundary",
        "run_id": "dg8typed-smoke",
        "ae_pid": 4242,
        "module_base": "0x7fffcd660000",
        "aex_sha256": module.AEX_SHA256,
        "project_bits_per_channel": 8,
        "rvas": [{"rva": "1170870", "hit_count": 3}, {"rva": "1170c90", "hit_count": 0}],
        "cases": cases,
        "raw_logs": {
            "launcher_stdout": raw_values["launcher_stdout"],
            "launcher_stderr": raw_values["launcher_stderr"],
            "queue_log": raw_values["queue_log"],
            "combined_cdb_trace": raw_values["combined_cdb_trace"],
            "cases": raw_cases,
        },
    }
    filenames = {
        "launcher_stdout": "afterfx_launcher_stdout.txt",
        "launcher_stderr": "afterfx_launcher_stderr.txt",
        "queue_log": "AE_TYPED_QUEUE.log",
        "combined_cdb_trace": "combined_cdb_trace.txt",
    }
    for case in module.CASES:
        filenames.update({
            f"{case}.ready_marker": f"ae_ready_{case}.marker",
            f"{case}.cdb_trace": f"cdb_trace_{case}.txt",
            f"{case}.cdb_stdout": f"cdb_stdout_{case}.txt",
            f"{case}.cdb_stderr": f"cdb_stderr_{case}.txt",
            f"{case}.ae_log": f"AE_SINGLE_CASE_{case}.log",
            f"{case}.ae_result": f"AE_SINGLE_CASE_{case}.json",
        })
    files = {f"return/{filenames[name]}": value.encode() for name, value in raw_values.items()}
    files["return/RETURN_RUNTIME_TRACE.json"] = json.dumps(payload).encode()
    return payload, files


def set_trace(payload: dict, files: dict[str, bytes], trace: str) -> None:
    payload["raw_logs"]["combined_cdb_trace"] = trace
    files[TRACE_MEMBER] = trace.encode()


def reject(module, payload: dict, files: dict[str, bytes], label: str) -> None:
    try:
        module.validate_payload(payload, files)
    except ValueError:
        return
    raise AssertionError(f"invalid typed-boundary return accepted: {label}")


def main() -> int:
    module = load_classifier()
    valid, files = valid_return(module)
    result = module.validate_payload(valid, files)
    assert result["classification"] == "accepted_complete_evidence"
    assert result["hit_counts"] == {"1170870": 3, "1170c90": 0}

    simple_mutations = (
        ("wrong schema", lambda p: p.update(schema="wrong")),
        ("wrong hash", lambda p: p.update(aex_sha256="0" * 64)),
        ("wrong depth", lambda p: p.update(project_bits_per_channel=16)),
        ("PF32 hit", lambda p: p["rvas"].__setitem__(1, {"rva": "1170c90", "hit_count": 1})),
        ("missing stage", lambda p: p["cases"][1]["stages"].pop("COMPOSE_OUT")),
        ("mixed PID", lambda p: p["cases"][2]["stages"]["HOST_STORE"].update(ae_pid="4243")),
        ("wrong output", lambda p: p["cases"][0]["stages"]["HOST_STORE"].update(output_addr="0x1001")),
        ("payload-only tamper", lambda p: p["cases"][1]["stages"]["COMPOSE_IN"].update(field_green="03")),
    )
    for label, mutate in simple_mutations:
        candidate = copy.deepcopy(valid)
        mutate(candidate)
        reject(module, candidate, copy.deepcopy(files), label)

    candidate = copy.deepcopy(valid)
    candidate_files = copy.deepcopy(files)
    candidate["cases"][0]["stages"]["FIELD_IN"].pop("field_addr")
    deleted_field_trace = candidate["raw_logs"]["combined_cdb_trace"].replace(" field_addr=0x3000", "", 1)
    set_trace(candidate, candidate_files, deleted_field_trace)
    reject(module, candidate, candidate_files, "stage field deletion")

    candidate = copy.deepcopy(valid)
    candidate_files = copy.deepcopy(files)
    raw_tamper = candidate["raw_logs"]["combined_cdb_trace"].replace("field_addr=0x3000", "field_addr=0x3001", 1)
    set_trace(candidate, candidate_files, raw_tamper)
    reject(module, candidate, candidate_files, "raw-only tamper")

    candidate = copy.deepcopy(valid)
    candidate_files = copy.deepcopy(files)
    trace = candidate["raw_logs"]["combined_cdb_trace"]
    duplicate_trace = trace + trace.splitlines()[0] + "\n"
    set_trace(candidate, candidate_files, duplicate_trace)
    reject(module, candidate, candidate_files, "duplicate marker")

    candidate = copy.deepcopy(valid)
    candidate_files = copy.deepcopy(files)
    kept_lines = [
        line for line in candidate["raw_logs"]["combined_cdb_trace"].splitlines()
        if not (line.startswith("DG8_DEPTH_SUMMARY ") and "case_id=case_0015" in line and "rva=1170870" in line)
    ]
    set_trace(candidate, candidate_files, "\n".join(kept_lines) + "\n")
    reject(module, candidate, candidate_files, "missing per-case depth")

    with tempfile.TemporaryDirectory(prefix="dg_typed_classifier_") as td:
        archive_path = Path(td) / "return.zip"
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        loaded, loaded_files = module.load_return(archive_path)
        assert module.validate_payload(loaded, loaded_files)["ae_pid"] == 4242

        missing = Path(td) / "missing_raw.zip"
        with zipfile.ZipFile(missing, "w") as archive:
            for name, data in files.items():
                if not name.endswith("AE_TYPED_QUEUE.log"):
                    archive.writestr(name, data)
        missing_payload, missing_files = module.load_return(missing)
        reject(module, missing_payload, missing_files, "missing raw ZIP member")

    print("[OK] DG 8bpc typed-boundary classifier smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
