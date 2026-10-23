#!/usr/bin/env python3
"""Close the public Mode-4 Diagonal-2 angle-representative seam."""
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import copy
import hashlib
import importlib.util
import json
import os
import struct
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
BASE = ROOT / "tools/emulation/test_olmkirakira_mode1_exported_effectmain_all_depths_20260812.py"
CORE_PROBE = ROOT / "tools/emulation/test_kirakira_mode4_canonical.cpp"
COMPOSE_ORACLE = ROOT / "tools/emulation/olmkirakira_outer_compose_oracle_20260728.py"
PUBLIC = ROOT / "refs/conformance/olmkirakira_mode4_diagonal2_solo_exported_effectmain_all_depths_20260812.json"
OUT = ROOT / "refs/conformance/olmkirakira_mode4_diagonal2_owner_angle_closure_20260812.json"
DOC = OUT.with_suffix(".md")

WORKER = Path(os.environ.get(
    "OLM_AEX_GUEST_WORKER",
    "/Users/onmk/Documents/Projects/Personal/04_Tools/"
    "AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker",
))
EXPECTED_AEX_SHA = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"
EXPECTED_WORKER_SHA = "46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61"
EXPECTED_ASM_SHA = "d23c749d225a934580c96f2929fb9d7253d07b1be208faa9de6ff89efc1f89b3"
EXPECTED_INPUT_PNG_SHA = "aa175f6a33d67ee4cdd8a8b7e4ef1c797a17f9ff1decfec69c87701b27c419f2"
EXPECTED_PUBLIC = {
    "PF8": (60, "30b58167110e9bcc125244395ee07a16a6e8d00142869fd283f10f264b1ae0f6"),
    "PF16": (120, "0853a40e66d15baf32fc85a6233b2fc387ec8413b1d4789df736c66afe5ea4b3"),
    "PF32": (240, "1eb072a44e5fad044073c09245f25ff1a4359f378e24c28cbaa6a62fd6025d27"),
}
EXPECTED_STAGE_SHA = {
    "seed": "4c52a6f9e0b97638c819e3a08d81fb98fadea274bdf24e6d460bcaad2a2ad4ad",
    "forward": "1944bc2f67ab8fe75ed2ba7008818f3e997e2cfc0d57e651eecf734e6bc45ce6",
    "inverse": "d881377ad739c571a881302f5ad542b52899ebf93932e874f52b718d0f1b870b",
    "ray": "6026b57821a052062b4346487727f7eccfc22a960661d8fcdfc43127fb4372c8",
    "glow": "c2725b89989892fa1fef3bb5bd62939d9b5b50738ce3c2cd459ee0047b786dab",
    "source": "5f19e68ee17627c45e8aebefa660ddc23f5eae72b21a5ef7fee354ecaa892a94",
    "output": EXPECTED_PUBLIC["PF32"][1],
}
EXPECTED_SUITES = ["PF Handle Suite v2", "AEGP Utility Suite v13", "PF ColorParamSuite v1"]
EXPECTED_PIXEL_FORMATS = {"PF8": "argb8", "PF16": "argb16", "PF32": "argb32f"}
EXPECTED_STAGE_BYTES = {"seed": 60, "forward": 324, "inverse": 324, "ray": 60,
                        "glow": 240, "source": 240, "output": 240}
OWNER_ANGLE_SITES = ("18114ce8e", "18114d45e", "18114da2e")
PARAMS = (
    "Blur Mode=4", "Vertical Length=0", "Horizontal Length=0",
    "Diagonal Length=0", "Diagonal 2 length=7", "Highlight Radius=0",
    "Merge mode=2", "Channel=1", "Brightness Gain=0.73",
    "Glow Rotation=fixed:1",
)
WIDTH, HEIGHT = 5, 3
RGBA = tuple((i * 15, i * 11, i * 7, 64 + i * 11) for i in range(15))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def captured(witness: dict, phase: str) -> bytes:
    item = witness.get(phase, {})
    if item.get("status") != "captured" or not item.get("hex"):
        raise AssertionError(f"{witness.get('watch_id')} {phase} was not captured")
    return bytes.fromhex(item["hex"])


def load_oracle():
    spec = importlib.util.spec_from_file_location("kira_d2_compose_oracle", COMPOSE_ORACLE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def natural_trace(directory: Path) -> dict[str, object]:
    input_png = directory / "input.png"
    output_png = directory / "output.png"
    image = Image.new("RGBA", (WIDTH, HEIGHT)); image.putdata(RGBA); image.save(input_png)
    watches = (
        "function=0x114e860,arg=stack6,size=2136,occurrence=1",
        "function=0x114d7f0,arg=stack5,size=128,occurrence=1",
        "function=0x1150790,arg=rdx,deref=16,size=60,occurrence=1",
        "function=0x1150790,arg=r8,deref=16,size=324,occurrence=1",
        "function=0x1150790,arg=stack5,deref=16,size=324,occurrence=1",
        "function=0x1150790,arg=r9,deref=16,size=60,occurrence=1",
        "function=0x1150790,arg=stack6,size=8,occurrence=1",
        "function=0x1150790,arg=stack7,size=8,occurrence=1",
        "function=0x1150790,arg=stack8,size=8,occurrence=1",
        "function=0x1150250,arg=rcx,size=240,occurrence=1",
        "function=0x114e460,arg=rcx,deref=400,size=240,occurrence=1",
        "function=0x114e460,arg=rcx,deref=296,size=240,occurrence=1",
        "function=0x114e460,arg=rdx,deref=24,size=240,occurrence=1",
    )
    command = [str(WORKER), "render-trace-png", str(AEX), str(input_png), str(output_png),
               "--pixel-format", "argb32f"]
    for watch in watches:
        command.extend(("--watch", watch))
    command.extend(PARAMS)
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    trace = json.loads(result.stdout)
    smart = next(item for item in trace["execution_traces"] if item["selector"] == "SMART_RENDER")
    by_id = {item["watch_id"]: item for item in smart["memory_witnesses"]}
    if set(by_id) != {f"watch-{index}" for index in range(1, 14)}:
        raise AssertionError(f"missing natural witnesses: {sorted(by_id)}")

    builder = captured(by_id["watch-1"], "after")
    owner = captured(by_id["watch-2"], "before")
    seed = captured(by_id["watch-3"], "before")
    forward = captured(by_id["watch-4"], "after")
    inverse = captured(by_id["watch-5"], "after")
    ray = captured(by_id["watch-6"], "after")
    glow = captured(by_id["watch-11"], "before")
    source = captured(by_id["watch-12"], "before")
    output = captured(by_id["watch-13"], "after")

    helper_witnesses = [by_id[f"watch-{index}"] for index in range(3, 10)]
    if {item["function_rva"] for item in helper_witnesses} != {0x1150790}:
        raise AssertionError("natural stage witnesses did not enter FUN_181150790")
    if {item["pc_rva"] for item in helper_witnesses} != {0x114F929}:
        raise AssertionError("natural stage witnesses have an unexpected owner callsite")
    angle = by_id["watch-7"]["before"]["address"]
    length = by_id["watch-8"]["before"]["address"]
    blur_mode = by_id["watch-9"]["before"]["address"]

    stage_bytes = {"seed": seed, "forward": forward, "inverse": inverse,
                   "ray": ray, "glow": glow, "source": source, "output": output}
    if {name: sha(data) for name, data in stage_bytes.items()} != EXPECTED_STAGE_SHA:
        raise AssertionError("natural stage identity changed")
    return {
        "trace_stdout_sha256": sha(result.stdout.encode()),
        "input_png_sha256": sha(input_png.read_bytes()),
        "raw_pixel_sha256": trace["raw_pixel_sha256"],
        "render_error": trace["render_error"],
        "guards_intact": trace["guards_intact"],
        "trace_truncated": smart["truncated"],
        "dropped_memory_witnesses": smart["dropped_memory_witnesses"],
        "owner_builder": {
            "rotation_raw_fixed_at_0x00": struct.unpack_from("<i", builder, 0)[0],
            "brightness_f32_bits_at_0x04": f"0x{struct.unpack_from('<I', builder, 4)[0]:08x}",
            "diagonal2_length_at_0x28": struct.unpack_from("<i", builder, 0x28)[0],
            "public_merge_at_0x44": struct.unpack_from("<i", builder, 0x44)[0],
            "aggregation_selector_at_0x48": struct.unpack_from("<i", builder, 0x48)[0],
            "blur_mode_at_0x4c": struct.unpack_from("<i", builder, 0x4C)[0],
        },
        "typed_owner": {
            "rotation_raw_fixed_at_0x00": struct.unpack_from("<i", owner, 0)[0],
            "diagonal2_length_at_0x28": struct.unpack_from("<i", owner, 0x28)[0],
            "public_merge_at_0x44": struct.unpack_from("<i", owner, 0x44)[0],
            "aggregation_selector_at_0x48": struct.unpack_from("<i", owner, 0x48)[0],
            "blur_mode_at_0x4c": struct.unpack_from("<i", owner, 0x4C)[0],
        },
        "helper": {
            "function_rva": "0x1150790", "owner_callsite_rva": "0x114f929",
            "angle_degrees": angle, "length": length, "blur_mode": blur_mode,
        },
        "stages": {
            name: {"bytes": len(data), "sha256": sha(data), "hex": data.hex()}
            for name, data in stage_bytes.items()
        },
        "fd90_dynamic_entry": {
            "internal_function_rva": "0x1150250",
            "internal_callsite_rva": f"0x{by_id['watch-10']['pc_rva']:x}",
            "hit": by_id["watch-10"]["function_rva"] == 0x1150250,
        },
    }


def compile_portable(directory: Path, seed: bytes, angle: int) -> dict[str, bytes]:
    executable = directory / f"mode4-{angle}"
    subprocess.run([_UCRT_CXX, "-std=c++20", "-O2", "-ffp-contract=off",
                    str(CORE_PROBE), "-o", str(executable)], cwd=ROOT, check=True)
    seed_values = struct.unpack("<15f", seed)
    padded = [0.0] * 81
    for y in range(HEIGHT):
        for x in range(WIDTH):
            padded[(y + 3) * 9 + x + 2] = seed_values[y * WIDTH + x]
    words = "\n".join(f"{struct.unpack('<I', struct.pack('<f', value))[0]:08x}" for value in padded) + "\n"
    output = subprocess.check_output([str(executable), "9", "9", "7", str(angle)],
                                     cwd=ROOT, input=words, text=True)
    stages: dict[str, list[int]] = {"forward": [], "recurrence": [], "inverse": []}
    for line in output.splitlines():
        stage, _index, word = line.split()
        stages["inverse" if stage == "final" else stage].append(int(word, 16))
    inverse = stages["inverse"]
    crop_indices = [(y + 3) * 9 + x + 2 for y in range(HEIGHT) for x in range(WIDTH)]
    return {
        "forward": struct.pack("<81I", *stages["forward"]),
        "recurrence": struct.pack("<81I", *stages["recurrence"]),
        "inverse": struct.pack("<81I", *inverse),
        "ray": struct.pack("<15I", *(inverse[index] for index in crop_indices)),
    }


def portable_downstream(ray: bytes, source: bytes) -> tuple[bytes, bytes]:
    oracle = load_oracle()
    glow_values: list[float] = []
    for amount in struct.unpack("<15f", ray):
        if amount <= f32(0.001):
            glow_values.extend((0.0, 0.0, 0.0, 0.0)); continue
        alpha = max(0.0, min(1.0, f32(amount * f32(0.73))))
        inverse = f32(f32(1.0) / alpha)
        rgb = f32(f32(alpha * f32(1.0)) * inverse)
        glow_values.extend((rgb, rgb, rgb, alpha))
    glow = struct.pack("<60f", *glow_values)
    source_values = struct.unpack("<60f", source)
    output = b"".join(
        oracle.stage_typed_writer(oracle.compose_pixel(
            glow_values[index * 4:index * 4 + 4],
            source_values[index * 4:index * 4 + 4],
            glow_opacity=1.0, source_opacity=1.0, merge_mode=2), depth="PF32")
        for index in range(15)
    )
    return glow, output


def static_owner_angle_table() -> dict[str, object]:
    text = ASM.read_text(encoding="utf-8")
    anchors = {}
    for site in OWNER_ANGLE_SITES:
        line = f"{site}  LEA EAX,[RCX + 0x87]"
        anchors["0x" + site] = text.count(line)
    if set(anchors.values()) != {1}:
        raise AssertionError(f"typed owner +135 anchors changed: {anchors}")
    source = SOURCE.read_text(encoding="utf-8")
    if "make_ray(info.diagonal2_length, 135.0 + glow_rotation)" not in source:
        raise AssertionError("production Diagonal 2 owner is not +135")
    if "make_ray(info.diagonal2_length, -45.0 + glow_rotation)" in source:
        raise AssertionError("stale -45 Diagonal 2 owner remains")
    return {"base_angle_degrees": 135, "typed_owner_anchors": anchors,
            "production_expression": "135.0 + glow_rotation"}


def run_public() -> dict[str, object]:
    env = os.environ.copy()
    env.update({
        "OLM_KIRA_EXPORTED_CASE": "mode4_diagonal2_solo",
        "OLM_KIRA_EXPORTED_REPORT": str(PUBLIC.relative_to(ROOT)),
        "OLM_KIRA_BLUR_MODE": "4", "OLM_KIRA_MERGE_MODE": "2",
        "OLM_KIRA_BRIGHTNESS_GAIN": "0.73",
        "OLM_KIRA_GLOW_ROTATION": "1", "OLM_KIRA_GLOW_ROTATION_RAW_FIXED": "1",
        "OLM_KIRA_HORIZONTAL_LENGTH": "0", "OLM_KIRA_HORIZONTAL_USE_RAMP": "0",
        "OLM_KIRA_DIAGONAL2_LENGTH": "7", "OLM_KIRA_HIGHLIGHT_RADIUS": "0",
        "OLM_KIRA_HIGHLIGHT_USE_RAMP": "0", "OLM_AEX_GUEST_WORKER": str(WORKER),
    })
    result = subprocess.run(["python3", str(BASE)], cwd=ROOT, env=env)
    if result.returncode:
        raise RuntimeError("public Diagonal 2 all-depth comparison did not close")
    return json.loads(PUBLIC.read_text(encoding="utf-8"))


def validate_report(report: dict[str, object]) -> bool:
    try:
        assert report["schema_version"] == 1
        assert report["kind"] == "olmkirakira_mode4_diagonal2_owner_angle_closure"
        identities = report["identities"]
        assert identities["aex_sha256"] == EXPECTED_AEX_SHA
        assert identities["aexcompat_worker_sha256"] == EXPECTED_WORKER_SHA
        assert identities["aexcompat_commit"] == "28d535469f84f67236ef3425afe4291ea2fb0991"
        assert identities["disassembly_sha256"] == EXPECTED_ASM_SHA
        assert identities["disassembly_sha256"] == sha(ASM.read_bytes())
        assert identities["production_source_sha256"] == sha(SOURCE.read_bytes())
        assert identities["generator_sha256"] == sha(Path(__file__).read_bytes())
        assert report["status"] == "raw_exact"
        assert report["fixture"] == {
            "dimensions": [5, 3], "padding": 12, "blur_mode": 4,
            "public_merge_mode": 2, "brightness_gain": 0.73,
            "rotation_raw_fixed": 1, "diagonal2_length": 7,
            "all_other_rays_zero": True, "all_ramps_off": True,
            "ordered_parameters": list(PARAMS),
            "ordered_parameters_sha256": sha("\0".join(PARAMS).encode()),
        }
        natural = report["natural_trace"]
        assert natural["render_error"] == 0 and natural["guards_intact"]
        assert natural["input_png_sha256"] == EXPECTED_INPUT_PNG_SHA
        assert not natural["trace_truncated"] and natural["dropped_memory_witnesses"] == 0
        assert natural["raw_pixel_sha256"] == EXPECTED_PUBLIC["PF32"][1]
        assert natural["owner_builder"] == {
            "rotation_raw_fixed_at_0x00": 1, "brightness_f32_bits_at_0x04": "0x3f3ae148",
            "diagonal2_length_at_0x28": 7, "public_merge_at_0x44": 2,
            "aggregation_selector_at_0x48": 1, "blur_mode_at_0x4c": 4,
        }
        assert natural["typed_owner"] == {
            "rotation_raw_fixed_at_0x00": 1, "diagonal2_length_at_0x28": 7,
            "public_merge_at_0x44": 2, "aggregation_selector_at_0x48": 1,
            "blur_mode_at_0x4c": 4,
        }
        assert natural["helper"] == {
            "function_rva": "0x1150790", "owner_callsite_rva": "0x114f929",
            "angle_degrees": 136, "length": 7, "blur_mode": 4,
        }
        assert natural["fd90_dynamic_entry"] == {
            "internal_function_rva": "0x1150250", "internal_callsite_rva": "0x114fdec",
            "hit": True,
        }
        assert set(natural["stages"]) == set(EXPECTED_STAGE_SHA)
        for name, expected in EXPECTED_STAGE_SHA.items():
            stage = natural["stages"][name]
            assert stage["bytes"] == EXPECTED_STAGE_BYTES[name]
            assert stage["sha256"] == expected
            assert stage["sha256"] == sha(bytes.fromhex(stage["hex"]))
            assert len(bytes.fromhex(stage["hex"])) == EXPECTED_STAGE_BYTES[name]
        angle = report["angle_representative_proof"]
        assert angle["natural_angle_degrees"] == 136
        assert angle["corrected_portable_angle_degrees"] == 136
        assert angle["counterfactual_old_angle_degrees"] == -44
        assert angle["corrected_stage_exact"] == {"forward_words": 81, "inverse_words": 81, "ray_words": 15}
        natural_ray_words = struct.unpack("<15I", bytes.fromhex(natural["stages"]["ray"]["hex"]))
        differences = angle["old_ray_differences"]
        assert [item["word"] for item in differences] == [6, 7, 12]
        for item in differences:
            word = item["word"]
            actual = int(item["natural"], 16)
            old = int(item["old_minus_180"], 16)
            assert actual == natural_ray_words[word]
            assert item["ulp"] == abs(actual - old) > 0
        assert angle["old_ray_difference_count"] == len(differences) == 3
        assert angle["old_ray_max_ulp"] == max(item["ulp"] for item in differences) == 2
        downstream = report["downstream_proof"]
        assert downstream["portable_glow_sha256"] == EXPECTED_STAGE_SHA["glow"]
        assert downstream["portable_output_sha256"] == EXPECTED_STAGE_SHA["output"]
        assert downstream["glow_exact"] and downstream["output_exact"]
        static = report["static_owner_angle_table"]
        assert static["base_angle_degrees"] == 135
        assert static["production_expression"] == "135.0 + glow_rotation"
        assert static["typed_owner_anchors"] == {"0x" + site: 1 for site in OWNER_ANGLE_SITES}
        public = report["public_all_depths"]
        assert public["status"] == "exact"
        assert [row["depth"] for row in public["rows"]] == ["PF8", "PF16", "PF32"]
        for row in public["rows"]:
            size, expected = EXPECTED_PUBLIC[row["depth"]]
            assert row["pixel_format"] == EXPECTED_PIXEL_FORMATS[row["depth"]]
            assert row["bytes"] == size and row["exact"]
            assert row["actual_exported_raw_sha256"] == expected
            assert row["mac_effectmain_raw_sha256"] == expected
            active = bytes.fromhex(row["mac_effectmain_active_hex"])
            assert len(active) == size and sha(active) == expected
            assert row["render_error"] == 0 and row["guards_intact"]
            assert row["input_unchanged"] and row["mac_padding_preserved"]
            assert row["suite_requests"] == EXPECTED_SUITES and row["unsupported_suite_calls"] == []
            assert row["smart_pre_render"]["selector"] == "SMART_PRE_RENDER"
            assert row["smart_render"]["selector"] == "SMART_RENDER"
            for lifecycle in (row["smart_pre_render"], row["smart_render"]):
                assert lifecycle["attempted"] and lifecycle["completed"]
                assert lifecycle["error"] == 0
        return True
    except (AssertionError, KeyError, TypeError, ValueError):
        return False


def main() -> int:
    if sha(AEX.read_bytes()) != EXPECTED_AEX_SHA:
        raise RuntimeError("unexpected OLMKiraKira AEX identity")
    if sha(WORKER.read_bytes()) != EXPECTED_WORKER_SHA:
        raise RuntimeError("Diagonal2 closure requires the pinned typed-angle worker")
    if sha(ASM.read_bytes()) != EXPECTED_ASM_SHA:
        raise RuntimeError("unexpected pinned OLMKiraKira disassembly identity")
    static = static_owner_angle_table()
    with tempfile.TemporaryDirectory(prefix="kira_mode4_d2_closure_") as raw:
        directory = Path(raw)
        natural = natural_trace(directory)
        seed = bytes.fromhex(natural["stages"]["seed"]["hex"])
        corrected = compile_portable(directory, seed, 136)
        old = compile_portable(directory, seed, -44)
    natural_forward = bytes.fromhex(natural["stages"]["forward"]["hex"])
    natural_inverse = bytes.fromhex(natural["stages"]["inverse"]["hex"])
    natural_ray = bytes.fromhex(natural["stages"]["ray"]["hex"])
    if corrected["forward"] != natural_forward or corrected["inverse"] != natural_inverse or corrected["ray"] != natural_ray:
        raise AssertionError("corrected +136 portable stages are not natural exact")
    old_words = struct.unpack("<15I", old["ray"])
    natural_words = struct.unpack("<15I", natural_ray)
    old_differences = [
        {"word": index, "natural": f"0x{actual:08x}", "old_minus_180": f"0x{prior:08x}",
         "ulp": abs(actual - prior)}
        for index, (actual, prior) in enumerate(zip(natural_words, old_words)) if actual != prior
    ]
    natural_source = bytes.fromhex(natural["stages"]["source"]["hex"])
    portable_glow, portable_output = portable_downstream(natural_ray, natural_source)
    natural_glow = bytes.fromhex(natural["stages"]["glow"]["hex"])
    natural_output = bytes.fromhex(natural["stages"]["output"]["hex"])
    if portable_glow != natural_glow or portable_output != natural_output:
        raise AssertionError("downstream aggregate/compose did not replay natural bytes")
    public = run_public()
    report = {
        "schema_version": 1,
        "kind": "olmkirakira_mode4_diagonal2_owner_angle_closure",
        "date": "2026-08-12", "status": "raw_exact",
        "claim_boundary": "fixed 5x3 Mode4 Diagonal2-only tuple, natural AEX Smart owner and Mac public EffectMain, PF8/PF16/PF32 raw bytes",
        "identities": {
            "aex_sha256": EXPECTED_AEX_SHA,
            "aexcompat_worker_sha256": EXPECTED_WORKER_SHA,
            "aexcompat_commit": "28d535469f84f67236ef3425afe4291ea2fb0991",
            "disassembly_sha256": EXPECTED_ASM_SHA,
            "production_source_sha256": sha(SOURCE.read_bytes()),
            "generator_sha256": sha(Path(__file__).read_bytes()),
        },
        "fixture": {
            "dimensions": [5, 3], "padding": 12, "blur_mode": 4,
            "public_merge_mode": 2, "brightness_gain": 0.73,
            "rotation_raw_fixed": 1, "diagonal2_length": 7,
            "all_other_rays_zero": True, "all_ramps_off": True,
            "ordered_parameters": list(PARAMS),
            "ordered_parameters_sha256": sha("\0".join(PARAMS).encode()),
        },
        "natural_trace": natural,
        "static_owner_angle_table": static,
        "angle_representative_proof": {
            "natural_angle_degrees": 136, "corrected_portable_angle_degrees": 136,
            "counterfactual_old_angle_degrees": -44,
            "corrected_stage_exact": {"forward_words": 81, "inverse_words": 81, "ray_words": 15},
            "old_ray_difference_count": len(old_differences),
            "old_ray_max_ulp": max(item["ulp"] for item in old_differences),
            "old_ray_differences": old_differences,
        },
        "downstream_proof": {
            "portable_glow_sha256": sha(portable_glow),
            "portable_output_sha256": sha(portable_output),
            "glow_exact": portable_glow == natural_glow,
            "output_exact": portable_output == natural_output,
        },
        "public_all_depths": {"status": public["status"], "rows": public["rows"]},
        "claims_not_made": [
            "No arbitrary angle, geometry, source, or parameter Cartesian-product promotion",
            "No live Windows AE or Mac AE pixel-exact claim",
            "No claim that -45 and +135 are generally interchangeable in the Mode4 chain",
        ],
    }
    if not validate_report(report):
        raise AssertionError("Diagonal2 closure report validation failed")
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    DOC.write_text(
        "# OLMKiraKira Mode 4 Diagonal 2 owner-angle closure（2026-08-12）\n\n"
        "Status: **raw exact**\n\n"
        "3つのWindows typed ownerはいずれもDiagonal 2 slotを`rotation+135`として構築する。"
        "Rotation raw-fixed 1の自然D2 helperは`136°`であり、counterfactualの`-44°`とは幾何学的に同軸でも"
        "Mode 4 recurrence/固定小数warpではbit-equivalentではない。`135+rotation`へ修正すると"
        "seed→forward 81 words→inverse 81 words→ray 15 words→fd90 glow→writerが自然AEXとexact、"
        "public PF8/PF16/PF32もraw exact。主張はこの5×3 tupleに限定する。\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "raw_exact", "depths": 3, "natural_angle": 136,
                      "old_ray_differences": len(old_differences)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
