#!/usr/bin/env python3
"""Prove the native-UCRT result for DirectionalBlur's six x86 cells."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "scripts/analyze_olm_math_ucrt_batch_return_20260814.py"
DOWNSTREAM = ROOT / "tools/emulation/test_olm_math_ucrt_downstream_replay_20260814.py"
CONSUMER = ROOT / "tools/emulation/run_olm_math_ucrt_native_dual_owner_replay_20260814.py"
PLUMBING = ROOT / "tools/emulation/test_olmdirectionalblur_same_table_dual_owner_plumbing_20260814.py"
CENSUS = ROOT / "tools/emulation/test_olmdirectionalblur_exported_smart_remaining6_census_20260814.py"
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
CANONICAL_RETURN = ROOT / "refs/conformance/olm_math_ucrt_batch_native_return_20260814.json"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_remaining6_native_ucrt_replay_20260815.json"
HEADER = ROOT / "core/dblur_native_ucrt_remaining6_20260815.h"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def generate(return_path: Path) -> dict[str, object]:
    print("stage: validate return", flush=True)
    downstream = load(DOWNSTREAM, "dblur_native_downstream")
    consumer = load(CONSUMER, "dblur_native_consumer")
    plumbing = load(PLUMBING, "dblur_native_plumbing")
    census = load(CENSUS, "dblur_native_census")
    expf, powf, validated = downstream.maps_from_return(return_path)
    if len(expf) != 377 or len(powf) != 850:
        raise RuntimeError("native result table cardinality")
    directional_keys = {
        (row["input_bits"], row["exponent_bits"])
        for row in json.loads(downstream.DB_POWF_VECTORS.read_text())
    }
    directional_powf = {key: powf[key] for key in directional_keys}
    if len(directional_powf) != 787:
        raise RuntimeError("Directional powf table cardinality")
    with tempfile.TemporaryDirectory(prefix="dblur-native-ucrt-replay-") as raw:
        root = Path(raw)
        table = root / "native-ucrt-table.txt"
        downstream.write_table(table, expf, directional_powf)
        print("stage: build workers", flush=True)
        worker, build = plumbing.build_worker(root)
        aex_root = root / "aex"; aex_root.mkdir()
        mac_root = root / "mac"; mac_root.mkdir()
        print("stage: exported AEX", flush=True)
        aex = consumer.directional_aex(worker, table, aex_root, census)
        print("stage: Mac direct", flush=True)
        mac, calls = consumer.directional_mac(table, mac_root, downstream, census, plumbing)
        table_sha256 = sha256(table)
    print("stage: assemble evidence", flush=True)
    prior = json.loads(census.REPORT.read_text())
    historical = {(row["depth"], row["tuple_index"]): row["historical_double_round_raw_sha256"]
                  for row in prior["rows"]}
    rows = []
    for left, right in zip(aex, mac, strict=True):
        if (left["depth"], left["tuple_index"]) != (right["depth"], right["tuple_index"]):
            raise RuntimeError("Directional row order")
        key = (left["depth"], left["tuple_index"])
        rows.append({
            "depth": left["depth"], "tuple_index": left["tuple_index"],
            "raw_bytes": left["raw_bytes"], "render_mode": left["render_mode"],
            "guards_intact": left["guards_intact"], "aex_raw_sha256": left["raw_sha256"],
            "mac_production_direct_raw_sha256": right["raw_sha256"],
            "same_table_full_raw_exact": left["raw_sha256"] == right["raw_sha256"],
            "preexisting_x86_raw_sha256": historical[key],
            "native_matches_preexisting_x86_raw": left["raw_sha256"] == historical[key],
        })
    if len(rows) != 6 or not all(row["same_table_full_raw_exact"] and
                                 row["native_matches_preexisting_x86_raw"] for row in rows):
        raise RuntimeError("Directional native-table RAW closure incomplete")
    tables = {
        "expf": [{"argument_bits": key, "result_bits": value} for key, value in sorted(expf.items())],
        "powf": [{"input_bits": key[0], "exponent_bits": key[1], "result_bits": value}
                 for key, value in sorted(directional_powf.items())],
    }
    canonical = json.loads(CANONICAL_RETURN.read_text())
    if canonical["return_sha256"] != validated["return_sha256"] or canonical["status"] != \
            "PASS_NATIVE_WINDOWS_UCRT_BATCH_RETURN_VALIDATED_NO_PROMOTION":
        raise RuntimeError("canonical return evidence mismatch")
    return {
        "schema": "olmdirectionalblur.remaining6-native-ucrt-replay/1",
        "status": "PASS_DIRECTIONAL_REMAINING6_NATIVE_UCRT_EXPORTED_AEX_MAC_DIRECT_RAW_EXACT",
        "authorities": {
            "return_sha256": validated["return_sha256"],
            "canonical_return_report_sha256": sha256(CANONICAL_RETURN),
            "analyzer_sha256": sha256(ANALYZER), "downstream_sha256": sha256(DOWNSTREAM),
            "consumer_sha256": sha256(CONSUMER), "plumbing_sha256": sha256(PLUMBING),
            "census_sha256": sha256(CENSUS), "pre_integration_source_sha256": sha256(SOURCE),
            "ucrtbase": validated["ucrtbase"],
        },
        "table": {"expf_keys": 377, "powf_keys": 787, "serialized_sha256": table_sha256,
                  "rows_sha256": digest(tables), **tables},
        "rows": rows, "rows_sha256": digest(rows),
        "mac_table_calls": calls,
        "decision": {
            "promotable_cells": 6,
            "contract": "x86_64 fixed 64x36 former-residual six only; admission-only source change",
            "production_math_change_required": False,
            "arbitrary_tuple_or_geometry": False, "production_changed_by_tool": False,
            "installed_binary_changed": False, "after_effects_launched": False,
        },
        "worker_build": build,
    }


def validate(value: object) -> bool:
    if not isinstance(value, dict) or value.get("schema") != "olmdirectionalblur.remaining6-native-ucrt-replay/1":
        return False
    if value.get("status") != "PASS_DIRECTIONAL_REMAINING6_NATIVE_UCRT_EXPORTED_AEX_MAC_DIRECT_RAW_EXACT":
        return False
    table = value.get("table")
    rows = value.get("rows")
    if not isinstance(table, dict) or len(table.get("expf", [])) != 377 or len(table.get("powf", [])) != 787:
        return False
    if table.get("rows_sha256") != digest({"expf": table["expf"], "powf": table["powf"]}):
        return False
    if not isinstance(rows, list) or len(rows) != 6 or value.get("rows_sha256") != digest(rows):
        return False
    if not all(row.get("same_table_full_raw_exact") is True and
               row.get("native_matches_preexisting_x86_raw") is True for row in rows):
        return False
    return value.get("decision") == {
        "promotable_cells": 6,
        "contract": "x86_64 fixed 64x36 former-residual six only; admission-only source change",
        "production_math_change_required": False,
        "arbitrary_tuple_or_geometry": False, "production_changed_by_tool": False,
        "installed_binary_changed": False, "after_effects_launched": False,
    }


def render_header(value: dict[str, object]) -> str:
    if not validate(value):
        raise RuntimeError("invalid Directional native-UCRT evidence")
    table = value["table"]
    lines = [
        "#pragma once", "", "#include <cstdint>", "#include <cstring>", "#include <cmath>", "",
        "namespace olm::dblur::native_ucrt {",
        "struct ExpfRow { std::uint32_t argument; std::uint32_t result; };",
        "struct PowfRow { std::uint32_t input; std::uint32_t exponent; std::uint32_t result; };",
        "inline constexpr ExpfRow kExpf[] = {",
    ]
    lines += [f"    {{{row['argument_bits']}u, {row['result_bits']}u}}," for row in table["expf"]]
    lines += ["};", "inline constexpr PowfRow kPowf[] = {"]
    lines += [f"    {{{row['input_bits']}u, {row['exponent_bits']}u, {row['result_bits']}u}},"
              for row in table["powf"]]
    lines += [
        "};", "",
        "inline thread_local bool active = false;",
        "inline thread_local bool missing = false;",
        "inline std::uint32_t word(float value) noexcept { std::uint32_t bits; std::memcpy(&bits, &value, 4); return bits; }",
        "inline float real(std::uint32_t bits) noexcept { float value; std::memcpy(&value, &bits, 4); return value; }",
        "class Scope {", "public:",
        "    explicit Scope(bool enable) noexcept : previous_(active), enabled_(enable) { if (enable) { active = true; missing = false; } }",
        "    ~Scope() noexcept { active = previous_; }",
        "    bool complete() const noexcept { return !enabled_ || !missing; }",
        "private: bool previous_; bool enabled_;", "};",
        "inline float expf_exact(float argument) noexcept {",
        "    if (!active) return ::expf(argument);",
        "    const auto key = word(argument); for (const auto& row : kExpf) if (row.argument == key) return real(row.result);",
        "    missing = true; return 0.0f;", "}",
        "inline float powf_exact(float input, float exponent) noexcept {",
        "    if (!active) return static_cast<float>(std::pow(static_cast<double>(input), static_cast<double>(exponent)));",
        "    const auto left = word(input), right = word(exponent);",
        "    for (const auto& row : kPowf) if (row.input == left && row.exponent == right) return real(row.result);",
        "    missing = true; return 0.0f;", "}",
        "}  // namespace olm::dblur::native_ucrt", "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("return_path", type=Path, nargs="?")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--write-header", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        value = json.loads(REPORT.read_text())
    else:
        if args.return_path is None:
            raise RuntimeError("return_path required")
        value = generate(args.return_path)
    if not validate(value):
        raise RuntimeError("Directional native-UCRT replay validation failed")
    if args.write:
        if REPORT.exists():
            raise RuntimeError("refusing to overwrite evidence")
        REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    if args.write_header:
        if HEADER.exists():
            raise RuntimeError("refusing to overwrite generated header")
        HEADER.write_text(render_header(value))
    print(value["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
