#!/usr/bin/env python3
"""Compare the retained natural AEX c280/cce0 boundary with the Mac helper."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NATURAL = ROOT / "tools/emulation/run_olmsmoother2_case0012_natural_post_f130_20260718.py"
ADAPTER = ROOT / "tools/emulation/olmsmoother2_case0012_c280_cce0_mac_helper_adapter_20260718.cpp"
MAC_SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
EXPECTED_AEX = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"


def compile_adapter(path: Path) -> None:
    command = [
        "clang++", "-std=c++17", "-O2", "-Icli/OLMSmoother2/shim",
        "-Imac/OLMSmoother2/Mac", str(ADAPTER), "-o", str(path),
    ]
    subprocess.run(command, cwd=ROOT, check=True)


def run(output_json: Path, output_md: Path) -> int:
    import sys
    sys.path.insert(0, str(ROOT / "tools" / "emulation"))
    import run_olmsmoother2_case0012_natural_post_f130_20260718 as natural

    if hashlib.sha256(natural.AEX_PATH.read_bytes()).hexdigest() != EXPECTED_AEX:
        raise RuntimeError("FAIL CLOSED: current AEX hash drift")

    # Reproduce the natural chain, retaining the exact source and generated
    # class plane that feed the actual AEX cce0 call.
    params = natural.read_case_parameters()
    loader = natural.AexLoader(str(natural.AEX_PATH), verbose=False, fast=False)
    loader.register_libm_impls(max_threads=1)
    smoother = natural.SmootherStruct(loader, natural.CROP_SIZE, natural.CROP_SIZE)
    natural.build_host_adapted_source(loader, smoother)
    vcomp = natural.SerialVcomp(loader)
    width = natural.alloc_i32(loader, natural.CROP_SIZE)
    left = natural.alloc_i32(loader, 0)
    height = natural.alloc_i32(loader, natural.CROP_SIZE)
    top = natural.alloc_i32(loader, 0)
    source_desc = loader.bump_alloc(24, align=16)
    loader.write_bytes(source_desc, struct.pack("<QiiQ", smoother.src_base, 16, 16, smoother.src_stride))
    key = loader.bump_alloc(16, align=16)
    loader.write_bytes(key, struct.pack("<4f", *params["Color Key"]))
    loader.call_function(natural.FUN_KEY_REMOVE, int_args=[width, left, height, top, source_desc, key], max_instructions=5_000_000)
    gamma_context = loader.bump_alloc(8, align=8)
    loader.write_bytes(gamma_context, b"\x00" * 8)
    loader.call_function(natural.FUN_SRGB_DECODE, int_args=[width, left, height, top, source_desc, gamma_context], max_instructions=10_000_000)
    source_plane, class_plane, rectangle, class_config = natural.install_descriptors(loader, smoother, int(params["Smooth Range"]))
    loader.call_function(natural.FUN_ADA0, int_args=[source_plane, class_plane, rectangle, class_config], max_instructions=20_000_000)

    pixels = loader.read_bytes(smoother.src_base, 16 * 16 * 16)
    classes = loader.read_bytes(smoother.class_base, 16 * 16 * 4)
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_c280_cce0_20260718_") as temp:
        temp_path = Path(temp)
        source_path = temp_path / "source_f32.bin"
        class_path = temp_path / "class_u8.bin"
        binary = temp_path / "mac_helper_boundary"
        source_path.write_bytes(pixels)
        class_path.write_bytes(classes)
        compile_adapter(binary)
        mac = json.loads(subprocess.check_output([str(binary), str(source_path), str(class_path)], text=True))

    actual = natural.run()
    actual_vertices = actual["events"]["cce0_input"]["vertices"]
    mac_vertices = mac["vertices"]
    comparisons = []
    channel_index = {"r": 0, "g": 1, "b": 2, "a": 3}
    for stage, left_values, right_values in (
        ("c280_or_post_f130", actual["events"]["post_f130_post_boost"]["vertices"], mac_vertices),
        ("cce0_input", actual_vertices, mac_vertices),
    ):
        for vi, (a, m) in enumerate(zip(left_values, right_values)):
            for label, av, mv in [("r", a["rgba"][0], m["rgba"][0]), ("g", a["rgba"][1], m["rgba"][1]), ("b", a["rgba"][2], m["rgba"][2]), ("a", a["rgba"][3], m["rgba"][3]), ("weight", a["weight"], m["weight"])]:
                mac_u32 = m["rgba_u32"][channel_index[label]] if label in channel_index else m["weight_u32"]
                actual_u32 = a["rgba_u32"][channel_index[label]] if label in channel_index else a["weight_u32"]
                comparisons.append({"stage": stage, "vertex": vi, "field": label, "actual": av, "mac": mv, "actual_u32": actual_u32, "mac_u32": mac_u32, "equal": actual_u32 == mac_u32})
    first = next((item for item in comparisons if not item["equal"]), None)
    verdict = "PASS_NO_C280_CCE0_MAC_HELPER_DIVERGENCE" if first is None else "DIVERGENCE_AT_FIRST_C280_CCE0_FLOAT32_WORD"
    report = {
        "schema": 1, "verdict": verdict,
        "scope": "retained case0012 natural checked-in AEX c280/cce0 input versus current Mac build_polygon helper",
        "binary": {"path": str(natural.AEX_PATH.relative_to(ROOT)), "sha256": EXPECTED_AEX},
        "mac_source": {"path": str(MAC_SOURCE.relative_to(ROOT)), "sha256": hashlib.sha256(MAC_SOURCE.read_bytes()).hexdigest()},
        "boundary": {"descriptor": actual["events"]["descriptor"]["host_translated"], "dispatch_key": actual["events"]["descriptor"]["key"], "actual_chain": actual["natural_chain"], "actual_cce0_input_count": len(actual_vertices), "mac_helper_count": mac["count"]},
        "actual_aex": {"post_f130_post_boost": actual["events"]["post_f130_post_boost"], "cce0_input": actual["events"]["cce0_input"], "cce0_output": actual["cce0_output"]},
        "mac_helper": mac,
        "comparisons": comparisons,
        "first_divergence": first,
        "claims_not_made": ["No Windows/After Effects host execution claim", "No production edit", "No writer or exported-byte attribution"],
    }
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# OLMSmoother2 case0012 c280/cce0 Mac-helper boundary - 2026-07-18", "", f"- Verdict: `{verdict}`", "", "## Boundary", "", f"- Actual-AEX descriptor: `{report['boundary']['descriptor']}`; dispatch key `{report['boundary']['dispatch_key']}`.", f"- Actual AEX natural chain reaches `{report['boundary']['actual_cce0_input_count']}` cce0 input vertices; the Mac helper produces `{report['boundary']['mac_helper_count']}`.", f"- First divergence: `{first}`." if first else "- First divergence: none; all compared float32 words match.", "", "## Interpretation", "", "This comparison begins after the byte-exact ADA0 worker boundary and stops at the polygon/cce0 float32 boundary. It does not authorize a production edit unless a differing word is independently confirmed as the first divergence in the retained chain.", "", "## Claims Not Made", "", "- No Windows/After Effects host execution claim.", "- No production edit.", "- No writer or exported-byte attribution.", ""]
    output_md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "first_divergence": first}, indent=2))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.output_json, args.output_md))
