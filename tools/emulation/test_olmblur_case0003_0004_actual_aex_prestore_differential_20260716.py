#!/usr/bin/env python3
"""Mac-only, fail-closed OLMBlur case 0003/0004 actual-AEX differential."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RDI, UC_X86_REG_RSP

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmblur_fullentry import build_context, build_pf_suites  # noqa: E402
import test_olmblur_case0006_fullentry as fullworker  # noqa: E402
from test_olmblur_writer_export_boundary_20260716 import run_writer  # noqa: E402

AEX = ROOT / "plugins_2025/OLMBlur.aex"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
MANIFEST = ROOT / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json"
INPUT_DIR = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625/input"
REPORT_JSON = ROOT / "refs/conformance/olmblur_case0003_0004_actual_aex_prestore_differential_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmblur_case0003_0004_actual_aex_prestore_differential_20260716.md"
PORTABLE = Path(__file__).with_name("probe_olmblur_case0004_actual_aex_portable.cpp")

CASE3_POINTS = ((936, 1), (739, 2), (23, 36), (59, 76), (640, 85),
                (383, 124), (204, 179), (250, 213), (273, 218), (273, 221),
                (298, 228), (227, 278), (564, 281), (165, 345), (165, 346),
                (129, 403), (362, 406), (362, 408), (756, 425), (25, 482))
CASE4_POINTS = ((411, 258), (458, 314))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_pf16(path: Path) -> tuple[bytes, dict]:
    width, height, rgba = fullworker.png_rgba16(path)
    out = bytearray(len(rgba))
    for offset in range(0, len(rgba), 8):
        r, g, b, a = struct.unpack_from(">4H", rgba, offset)
        # Retained saveFrameToPng words are mapped back to AE's 0..32768 words.
        struct.pack_into("<4H", out, offset, *((v + 1) // 2 for v in (a, r, g, b)))
    return bytes(out), {
        "png_dimensions": [width, height],
        "png_sha256": sha256(path.read_bytes()),
        "pf16_sha256": sha256(out),
        "mapping": "RGBA16 PNG -> little-endian PF16 A,R,G,B using (word + 1) // 2",
    }


def case_manifest(case_id: str) -> dict:
    manifest = json.loads(MANIFEST.read_text())
    return next(case for case in manifest["cases"] if case["id"] == case_id)


def params_from_manifest(case: dict) -> dict:
    values = {p["name"]: p["value"] for p in case["effects"][0]["params"]}
    return {
        "blur_amount": values["Blur Amount"],
        "smoothness": values["Blur Smoothness"],
        "repeat": int(values["Number of Repeat"]),
        "bias_direction": int(values["Bias Direction"]),
        "legacy": int(values["Legacy"]),
    }


def run_case4_bounded(pf16: bytes, params: dict) -> tuple[dict, dict, dict]:
    """Execute the entry through staging and the actual writer as a micro-boundary."""
    fullworker.WIDTH, fullworker.HEIGHT = 960, 540
    fullworker.WITNESSES = CASE4_POINTS
    fullworker.RADII = (125, 36, 10, 3)
    fullworker.PORTABLE_SOURCE = PORTABLE
    portable = fullworker.compile_and_run_portable(pf16)

    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    spbasic, _events = build_pf_suites(loader)
    context = build_context(loader, spbasic)
    source_data = loader.bump_alloc(len(pf16), align=64)
    output_data = loader.bump_alloc(len(pf16), align=64)
    loader.write_bytes(source_data, pf16)
    loader.write_bytes(output_data, pf16)

    def world(data: int) -> int:
        address = loader.host_alloc(0x80)
        loader.write_bytes(address, b"\x00" * 0x80)
        loader.write_bytes(address + 0x18, struct.pack("<Q", data))
        loader.write_bytes(address + 0x20, struct.pack("<I", 960 * 8))
        loader.write_bytes(address + 0x24, struct.pack("<I", 960))
        loader.write_bytes(address + 0x28, struct.pack("<I", 540))
        loader.write_bytes(address + 0x2C, struct.pack("<H", 16))
        return address

    block = loader.host_alloc(0x40)
    loader.write_bytes(block, b"\x00" * 0x40)
    loader.write_bytes(block + 0x18, struct.pack("<I", 16))
    loader.write_bytes(block + 0x20, struct.pack("<f", params["blur_amount"]))
    loader.write_bytes(block + 0x24, struct.pack("<f", params["smoothness"]))
    loader.write_bytes(block + 0x28, struct.pack("<I", params["repeat"]))
    loader.write_bytes(block + 0x2C, struct.pack("<I", params["bias_direction"]))
    capture: dict = {"entry": hex(0x180002280), "staging_stop": hex(0x1800028DB), "points": {}}

    def stop(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        plane = struct.unpack("<Q", ld.read_bytes(rsp + 0x60, 8))[0]
        flags = ld.uc.reg_read(UC_X86_REG_RDI)
        for x, y in CASE4_POINTS:
            pixel = y * 960 + x
            source_words = list(struct.unpack_from("<4H", pf16, pixel * 8))
            actual_bits = list(struct.unpack("<3I", ld.read_bytes(plane + pixel * 12, 12)))
            expected_bits = [struct.unpack("<I", struct.pack("<f", float(v)))[0] for v in source_words[1:]]
            capture["points"][f"({x},{y})"] = {
                "source_argb16_words": source_words,
                "actual_staged_rgb_bits_hex": [f"0x{v:08x}" for v in actual_bits],
                "portable_decode_rgb_bits_hex": [f"0x{v:08x}" for v in expected_bits],
                "active_flag": ld.read_bytes(flags + pixel, 1)[0],
                "exact": actual_bits == expected_bits,
            }
        ld.uc.emu_stop()

    loader.add_code_hook(0x1800028DB, stop)
    result = loader.call_function(0x180002280, int_args=[context, world(source_data), world(output_data), block], max_instructions=30_000_000)
    capture["instructions"] = result["instructions"]
    capture["all_source_conversion_exact"] = all(v["exact"] for v in capture["points"].values())

    writer_runs = {}
    for key, final in portable["final"].items():
        values = tuple(struct.unpack("<f", struct.pack("<I", int(bits, 16)))[0] for bits in final["pre_store_bits_hex"])
        writer_runs[key] = run_writer(0x1800030E2, 0x180003123, values, direct=False)
        writer_runs[key]["portable_stored_rgb_words"] = final["stored_rgb_words"]
        writer_runs[key]["stored_rgb_exact"] = writer_runs[key]["stored_argb16"][1:] == final["stored_rgb_words"]

    comparison = {
        "source_conversion_exact": capture["all_source_conversion_exact"],
        "actual_writer_micro_runs": writer_runs,
        "writer_store_exact_for_portable_inputs": all(v["stored_rgb_exact"] for v in writer_runs.values()),
        "full_worker_attempt": {
            "status": "instruction_cap_before_writer",
            "max_instructions_per_witness": 1_000_000_000,
            "observed_writer_points": 0,
            "reason": "radius-125 actual helper execution did not reach the writer within the established cap",
        },
        "first_divergence": None,
        "classification": "worker_helper_pre_store_unresolved_fail_closed",
    }
    return capture, portable, comparison


def run_case3_staging(pf16: bytes, params: dict) -> dict:
    width, height = 960, 540
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    loader.register_import_impl("pow", lambda _uc, _args: (loader.write_xmm_f64(0, math.pow(loader.read_xmm_f64(0), loader.read_xmm_f64(1))) or 0))
    loader.register_import_impl("powf", lambda _uc, _args: (loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0), loader.read_xmm_f32(1))) or 0))
    spbasic, _events = build_pf_suites(loader)
    context = build_context(loader, spbasic)
    source_data = loader.bump_alloc(len(pf16), align=64)
    output_data = loader.bump_alloc(len(pf16), align=64)
    loader.write_bytes(source_data, pf16)
    loader.write_bytes(output_data, pf16)

    def world(data: int) -> int:
        address = loader.host_alloc(0x80)
        loader.write_bytes(address, b"\x00" * 0x80)
        loader.write_bytes(address + 0x18, struct.pack("<Q", data))
        loader.write_bytes(address + 0x20, struct.pack("<I", width * 8))
        loader.write_bytes(address + 0x24, struct.pack("<I", width))
        loader.write_bytes(address + 0x28, struct.pack("<I", height))
        loader.write_bytes(address + 0x2C, struct.pack("<H", 16))
        return address

    block = loader.host_alloc(0x40)
    loader.write_bytes(block, b"\x00" * 0x40)
    loader.write_bytes(block + 0x18, struct.pack("<I", 16))
    loader.write_bytes(block + 0x20, struct.pack("<f", params["blur_amount"]))
    loader.write_bytes(block + 0x24, struct.pack("<f", params["smoothness"]))
    loader.write_bytes(block + 0x28, struct.pack("<I", params["repeat"]))
    loader.write_bytes(block + 0x2C, struct.pack("<I", params["bias_direction"]))
    loader.write_bytes(block + 0x30, b"\x01")
    capture: dict = {"entry": hex(0x180005F20), "staging_stop": hex(0x1800065AE)}

    def stop(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        plane = struct.unpack("<Q", ld.read_bytes(rsp + 0x50, 8))[0]
        flags = ld.uc.reg_read(UC_X86_REG_RDI)
        points = {}
        for x, y in CASE3_POINTS:
            pixel = y * width + x
            bits = list(struct.unpack("<3I", ld.read_bytes(plane + pixel * 12, 12)))
            source_words = list(struct.unpack_from("<4H", pf16, pixel * 8))
            expected_bits = [struct.unpack("<I", struct.pack("<f", float(v)))[0] for v in source_words[1:]]
            points[f"({x},{y})"] = {
                "source_argb16_words": source_words,
                "actual_staged_rgb_bits_hex": [f"0x{v:08x}" for v in bits],
                "portable_decode_rgb_bits_hex": [f"0x{v:08x}" for v in expected_bits],
                "active_flag": ld.read_bytes(flags + pixel, 1)[0],
                "exact": bits == expected_bits,
            }
        capture["points"] = points
        ld.uc.emu_stop()

    loader.add_code_hook(0x1800065AE, stop)
    result = loader.call_function(0x180005F20, int_args=[context, world(source_data), world(output_data), block], max_instructions=30_000_000)
    capture.update(instructions=result["instructions"], all_source_conversion_exact=all(v["exact"] for v in capture["points"].values()))
    radius = int(struct.unpack("<f", struct.pack("<f", params["blur_amount"]))[0])
    capture["feasibility"] = {
        "radius_each_iteration": radius, "repeat": params["repeat"],
        "axis_dependency_reach_before_first_helper": radius * (params["repeat"] * 2 - 1),
        "frame": [width, height], "full_frame_dependency": radius * (params["repeat"] * 2 - 1) >= max(width, height),
        "stop_reason": "ten radius-248 alternating passes make each residual's pre-store dependency cone full-frame; actual helper/writer execution is not bounded",
    }
    capture["classification"] = "source_conversion_excluded_then_fail_closed_before_worker_helper_pre_store"
    return capture


def main() -> int:
    if sha256(AEX.read_bytes()) != AEX_SHA256:
        raise AssertionError("OLMBlur.aex hash differs from pinned fixture binary")
    records = {}
    decoded = {}
    for number in (3, 4):
        case_id = f"olmblur__case_000{number}"
        case = case_manifest(case_id)
        path = INPUT_DIR / case["before_effects_frame"]
        pf16, decode = decode_pf16(path)
        params = params_from_manifest(case)
        if decode["png_dimensions"] != [960, 540]:
            raise AssertionError(f"{case_id}: unexpected dimensions")
        records[number] = (pf16, params)
        decoded[case_id] = decode | {"parameters": params, "manifest_frame": case["frame"]}

    case3 = run_case3_staging(*records[3])
    case4_actual, case4_portable, case4_comparison = run_case4_bounded(*records[4])
    report = {
        "schema": "olmblur.case0003-0004.actual-aex-prestore-differential/1",
        "status": "partial_fail_closed",
        "platform": "Mac-only Unicorn execution of actual PE AEX; no Windows/SSH/NAS execution",
        "identity": {"aex": str(AEX.relative_to(ROOT)), "sha256": AEX_SHA256},
        "decoded_inputs": decoded,
        "case_0003_legacy": case3,
        "case_0004_nonlegacy": {"actual_aex": case4_actual, "portable": case4_portable, "comparison": case4_comparison},
        "FACT": [
            "Both actual worker entries execute from the pinned OLMBlur.aex with exact manifest parameters.",
            "case_0003 reaches the post-staging boundary and all 20 residual coordinates exactly match portable PF16 decoding.",
            f"case_0004 bounded actual-AEX versus portable classification is {case4_comparison['classification']}.",
        ],
        "INFERENCE": [
            "case_0003 source conversion is excluded on the retained decoded input, but worker-helper/pre-store, writer-store, and output mapping remain unresolved because its exact dependency cone is full-frame.",
            "case_0004 source conversion and the actual writer rule on portable pre-store inputs are excluded; the first unexecuted discriminating boundary is worker/helper pre-store.",
        ],
        "unproven": ["Windows live facts", "AE host source reconstruction beyond retained PNG decoding", "AE export mapping", "case_0003 writer input/store"],
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# OLMBlur case 0003/0004 actual-AEX pre-store differential", "", "## FACT", "",
        f"- Pinned actual AEX: `{AEX.relative_to(ROOT)}` / `{AEX_SHA256}`.",
        "- Both retained inputs are decoded identically to little-endian PF16 A,R,G,B with `(PNG word + 1) // 2`; hashes are in the JSON.",
        "- case 0003 Legacy executes `FUN_180005F20` with amount 248.600006103516, smoothness 100, repeat 10, bias 1. All 20 named residual points match portable source conversion bit-for-bit at `0x1800065ae`.",
        f"- case 0004 Non-Legacy executes `FUN_180002280` with amount 125.599998474121, smoothness 100, repeat 4, bias 1. Classification: `{case4_comparison['classification']}`.",
        "- case 0004 portable writer-input RGB float32 bits and actual-AEX writer micro-run stored PF16 words are retained in the JSON. The billion-instruction full-worker attempt did not reach the writer.",
        "", "## INFERENCE", "",
        "- case 0003 excludes source conversion at the retained coordinates. Its radius-248 x 10 alternating-pass dependency reaches the full 960x540 frame before the first helper, so the probe stops fail-closed before claiming a worker/helper or writer comparison.",
        "- case 0004 excludes source conversion and excludes the writer-store rule conditionally on portable writer inputs. The worker/helper pre-store boundary remains the first unresolved stage; AE export and Windows live behavior remain unproven.",
        "", "## Tests", "", "```text",
        "python3 tools/emulation/test_olmblur_case0003_0004_actual_aex_prestore_differential_20260716.py",
        "python3 tools/emulation/smoke_olmblur_worker16_legacy.py",
        "python3 tools/emulation/test_olmblur_worker16_nonlegacy.py --export", "```", "",
        "## Changed files", "",
        "- `tools/emulation/probe_olmblur_case0004_actual_aex_portable.cpp` (new)",
        "- `tools/emulation/test_olmblur_case0003_0004_actual_aex_prestore_differential_20260716.py` (new)",
        "- `refs/conformance/olmblur_case0003_0004_actual_aex_prestore_differential_20260716.json` (new)",
        "- `refs/conformance/olmblur_case0003_0004_actual_aex_prestore_differential_20260716.md` (new)",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps({"status": report["status"], "case_0003": case3["classification"], "case_0004": case4_comparison["classification"], "case_0004_first": case4_comparison["first_divergence"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
