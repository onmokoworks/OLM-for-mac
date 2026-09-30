#!/usr/bin/env python3
"""Independent amount-boundary witnesses for Thin metric hypotheses.

Tests integer-plane 255/256 boundaries and PF32 shape changes, not only +/-1.
No production source or public admission changes.
"""
from __future__ import annotations

import json
import math
import struct
import subprocess
import tempfile
from pathlib import Path

import probe_olmcolorkey_legal_composition_20261001 as base
import probe_olmcolorkey_composition_hypotheses_20261001 as hypotheses

ROOT = base.ROOT
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
MODES = [(amount, blur) for amount in (0, -1, 1, -4, 4, -255, 255, -256, 256) for blur in (0, 4)]
DEPTHS = ("PF8", "PF16", "PF32")


def compile_core(body: str) -> bytes:
    with tempfile.TemporaryDirectory(prefix="olmck_metric_boundary_") as raw:
        directory = Path(raw)
        modified = directory / "OLMColorKey.cpp"
        body = base.replace_once(body, '#include "OLMColorKey.h"',
                                 '#include "' + str(SOURCE.with_suffix(".h")) + '"')
        modified.write_text(body)
        saved = base.retained.mac_adapter.SOURCE
        try:
            base.retained.mac_adapter.SOURCE = modified
            base.retained.mac_adapter.compile_probe(directory)
        finally:
            base.retained.mac_adapter.SOURCE = saved
        main = base.retained.CUSTOM_MAIN
        main = base.replace_once(main, "const Mode modes[]={{0,0},{-4,0},{4,0},{0,4},{-4,4},{4,4}};",
                                 "const Mode modes[]={" + ",".join("{" + f"{a},{b}" + "}" for a, b in MODES) + "};")
        main = base.replace_once(main, "for(int replace: {0,1})for(Mode mode:modes)for(int depth: {8,16,32})",
                                 "for(int replace: {0})for(int distance: {1,2,3})for(Mode mode:modes)for(int depth: {8,16,32})")
        main = base.replace_once(main, "info.edge_thin_distance_type=2;", "info.edge_thin_distance_type=distance;")
        source = directory / "olmcolorkey_mac_smartrender_adapter_probe.cpp"
        source.write_text(base.replace_once(source.read_text(), "int main(){", "int legacy_main(){") + main)
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
        exe = directory / "boundary"
        subprocess.run(["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
                        "-ffp-contract=off", "-isysroot", sdk, "-I", str(directory), str(source),
                        "-framework", "Cocoa", "-o", str(exe)], capture_output=True, check=True)
        return subprocess.run([str(exe)], capture_output=True, check=True).stdout


def main() -> int:
    original = SOURCE.read_text()
    variants = hypotheses.kernel_variants(original)
    variants.pop("positive_typed_scale")
    candidates = {name: compile_core(body) for name, body in variants.items()}
    popup = base.popup_reader()
    probe = base.retained.actual_probe
    probe.WIDTH, probe.HEIGHT = base.retained.WIDTH, base.retained.HEIGHT
    probe.fixture = base.retained.fixture
    base.retained.CURRENT_REPLACE = False
    distance = 1

    def parameters(*values):
        payload = bytearray(base.retained.parameter_record(*values))
        struct.pack_into("<i", payload, 0x2C, distance)
        return bytes(payload)

    probe.parameter_record = parameters
    rows, offset = [], 0
    for distance in (1, 2, 3):
        for amount, blur in MODES:
            base.retained.CURRENT_MODE = {"thin": amount, "blur": blur}
            for depth in DEPTHS:
                probe.PIXEL_FORMAT = depth
                case = probe.execute_case(probe.AEX, True, blur, "single", 2, 2, 2)
                required = ("normal_return", "exact_dispatch_hits", "checkout_callbacks_exact", "output_padding_preserved")
                if not all(case["acceptance_gates"][k] for k in required):
                    raise RuntimeError("actual AEX execution/padding failed")
                actual = b"".join(bytes.fromhex(r) + b"\xcc" * 8 for r in case["captures"]["output_active_rows_hex"])
                actual_sha = base.sha(actual)
                hashes = {name: base.sha(raw[offset:offset + len(actual)]) for name, raw in candidates.items()}
                offset += len(actual)
                # With no Blur, the worker's allocated float world retains its
                # native Thin distance plane. Preserve f32 bits, not decimal
                # tolerance, while excluding other typed temporary worlds.
                planes = []
                if blur == 0 and amount != 0:
                    for world in case["execution"]["temporary_worlds"]:
                        if world["pixel_format"] == "0x32336561":
                            values = world["first_channel_f32"]
                            if not all(math.isfinite(v) for v in values):
                                raise RuntimeError("nonfinite native distance plane")
                            words = sorted({struct.pack("<f", v).hex() for v in values})
                            planes.append({"sha256": world["sha256"], "distinct_first_channel_f32_le_hex": words})
                rows.append({"type": distance, "thin": amount, "blur": blur, "depth": depth,
                             "actual_sha256": actual_sha, "candidate_sha256": hashes,
                             "exact": {name: h == actual_sha for name, h in hashes.items()},
                             "native_float_planes": planes})
            print(f"measured type={distance} thin={amount} blur={blur}", flush=True)
    if any(offset != len(raw) for raw in candidates.values()):
        raise RuntimeError("candidate output size mismatch")
    summary = {name: {"exact": sum(r["exact"][name] for r in rows),
                      "regressions_against_current": sum(r["exact"]["current"] and not r["exact"][name] for r in rows)}
               for name in candidates}
    report = {"schema": "olmcolorkey.thin-metric-boundaries/1", "date": "2026-10-01",
              "status": "measured", "case_count": len(rows), "summary": summary,
              "source_sha256": base.sha(SOURCE.read_bytes()), "aex_sha256": probe.AEX_SHA256,
              "probe_sha256": base.sha(Path(__file__).read_bytes()), "popup_reader": popup,
              "dependency_sha256": {str(Path(p).relative_to(ROOT)): base.sha(Path(p).read_bytes())
                                    for p in (base.__file__, hypotheses.__file__, base.retained.__file__,
                                              probe.__file__, base.retained.mac_adapter.__file__)},
              "cases": rows, "scope": "Actual typed AEX worker/declared materializer record versus temporary Mac core variants; opaque 13x11 two-key source; no public owner/native AE/general-input claim"}
    (ROOT / "reports/colorkey_thin_metric_boundaries_20261001.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
