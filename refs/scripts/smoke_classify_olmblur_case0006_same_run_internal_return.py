#!/usr/bin/env python3
"""Smoke-test the OLMBlur case_0006 same-run internal return classifier."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLASSIFIER_PATH = ROOT / "scripts/classify_olmblur_case0006_same_run_internal_return.py"


def load_classifier():
    spec = importlib.util.spec_from_file_location("olmblur_case0006_classifier", CLASSIFIER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_payload(module: object) -> dict:
    run = {
        "run_id": "windows-run-from-fixture",
        "ae_pid": 5936,
        "module": module.MODULE,
        "module_base": "0x7fffcd660000",
        "aex_sha256": module.AEX_SHA256,
        "project_depth": 16,
    }
    witnesses = [
        {**run, "xy": [29, 71], "pre_store_rgb_bits_hex": ["0x4435beb4"] * 3, "stored_rgb16": [727] * 3},
        {**run, "xy": [314, 14], "pre_store_rgb_bits_hex": ["0x45098f32"] * 3, "stored_rgb16": [2201] * 3},
    ]
    png_bytes = module.PNG_SIGNATURE + b"synthetic PNG identity for the classifier contract"
    exported = {
        **run,
        "archive_path": "return/exported_case_0006.png",
        "png_sha256": hashlib.sha256(png_bytes).hexdigest(),
        "png_size_bytes": len(png_bytes),
        "witnesses": [
            {**run, "xy": [29, 71], "rgba16": [725, 725, 725, 65535]},
            {**run, "xy": [314, 14], "rgba16": [2201, 2201, 2201, 65535]},
        ],
    }
    return {"schema": module.SCHEMA, "status": "answered", "case_id": module.CASE_ID,
            "run": run, "witnesses": witnesses, "exported_png": exported}


def expect_rejected(module: object, payload: dict, label: str) -> None:
    try:
        module.validate_payload(payload)
    except ValueError:
        return
    raise AssertionError(f"invalid payload accepted: {label}")


def main() -> int:
    module = load_classifier()
    payload = valid_payload(module)
    result = module.validate_payload(payload)
    assert result["classification"] == "accepted_same_run_internal_store_and_png_identity"
    assert result["coordinates"] == [[29, 71], [314, 14]]
    assert result["png_verification_scope"] == "metadata-only"

    mutations = {
        "wrong depth": ("run", "project_depth", 8),
        "wrong hash": ("run", "aex_sha256", "0" * 64),
        "mixed witness PID": ("witnesses", 0, "ae_pid", 5937),
        "missing pre-store bits": ("witnesses", 1, "pre_store_rgb_bits_hex", None),
        "invalid stored RGB16": ("witnesses", 0, "stored_rgb16", [65536, 727, 727]),
        "mixed export run": ("exported_png", "run_id", "other-run"),
        "missing PNG identity": ("exported_png", "png_sha256", None),
        "missing coordinate": ("witnesses", 0, "xy", [1, 2]),
    }
    for label, mutation in mutations.items():
        candidate = copy.deepcopy(payload)
        if len(mutation) == 3:
            section, field, value = mutation
            candidate[section][field] = value
        else:
            section, index, field, value = mutation
            candidate[section][index][field] = value
        expect_rejected(module, candidate, label)

    with tempfile.TemporaryDirectory(prefix="olmblur_case0006_classifier_", dir="/tmp") as td:
        source = Path(td) / "return.json"
        package = Path(td) / "return.zip"
        output = Path(td) / "classified.json"
        source.write_text(json.dumps(payload), encoding="utf-8")
        loaded = module.load_return(source)
        assert module.validate_payload(loaded)["project_depth"] == 16
        with zipfile.ZipFile(package, "w") as archive:
            archive.writestr("RETURN_OLMBLUR_CASE0006.json", source.read_bytes())
            archive.writestr(payload["exported_png"]["archive_path"],
                             module.PNG_SIGNATURE + b"synthetic PNG identity for the classifier contract")
        module.verify_zip_png(package, payload)
        assert module.validate_payload(payload, png_scope="zip-png-bytes-verified")["png_verification_scope"] == "zip-png-bytes-verified"
        subprocess.run(["python3", str(CLASSIFIER_PATH), str(package), "--output-json", str(output)],
                       cwd=ROOT, check=True, stdout=subprocess.PIPE, text=True)
        classified = json.loads(output.read_text(encoding="utf-8"))
        assert classified["case_id"] == module.CASE_ID
        assert classified["png_verification_scope"] == "zip-png-bytes-verified"

        missing_png = Path(td) / "missing_png.zip"
        with zipfile.ZipFile(missing_png, "w") as archive:
            archive.writestr("RETURN_OLMBLUR_CASE0006.json", source.read_bytes())
        expect_zip_rejected(module, missing_png, payload, "missing PNG")

        tampered_png = Path(td) / "tampered_png.zip"
        with zipfile.ZipFile(tampered_png, "w") as archive:
            archive.writestr("RETURN_OLMBLUR_CASE0006.json", source.read_bytes())
            archive.writestr(payload["exported_png"]["archive_path"], module.PNG_SIGNATURE + b"tampered")
        expect_zip_rejected(module, tampered_png, payload, "tampered PNG")

        unsafe_payload = copy.deepcopy(payload)
        unsafe_payload["exported_png"]["archive_path"] = "../exported_case_0006.png"
        unsafe_png = Path(td) / "unsafe_path.zip"
        with zipfile.ZipFile(unsafe_png, "w") as archive:
            archive.writestr("RETURN_OLMBLUR_CASE0006.json", json.dumps(unsafe_payload))
            archive.writestr("../exported_case_0006.png", module.PNG_SIGNATURE + b"unsafe")
        expect_zip_rejected(module, unsafe_png, unsafe_payload, "unsafe PNG path")
    print("[OK] OLMBlur case_0006 same-run internal return classifier smoke passed")
    return 0


def expect_zip_rejected(module: object, package: Path, payload: dict, label: str) -> None:
    try:
        module.verify_zip_png(package, payload)
    except ValueError:
        return
    raise AssertionError(f"invalid ZIP accepted: {label}")


if __name__ == "__main__":
    raise SystemExit(main())
