#!/usr/bin/env python3
"""Contract tests for DG 8bpc live depth-control intake."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/classify_olmdistancegradation_8bpc_depth_control_return.py"


def load_module():
    spec = importlib.util.spec_from_file_location("dg_depth_classifier", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def payload(module) -> dict:
    return {
        "status": "answered",
        "kind": "depth_control",
        "request_id": module.REQUEST_ID,
        "run_id": "dglive-smoke",
        "ae_pid": 4242,
        "module_base": "0x7ff600000000",
        "aex_sha256": module.AEX_SHA256,
        "project_bits_per_channel": 8,
        "rvas": [
            {"rva": "1170870", "hit_count": 3},
            {"rva": "1170c90", "hit_count": 0},
        ],
    }


def reject(module, candidate: dict, label: str) -> None:
    try:
        module.validate_payload(candidate)
    except ValueError:
        return
    raise AssertionError(f"invalid DG depth control accepted: {label}")


def main() -> int:
    module = load_module()
    valid = payload(module)
    result = module.validate_payload(valid)
    assert result["classification"] == "pf8_live_pf32_negative_control_exact"

    mutations = []
    for label, section, key, value in (
        ("wrong hash", None, "aex_sha256", "0" * 64),
        ("wrong depth", None, "project_bits_per_channel", 32),
        ("no PF8", "rvas", 0, {"rva": "1170870", "hit_count": 0}),
        ("PF32 hit", "rvas", 1, {"rva": "1170c90", "hit_count": 1}),
        ("missing run", None, "run_id", ""),
    ):
        candidate = copy.deepcopy(valid)
        if section == "rvas":
            candidate[section][key] = value
        else:
            candidate[key] = value
        mutations.append((label, candidate))
    for label, candidate in mutations:
        reject(module, candidate, label)

    with tempfile.TemporaryDirectory(prefix="dg_depth_classifier_") as temporary:
        archive_path = Path(temporary) / "return.zip"
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("return/RETURN_RUNTIME_TRACE.json", json.dumps(valid))
        assert module.validate_payload(module.load_return(archive_path))["hit_counts"]["1170870"] == 3

    print("PASS DG depth-control classifier rejects wrong depth/hash/callback dispatch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
