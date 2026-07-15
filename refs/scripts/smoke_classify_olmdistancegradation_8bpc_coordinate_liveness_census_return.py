#!/usr/bin/env python3
"""Focused smoke for the DG8 census return classifier and omission gates."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLASSIFIER_PATH = ROOT / "scripts/classify_olmdistancegradation_8bpc_coordinate_liveness_census_return.py"
PACKAGE = ROOT / "refs/runtime_trace_packages/olmdistancegradation_8bpc_coordinate_liveness_census_20260715.zip"


def load_module():
    spec = importlib.util.spec_from_file_location("dg8_census_classifier", CLASSIFIER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_payload(module: object) -> dict:
    with zipfile.ZipFile(PACKAGE) as source:
        lines = source.read("fixtures/complete_census.txt").decode().splitlines()
        outputs = {case: source.read(f"request/expected/{case}.png") for case in module.CASES}
    parsed = {}
    for case in module.CASES:
        rows = [{part.split("=", 1)[0]: part.split("=", 1)[1] for part in line.split()[1:]}
                for line in lines if f"case_id={case}" in line]
        coord, neighbor, summary, pf32 = rows
        sample = lambda row: {"callback_index": int(row["callback_index"]), "x": int(row["x"]), "y": int(row["y"]), "output_addr": row["output_addr"]}
        parsed[case] = {
            "status": "answered", "case_id": case, "run_id": coord["run_id"], "ae_pid": int(coord["ae_pid"]),
            "module_base": coord["module_base"], "aex_sha256": coord["aex_sha256"], "ae_version": coord["ae_version"],
            "renderer": coord["renderer"], "project_bits_per_channel": 8, "input_sha256": coord["input_sha256"], "output_sha256": coord["output_sha256"],
            "pf8": {"total_count": int(summary["total_count"]), "min_x": int(summary["min_x"]), "max_x": int(summary["max_x"]), "min_y": int(summary["min_y"]), "max_y": int(summary["max_y"]), "first16": [sample(coord)], "target_neighborhood_count": int(summary["target_neighborhood_count"]), "target_neighborhood_samples": [sample(neighbor)], "target_coordinate_observed": True, "output_pointer_sample": [coord["output_addr"]]},
            "pf32": {"count": int(pf32["count"])}, "ae_result": {"output_png_archive_path": f"outputs/{case}.png"},
        }
    return {"schema": module.SCHEMA, "status": "answered", "kind": module.FIXTURE_KIND, "request_id": module.REQUEST_ID, "request_satisfied": True, "exactness_claim": False, "run_id": "fixture-census", "aex_sha256": module.AEX_SHA256, "renderer": "Software", "project_bits_per_channel": 8, "cases": list(parsed.values()), "raw_logs": {"combined_cdb_trace": "DG8_PF8_SUMMARY fixture"}, "_outputs": outputs}


def write_zip(path: Path, payload: dict) -> None:
    outputs = payload.pop("_outputs")
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("RETURN_RUNTIME_TRACE.json", json.dumps(payload))
        archive.writestr("logs/combined_cdb_trace.txt", "DG8_CENSUS_BREAKPOINTS_ARMED\n")
        for case, data in outputs.items():
            archive.writestr(f"outputs/{case}.png", data)


def rejected(module: object, payload: dict, label: str) -> None:
    try:
        module.validate_payload(payload)
    except ValueError:
        return
    raise AssertionError(f"invalid payload accepted: {label}")


def main() -> int:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="dg8_census_smoke_") as temp:
        root = Path(temp)
        payload = fixture_payload(module)
        package = root / "return.zip"
        write_zip(package, payload)
        loaded, archive, names = module.load_return(package)
        try:
            report = module.validate_payload(loaded, archive, names)
        finally:
            archive.close()
        assert report["status"] == "accepted_coordinate_liveness_census"
        assert report["format_drift"] is True
        real_shape = copy.deepcopy(loaded)
        real_shape.pop("schema")
        real_shape.pop("raw_logs")
        for row in real_shape["cases"]:
            row.pop("ae_result")
        real_package = root / "real_shape.zip"
        outputs = {case: (ROOT / f"refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712/request/expected/{case}.png").read_bytes() for case in module.CASES}
        with zipfile.ZipFile(real_package, "w") as archive:
            archive.writestr("RETURN_RUNTIME_TRACE.json", json.dumps(real_shape))
            archive.writestr("runtime_trace/combined_cdb_trace.txt", "trace")
            for case, data in outputs.items():
                prefix = f"runtime_trace/{case}"
                archive.writestr(f"{prefix}/output/{case}.png", data)
                archive.writestr(f"{prefix}/AE_SINGLE_CASE.log", "ok")
                archive.writestr(f"{prefix}/AE_SINGLE_CASE_RESULT.json", json.dumps({"status": "ok", "project_bits_per_channel": 8}))
                archive.writestr(f"{prefix}/cdb_trace.txt", f"DG8_PF8_SUMMARY case_id={case}")
        real_loaded, real_archive, real_names = module.load_return(real_package)
        try:
            assert module.validate_payload(real_loaded, real_archive, real_names)["format_drift"] is True
        finally:
            real_archive.close()
        for label, mutate in {
            "missing case": lambda p: p["cases"].pop(),
            "missing first16": lambda p: p["cases"][0]["pf8"].pop("first16"),
            "missing neighborhood": lambda p: p["cases"][1]["pf8"].pop("target_neighborhood_samples"),
            "PF32 positive": lambda p: p["cases"][2]["pf32"].update(count=1),
            "mixed run": lambda p: p["cases"][1].update(run_id="other-run"),
            "wrong output hash": lambda p: p["cases"][0].update(output_sha256="0" * 64),
            "request unsatisfied": lambda p: p.update(request_satisfied=False),
        }.items():
            candidate = copy.deepcopy(loaded)
            mutate(candidate)
            rejected(module, candidate, label)
        canonical = copy.deepcopy(loaded)
        canonical["kind"] = module.CANONICAL_KIND
        for field in ("run_id", "aex_sha256", "renderer", "project_bits_per_channel"):
            candidate = copy.deepcopy(canonical)
            candidate.pop(field)
            rejected(module, candidate, f"canonical missing {field}")
        missing = root / "missing_output.zip"
        with zipfile.ZipFile(missing, "w") as archive:
            archive.writestr("RETURN_RUNTIME_TRACE.json", json.dumps(loaded))
            archive.writestr("logs/combined_cdb_trace.txt", "trace")
        try:
            module.validate_payload(*module.load_return(missing))
        except (ValueError, KeyError):
            pass
        else:
            raise AssertionError("missing output artifact accepted")
        out_json, out_md = root / "report.json", root / "report.md"
        subprocess.run(["python3", str(CLASSIFIER_PATH), str(package), "--output-json", str(out_json), "--output-md", str(out_md)], cwd=ROOT, check=True)
        assert "Format drift: `true`" in out_md.read_text()
        exchange_root = os.environ.get("OLM_EXCHANGE_ROOT")
        return_dir = Path(exchange_root) / "new/mac_returns" if exchange_root else None
        candidates = list(return_dir.glob("RETURN*OLMDISTANCEGRADATION*COORDINATE_LIVENESS_CENSUS*.zip")) if return_dir and return_dir.is_dir() else []
        for candidate in candidates[:1]:
            subprocess.run(["python3", str(CLASSIFIER_PATH), str(candidate), "--output-json", str(root / "nas.json"), "--output-md", str(root / "nas.md")], cwd=ROOT, check=True)
    print("[OK] DG8 coordinate-liveness census return classifier smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
