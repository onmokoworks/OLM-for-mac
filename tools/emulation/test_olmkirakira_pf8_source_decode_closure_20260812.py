#!/usr/bin/env python3
"""Hash-bound the bounded OLMKiraKira PF8 reciprocal-multiply source decode."""
from __future__ import annotations

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
CORE = ROOT / "core/kirakira_highlight.h"
BASE = ROOT / "tools/emulation/test_olmkirakira_mode1_exported_effectmain_all_depths_20260812.py"
ORACLE = ROOT / "tools/emulation/olmkirakira_outer_compose_oracle_20260728.py"
OUT = ROOT / "refs/conformance/olmkirakira_pf8_source_decode_closure_20260812.json"
DOC = OUT.with_suffix(".md")
WORKER = Path(os.environ.get(
    "OLM_AEX_GUEST_WORKER",
    "/Users/onmk/Documents/Projects/Personal/04_Tools/"
    "AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker",
))

EXPECTED = {
    "aex": "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7",
    "worker": "46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61",
    "source": "f2e285be7e6caae764bef7c4fa4a6c422bd5312368ba3481022b9eabe9035492",
    "core": "e98232e4224b6ae4dd372216e10c29f3ba6621f68ab6cb10b56a02b9cc248390",
    "base": "9197fdec52592eaeea736889c9f0153406741c1d4a398fdd42bd10b0c161cf1a",
    "oracle": "6476b53fa377ca77fce3691d1cd5263a446878f459a8fac2bf7fa30b0dc4ce1e",
}
COMMIT = "28d535469f84f67236ef3425afe4291ea2fb0991"
INPUT_SHA = {
    "alpha_i_over_17": "192e69a33dde3ca1fcb13d54e9d4a311ddbd844a95626980571e8b9116f70818",
    "semi_transparent_color": "aa175f6a33d67ee4cdd8a8b7e4ef1c797a17f9ff1decfec69c87701b27c419f2",
}
PLANE_SHA = {
    "alpha_i_over_17": "b44884196d99b474887de19714105178a584a4db37fa3b8712c05cea60d53edb",
    "semi_transparent_color": "29d592bf7835777be4d5443b622b93ff41bdb3094f67dc63bc927a83d96c8d42",
}
SEED_SHA = "807a38189f7c835efc9c0aa2f8e9bbdffa08087a8fb150dae52bb6074273a5f3"
DIVIDE_SEED_SHA = "281139cc61343bc478d88ec592f27d909977147bc221ac1c7f96425e0d9f5376"
RAY_SHA = "77779fb72175473f3940c87892bb2a8a823ccf5c86876a48a19ec2de5e103259"
DIVIDE_RAY_SHA = "b68489d06eaf3491363568933851a9d06e4366f81bb38b45a1bb2f77ecb05815"
GLOW_SHA = "bd403de80a12e09679ab553ddf4d86f088b912b40b598e0d31423c873ca7b7dc"
FINAL_SHA = "46245e23f8902a243be948ae282b0b1b3bf53a9f276c0566bc820917076e5ec9"
DIVIDE_FINAL_SHA = "bc324d7262a0db99a20add695b708f1fa1ad82d399b15e3257d200f94edea73c"
PUBLIC_SHA = {
    "PF8": FINAL_SHA,
    "PF16": "71c2c1ae26ae4e63dc7e985f5b3666bd1a912fcc36d91842a0a2e65841693b13",
    "PF32": "df36edb6a9a16c88c2eb7582928b80493df46da1a46708ee75495a2e513c3dc4",
}
REGRESSION_SHA = {
    "PF8": "ff4de3ff2622faf02c62afe42a7c850586fea7f0fa7a3777f329b1d82b88ed5b",
    "PF16": "ee37cf06360d144b85b8d7a32ce9b0612af1f354a0a988c9e1e952e58b9ce41d",
    "PF32": "0d50d86e40f9dd25daef5683e78bc3c066501477ccc36c8c4c7eab0c274b2cb6",
}
LIFECYCLE_SHA = "32909aa0670cf57563ce0af1d7a047884cf4be7c421eeab9796229012c36bfa3"
SUITES = ["PF Handle Suite v2", "AEGP Utility Suite v13", "PF ColorParamSuite v1"]
FORMATS = {"PF8": "argb8", "PF16": "argb16", "PF32": "argb32f"}
SIZES = {"PF8": 60, "PF16": 120, "PF32": 240}
CLAIM = (
    "OLMKiraKira PF8 source decode only: fixed 5x3 alpha_i_over_17 and "
    "semi_transparent_color natural/exported fixtures"
)
RECIPROCAL_VA = 0x1814D65A4
RECIPROCAL_WORD = 0x3B808081
EXHAUSTIVE_DIFFERING_CODES_SHA = "47415d13b6e9cf7f14db3e4176827f70461302fa1bb233e19748f3c8cb1133c8"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def word(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def json_sha(value: object) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def read_pe_word(path: Path, va: int) -> dict[str, object]:
    data = path.read_bytes()
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    section_count = struct.unpack_from("<H", data, pe_offset + 6)[0]
    optional_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
    optional = pe_offset + 24
    magic = struct.unpack_from("<H", data, optional)[0]
    if magic != 0x20B:
        raise AssertionError("OLMKiraKira AEX is not PE32+")
    image_base = struct.unpack_from("<Q", data, optional + 24)[0]
    rva = va - image_base
    sections = optional + optional_size
    for index in range(section_count):
        offset = sections + index * 40
        name = data[offset:offset + 8].rstrip(b"\0").decode("ascii")
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from(
            "<IIII", data, offset + 8)
        if virtual_address <= rva < virtual_address + max(virtual_size, raw_size):
            file_offset = raw_pointer + rva - virtual_address
            raw = data[file_offset:file_offset + 4]
            if len(raw) != 4:
                raise AssertionError("reciprocal word falls outside AEX raw data")
            return {"va": f"0x{va:x}", "rva": f"0x{rva:x}", "section": name,
                    "file_offset": f"0x{file_offset:x}", "raw_hex": raw.hex(),
                    "u32_word": f"0x{struct.unpack('<I', raw)[0]:08x}"}
    raise AssertionError("reciprocal VA does not map to an AEX section")


def exhaustive_byte_domain() -> dict[str, object]:
    reciprocal = f32(1.0 / 255.0)
    differences = []
    for code in range(256):
        lane = f32(float(code))
        multiply = word(f32(lane * reciprocal))
        divide = word(f32(lane / f32(255.0)))
        if multiply != divide:
            differences.append({"code": code, "multiply": f"0x{multiply:08x}",
                                "divide": f"0x{divide:08x}",
                                "ulp": multiply - divide})
    return {"codes_tested": 256, "equal_codes": 256 - len(differences),
            "differing_codes": len(differences),
            "all_multiply_equals_divide_plus_one_ulp":
                all(item["ulp"] == 1 for item in differences),
            "differing_code_bytes_sha256": sha(bytes(item["code"] for item in differences)),
            "differences": differences}


def rgba(pattern: str) -> tuple[tuple[int, int, int, int], ...]:
    if pattern == "alpha_i_over_17":
        return tuple((0, 0, 0, i * 15) for i in range(15))
    if pattern == "semi_transparent_color":
        return tuple((i * 15, i * 11, i * 7, 64 + i * 11) for i in range(15))
    raise ValueError(pattern)


def captured(witness: dict, phase: str) -> bytes:
    item = witness[phase]
    if item.get("status") != "captured" or not item.get("hex"):
        raise AssertionError(f"{witness['watch_id']} {phase} not captured")
    return bytes.fromhex(item["hex"])


def natural_trace(directory: Path, pattern: str, full: bool) -> dict[str, object]:
    input_png = directory / f"{pattern}.png"
    output_png = directory / f"{pattern}-out.png"
    image = Image.new("RGBA", (5, 3)); image.putdata(rgba(pattern)); image.save(input_png)
    watches = ["function=0x114e110,arg=rcx,deref=296,size=240,occurrence=1"]
    if full:
        watches = [
            "function=0x114e110,arg=rcx,deref=400,size=240,occurrence=1",
            *watches,
            "function=0x114e110,arg=rdx,deref=24,size=60,occurrence=1",
        ]
    command = [str(WORKER), "render-trace-png", str(AEX), str(input_png), str(output_png),
               "--pixel-format", "argb8"]
    for watch in watches:
        command.extend(("--watch", watch))
    command.extend((
        "Blur Mode=1", "Vertical Length=0", "Horizontal Length=0",
        "Diagonal Length=0", "Diagonal 2 length=0", "Highlight Radius=3",
        "Merge mode=1", "Channel=1", "Brightness Gain=1", "Glow Rotation=0",
    ))
    process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if process.returncode:
        raise RuntimeError(process.stderr)
    trace = json.loads(process.stdout)
    smart = next(item for item in trace["execution_traces"] if item["selector"] == "SMART_RENDER")
    witnesses = {item["watch_id"]: item for item in smart["memory_witnesses"]}
    expected_ids = {f"watch-{i}" for i in range(1, len(watches) + 1)}
    if set(witnesses) != expected_ids:
        raise AssertionError(f"missing PF8 natural watches: {set(witnesses)}")
    source_id = "watch-2" if full else "watch-1"
    source = captured(witnesses[source_id], "before")
    result: dict[str, object] = {
        "input_png_sha256": sha(input_png.read_bytes()),
        "raw_pixel_sha256": trace["raw_pixel_sha256"],
        "render_error": trace["render_error"], "guards_intact": trace["guards_intact"],
        "trace_truncated": smart["truncated"],
        "dropped_memory_witnesses": smart["dropped_memory_witnesses"],
        "source_plane": {"bytes": len(source), "sha256": sha(source), "hex": source.hex()},
        "source_watch": {"function_rva": f"0x{witnesses[source_id]['function_rva']:x}",
                         "callsite_rva": f"0x{witnesses[source_id]['pc_rva']:x}",
                         "object_deref": 296},
    }
    if full:
        glow = captured(witnesses["watch-1"], "before")
        output = captured(witnesses["watch-3"], "after")
        result.update({
            "writer_glow": {"bytes": len(glow), "sha256": sha(glow), "hex": glow.hex()},
            "writer_output": {"bytes": len(output), "sha256": sha(output), "hex": output.hex()},
        })
    return result


RAY_CPP = r'''#include "__CORE__"
#include <bit>
#include <cstdint>
#include <cstdio>
#include <vector>
int main(){std::vector<float>x(15);for(float&v:x){unsigned w=0;if(std::scanf("%x",&w)!=1)return 2;v=std::bit_cast<float>((std::uint32_t)w);}auto y=olm::kirakira::highlight_isotropic_box_blur(x,5,3,7,1);for(float v:y)std::printf("%08x\n",std::bit_cast<std::uint32_t>(v));}
'''


def compile_ray(directory: Path, seed: bytes) -> bytes:
    source = directory / "pf8-one-pass.cpp"
    source.write_text(RAY_CPP.replace("__CORE__", str(CORE)), encoding="utf-8")
    executable = directory / "pf8-one-pass"
    subprocess.run(["c++", "-std=c++20", "-O2", "-ffp-contract=off", str(source),
                    "-o", str(executable)], cwd=ROOT, check=True)
    values = struct.unpack("<15I", seed)
    output = subprocess.check_output([str(executable)], cwd=ROOT,
                                     input="\n".join(f"{v:08x}" for v in values) + "\n",
                                     text=True)
    words = [int(line, 16) for line in output.splitlines()]
    if len(words) != 15:
        raise AssertionError("one-pass Highlight probe returned the wrong word count")
    return struct.pack("<15I", *words)


def load_oracle():
    spec = importlib.util.spec_from_file_location("kira_pf8_decode_oracle", ORACLE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def fd90_glow(ray: bytes) -> bytes:
    values: list[float] = []
    for amount in struct.unpack("<15f", ray):
        if amount <= f32(0.001):
            values.extend((0.0, 0.0, 0.0, 0.0)); continue
        alpha = max(0.0, min(1.0, f32(amount * f32(1.0))))
        premul = f32(alpha * f32(1.0))
        normalized = f32(premul * f32(f32(1.0) / alpha))
        values.extend((normalized, normalized, normalized, alpha))
    return struct.pack("<60f", *values)


def final_pf8(glow: bytes, source: bytes) -> bytes:
    oracle = load_oracle()
    glow_values = struct.unpack("<60f", glow)
    source_values = struct.unpack("<60f", source)
    return b"".join(
        oracle.stage_typed_writer(oracle.compose_pixel(
            glow_values[i * 4:i * 4 + 4], source_values[i * 4:i * 4 + 4],
            glow_opacity=1.0, source_opacity=1.0, merge_mode=1), depth="PF8")
        for i in range(15)
    )


def expected_plane(pattern: str, multiply: bool) -> bytes:
    reciprocal = f32(1.0 / 255.0)
    values = []
    for pixel in rgba(pattern):
        for lane in pixel:
            lane_f = f32(float(lane))
            values.append(f32(lane_f * reciprocal) if multiply else f32(lane_f / f32(255.0)))
    return struct.pack("<60f", *values)


def alpha_seed(plane: bytes) -> bytes:
    words = struct.unpack("<60I", plane)
    return struct.pack("<15I", *(words[i * 4 + 3] for i in range(15)))


def run_public(directory: Path, pattern: str, highlight: bool) -> dict[str, object]:
    report_path = directory / f"public-{pattern}.json"
    env = os.environ.copy()
    env.update({
        "OLM_KIRA_EXPORTED_CASE": f"pf8_source_decode_{pattern}",
        "OLM_KIRA_EXPORTED_REPORT": str(report_path),
        "OLM_KIRA_BLUR_MODE": "1", "OLM_KIRA_MERGE_MODE": "1",
        "OLM_KIRA_BRIGHTNESS_GAIN": "1" if highlight else "0.1",
        "OLM_KIRA_HORIZONTAL_LENGTH": "0" if highlight else "7",
        "OLM_KIRA_HIGHLIGHT_RADIUS": "3" if highlight else "0",
        "OLM_KIRA_SOURCE_PATTERN": pattern,
        "OLM_AEX_GUEST_WORKER": str(WORKER),
    })
    process = subprocess.run(["python3", str(BASE)], cwd=ROOT, env=env,
                             capture_output=True, text=True)
    if process.returncode:
        raise RuntimeError(
            f"public PF8 source-decode fixture failed: {pattern}: {process.stderr}")
    return json.loads(report_path.read_text(encoding="utf-8"))


def summarize_public(report: dict[str, object]) -> dict[str, object]:
    rows = []
    for row in report["rows"]:
        lifecycle = {"smart_pre_render": row["smart_pre_render"],
                     "smart_render": row["smart_render"]}
        rows.append({
            "depth": row["depth"], "pixel_format": row["pixel_format"],
            "bytes": row["bytes"], "exact": row["exact"],
            "actual_exported_raw_sha256": row["actual_exported_raw_sha256"],
            "mac_effectmain_raw_sha256": row["mac_effectmain_raw_sha256"],
            "mac_active_bytes_sha256": sha(bytes.fromhex(row["mac_effectmain_active_hex"])),
            "lifecycle": lifecycle, "lifecycle_sha256": json_sha(lifecycle),
            "render_error": row["render_error"], "guards_intact": row["guards_intact"],
            "input_unchanged": row["input_unchanged"],
            "mac_padding_preserved": row["mac_padding_preserved"],
            "suite_requests": row["suite_requests"],
            "unsupported_suite_calls": row["unsupported_suite_calls"],
        })
    return {"status": report["status"], "fixture": report["fixture"], "rows": rows}


def source_contract() -> dict[str, object]:
    text = SOURCE.read_text(encoding="utf-8")
    start = text.index("struct PixelTraits<PF_Pixel8>")
    end = text.index("template <>\nstruct PixelTraits<PF_Pixel16>", start)
    block = text[start:end]
    anchors = {
        "float32_reciprocal_declaration": block.count("constexpr float kByteToFloat = 1.0f / 255.0f;"),
        "lane_multiply_count": block.count("* kByteToFloat"),
        "stale_lane_divide_count": sum(block.count(f"p.{lane} / 255.0f")
                                       for lane in ("red", "green", "blue", "alpha")),
    }
    if anchors != {"float32_reciprocal_declaration": 1, "lane_multiply_count": 4,
                   "stale_lane_divide_count": 0}:
        raise AssertionError(f"PF8 source contract changed: {anchors}")
    binary = read_pe_word(AEX, RECIPROCAL_VA)
    if binary["u32_word"] != f"0x{RECIPROCAL_WORD:08x}":
        raise AssertionError(f"AEX PF8 reciprocal word changed: {binary}")
    return {"reciprocal_f32_word": "0x3b808081", "operation": "f32(byte * f32(1/255))",
            "aex_binary_reciprocal": binary, "production_anchors": anchors}


def validate_public(section: dict[str, object], expected: dict[str, str], pattern: str,
                    highlight: bool) -> None:
    assert section["status"] == "exact"
    fixture = section["fixture"]
    assert fixture["dimensions"] == [5, 3] and fixture["padding"] == 12
    assert fixture["source_pattern"] == pattern
    assert fixture["blur_mode"] == 1 and fixture["merge_mode"] == 1
    assert fixture["channel"] == 1 and fixture["glow_rotation"] == 0.0
    assert fixture["active_rays"] == ([{"name": "Highlight", "length": 3,
                                        "use_ramp": False}] if highlight else
                                      [{"name": "Horizontal", "length": 7,
                                        "use_ramp": False}])
    assert fixture["brightness_gain"] == (1.0 if highlight else 0.1)
    assert [row["depth"] for row in section["rows"]] == ["PF8", "PF16", "PF32"]
    for row in section["rows"]:
        depth = row["depth"]
        assert row["pixel_format"] == FORMATS[depth] and row["bytes"] == SIZES[depth]
        assert row["exact"]
        assert row["actual_exported_raw_sha256"] == expected[depth]
        assert row["mac_effectmain_raw_sha256"] == expected[depth]
        assert row["mac_active_bytes_sha256"] == expected[depth]
        assert row["lifecycle_sha256"] == LIFECYCLE_SHA
        assert row["lifecycle_sha256"] == json_sha(row["lifecycle"])
        assert row["render_error"] == 0 and row["guards_intact"]
        assert row["input_unchanged"] and row["mac_padding_preserved"]
        assert row["suite_requests"] == SUITES and row["unsupported_suite_calls"] == []
        for lifecycle in row["lifecycle"].values():
            assert lifecycle["attempted"] and lifecycle["completed"] and lifecycle["error"] == 0


def validate_report(report: dict[str, object]) -> bool:
    try:
        assert report["schema_version"] == 1
        assert report["kind"] == "olmkirakira_pf8_source_decode_closure"
        assert report["status"] == "raw_exact" and report["claim_boundary"] == CLAIM
        assert report["fixture"] == {
            "dimensions": [5, 3], "pixel_format": "PF8/argb8",
            "source_patterns": ["alpha_i_over_17", "semi_transparent_color"],
            "natural_parameters": [
                "Blur Mode=1", "Vertical Length=0", "Horizontal Length=0",
                "Diagonal Length=0", "Diagonal 2 length=0", "Highlight Radius=3",
                "Merge mode=1", "Channel=1", "Brightness Gain=1", "Glow Rotation=0",
            ],
        }
        identities = report["identities"]
        for key, path in (("aex", AEX), ("worker", WORKER), ("source", SOURCE),
                          ("core", CORE), ("base", BASE), ("oracle", ORACLE)):
            assert identities[f"{key}_sha256"] == EXPECTED[key]
            assert identities[f"{key}_sha256"] == sha(path.read_bytes())
        assert identities["generator_sha256"] == sha(Path(__file__).read_bytes())
        assert identities["aexcompat_commit"] == COMMIT
        contract = report["source_decode_contract"]
        assert contract["reciprocal_f32_word"] == "0x3b808081"
        assert contract["operation"] == "f32(byte * f32(1/255))"
        assert contract["aex_binary_reciprocal"] == read_pe_word(AEX, RECIPROCAL_VA)
        assert contract["aex_binary_reciprocal"] == {
            "va": "0x1814d65a4", "rva": "0x14d65a4", "section": ".rdata",
            "file_offset": "0x14d57a4", "raw_hex": "8180803b",
            "u32_word": "0x3b808081",
        }
        assert contract["production_anchors"] == {
            "float32_reciprocal_declaration": 1, "lane_multiply_count": 4,
            "stale_lane_divide_count": 0}
        exhaustive = report["exhaustive_byte_domain"]
        assert exhaustive == exhaustive_byte_domain()
        assert exhaustive["codes_tested"] == 256 and exhaustive["equal_codes"] == 130
        assert exhaustive["differing_codes"] == 126
        assert exhaustive["all_multiply_equals_divide_plus_one_ulp"]
        assert exhaustive["differing_code_bytes_sha256"] == EXHAUSTIVE_DIFFERING_CODES_SHA
        assert len(exhaustive["differences"]) == 126
        natural = report["natural_pf8"]
        for pattern in ("alpha_i_over_17", "semi_transparent_color"):
            item = natural[pattern]
            assert item["input_png_sha256"] == INPUT_SHA[pattern]
            assert item["source_plane"]["bytes"] == 240
            assert item["source_plane"]["sha256"] == PLANE_SHA[pattern]
            plane = bytes.fromhex(item["source_plane"]["hex"])
            assert len(plane) == 240 and sha(plane) == PLANE_SHA[pattern]
            assert plane == expected_plane(pattern, True)
            assert item["source_watch"] == {"function_rva": "0x114e110",
                                             "callsite_rva": "0x114d73d",
                                             "object_deref": 296}
            assert item["render_error"] == 0 and item["guards_intact"]
            assert not item["trace_truncated"] and item["dropped_memory_witnesses"] == 0
        alpha = natural["alpha_i_over_17"]
        assert alpha["raw_pixel_sha256"] == FINAL_SHA
        chain = report["alpha_highlight_chain"]
        source = bytes.fromhex(alpha["source_plane"]["hex"])
        seed = alpha_seed(source)
        ray = bytes.fromhex(chain["natural_ray_hex"])
        glow = bytes.fromhex(alpha["writer_glow"]["hex"])
        output = bytes.fromhex(alpha["writer_output"]["hex"])
        assert sha(seed) == chain["seed_sha256"] == SEED_SHA and len(seed) == 60
        assert sha(ray) == chain["natural_ray_sha256"] == RAY_SHA and len(ray) == 60
        assert chain["portable_one_pass_ray_sha256"] == RAY_SHA and chain["ray_exact"]
        assert sha(glow) == alpha["writer_glow"]["sha256"] == GLOW_SHA and len(glow) == 240
        assert chain["portable_fd90_glow_sha256"] == GLOW_SHA and chain["glow_exact"]
        assert sha(output) == alpha["writer_output"]["sha256"] == FINAL_SHA and len(output) == 60
        assert chain["portable_compose_writer_sha256"] == FINAL_SHA and chain["final_exact"]
        counter = report["divide_counterfactual"]
        divide_seed = expected_plane("alpha_i_over_17", False)
        divide_seed = alpha_seed(divide_seed)
        assert counter["seed_sha256"] == DIVIDE_SEED_SHA == sha(divide_seed)
        assert counter["ray_sha256"] == DIVIDE_RAY_SHA
        assert counter["final_pf8_sha256"] == DIVIDE_FINAL_SHA
        expected_differences = []
        actual_words = struct.unpack("<15I", seed); divide_words = struct.unpack("<15I", divide_seed)
        for index, (actual_word, divide_word) in enumerate(zip(actual_words, divide_words)):
            if actual_word != divide_word:
                expected_differences.append({"word": index, "source_byte": index * 15,
                    "actual_mul": f"0x{actual_word:08x}", "divide": f"0x{divide_word:08x}",
                    "ulp": abs(actual_word - divide_word)})
        assert counter["alpha_word_differences"] == expected_differences
        assert counter["alpha_difference_count"] == len(expected_differences) == 7
        assert counter["alpha_max_ulp"] == 1
        validate_public(report["public_alpha_i_over_17"], PUBLIC_SHA,
                        "alpha_i_over_17", True)
        validate_public(report["existing_semi_transparent_regression"], REGRESSION_SHA,
                        "semi_transparent_color", False)
        assert report["promotion"] == (
            "Mode 1 Highlight Radius=3 alpha_i_over_17 PF8/PF16/PF32; "
            "PF8 source decode is bounded to the two named 5x3 fixtures"
        )
        assert report["claims_not_made"] == [
            "No arbitrary source, dimensions, rowbytes, channel, parameter Cartesian product, or live-AE claim",
            "No PF16/PF32 source-decode rule change; those depths are regression controls",
            "No OLM plugin other than OLMKiraKira is covered by this closure",
        ]
        return True
    except (AssertionError, KeyError, TypeError, ValueError, struct.error):
        if os.environ.get("OLM_KIRA_CLOSURE_DEBUG") == "1":
            raise
        return False


def main() -> int:
    for key, path in (("aex", AEX), ("worker", WORKER), ("source", SOURCE),
                      ("core", CORE), ("base", BASE), ("oracle", ORACLE)):
        if sha(path.read_bytes()) != EXPECTED[key]:
            raise RuntimeError(f"unexpected pinned {key} identity")
    contract = source_contract()
    with tempfile.TemporaryDirectory(prefix="kira_pf8_source_decode_closure_") as raw:
        directory = Path(raw)
        alpha = natural_trace(directory, "alpha_i_over_17", True)
        semi = natural_trace(directory, "semi_transparent_color", False)
        actual_plane = bytes.fromhex(alpha["source_plane"]["hex"])
        seed = alpha_seed(actual_plane)
        ray = compile_ray(directory, seed)
        natural_glow = bytes.fromhex(alpha["writer_glow"]["hex"])
        natural_ray = struct.pack("<15I", *(struct.unpack("<60I", natural_glow)[i * 4 + 3]
                                            for i in range(15)))
        glow = fd90_glow(ray)
        final = final_pf8(glow, actual_plane)
        divide_plane = expected_plane("alpha_i_over_17", False)
        divide_seed = alpha_seed(divide_plane)
        divide_ray = compile_ray(directory, divide_seed)
        divide_glow = fd90_glow(divide_ray)
        divide_final = final_pf8(divide_glow, divide_plane)
        public = summarize_public(run_public(directory, "alpha_i_over_17", True))
        regression = summarize_public(run_public(directory, "semi_transparent_color", False))
    if ray != natural_ray or glow != natural_glow or final != bytes.fromhex(alpha["writer_output"]["hex"]):
        raise AssertionError("PF8 source decode chain is not natural-AEX exact")
    actual_words = struct.unpack("<15I", seed); divide_words = struct.unpack("<15I", divide_seed)
    differences = [{"word": index, "source_byte": index * 15,
                    "actual_mul": f"0x{actual_word:08x}",
                    "divide": f"0x{divide_word:08x}", "ulp": abs(actual_word - divide_word)}
                   for index, (actual_word, divide_word) in enumerate(zip(actual_words, divide_words))
                   if actual_word != divide_word]
    report = {
        "schema_version": 1, "kind": "olmkirakira_pf8_source_decode_closure",
        "date": "2026-08-12", "status": "raw_exact", "claim_boundary": CLAIM,
        "fixture": {
            "dimensions": [5, 3], "pixel_format": "PF8/argb8",
            "source_patterns": ["alpha_i_over_17", "semi_transparent_color"],
            "natural_parameters": [
                "Blur Mode=1", "Vertical Length=0", "Horizontal Length=0",
                "Diagonal Length=0", "Diagonal 2 length=0", "Highlight Radius=3",
                "Merge mode=1", "Channel=1", "Brightness Gain=1", "Glow Rotation=0",
            ],
        },
        "identities": {"aex_sha256": sha(AEX.read_bytes()),
                       "worker_sha256": sha(WORKER.read_bytes()),
                       "source_sha256": sha(SOURCE.read_bytes()),
                       "core_sha256": sha(CORE.read_bytes()),
                       "base_sha256": sha(BASE.read_bytes()),
                       "oracle_sha256": sha(ORACLE.read_bytes()),
                       "generator_sha256": sha(Path(__file__).read_bytes()),
                       "aexcompat_commit": COMMIT},
        "source_decode_contract": contract,
        "exhaustive_byte_domain": exhaustive_byte_domain(),
        "natural_pf8": {"alpha_i_over_17": alpha, "semi_transparent_color": semi},
        "alpha_highlight_chain": {
            "seed_bytes": 60, "seed_sha256": sha(seed),
            "natural_ray_hex": natural_ray.hex(), "natural_ray_sha256": sha(natural_ray),
            "portable_one_pass_ray_sha256": sha(ray), "ray_exact": ray == natural_ray,
            "portable_fd90_glow_sha256": sha(glow), "glow_exact": glow == natural_glow,
            "portable_compose_writer_sha256": sha(final),
            "final_exact": final == bytes.fromhex(alpha["writer_output"]["hex"]),
        },
        "divide_counterfactual": {
            "operation": "f32(byte / f32(255))",
            "seed_sha256": sha(divide_seed), "ray_sha256": sha(divide_ray),
            "final_pf8_sha256": sha(divide_final),
            "alpha_difference_count": len(differences),
            "alpha_max_ulp": max(item["ulp"] for item in differences),
            "alpha_word_differences": differences,
        },
        "public_alpha_i_over_17": public,
        "existing_semi_transparent_regression": regression,
        "promotion": ("Mode 1 Highlight Radius=3 alpha_i_over_17 PF8/PF16/PF32; "
                      "PF8 source decode is bounded to the two named 5x3 fixtures"),
        "claims_not_made": [
            "No arbitrary source, dimensions, rowbytes, channel, parameter Cartesian product, or live-AE claim",
            "No PF16/PF32 source-decode rule change; those depths are regression controls",
            "No OLM plugin other than OLMKiraKira is covered by this closure",
        ],
    }
    if not validate_report(report):
        raise AssertionError("PF8 source-decode closure report validation failed")
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    DOC.write_text(
        "# OLMKiraKira PF8 source-decode closure（2026-08-12）\n\n"
        "Status: **raw exact**\n\n"
        "5×3 `alpha_i_over_17` と既存半透明fixtureに限定し、PF8 byte laneを"
        "`f32(byte * f32(1/255))`で読むWindows規則を自然AEX source planeで固定した。"
        "alpha fixtureはdivision counterfactualより7 wordsが各1 ULP高い。修正後は"
        "seed→Mode 1 Highlight ray→fd90 glow→compose/writer→public PF8がraw exactで、"
        "同じpublic tupleのPF16/PF32もexact。既存半透明3-depth hashも不変。\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "raw_exact", "alpha_word_differences": len(differences),
                      "public_depths": 3, "regression_depths": 3}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
