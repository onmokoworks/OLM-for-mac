#!/usr/bin/env python3
"""Replay the preserved Mac-AE PF32 control through production RenderWorld."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from scripts.compare_float_exr import read_planes
from tools.emulation.olm_installed_identity import MANIFEST as IDENTITY_MANIFEST, verified_binary

SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
DEFAULT_RUN = Path("/tmp/olmradialblur_pf32_20260806.8xa7UB")
INPUT = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
MAPPING = ROOT / "refs/fixtures/olmradialblur_case0009_ae_control_u8_to_f32_20260806.json"
REPORT = ROOT / "refs/conformance/olmradialblur_case0009_pf32_ae_control_replay_20260806.json"
DIAGNOSTIC_REPORT = ROOT / "refs/conformance/olmradialblur_case0009_pf32_world_capture_result_20260806.json"
WIDTH, HEIGHT = 1920, 1080


def semantic(planes: dict[str, bytes], order: str) -> bytes:
    output = bytearray(WIDTH * HEIGHT * len(order) * 4)
    for pixel in range(WIDTH * HEIGHT):
        src = pixel * 4
        dst = pixel * len(order) * 4
        for channel, name in enumerate(order):
            output[dst + channel * 4:dst + channel * 4 + 4] = planes[name][src:src + 4]
    return bytes(output)


def compare_words(expected: bytes, actual: bytes) -> dict[str, object]:
    assert len(expected) == len(actual)
    different = 0
    first = None
    max_raw_delta = 0
    by_channel = {name: 0 for name in "RGBA"}
    raw_delta_counts: dict[str, int] = {}
    for offset in range(0, len(expected), 4):
        left = struct.unpack_from("<I", expected, offset)[0]
        right = struct.unpack_from("<I", actual, offset)[0]
        if left != right:
            different += 1
            by_channel["RGBA"[(offset // 4) % 4]] += 1
            if first is None:
                first = offset // 4
            delta = abs(left - right)
            max_raw_delta = max(max_raw_delta, delta)
            raw_delta_counts[str(delta)] = raw_delta_counts.get(str(delta), 0) + 1
    return {"different_words": different, "first_word": first,
            "different_words_by_channel": by_channel,
            "raw_u32_delta_counts": raw_delta_counts,
            "max_raw_u32_delta": max_raw_delta, "exact": different == 0}


def argb_to_rgba(raw: bytes) -> bytes:
    words = np.frombuffer(raw, dtype=np.uint8).reshape(HEIGHT, WIDTH, 4, 4)
    return np.ascontiguousarray(words[:, :, [1, 2, 3, 0], :]).tobytes()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", type=Path)
    parser.add_argument("--capture-dir", type=Path)
    args = parser.parse_args()
    fixture = json.loads(MAPPING.read_text(encoding="utf-8"))
    if hashlib.sha256(INPUT.read_bytes()).hexdigest() != fixture["source_png_sha256"]:
        raise AssertionError("pinned PNG identity drifted")
    mapping = base64.b64decode(fixture["mapping_f32_le_base64"], validate=True)
    if len(mapping) != 256 * 4:
        raise AssertionError("mapping cardinality drifted")
    png = np.asarray(Image.open(INPUT).convert("RGBA"), dtype=np.uint8)
    if png.shape != (HEIGHT, WIDTH, 4) or np.any(png[:, :, 3] != 255):
        raise AssertionError("opaque source contract drifted")
    control_argb = bytearray(WIDTH * HEIGHT * 16)
    flat = png.reshape(-1, 4)
    alpha_one = mapping[255 * 4:256 * 4]
    for pixel, rgba8 in enumerate(flat):
        base = pixel * 16
        control_argb[base:base + 4] = alpha_one
        for channel in range(3):
            value = int(rgba8[channel])
            control_argb[base + (channel + 1) * 4:base + (channel + 2) * 4] = mapping[value * 4:(value + 1) * 4]
    control_argb = bytes(control_argb)
    generated_control_rgba = argb_to_rgba(control_argb)
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="olmradial-pf32-control-replay-") as td_raw:
        td = Path(td_raw)
        input_path, output_path = td / "control.argb", td / "production.argb"
        input_path.write_bytes(control_argb)
        cpp, exe = td / "probe.cpp", td / "probe"
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <fstream>
#include <vector>
int main(int argc,char**argv){{constexpr int W={WIDTH},H={HEIGHT};
std::vector<PF_PixelFloat> input(W*H),output(W*H);
std::ifstream in(argv[1],std::ios::binary);in.read((char*)input.data(),input.size()*sizeof(PF_PixelFloat));if(!in)return 2;
PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)input.data();iw.rowbytes=W*sizeof(PF_PixelFloat);iw.width=W;iw.height=H;
ow.data=(PF_PixelPtr)output.data();ow.rowbytes=W*sizeof(PF_PixelFloat);ow.width=W;ow.height=H;
OLMRadialBlurInfo i{{}};i.blur_type=1;i.center_x=960;i.center_y=540;i.outer_strength=1717;i.outer_offset_mode=1;
i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=W;i.comp_height=H;
if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,32)!=PF_Err_NONE)return 3;
std::ofstream(argv[2],std::ios::binary).write((char*)output.data(),output.size()*sizeof(PF_PixelFloat));return 0;}}''', encoding="utf-8")
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        cmd = [os.environ.get("CXX", "clang++"), "-std=c++17", "-arch", "arm64", "-O2",
               "-fno-fast-math", "-ffp-contract=off", "-Wno-unused-function", "-Wno-unused-parameter",
               "-isysroot", sdk, "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
               "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"), "-ffunction-sections",
               "-fdata-sections", str(cpp), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            raise AssertionError(built.stderr)
        subprocess.run([str(exe), str(input_path), str(output_path)], cwd=ROOT, check=True)
        production_argb = output_path.read_bytes()

    # Convert production A,R,G,B memory into semantic R,G,B,A for a direct
    # raw-word comparison with the preserved effect EXR.
    production_rgba = argb_to_rgba(production_argb)
    replay_hash = hashlib.sha256(production_rgba).hexdigest()
    if replay_hash != "a0fe5f150e686aea4623ee22adc46898e7668639c0825b94390dfcc54437e510":
        raise AssertionError(f"portable production replay drifted: {replay_hash}")
    replay_array = np.frombuffer(production_rgba, dtype="<f4").reshape(HEIGHT, WIDTH, 4)
    premultiplied_array = replay_array.copy()
    premultiplied_array[:, :, :3] = np.float32(
        premultiplied_array[:, :, :3] * premultiplied_array[:, :, 3:4])
    premultiplied_rgba = premultiplied_array.tobytes()
    premultiplied_hash = hashlib.sha256(premultiplied_rgba).hexdigest()
    if premultiplied_hash != "d66dc120c1f67ea8631dc0fe43f877c51f8e6b5554eafd1c4cb34901ee7525f8":
        raise AssertionError(f"premultiplied output-module replay drifted: {premultiplied_hash}")
    optional = None
    if args.source_run is not None:
        control_planes, cw, ch = read_planes(args.source_run / "control.exr00000")
        effect_planes, ew, eh = read_planes(args.source_run / "effect_on.exr00000")
        if (cw, ch) != (WIDTH, HEIGHT) or (ew, eh) != (WIDTH, HEIGHT):
            raise AssertionError("preserved AE artifact dimensions drifted")
        observed_control_argb = semantic(control_planes, "ARGB")
        if observed_control_argb != control_argb:
            raise AssertionError("compact mapping does not regenerate preserved control exactly")
        uniqueness = {}
        for channel_index, name in enumerate("RGB"):
            words = np.frombuffer(control_planes[name], dtype="<u4").reshape(HEIGHT, WIDTH)
            channel = png[:, :, channel_index]
            missing = []
            ambiguous = []
            for value in range(256):
                observed = np.unique(words[channel == value])
                if observed.size == 0:
                    missing.append(value)
                elif observed.size != 1:
                    ambiguous.append(value)
            if missing or ambiguous:
                raise AssertionError(f"non-unique AE mapping {name}: missing={missing} ambiguous={ambiguous}")
            uniqueness[name] = {"observed_byte_values": 256, "ambiguous_values": 0}
        effect_rgba = semantic(effect_planes, "RGBA")
        comparison = compare_words(effect_rgba, bytes(production_rgba))
        if hashlib.sha256(effect_rgba).hexdigest() != "d66dc120c1f67ea8631dc0fe43f877c51f8e6b5554eafd1c4cb34901ee7525f8":
            raise AssertionError("preserved effect artifact identity drifted")
        if comparison["different_words"] != 80625 or comparison["max_raw_u32_delta"] != 3:
            raise AssertionError(f"control-replay discriminator drifted: {comparison}")
        premultiplied_comparison = compare_words(effect_rgba, premultiplied_rgba)
        if not premultiplied_comparison["exact"]:
            raise AssertionError(f"effect EXR is not exact premultiplied output: {premultiplied_comparison}")
        optional = {"source_run": str(args.source_run), "mapping_uniqueness": uniqueness,
                    "effect_semantic_rgba_sha256": hashlib.sha256(effect_rgba).hexdigest(),
                    "effect_comparison_before_output_module_premultiply": comparison,
                    "effect_comparison_after_output_module_premultiply": premultiplied_comparison}
    if args.capture_dir is not None:
        if optional is None:
            raise AssertionError("--capture-dir requires --source-run")
        def captured_semantic(stage: str) -> bytes:
            metadata = json.loads((args.capture_dir / f"{stage}.json").read_text(encoding="utf-8"))
            if metadata["width"] != WIDTH or metadata["height"] != HEIGHT or metadata["rowbytes"] < WIDTH * 16:
                raise AssertionError(f"invalid {stage} capture metadata")
            raw = np.memmap(args.capture_dir / f"{stage}.argb128.rows", dtype=np.uint8, mode="r",
                            shape=(HEIGHT, metadata["rowbytes"]))
            active = np.ascontiguousarray(raw[:, :WIDTH * 16]).reshape(HEIGHT, WIDTH, 4, 4)
            return np.ascontiguousarray(active[:, :, [1, 2, 3, 0], :]).tobytes()
        captured_input = captured_semantic("input")
        captured_output = captured_semantic("output")
        captured_checks = {
            "input_vs_control": compare_words(semantic(control_planes, "RGBA"), captured_input),
            "input_vs_compact_mapping": compare_words(generated_control_rgba, captured_input),
            "output_vs_local_renderworld": compare_words(bytes(production_rgba), captured_output),
            "output_vs_effect_before_premultiply": compare_words(effect_rgba, captured_output),
        }
        if not captured_checks["input_vs_control"]["exact"] or not captured_checks["output_vs_local_renderworld"]["exact"]:
            raise AssertionError(f"captured boundary mismatch: {captured_checks}")
        optional["capture_dir"] = str(args.capture_dir)
        optional["captured_world_checks"] = captured_checks
        ae_return = json.loads((args.source_run / "ae_return.json").read_text(encoding="utf-8"))
        _installed_binary, installed_row = verified_binary("OLMRadialBlur")
        diagnostic_result = {
            "kind": "olmradialblur_case0009_pf32_world_capture_result_20260806",
            "status": "output_module_premultiply_exact",
            "diagnostic_bundle_sha256": ae_return["plugin"]["sha256"],
            "normal_restored_bundle_sha256": installed_row["sha256"],
            "normal_restore_identity_manifest": str(IDENTITY_MANIFEST.relative_to(ROOT)),
            "normal_restore_identity_exact": True,
            "normal_restore_preflight": "all_10_installed_identities_exact; ae_not_running",
            "capture": {
                "input_raw_argb_rows_sha256": hashlib.sha256((args.capture_dir / "input.argb128.rows").read_bytes()).hexdigest(),
                "input_semantic_rgba_sha256": hashlib.sha256(captured_input).hexdigest(),
                "output_raw_argb_rows_sha256": hashlib.sha256((args.capture_dir / "output.argb128.rows").read_bytes()).hexdigest(),
                "output_semantic_rgba_sha256": hashlib.sha256(captured_output).hexdigest(),
            },
            "exr": {
                "control_file_sha256": hashlib.sha256((args.source_run / "control.exr00000").read_bytes()).hexdigest(),
                "control_semantic_rgba_sha256": hashlib.sha256(semantic(control_planes, "RGBA")).hexdigest(),
                "effect_file_sha256": hashlib.sha256((args.source_run / "effect_on.exr00000").read_bytes()).hexdigest(),
                "effect_semantic_rgba_sha256": hashlib.sha256(effect_rgba).hexdigest(),
            },
            "comparisons": {
                "captured_input_vs_control_exr": captured_checks["input_vs_control"],
                "captured_input_vs_compact_mapping": captured_checks["input_vs_compact_mapping"],
                "captured_output_vs_local_renderworld": captured_checks["output_vs_local_renderworld"],
                "captured_output_vs_effect_before_premultiply": captured_checks["output_vs_effect_before_premultiply"],
                "premultiplied_output_vs_effect": premultiplied_comparison,
            },
            "first_divergent_boundary": "AE Output Module Color: Premultiplied (Matted)",
            "exact_transform": "RGB=float32(RGB*alpha); alpha unchanged",
            "windows_ae_exact": False,
        }
        DIAGNOSTIC_REPORT.write_text(json.dumps(diagnostic_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = {
        "kind": "olmradialblur_case0009_pf32_ae_control_replay_20260806",
        "status": "portable_replay_exact",
        "dimensions": [WIDTH, HEIGHT],
        "input_contract": "pinned PNG regenerated through compact AE-control byte-to-float mapping into PF_PixelFloat ARGB",
        "compact_mapping_fixture": str(MAPPING.relative_to(ROOT)),
        "production_replay_semantic_rgba_sha256": replay_hash,
        "output_module_premultiplied_semantic_rgba_sha256": premultiplied_hash,
        "portable_output_module_transform": "RGB=float32(RGB*alpha), alpha unchanged",
        "optional_retained_artifact_verification": optional,
        "claim_boundary": {
            "ae_control_words_replayed": True,
            "portable_control_regeneration_exact": True,
            "production_replay_hash_pinned": True,
            "output_module_premultiply_reproduces_effect_hash": True,
            "production_renderworld_matches_effect_exr": False,
            "actual_ae_checkout_world_identical_to_control_exr": bool(
                optional and optional.get("captured_world_checks", {}).get("input_vs_control", {}).get("exact")),
            "windows_ae_exact": False,
        },
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
