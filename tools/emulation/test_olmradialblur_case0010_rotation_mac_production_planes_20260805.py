#!/usr/bin/env python3
"""Compare the Mac production Rotation path with retained case_0010 AEX planes."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
INPUT = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0010_before_effects.png"
FIXTURE = ROOT / "refs/fixtures/olmradialblur_case0010_rotation_full_planes_20260805"
FULL_PF8_FIXTURE = FIXTURE / "post_worker_full_pf8_argb.bin.zlib"
FULL_PF8_REPORT = ROOT / "refs/conformance/olmradialblur_case0010_full_pf8_actual_aex_20260805.json"
EXPECTED_FULL_PF8_ZLIB_SHA256 = "b18b2b11e627db82bc79365196a581e01198739fd7708da6af279ef3e2b9e2f1"
EXPECTED_FULL_PF8_RAW_SHA256 = "cb39306e0e340bfa121e5ea55c9e1b43f87696237b4d6c855a47ce09dba188fc"
REPORT = ROOT / "refs/conformance/olmradialblur_case0010_rotation_mac_production_planes_20260805.json"
ACTUAL_AEX_WRITEBACK = ROOT / "refs/conformance/olmradialblur_case0010_pf8_writeback_actual_aex_20260805.json"
WIDTH, HEIGHT = 1920, 1080
POLAR_WIDTH, POLAR_HEIGHT = 1800, 1104
CELLS = POLAR_WIDTH * POLAR_HEIGHT
FLOATS = CELLS * 4


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads((FIXTURE / "manifest.json").read_text())
    full_pf8_report = json.loads(FULL_PF8_REPORT.read_text())
    full_pf8_fixture_identity = {
        "compressed_sha256_exact": sha256(FULL_PF8_FIXTURE) == EXPECTED_FULL_PF8_ZLIB_SHA256,
        "report_status_exact": full_pf8_report.get("status") == "exact",
        "report_raw_sha256_exact": full_pf8_report.get("frame", {}).get("raw_sha256") == EXPECTED_FULL_PF8_RAW_SHA256,
        "report_zlib_sha256_exact": full_pf8_report.get("frame", {}).get("zlib_sha256") == EXPECTED_FULL_PF8_ZLIB_SHA256,
        "report_fixture_path_exact": full_pf8_report.get("frame", {}).get("zlib_path") == str(FULL_PF8_FIXTURE.relative_to(ROOT)),
    }
    if not all(full_pf8_fixture_identity.values()):
        raise AssertionError(f"full PF8 fixture identity failed: {full_pf8_fixture_identity}")
    actual_aex_writeback = json.loads(ACTUAL_AEX_WRITEBACK.read_text())
    actual_identity = actual_aex_writeback["identity"]
    identity_paths = {
        "aex": Path(actual_identity["aex_path"]),
        "input": Path(actual_identity["input_path"]),
        "manifest": Path(actual_identity["manifest_path"]),
    }
    actual_aex_identity_checks = {
        "aex_sha256": identity_paths["aex"].is_file() and sha256(identity_paths["aex"]) == actual_identity["aex_sha256"],
        "input_sha256": identity_paths["input"].resolve() == INPUT.resolve() and sha256(INPUT) == actual_identity["input_sha256"],
        "manifest_sha256": identity_paths["manifest"].is_file() and sha256(identity_paths["manifest"]) == actual_identity["manifest_sha256"],
        "scope_case": actual_aex_writeback.get("scope", {}).get("case_id") == "case_0010",
        "scope_pixel_format": actual_aex_writeback.get("scope", {}).get("pixel_format") == "PF8 ARGB",
    }
    partial_calls = actual_aex_writeback.get("sampler_calls", [])
    partial_by_xy = {tuple(call["xy"]): call for call in partial_calls}
    partial_sampler_available = set(partial_by_xy) == {(1612, 6), (1614, 6)}
    stages = {stage["stage"]: stage for stage in manifest["stages"]}
    expected = {
        "polar": stages["pre_scatter"]["planes"]["normalized_or_polar_rgba"]["raw_sha256"],
        "eligibility": stages["post_scatter_pre_gather"]["planes"]["eligibility_mask"]["raw_sha256"],
        "source_scalar": stages["pre_scatter"]["planes"]["slot_0x10"]["raw_sha256"],
        "accum": stages["post_normalize"]["planes"]["accum_rgba"]["raw_sha256"],
        "max_alpha": stages["post_normalize"]["planes"]["max_alpha"]["raw_sha256"],
        "normalized": stages["post_normalize"]["planes"]["normalized_or_polar_rgba"]["raw_sha256"],
    }
    expected_locations = {
        "polar": ("pre_scatter", "normalized_or_polar_rgba"),
        "eligibility": ("post_scatter_pre_gather", "eligibility_mask"),
        "source_scalar": ("pre_scatter", "slot_0x10"),
        "accum": ("post_normalize", "accum_rgba"),
        "max_alpha": ("post_normalize", "max_alpha"),
        "normalized": ("post_normalize", "normalized_or_polar_rgba"),
    }
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="olmradialblur_rotation_production_") as raw_temp:
        temp = Path(raw_temp)
        input_path = temp / "input.argb8"
        rgba = np.asarray(Image.open(INPUT).convert("RGBA"), dtype=np.uint8)
        rgba[:, :, [3, 0, 1, 2]].copy().tofile(input_path)
        probe = temp / "probe.cpp"
        binary = temp / "probe"
        probe.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <fstream>
#include <limits>
#include <vector>
int main(int argc, char **argv) {{
  if (argc != 10) return 2;
  if (RadialCVTTSS2SI(-1.875f) != -1 ||
      RadialCVTTSS2SI(std::numeric_limits<float>::quiet_NaN()) != INT32_MIN ||
      RadialCVTTSS2SI(std::numeric_limits<float>::infinity()) != INT32_MIN ||
      RadialCVTTSS2SI(2147483648.0f) != INT32_MIN) return 6;
  constexpr int W={WIDTH}, H={HEIGHT}, CELLS={CELLS}, FLOATS={FLOATS};
  std::vector<PF_Pixel8> input(W*H), output(W*H);
  std::vector<float> polar(FLOATS), scalar(CELLS), accum(FLOATS), maximum(CELLS), normalized(FLOATS);
  std::vector<A_u_char> eligibility(CELLS);
  std::ifstream in(argv[1], std::ios::binary);
  in.read(reinterpret_cast<char *>(input.data()), input.size()*sizeof(PF_Pixel8));
  if (!in || in.gcount() != static_cast<std::streamsize>(input.size()*sizeof(PF_Pixel8))) return 3;
  PF_EffectWorld iw{{}}, ow{{}};
  iw.data=(PF_PixelPtr)input.data(); iw.rowbytes=W*sizeof(PF_Pixel8); iw.width=W; iw.height=H;
  iw.extent_hint={{0,0,W,H}}; ow.data=(PF_PixelPtr)output.data(); ow.rowbytes=W*sizeof(PF_Pixel8);
  ow.width=W; ow.height=H; ow.extent_hint={{0,0,W,H}};
  OLMRadialBlurInfo info{{}}; info.blur_type=2; info.center_x=960; info.center_y=540;
  info.outer_strength=4; info.outer_offset_mode=1; info.inner_offset_mode=1;
  info.repeat_border=TRUE; info.ratio=1; info.quality=5; info.brightness_gain=1;
  info.noise_type=1; info.seed=1; info.thickness=10; info.comp_width=W; info.comp_height=H;
  RadialBlurTestRotationCapture capture{{}};
  capture.polar_rgba=polar.data(); capture.eligibility=eligibility.data();
  capture.source_scalar=scalar.data(); capture.accum_rgba=accum.data();
  capture.max_alpha=maximum.data(); capture.normalized_rgba=normalized.data();
  capture.capacity_cells=CELLS;
  const PF_Err err=OLMRadialBlurTestRenderRotation8AndCapture(&iw,&ow,&info,&capture);
  if (err != PF_Err_NONE || capture.written_cells != CELLS ||
      capture.width != {POLAR_WIDTH} || capture.height != {POLAR_HEIGHT}) return 4;
  std::ofstream(argv[2],std::ios::binary).write(reinterpret_cast<char *>(polar.data()),polar.size()*sizeof(float));
  std::ofstream(argv[3],std::ios::binary).write(reinterpret_cast<char *>(eligibility.data()),eligibility.size());
  std::ofstream(argv[4],std::ios::binary).write(reinterpret_cast<char *>(scalar.data()),scalar.size()*sizeof(float));
  std::ofstream(argv[5],std::ios::binary).write(reinterpret_cast<char *>(accum.data()),accum.size()*sizeof(float));
  std::ofstream(argv[6],std::ios::binary).write(reinterpret_cast<char *>(maximum.data()),maximum.size()*sizeof(float));
  std::ofstream(argv[7],std::ios::binary).write(reinterpret_cast<char *>(normalized.data()),normalized.size()*sizeof(float));
  std::ofstream(argv[8],std::ios::binary).write(reinterpret_cast<char *>(output.data()),output.size()*sizeof(PF_Pixel8));
  std::ofstream witness(argv[9],std::ios::binary);
  witness.write(reinterpret_cast<char *>(capture.inverse_coordinates),sizeof(capture.inverse_coordinates));
  witness.write(reinterpret_cast<char *>(capture.inverse_rgba),sizeof(capture.inverse_rgba));
  witness.write(reinterpret_cast<char *>(capture.packer_rgba),sizeof(capture.packer_rgba));
  witness.write(reinterpret_cast<char *>(capture.packed_argb),sizeof(capture.packed_argb));
  witness.write(reinterpret_cast<char *>(&capture.inverse_witness_mask),sizeof(capture.inverse_witness_mask));
  witness.write(reinterpret_cast<char *>(capture.residual_coordinates),sizeof(capture.residual_coordinates));
  witness.write(reinterpret_cast<char *>(capture.residual_angle_raw),sizeof(capture.residual_angle_raw));
  witness.write(reinterpret_cast<char *>(capture.residual_rgba),sizeof(capture.residual_rgba));
  witness.write(reinterpret_cast<char *>(&capture.residual_witness_mask),sizeof(capture.residual_witness_mask));
  if (!witness || capture.inverse_witness_mask != 3 || capture.residual_witness_mask != 7) return 5;
  return 0;
}}
''', encoding="utf-8")
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
        command = [os.environ.get("CXX", "clang++"), "-std=c++17", "-arch", "arm64", "-O2",
                   "-fno-fast-math", "-ffp-contract=off", "-Wno-unused-function", "-Wno-unused-parameter",
                   "-isysroot", sdk, "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
                   "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
                   "-ffunction-sections", "-fdata-sections", str(probe), "-Wl,-dead_strip",
                   "-framework", "Cocoa", "-o", str(binary)]
        build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise AssertionError(build.stderr)
        paths = {name: temp / f"{name}.bin" for name in expected}
        output_path = temp / "output.argb8"
        witness_path = temp / "inverse_writer_witness.bin"
        run = subprocess.run([str(binary), str(input_path), *(str(paths[name]) for name in expected),
                              str(output_path), str(witness_path)], cwd=ROOT, capture_output=True, text=True)
        if run.returncode:
            raise AssertionError(f"probe failed rc={run.returncode}\n{run.stdout}{run.stderr}")
        actual = {name: sha256(path) for name, path in paths.items()}
        matches = {name: actual[name] == expected[name] for name in expected}
        differences = {}
        for name, path in paths.items():
            stage, plane = expected_locations[name]
            metadata = stages[stage]["planes"][plane]
            expected_raw = zlib.decompress((FIXTURE / metadata["path"]).read_bytes())
            actual_raw = path.read_bytes()
            if name == "eligibility":
                left = np.frombuffer(actual_raw, dtype=np.uint8)
                right = np.frombuffer(expected_raw, dtype=np.uint8)
            else:
                left = np.frombuffer(actual_raw, dtype="<u4")
                right = np.frombuffer(expected_raw, dtype="<u4")
            different = np.flatnonzero(left != right)
            differences[name] = {
                "different_values": int(different.size),
                "different_mod4": {
                    str(lane): int(np.count_nonzero((different % 4) == lane)) for lane in range(4)
                } if name in {"polar", "accum", "normalized"} else None,
                "first_different": int(different[0]) if different.size else None,
            }
        output_argb = np.fromfile(output_path, dtype=np.uint8).reshape(HEIGHT, WIDTH, 4)
        expected_output_raw = zlib.decompress(FULL_PF8_FIXTURE.read_bytes())
        if hashlib.sha256(expected_output_raw).hexdigest() != EXPECTED_FULL_PF8_RAW_SHA256:
            raise AssertionError("full PF8 raw fixture SHA256 mismatch")
        actual_output_raw = output_path.read_bytes()
        if len(expected_output_raw) != WIDTH * HEIGHT * 4:
            raise AssertionError(f"unexpected full PF8 fixture byte count: {len(expected_output_raw)}")
        expected_output_argb = np.frombuffer(expected_output_raw, dtype=np.uint8).reshape(HEIGHT, WIDTH, 4)
        output_different_channels = output_argb != expected_output_argb
        output_delta = np.abs(output_argb.astype(np.int16) - expected_output_argb.astype(np.int16))
        different_yx = np.argwhere(np.any(output_different_channels, axis=2))
        full_output = {
            "expected_raw_sha256": hashlib.sha256(expected_output_raw).hexdigest(),
            "actual_raw_sha256": hashlib.sha256(actual_output_raw).hexdigest(),
            "exact": actual_output_raw == expected_output_raw,
            "different_pixels": int(np.count_nonzero(np.any(output_different_channels, axis=2))),
            "different_channels_argb": [
                int(np.count_nonzero(output_different_channels[:, :, channel])) for channel in range(4)
            ],
            "maximum_absolute_difference": int(output_delta.max()),
            "first_differences": [
                {
                    "xy": [int(x), int(y)],
                    "expected_argb": expected_output_argb[y, x].tolist(),
                    "actual_argb": output_argb[y, x].tolist(),
                }
                for y, x in different_yx[:32]
            ],
        }
        witness_raw = witness_path.read_bytes()
        if len(witness_raw) != 174:
            raise AssertionError(f"unexpected witness byte count: {len(witness_raw)}")
        inverse_coordinates = struct.unpack_from("<4f", witness_raw, 0)
        inverse_rgba = struct.unpack_from("<8f", witness_raw, 16)
        packer_rgba = struct.unpack_from("<8f", witness_raw, 48)
        packed_argb = tuple(witness_raw[80:88])
        witness_mask = witness_raw[88]
        residual_coordinates = struct.unpack_from("<6f", witness_raw, 89)
        residual_angle_raw = struct.unpack_from("<3f", witness_raw, 113)
        residual_rgba = struct.unpack_from("<12f", witness_raw, 125)
        residual_witness_mask = witness_raw[173]
        if not partial_sampler_available:
            raise AssertionError("actual-AEX artifact lacks the two required partial sampler tuples")
        expected_coordinate_words = tuple(
            int(partial_by_xy[xy][field], 16)
            for xy in ((1612, 6), (1614, 6))
            for field in ("sample_angle_word", "sample_radius_word")
        )
        expected_sampler_words = tuple(
            int(word, 16)
            for xy in ((1612, 6), (1614, 6))
            for word in partial_by_xy[xy]["returned_rgba_words"]
        )
        float_words = lambda values: tuple(struct.unpack("<" + "I" * len(values), struct.pack("<" + "f" * len(values), *values)))
        coordinate_words = float_words(inverse_coordinates)
        sampler_words = float_words(inverse_rgba)
        expected_packed_argb = (255, 5, 5, 5, 255, 255, 255, 255)
        inverse_writer_checks = {
            "both_witnesses_captured": witness_mask == 3,
            "ordered_inverse_coordinate_words_exact": coordinate_words == expected_coordinate_words,
            "partial_actual_aex_sampler_words_exact": sampler_words == expected_sampler_words,
            "modeled_pf8_low_byte_argb_exact": packed_argb == expected_packed_argb,
            "output_world_matches_test_seam": (
                tuple(int(v) for v in output_argb[6, 1612]) == packed_argb[:4]
                and tuple(int(v) for v in output_argb[6, 1614]) == packed_argb[4:]
            ),
        }
        writeback_reference_status = "exact" if actual_aex_writeback.get("status") == "exact" else "pending"
        native_writer_checks = {}
        if writeback_reference_status == "exact":
            native_calls = {
                tuple(call["xy"]): call for call in actual_aex_writeback.get("pf8_calls", [])
            }
            native_checks_recorded = actual_aex_writeback.get("checks", {})
            native_writer_checks = {
                "all_actual_aex_checks_exact": bool(native_checks_recorded) and all(native_checks_recorded.values()),
                "exact_witness_coordinates": set(native_calls) == {(1612, 6), (1614, 6)},
                "packer_rgba_words_exact": float_words(packer_rgba) == tuple(
                    int(word, 16)
                    for xy in ((1612, 6), (1614, 6))
                    for word in native_calls[xy]["rgba_words"]
                ) if set(native_calls) == {(1612, 6), (1614, 6)} else False,
                "native_after_argb_exact": packed_argb == tuple(
                    byte
                    for xy in ((1612, 6), (1614, 6))
                    for byte in native_calls[xy]["after_argb"]
                ) if set(native_calls) == {(1612, 6), (1614, 6)} else False,
                "native_oracle_argb_exact": packed_argb == tuple(
                    byte
                    for xy in ((1612, 6), (1614, 6))
                    for byte in native_calls[xy]["oracle_argb"]
                ) if set(native_calls) == {(1612, 6), (1614, 6)} else False,
                "pf8_scale_word_exact": all(
                    call.get("pf8_scale_word") == "0x437f0000" for call in native_calls.values()
                ) and len(native_calls) == 2,
            }
        internal_exact = all(matches.values())
        full_output_exact = full_output["exact"]
        modeled_writer_exact = all(inverse_writer_checks.values()) and all(actual_aex_identity_checks.values())
        native_writer_pending = writeback_reference_status != "exact"
        native_writer_exact = (
            writeback_reference_status == "exact"
            and all(actual_aex_identity_checks.values())
            and bool(native_writer_checks)
            and all(native_writer_checks.values())
        )
        report = {
            "kind": "olmradialblur_case0010_rotation_mac_production_planes_20260805",
            "status": (
                "modeled_pass_native_pending" if internal_exact and full_output_exact and modeled_writer_exact and native_writer_pending
                else "native_exact" if internal_exact and full_output_exact and modeled_writer_exact and native_writer_exact
                else "diagnostic_mismatch"
            ),
            "conformance_status": {
                "internal_exact": internal_exact,
                "full_native_pf8_output_exact": full_output_exact,
                "modeled_writer_exact": modeled_writer_exact,
                "native_writer_pending": native_writer_pending,
                "native_writer_exact": native_writer_exact,
            },
            "scope": "Mac production RenderRotation8 internal planes plus bounded modeled inverse/PF8 writer for case_0010; no AE host claim",
            "expected_actual_aex_sha256": expected,
            "mac_production_sha256": actual,
            "matches": matches,
            "differences": differences,
            "output_argb8_sha256": sha256(output_path),
            "full_native_pf8_output": full_output,
            "full_native_pf8_fixture_identity": full_pf8_fixture_identity,
            "inverse_writer": {
                "cvtt_edge_semantics_exercised": True,
                "checks": inverse_writer_checks,
                "actual_aex_writeback_reference_status": writeback_reference_status,
                "actual_aex_writeback_artifact_status": actual_aex_writeback.get("status"),
                "actual_aex_identity_checks": actual_aex_identity_checks,
                "native_writer_checks": native_writer_checks,
                "reference_policy": (
                    "The exact actual-AEX artifact is accepted only after identity, XMM input words, "
                    "PF8 scale, native after-store ARGB, and native oracle ARGB all match."
                    if native_writer_exact else
                    "The actual-AEX final writer remains pending or mismatched; only validated inverse-sampler tuples are partial anchors."
                ),
                "coordinates": [[1612, 6], [1614, 6]],
                "inverse_coordinate_words": [f"0x{word:08x}" for word in coordinate_words],
                "inverse_rgba_words": [f"0x{word:08x}" for word in sampler_words],
                "packer_rgba_words": [f"0x{word:08x}" for word in float_words(packer_rgba)],
                "packed_argb": [list(packed_argb[:4]), list(packed_argb[4:])],
                "residual_probe": {
                    "coordinates": [[1462, 0], [1484, 0], [1426, 8]],
                    "mask": residual_witness_mask,
                    "coordinate_words": [f"0x{word:08x}" for word in float_words(residual_coordinates)],
                    "angle_raw_words": [f"0x{word:08x}" for word in float_words(residual_angle_raw)],
                    "rgba_words": [f"0x{word:08x}" for word in float_words(residual_rgba)],
                },
            },
        }
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "native_exact" else 1


if __name__ == "__main__":
    raise SystemExit(main())
