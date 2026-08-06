#!/usr/bin/env python3
"""Compare complete actual-AEX setup writes with production setup semantics."""

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader

AEX = ROOT / "plugins_2025/OLMSmoother.aex"
AEX_SHA256 = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
ENTRY = 0x18000A2C0
GLOBAL_SETUP = 1
PARAMS_SETUP = 4
GLOBAL_HARNESS = ROOT / "tools/emulation/olmsmoother_v1_global_setup_production_harness_20260805.cpp"
PARAMS_HARNESS = ROOT / "tools/emulation/olmsmoother_v1_params_setup_production_harness_20260805.cpp"
RETAINED = ROOT / "refs/conformance/olmsmoother_v1_independent_binary_discriminator_full_20260730.json"
RETAINED_SHA256 = "3008b8239c48e56c6d0fb0aa707ef7e46df41d311c8f8aa710a79503e2d75735"
OUT = ROOT / "refs/conformance/olmsmoother_v1_setup_raw_actual_production_20260806.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_json(source: Path, output: Path) -> dict:
    subprocess.run([
        "clang++", "-std=c++17", "-I" + str(ROOT / "cli/OLMSmoother/shim"),
        str(source), "-o", str(output),
    ], cwd=ROOT, check=True, capture_output=True)
    return json.loads(subprocess.run([str(output)], check=True, capture_output=True,
                                     text=True).stdout)


def changed_spans(raw: bytes, fill: int) -> list[dict]:
    spans = []
    start = None
    for index, value in enumerate(raw + bytes((fill,))):
        changed = value != fill
        if changed and start is None:
            start = index
        elif not changed and start is not None:
            spans.append({"offset": start, "size": index - start,
                          "hex": raw[start:index].hex()})
            start = None
    return spans


def main() -> None:
    assert sha256(AEX) == AEX_SHA256
    assert sha256(RETAINED) == RETAINED_SHA256
    retained = json.loads(RETAINED.read_text())
    retained_setup = retained["setup"]["v1"]
    retained_names = [item["name"] for item in retained_setup["parameters"]]
    assert retained_names == ["Use Color Key", "Color Key", "Do Smooth Range"]

    loader = AexLoader(str(AEX), verbose=False, fast=True)
    in_data = loader.host_alloc(0x200, align=16)
    out_data = loader.host_alloc(0x300, align=16)
    loader.write_bytes(in_data, b"\0" * 0x200)

    # GLOBAL_SETUP writes into the real Windows PF_OutData offsets. Seed every
    # byte to prove the complete write footprint, not merely the three values.
    loader.write_bytes(out_data, b"\xCC" * 0x300)
    global_result = loader.call_function(
        ENTRY, [GLOBAL_SETUP, in_data, out_data, 0, 0], max_instructions=100000)
    actual_global_raw = loader.read_bytes(out_data, 0x194)
    expected_spans = [
        {"offset": 0, "size": 4, "hex": "00080900"},
        {"offset": 0x60, "size": 4, "hex": "40000002"},
        {"offset": 0x190, "size": 4, "hex": "00000008"},
    ]
    actual_spans = changed_spans(actual_global_raw, 0xCC)

    captured = []

    def add_param(ld: AexLoader, args: list[int]) -> int:
        captured.append(ld.read_bytes(args[2], 0xB0))
        return 0

    callback = loader.install_callback("olmsmoother_v1_add_param_raw", add_param)
    loader.write_bytes(in_data + 0x10, struct.pack("<Q", callback))
    loader.write_bytes(in_data + 0xB8, struct.pack("<Q", 0x12345678))
    loader.write_bytes(out_data, b"\xCC" * 0x300)
    params_result = loader.call_function(
        ENTRY, [PARAMS_SETUP, in_data, out_data, 0, 0], max_instructions=1000000)

    actual_headers = []
    normalized_raw = []
    for slot, raw in enumerate(captured, 1):
        item = bytearray(raw)
        # +0x40 is an AEX image pointer to the fixed empty description string.
        # Normalize only that relocation-bearing pointer; retain all other 168
        # bytes verbatim, including the complete parameter union.
        pointer = struct.unpack_from("<Q", item, 0x40)[0]
        item[0x40:0x48] = b"\0" * 8
        normalized_raw.append(bytes(item))
        actual_headers.append({
            "slot": slot,
            "disk_id": struct.unpack_from("<I", raw, 0)[0],
            "flags": struct.unpack_from("<I", raw, 4)[0],
            "ui_flags": struct.unpack_from("<I", raw, 8)[0],
            "param_type": struct.unpack_from("<I", raw, 0xC)[0],
            "description_pointer": hex(pointer),
            "normalized_raw_sha256": hashlib.sha256(item).hexdigest(),
            "normalized_raw_hex": item.hex(),
        })

    with tempfile.TemporaryDirectory(prefix="olmsmoother-v1-setup-raw-") as name:
        temporary = Path(name)
        production_global = compile_json(GLOBAL_HARNESS, temporary / "global")
        production_params = compile_json(PARAMS_HARNESS, temporary / "params")

    expected_global = {
        "error": 0, "my_version": 0x00090800,
        "out_flags": 0x02000040, "out_flags2": 0x08000000,
    }
    expected_headers = [
        {"slot": 1, "disk_id": 1, "flags": 0, "ui_flags": 0, "param_type": 4},
        {"slot": 2, "disk_id": 2, "flags": 0, "ui_flags": 0, "param_type": 5},
        {"slot": 3, "disk_id": 3, "flags": 0, "ui_flags": 0, "param_type": 1},
    ]
    observed_headers = [{key: item[key] for key in expected_headers[0]}
                        for item in actual_headers]
    production_header_semantics = [
        {"slot": index, "disk_id": item["disk_id"], "flags": item["flags"],
         "ui_flags": item["ui_flags"], "param_type": kind}
        for index, (item, kind) in enumerate(zip(
            production_params["parameters"], (4, 5, 1)), 1)
    ]
    gates = {
        "actual_global_return": global_result["rax"] == 0,
        "actual_global_complete_write_footprint": actual_spans == expected_spans,
        "production_global_exact": production_global == expected_global,
        "actual_params_return": params_result["rax"] == 0,
        "actual_params_count": len(captured) == 3,
        "actual_out_num_params": loader.read_bytes(out_data + 0x30, 4) == struct.pack("<I", 4),
        "actual_param_headers_exact": observed_headers == expected_headers,
        "production_param_headers_exact": production_header_semantics == expected_headers,
        "retained_names_and_types_exact": [
            (item["name"], item["param_type"])
            for item in retained_setup["parameters"]
        ] == [("Use Color Key", 4), ("Color Key", 5), ("Do Smooth Range", 1)],
    }
    report = {
        "schema_version": 1,
        "status": "exact" if all(gates.values()) else "fail",
        "scope": "OLMSmoother v1 actual-AEX complete GLOBAL_SETUP write footprint and complete normalized 0xb0 PARAMS_SETUP records, with production semantic comparison",
        "actual_aex_sha256": AEX_SHA256,
        "retained_name_fixture_sha256": RETAINED_SHA256,
        "gates": gates,
        "global_setup": {
            "actual_changed_spans": actual_spans,
            "raw_window_size": len(actual_global_raw),
            "production": production_global,
        },
        "params_setup": {
            "actual_records": actual_headers,
            "production": production_params,
            "advertised_num_params": 4,
            "retained_names": retained_names,
        },
        "claim_boundary": {
            "flags_and_ui_flags": "exact zero for all three public parameter records",
            "names": "only the three retained English strings are proven; no localization claim",
            "rendering": "not exercised",
            "ae_host_ui": "not exercised",
        },
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    assert report["status"] == "exact"


if __name__ == "__main__":
    main()
