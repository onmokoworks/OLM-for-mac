#!/usr/bin/env python3
"""Fail-closed contract tests for the KiraKira live Gaussian classifier."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLASSIFIER_PATH = ROOT / "scripts/classify_olmkirakira_mode3_live_gaussian_return.py"


def load_classifier():
    spec = importlib.util.spec_from_file_location("kirakira_live_classifier", CLASSIFIER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_payload(module, words: list[int]) -> dict:
    run_id = "smoke-20260713"
    base = 0x180000000
    markers = [
        f"KK_RUN_START request_id={module.REQUEST_ID} run_id={run_id} case_id={module.CASE_ID}",
        f"KK_MODULE run_id={run_id} module=OLMKiraKira.aex module_base=0x{base:x} sha256={module.AEX_SHA256} size={module.AEX_SIZE}",
        f"KK_BREAKPOINTS_READY run_id={run_id}",
        f"KK_WRAPPER run_id={run_id}",
        f"KK_CREATE run_id={run_id}",
        f"KK_KERNEL_ENTRY run_id={run_id}",
        f"KK_KERNEL_RETURN run_id={run_id}",
    ]
    return {
        "schema": module.SCHEMA,
        "request_id": module.REQUEST_ID,
        "status": "answered",
        "run_id": run_id,
        "preflight": {
            "status": "ready",
            "marker": "AE_JSX_PREFLIGHT_READY ae_version=25.2",
            "ae_pid": 1234,
        },
        "run": {
            "run_id": run_id,
            "case_id": module.CASE_ID,
            "module": "OLMKiraKira.aex",
            "module_base": f"0x{base:x}",
            "aex_sha256": module.AEX_SHA256,
            "aex_size": module.AEX_SIZE,
        },
        "binding": {
            **{f"{name}_rva": f"0x{rva:x}" for name, rva in module.EXPECTED_RVAS.items()},
            **{name: f"0x{base + rva:x}" for name, rva in module.EXPECTED_RVAS.items()},
        },
        "case": {
            "blur_mode_manifest": 3,
            "overrides_match_name": {
                "OLM OLM Kira Kira-0003": 5,
                "OLM OLM Kira Kira-0004": 0,
                "OLM OLM Kira Kira-0005": 0,
                "OLM OLM Kira Kira-0026": 0,
            },
        },
        "observation": {
            "module_marker": markers[1],
            "first_getKernel": {"ecx": 21, "xmm1": 2.5, "r8": 5, "output_mat": "0x20000000"},
            "return_data": "0x20000100",
            "raw_words_u32": [f"{word:08x}" for word in words],
            "raw_bytes": 84,
        },
        "trace": "\n".join(markers) + "\n",
    }


def expect_rejected(module, payload: dict, label: str) -> None:
    try:
        module.validate_payload(payload)
    except ValueError:
        return
    raise AssertionError(f"invalid payload accepted: {label}")


def main() -> int:
    module = load_classifier()
    gaussian = module.opencv_words()
    payload = valid_payload(module, gaussian)
    assert module.validate_payload(payload) == gaussian

    mutations = {
        "wrong hash": ("run", "aex_sha256", "0" * 64),
        "mixed run": ("run", "run_id", "another-run"),
        "wrong absolute hook": ("binding", "getKernel", "0x180000001"),
        "wrong sigma": ("observation", "first_getKernel", {"ecx": 21, "xmm1": 2.0, "r8": 5, "output_mat": "0x20000000"}),
        "missing preflight": ("preflight", "status", "missing"),
        "wrong byte count": ("observation", "raw_bytes", 80),
    }
    for label, (section, field, value) in mutations.items():
        candidate = copy.deepcopy(payload)
        candidate[section][field] = value
        expect_rejected(module, candidate, label)

    missing_marker = copy.deepcopy(payload)
    missing_marker["trace"] = "\n".join(
        line for line in missing_marker["trace"].splitlines() if not line.startswith("KK_KERNEL_RETURN")
    )
    expect_rejected(module, missing_marker, "missing trace marker")

    with tempfile.TemporaryDirectory(prefix="kirakira_live_classifier_") as temporary:
        source = Path(temporary) / "return.json"
        source.write_text(json.dumps(payload), encoding="utf-8")
        loaded = module.load_return(source)
        assert module.validate_payload(loaded) == gaussian

    print("PASS KiraKira live Gaussian classifier rejects unbound/mixed-run evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
