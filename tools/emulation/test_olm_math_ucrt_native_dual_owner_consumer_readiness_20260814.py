#!/usr/bin/env python3
"""Freeze the synthetic end-to-end readiness of the native dual-owner consumer."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONSUMER = ROOT / "tools/emulation/run_olm_math_ucrt_native_dual_owner_replay_20260814.py"
RETURN_TEST = ROOT / "tests/test_olm_math_ucrt_batch_return_20260814.py"
DB_CONTROL = ROOT / "refs/conformance/olmdirectionalblur_same_table_dual_owner_plumbing_20260814.json"
DG_CONTROL = ROOT / "refs/conformance/olmdistancegradation_same_table_dual_owner_plumbing_20260814.json"
REPORT = ROOT / "refs/conformance/olm_math_ucrt_native_dual_owner_consumer_readiness_20260814.json"
MARKDOWN = REPORT.with_suffix(".md")

EXPECTED_DIRECTIONAL_ROWS_SHA256 = "19f2e545a869c4fc1da5ac2687343c311a2c4e1c5e68ca479d5b6a3b598dd8c2"
EXPECTED_DISTANCE_ROWS_SHA256 = "a3e7957c2677093ef5ac216b5c8c025620a31b7e30af34355e719b2e3a0392a0"
EXPECTED_SYNTHETIC_TABLE_SHA256 = "487191c9e48617a316eda7040ce87931f09aeb882158fd2f2324f59dc0ed211c"
EXPECTED_WORKER_BUILD = {
    "clean_clone": True, "release_build": True,
    "worker_sha256": "c2f28fd0f28b73ebb57b68e7ffefc9e11c254f016aae5d0ed157f7ab3d3f6af7",
    "worker_bytes": 3887728,
    "patched_callbacks_sha256": "c6db8fea04e2db211943ff923bbfe8b22655859dcf07210e403516a80c4b9aca",
    "patched_imports_sha256": "27ad9a37a640c13dbed6e95a8eb7cca27406db8d48b3c89b9573075546f4d466",
    "patched_main_sha256": "5efc9609220a4cf5f077ef975e92a5815359d6323d2019f14c6bddc307df90b7",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identities() -> dict[str, str]:
    return {"consumer_sha256": sha256(CONSUMER), "synthetic_return_builder_sha256": sha256(RETURN_TEST),
            "directional_host_control_sha256": sha256(DB_CONTROL),
            "distance_host_control_sha256": sha256(DG_CONTROL)}


def generate(*, run_build: bool) -> dict[str, Any]:
    if not run_build:
        raise RuntimeError("readiness generation requires --run-build")
    consumer = load(CONSUMER, "olm_native_consumer_readiness_consumer")
    return_test = load(RETURN_TEST, "olm_native_consumer_readiness_return")
    with tempfile.TemporaryDirectory(prefix="olm-native-consumer-readiness-") as raw:
        case = return_test.OLMUcrtMathBatchReturnTest()
        case.module = return_test.load_module()
        return_path = case.build_valid_return(Path(raw))
        result = consumer.generate(return_path)
    return {
        "schema": "olm.math-ucrt-native-dual-owner-consumer-readiness/1",
        "status": "PASS_SYNTHETIC_VALIDATED_RETURN_CONSUMER_AEX_MAC_DIRECT_14_OF_14",
        "identities": identities(),
        "synthetic_return": {"explicitly_not_native_windows_evidence": True,
                             "ucrt_file_version": result["inputs"]["return_analysis"]["ucrtbase"]["file_version"],
                             "ucrt_sha256": result["inputs"]["return_analysis"]["ucrtbase"]["sha256"],
                             "validated_vectors": result["inputs"]["return_analysis"]["vectors"]},
        "consumer": {"status": result["status"], "table": result["table"],
                     "worker_build": result["worker_build"],
                     "directional_rows": result["directional_rows"],
                     "directional_rows_sha256": result["directional_rows_sha256"],
                     "distance_rows": result["distance_rows"],
                     "distance_rows_sha256": result["distance_rows_sha256"],
                     "directional_mac_table_calls": result["directional_mac_table_calls"],
                     "summary": result["summary"], "decision": result["decision"]},
        "scope": {"consumer_code_path_executed": True, "clean_aexcompat_release_build": True,
                  "strict_return_analyzer_executed": True, "native_windows_return_received": False,
                  "native_windows_result_claimed": False, "production_changed": False,
                  "installed_binary_changed": False, "after_effects_launched": False,
                  "network_changed": False},
    }


def validate(value: Any, *, live: bool = True) -> bool:
    if not isinstance(value, dict) or set(value) != {"schema", "status", "identities", "synthetic_return",
                                                      "consumer", "scope"}:
        return False
    if value["schema"] != "olm.math-ucrt-native-dual-owner-consumer-readiness/1" or value["status"] != \
            "PASS_SYNTHETIC_VALIDATED_RETURN_CONSUMER_AEX_MAC_DIRECT_14_OF_14":
        return False
    if live:
        try:
            if value["identities"] != identities():
                return False
        except OSError:
            return False
    if value["synthetic_return"] != {
        "explicitly_not_native_windows_evidence": True, "ucrt_file_version": "10.0.test",
        "ucrt_sha256": "1" * 64,
        "validated_vectors": {"directional_expf": 494, "directional_powf": 787,
                              "distance_powf": 63, "total": 1344},
    }:
        return False
    consumer = value["consumer"]
    if not isinstance(consumer, dict) or set(consumer) != {
        "status", "table", "worker_build", "directional_rows", "directional_rows_sha256",
        "distance_rows", "distance_rows_sha256", "directional_mac_table_calls",
        "summary", "decision"
    }:
        return False
    if consumer["status"] != "PASS_NATIVE_TABLE_EXPORTED_AEX_MAC_DIRECT_FULL_RAW_14_OF_14":
        return False
    if consumer["table"] != {"expf_unique_keys": 377, "powf_unique_keys": 850,
                              "total_unique_keys": 1227, "sha256": EXPECTED_SYNTHETIC_TABLE_SHA256,
                              "source": "validated_native_windows_ucrt_return"}:
        return False
    if consumer["worker_build"] != EXPECTED_WORKER_BUILD:
        return False
    if consumer["directional_mac_table_calls"] != {"expf": 996, "powf": 0, "pow": 47514}:
        return False
    native_consumer = load(CONSUMER, "olm_native_consumer_readiness_validate")
    if consumer["directional_rows_sha256"] != native_consumer.digest(consumer["directional_rows"]) or \
            consumer["directional_rows_sha256"] != EXPECTED_DIRECTIONAL_ROWS_SHA256:
        return False
    if consumer["distance_rows_sha256"] != native_consumer.digest(consumer["distance_rows"]) or \
            consumer["distance_rows_sha256"] != EXPECTED_DISTANCE_ROWS_SHA256:
        return False
    if len(consumer["directional_rows"]) != 6 or len(consumer["distance_rows"]) != 8 or \
            not all(row.get("same_table_full_raw_exact") is True for row in
                    consumer["directional_rows"] + consumer["distance_rows"]):
        return False
    if consumer["summary"] != {"directional_same_table_exact": 6, "distance_same_table_exact": 8,
                                "total_same_table_exact": 14}:
        return False
    if consumer["decision"] != {"production_promoted": False, "installed_binary_changed": False,
                                  "directional_public_effectmain_closure_still_required": True,
                                  "distance_public_smart_closure_still_required": True,
                                  "after_effects_launched": False, "network_changed": False}:
        return False
    return value["scope"] == {"consumer_code_path_executed": True,
                               "clean_aexcompat_release_build": True,
                               "strict_return_analyzer_executed": True,
                               "native_windows_return_received": False,
                               "native_windows_result_claimed": False,
                               "production_changed": False, "installed_binary_changed": False,
                               "after_effects_launched": False, "network_changed": False}


def markdown(value: dict[str, Any]) -> str:
    return (
        "# Native UCRT dual-owner consumer readiness\n\n"
        f"Status: `{value['status']}`.\n\n"
        "The exact consumer intended for the future 1,344-row return was exercised end-to-end with the "
        "strict analyzer's synthetic test fixture. One clean AEXCompat release worker and one derived table "
        "drove Directional exported AEX versus Mac production direct (6/6) and Distance exported AEX versus "
        "Mac RenderBits (8/8), full RAW exact. Directional records 996 expf and 47,514 double-pow table "
        "lookups, so both imported-math families are exercised. The synthetic UCRT identity is explicitly test-only and is "
        "not native Windows evidence. No public route was promoted, and AE/network/install state was untouched.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-build", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        value = generate(run_build=args.run_build)
        REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        MARKDOWN.write_text(markdown(value))
    else:
        value = json.loads(REPORT.read_text())
    if not validate(value) or MARKDOWN.read_text() != markdown(value):
        raise RuntimeError("native dual-owner consumer readiness invalid")
    print(value["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
