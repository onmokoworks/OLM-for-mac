#!/usr/bin/env python3
"""Emit bounded native-UCRT lookup evidence only after dual-owner RAW exactness.

This tool never edits production.  It validates the returned Windows batch,
replays both plug-ins through their final RAW buffers, and emits keyed result
tables only when all six DirectionalBlur and all eight DistanceGradation cells
are exact through exported Windows AEX and Mac production direct owners using
the same table.  The tables are integration inputs, not an admission patch or
a Mac public-path claim.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOWNSTREAM = ROOT / "tools/emulation/test_olm_math_ucrt_downstream_replay_20260814.py"
CONSUMER = ROOT / "tools/emulation/run_olm_math_ucrt_native_dual_owner_replay_20260814.py"
DIRECTIONAL_SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
DISTANCE_SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
GAUSSIAN_SOURCE = ROOT / "core/dblur_gaussian.h"

SOURCE_SHA256 = {
    "core/dblur_gaussian.h": "c51bfca6d7f8a3d30ac58f3a2605a2bade053876c42f1179c0e02f60adb8258c",
    "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp": "494116880d037a0d44a48b0e0ebe0fc5358b4cd8892b90ca8c61ea8a7bb2e845",
    "mac/OLMDistanceGradation/OLMDistanceGradation.cpp": "06ffc5b7a2af5cf54a2503d3bf03f9baf2269acbf1277f034937ac79c4a7aba5",
}


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def render_header(report: dict[str, object]) -> str:
    """Render a no-fallback uint32 lookup header from a validated report."""
    if not validate(report, live=False):
        raise RuntimeError("refuse header from invalid promotion table report")
    expf = report["tables"]["directional_expf"]
    directional_powf = report["tables"]["directional_powf"]
    distance_powf = report["tables"]["distance_powf"]
    lines = [
        "#pragma once",
        "#include <cstddef>",
        "#include <cstdint>",
        "namespace olm::native_ucrt {",
        "struct ExpfRow { std::uint32_t argument; std::uint32_t result; };",
        "struct PowfRow { std::uint32_t input; std::uint32_t exponent; std::uint32_t result; };",
        "inline constexpr ExpfRow kDirectionalExpf[] = {",
    ]
    lines.extend(f"    {{{row['argument_bits']}u, {row['native_ucrt_result_bits']}u}}," for row in expf)
    lines += [
        "};",
        "inline constexpr PowfRow kDirectionalPowf[] = {",
    ]
    lines.extend(
        f"    {{{row['input_bits']}u, {row['exponent_bits']}u, {row['native_ucrt_result_bits']}u}},"
        for row in directional_powf
    )
    lines += [
        "};",
        "inline constexpr PowfRow kDistancePowf[] = {",
    ]
    lines.extend(
        f"    {{{row['input_bits']}u, {row['exponent_bits']}u, {row['native_ucrt_result_bits']}u}},"
        for row in distance_powf
    )
    lines += [
        "};",
        "inline constexpr std::size_t kDirectionalExpfCount = sizeof(kDirectionalExpf) / sizeof(kDirectionalExpf[0]);",
        "inline constexpr std::size_t kDirectionalPowfCount = sizeof(kDirectionalPowf) / sizeof(kDirectionalPowf[0]);",
        "inline constexpr std::size_t kDistancePowfCount = sizeof(kDistancePowf) / sizeof(kDistancePowf[0]);",
        "inline bool lookup_directional_expf(std::uint32_t argument, std::uint32_t& result) noexcept {",
        "    for (const auto& row : kDirectionalExpf) { if (row.argument == argument) { result = row.result; return true; } }",
        "    return false;",
        "}",
        "inline bool lookup_directional_powf(std::uint32_t input, std::uint32_t exponent, std::uint32_t& result) noexcept {",
        "    for (const auto& row : kDirectionalPowf) { if (row.input == input && row.exponent == exponent) { result = row.result; return true; } }",
        "    return false;",
        "}",
        "inline bool lookup_distance_powf(std::uint32_t input, std::uint32_t exponent, std::uint32_t& result) noexcept {",
        "    for (const auto& row : kDistancePowf) { if (row.input == input && row.exponent == exponent) { result = row.result; return true; } }",
        "    return false;",
        "}",
        "}  // namespace olm::native_ucrt",
        "",
    ]
    return "\n".join(lines)


def live_source_gate() -> dict[str, str]:
    actual = {name: sha(ROOT / name) for name in SOURCE_SHA256}
    if actual != SOURCE_SHA256:
        raise RuntimeError(f"production source drift: {actual}")
    directional = DIRECTIONAL_SOURCE.read_text()
    distance = DISTANCE_SOURCE.read_text()
    required_directional = (
        "static bool PublicDualSideExportedSmartExact(",
        "#if defined(__x86_64__)",
        "if (bitdepth == 32) {\n\t\treturn false;",
        "x86_64 retains the narrower exact subset above",
    )
    required_distance = (
        "static bool is_admitted_pf32_smart_exported_matrix(",
        "p.interp_mode > INTERP_POWER || p.interp_mode == INTERP_POWER ||",
        "PF32 Power is not an admissible public",
    )
    if any(token not in directional for token in required_directional):
        raise RuntimeError("Directional fail-closed source contract drift")
    if any(token not in distance for token in required_distance):
        raise RuntimeError("Distance fail-closed source contract drift")
    return actual


def build_from_consumer(return_path: Path, replay: dict[str, object]) -> dict[str, object]:
    sources = live_source_gate()
    downstream = load(DOWNSTREAM, "olm_ucrt_downstream_for_promotion_table")
    if replay.get("status") != "PASS_NATIVE_TABLE_EXPORTED_AEX_MAC_DIRECT_FULL_RAW_14_OF_14" or \
            replay.get("summary") != {"directional_same_table_exact": 6,
                                      "distance_same_table_exact": 8,
                                      "total_same_table_exact": 14}:
        raise RuntimeError("native-derived direct-owner RAW closure incomplete")
    expf, powf, validated = downstream.maps_from_return(return_path)
    expf_rows = [
        {"argument_bits": argument, "native_ucrt_result_bits": result}
        for argument, result in sorted(expf.items())
    ]
    directional_keys = {(row["input_bits"], row["exponent_bits"])
                        for row in json.loads(downstream.DB_POWF_VECTORS.read_text())}
    distance_keys = {(row["input_bits"], row["exponent_bits"])
                     for row in json.loads(downstream.DG_VECTORS.read_text())}
    directional_powf_rows = [
        {"input_bits": left, "exponent_bits": right, "native_ucrt_result_bits": powf[(left, right)]}
        for left, right in sorted(directional_keys)
    ]
    distance_powf_rows = [
        {"input_bits": left, "exponent_bits": right, "native_ucrt_result_bits": result}
        for (left, right), result in sorted(powf.items()) if (left, right) in distance_keys
    ]
    if len(expf_rows) != 377 or len(directional_powf_rows) != 787 or len(distance_powf_rows) != 63:
        raise RuntimeError("native table cardinality")
    if any(row["argument_bits"] == "0x80000000" for row in expf_rows):
        raise RuntimeError("negative zero was not normalized")
    if not any(row == {"argument_bits": "0x00000000", "native_ucrt_result_bits": "0x3f800000"}
               for row in expf_rows):
        raise RuntimeError("signed-zero normalization boundary")
    tables = {"directional_expf": expf_rows, "directional_powf": directional_powf_rows,
              "distance_powf": distance_powf_rows}
    return {
        "schema": "olm.native-ucrt-promotion-tables/1",
        "status": "READY_BOUNDED_NATIVE_UCRT_TABLES_DIRECT_OWNER_EXACT_PUBLIC_NOT_INTEGRATED",
        "return": {
            "path": str(return_path.resolve()),
            "sha256": validated["return_sha256"],
            "ucrtbase": validated["ucrtbase"],
            "vectors": validated["vectors"],
        },
        "authorities": {
            "downstream_replay_sha256": sha(DOWNSTREAM),
            "native_dual_owner_consumer_sha256": sha(CONSUMER),
            "production_source_sha256": sources,
        },
        "final_raw": {
            "directional_matching_cells": replay["summary"]["directional_same_table_exact"],
            "distance_matching_cells": replay["summary"]["distance_same_table_exact"],
            "directional_cells": replay["directional_rows"],
            "distance_cells": replay["distance_rows"],
        },
        "tables": tables,
        "tables_sha256": digest(tables),
        "integration_contract": {
            "directional": "keyed expf and powf results only inside the six existing fixed 64x36 x86_64 residual predicates; missing key remains fail-closed",
            "distance": "keyed powf results only inside the eight existing fixed17x11 PF32 Power predicates; missing key remains fail-closed",
            "libsystem_fallback_for_promoted_cells": False,
            "mac_public_effectmain_exact_claimed": False,
            "separate_public_route_closure_required": True,
            "arbitrary_tuple_or_geometry": False,
            "production_edited_by_this_tool": False,
            "after_effects_launched": False,
        },
    }


def build(return_path: Path) -> dict[str, object]:
    consumer = load(CONSUMER, "olm_ucrt_native_dual_owner_consumer_for_promotion")
    return build_from_consumer(return_path, consumer.generate(return_path))


def validate(report: object, *, live: bool = True) -> bool:
    if not isinstance(report, dict) or set(report) != {
        "schema", "status", "return", "authorities", "final_raw", "tables",
        "tables_sha256", "integration_contract"
    }:
        return False
    if report["schema"] != "olm.native-ucrt-promotion-tables/1" or report["status"] != \
            "READY_BOUNDED_NATIVE_UCRT_TABLES_DIRECT_OWNER_EXACT_PUBLIC_NOT_INTEGRATED":
        return False
    if live:
        try:
            return report == build(Path(report["return"]["path"]))
        except (KeyError, OSError, RuntimeError, TypeError, ValueError):
            return False
    if set(report["return"]) != {"path", "sha256", "ucrtbase", "vectors"}:
        return False
    if report["return"]["vectors"] != {"directional_expf": 494, "directional_powf": 787, "distance_powf": 63, "total": 1344}:
        return False
    if report["authorities"] != {
        "downstream_replay_sha256": sha(DOWNSTREAM),
        "native_dual_owner_consumer_sha256": sha(CONSUMER),
        "production_source_sha256": SOURCE_SHA256,
    }:
        return False
    final_raw = report["final_raw"]
    if not isinstance(final_raw, dict) or set(final_raw) != {
        "directional_matching_cells", "distance_matching_cells", "directional_cells", "distance_cells"
    }:
        return False
    if final_raw["directional_matching_cells"] != 6 or final_raw["distance_matching_cells"] != 8 or \
            not isinstance(final_raw["directional_cells"], list) or len(final_raw["directional_cells"]) != 6 or \
            not isinstance(final_raw["distance_cells"], list) or len(final_raw["distance_cells"]) != 8:
        return False
    if any(not isinstance(row, dict) or row.get("same_table_full_raw_exact") is not True
           for row in final_raw["directional_cells"] + final_raw["distance_cells"]):
        return False
    tables = report["tables"]
    if not isinstance(tables, dict) or set(tables) != {"directional_expf", "directional_powf", "distance_powf"} or \
            report["tables_sha256"] != digest(tables):
        return False
    expf = tables["directional_expf"]
    directional_powf = tables["directional_powf"]
    distance_powf = tables["distance_powf"]
    if not isinstance(expf, list) or len(expf) != 377 or not isinstance(directional_powf, list) or \
            not isinstance(distance_powf, list) or len(directional_powf) != 787 or len(distance_powf) != 63:
        return False
    if expf != sorted(expf, key=lambda row: row.get("argument_bits", "")) or \
            directional_powf != sorted(directional_powf, key=lambda row: (row.get("input_bits", ""), row.get("exponent_bits", ""))) or \
            distance_powf != sorted(distance_powf, key=lambda row: (row.get("input_bits", ""), row.get("exponent_bits", ""))):
        return False
    if any(set(row) != {"argument_bits", "native_ucrt_result_bits"} for row in expf) or \
            any(set(row) != {"input_bits", "exponent_bits", "native_ucrt_result_bits"} for row in directional_powf + distance_powf):
        return False
    if any(row["argument_bits"] == "0x80000000" for row in expf) or \
            {"argument_bits": "0x00000000", "native_ucrt_result_bits": "0x3f800000"} not in expf:
        return False
    return report["integration_contract"] == {
        "directional": "keyed expf and powf results only inside the six existing fixed 64x36 x86_64 residual predicates; missing key remains fail-closed",
        "distance": "keyed powf results only inside the eight existing fixed17x11 PF32 Power predicates; missing key remains fail-closed",
        "libsystem_fallback_for_promoted_cells": False,
        "mac_public_effectmain_exact_claimed": False,
        "separate_public_route_closure_required": True,
        "arbitrary_tuple_or_geometry": False,
        "production_edited_by_this_tool": False,
        "after_effects_launched": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("return_path", type=Path, nargs="?")
    parser.add_argument("--write", type=Path)
    parser.add_argument("--header", type=Path)
    args = parser.parse_args()
    if args.return_path is None:
        live_source_gate()
        print("READY_FAIL_CLOSED_AWAITING_NATIVE_UCRT_RETURN")
        return 0
    report = build(args.return_path)
    if not validate(report):
        raise RuntimeError("generated promotion table report failed validation")
    if args.write:
        args.write.write_bytes(canonical(report))
    if args.header:
        args.header.write_text(render_header(report))
    print(report["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
