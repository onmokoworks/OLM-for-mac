#!/usr/bin/env python3
"""Measure legal Thin popup composition without widening production admission.

Runs the actual AEX popup reader and typed worker locally. The worker's full
parameter materializer remains replaced by the existing pinned record harness;
this is explicitly not an exported-owner or native AE conformance claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RSP

import test_olmcolorkey_replace_edge_composition_actual_aex_20260811 as retained
from aex_loader import AexLoader

ROOT = Path(__file__).resolve().parents[2]
MODES = (
    {"name": "none", "thin": 0, "blur": 0.0},
    {"name": "thin_negative1", "thin": -1, "blur": 0.0},
    {"name": "thin_positive1", "thin": 1, "blur": 0.0},
    {"name": "blur4", "thin": 0, "blur": 4.0},
    {"name": "thin_negative1_blur4", "thin": -1, "blur": 4.0},
    {"name": "thin_positive1_blur4", "thin": 1, "blur": 4.0},
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"retained harness shape drift: {old}")
    return text.replace(old, new, 1)


def popup_reader() -> list[dict]:
    """Execute FUN_18000e050, including real checkout/copy/checkin code.

    Disk-ID lookup, output +0x38, and six-argument checkout ABI are grounded
    in the checked-in disassembly, not in the old zero-initialized record.
    """
    probe = retained.actual_probe
    if sha(probe.AEX.read_bytes()) != probe.AEX_SHA256:
        raise RuntimeError("AEX hash drift")
    ld = AexLoader(str(probe.AEX), verbose=False, fast=False)
    mapping = ld.host_alloc(0x388)
    ld.write_bytes(mapping, b"\xff" * 0x388)
    ld.write_bytes(mapping + 8, struct.pack("<i", 0x0E))
    context = ld.host_alloc(0x200)
    ld.write_bytes(context, b"\0" * 0x200)
    output = ld.host_alloc(4)
    events = []
    current = 0

    def checkout(loader, args):
        rsp = loader.uc.reg_read(UC_X86_REG_RSP)
        param = struct.unpack("<Q", loader.read_bytes(rsp + 0x30, 8))[0]
        if args[1] != 0:
            raise RuntimeError("disk ID 0x0e failed to resolve to checkout index 0")
        loader.write_bytes(param + 0x38, struct.pack("<i", current))
        events.append({"event": "checkout", "index": args[1], "value": current})
        return 0

    def checkin(loader, args):
        events.append({"event": "checkin"})
        return 0

    ld.write_bytes(context, struct.pack("<2Q", ld.install_callback("checkout", checkout),
                                       ld.install_callback("checkin", checkin)))
    rows = []
    for current in (1, 2, 3):
        events.clear()
        ld.write_bytes(output, b"\xa5" * 4)
        execution = ld.call_function(0x18000E050,
                                     int_args=[mapping, context, 0x0E, output],
                                     max_instructions=10000)
        observed = struct.unpack("<i", ld.read_bytes(output, 4))[0]
        if execution["instructions"] >= 10000 or observed != current or len(events) != 2:
            raise RuntimeError(f"popup reader failed: {execution}, {observed}, {events}")
        rows.append({"public_value": current, "observed_internal_value": observed,
                     "events": list(events)})
    return rows


def production(depths: tuple[str, ...]) -> bytes:
    depth_numbers = {"PF8": 8, "PF16": 16, "PF32": 32}
    main = retained.CUSTOM_MAIN
    main = replace_once(main, "const Mode modes[]={{0,0},{-4,0},{4,0},{0,4},{-4,4},{4,4}};",
                        "const Mode modes[]={{0,0},{-1,0},{1,0},{0,4},{-1,4},{1,4}};")
    main = replace_once(main, "for(int replace: {0,1})for(Mode mode:modes)for(int depth: {8,16,32})",
                        "for(int replace: {0,1})for(int distance: {1,2,3})for(Mode mode:modes)for(int depth: {" +
                        ",".join(str(depth_numbers[d]) for d in depths) + "})")
    main = replace_once(main, "info.edge_thin_distance_type=2;", "info.edge_thin_distance_type=distance;")
    with tempfile.TemporaryDirectory(prefix="olmck_legal_comp_") as raw:
        directory = Path(raw)
        retained.mac_adapter.compile_probe(directory)
        source = directory / "olmcolorkey_mac_smartrender_adapter_probe.cpp"
        source.write_text(replace_once(source.read_text(), "int main(){", "int legacy_main(){") + main)
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
        exe = directory / "composition"
        subprocess.run(["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
                        "-ffp-contract=off", "-isysroot", sdk, "-I", str(directory), str(source),
                        "-framework", "Cocoa", "-o", str(exe)], check=True, capture_output=True)
        return subprocess.run([str(exe)], check=True, capture_output=True).stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=ROOT / "reports/colorkey_legal_composition_20261001.json")
    parser.add_argument("--all-depths", action="store_true")
    parser.add_argument("--popup-only", action="store_true")
    args = parser.parse_args()
    popup = popup_reader()
    if args.popup_only:
        print(json.dumps(popup))
        return 0
    depths = ("PF8", "PF16", "PF32") if args.all_depths else ("PF8",)
    candidate = production(depths)
    probe = retained.actual_probe
    probe.WIDTH, probe.HEIGHT = retained.WIDTH, retained.HEIGHT
    probe.fixture = retained.fixture
    distance = 1

    def parameters(*values):
        payload = bytearray(retained.parameter_record(*values))
        struct.pack_into("<i", payload, 0x2C, distance)
        return bytes(payload)

    probe.parameter_record = parameters
    rows, offset, outputs = [], 0, {}
    for replace in (False, True):
        retained.CURRENT_REPLACE = replace
        for distance in (1, 2, 3):
            for mode in MODES:
                retained.CURRENT_MODE = mode
                for depth in depths:
                    probe.PIXEL_FORMAT = depth
                    case = probe.execute_case(probe.AEX, True, mode["blur"], "single", 2, 2, 2)
                    # Retained helper gates also assume a single keyed pixel
                    # and no Thin stage. Those assertions do not describe this
                    # multi-key composition fixture. Execution/padding gates
                    # still apply and must never be suppressed.
                    required = ("normal_return", "exact_dispatch_hits", "checkout_callbacks_exact",
                                "output_padding_preserved", "direct_actual_pixel_callback_normal_returns",
                                "direct_actual_final_pixel_callback_normal_returns")
                    failed = [name for name in required if not case["acceptance_gates"][name]]
                    if failed:
                        raise RuntimeError(f"AEX execution gates failed: {failed}")
                    pb = retained.FORMATS[depth]
                    actual = b"".join(bytes.fromhex(r) + b"\xcc" * retained.PADDING
                                      for r in case["captures"]["output_active_rows_hex"])
                    expected = candidate[offset:offset + len(actual)]
                    offset += len(actual)
                    if len(expected) != len(actual):
                        raise RuntimeError("production output truncated")
                    different = [i for i, (a, b) in enumerate(zip(actual, expected)) if a != b]
                    row = {"replace": replace, "thin_distance_type": distance, "mode": mode,
                           "depth": depth, "exact": not different, "different_bytes": len(different),
                           "first_different_byte": different[0] if different else None,
                           "first_actual_byte": actual[different[0]] if different else None,
                           "first_production_byte": expected[different[0]] if different else None,
                           "actual_sha256": sha(actual), "production_sha256": sha(expected),
                           "actual_alpha_sha256": sha(retained.alpha_plane(actual, pb)),
                           "production_alpha_sha256": sha(retained.alpha_plane(expected, pb)),
                           "execution_gates": {name: case["acceptance_gates"][name] for name in required},
                           "worker_hits": case["execution"]["hits"]}
                    outputs[(replace, distance, mode["name"], depth)] = actual
                    rows.append(row)
                    print(json.dumps({k: row[k] for k in ("replace", "thin_distance_type", "mode", "depth", "exact", "different_bytes")}), flush=True)
    if offset != len(candidate):
        raise RuntimeError("unexpected production output tail")
    distinguish = []
    for replace in (False, True):
        for mode in MODES:
            for depth in depths:
                hashes = [sha(outputs[(replace, d, mode["name"], depth)]) for d in (1, 2, 3)]
                distinguish.append({"replace": replace, "mode": mode["name"], "depth": depth,
                                    "distinct_distance_outputs": len(set(hashes)), "hashes": hashes})
    report = {"schema": "olmcolorkey.legal-composition-diagnostic/1", "date": "2026-10-01",
              "status": "measured", "actual_aex_sha256": probe.AEX_SHA256,
              "production_source_sha256": sha((ROOT / "mac/OLMColorKey/OLMColorKey.cpp").read_bytes()),
              "probe_sha256": sha(Path(__file__).read_bytes()), "popup_reader": popup,
              "dependency_sha256": {str(Path(p).relative_to(ROOT)): sha(Path(p).read_bytes())
                                    for p in (retained.__file__, retained.actual_probe.__file__,
                                              retained.mac_adapter.__file__, ROOT / "tools/emulation/aex_loader.py")},
              "fixture": {"width": retained.WIDTH, "height": retained.HEIGHT, "padding": retained.PADDING},
              "case_count": len(rows), "exact_count": sum(r["exact"] for r in rows), "cases": rows,
              "distance_distinguishability": distinguish,
              "scope": "Actual AEX popup reader plus typed worker versus current Mac RenderWorldDirect; full parameter materializer replaced, Mac public admission bypassed; no native AE or exported-owner claim"}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "measured", "cases": len(rows), "exact": report["exact_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
