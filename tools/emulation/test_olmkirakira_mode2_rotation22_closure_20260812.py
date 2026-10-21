#!/usr/bin/env python3
"""Close the Rotation-22 public Mode-2 seam against the natural AEX owner."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
BASE = ROOT / "tools/emulation/test_olmkirakira_mode1_exported_effectmain_all_depths_20260812.py"
PUBLIC = ROOT / "refs/conformance/olmkirakira_mode2_rotation22_exported_effectmain_all_depths_20260812.json"
OUT = ROOT / "refs/conformance/olmkirakira_mode2_rotation22_closure_20260812.json"
DOC = OUT.with_suffix(".md")
HISTORICAL = ROOT / "refs/conformance/olmkirakira_mode2_rotation22_pf32_seam_20260812.json"
CONSTRUCTED_FD0 = ROOT / "refs/conformance/olmkirakira_mode2_rotation22_ramp_helper_exact_20260812.json"
LOADER_PATH = ROOT / "tools/emulation/aex_loader.py"

WORKER = Path(os.environ.get(
    "OLM_AEX_GUEST_WORKER",
    "/Users/onmk/Documents/Projects/Personal/04_Tools/"
    "AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker",
))
EXPECTED_AEX_SHA = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"
EXPECTED_WORKER_SHA = "46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61"
EXPECTED_HISTORICAL_SHA = "f6711895b0cc6090dc2521701ecf73f56dc96aaad51f14b7dc0733a840cba91a"
EXPECTED_CONSTRUCTED_FD0_SHA = "b0f5ee885355e6791f00c3fe80d6ddf7d109092b38b2c6447cf7b460852d8bea"
EXPECTED_PUBLIC = {
    "PF8": (60, "189bb206a4ed6bf15e184de6f63fa2b4b72d21419b86e65ee6685d3b50f9f1c8"),
    "PF16": (120, "78700c7c4e5f680fcc9fc4b8fbd86d6e8ba364b252b6755cb47178c1b9014625"),
    "PF32": (240, "8c86b78f9a81cf7988ef7c76c2108e221b8cfc65fd129ac166e0b5e73651014f"),
}
EXPECTED_INPUT_PNG_SHA = "aa175f6a33d67ee4cdd8a8b7e4ef1c797a17f9ff1decfec69c87701b27c419f2"
EXPECTED_NATURAL_GLOW_SHA = "d3a6b01dfc10fa6e518821b5befd1fc559d4f766e2b479ed0100c9463f92e100"
EXPECTED_RAMP_PAYLOAD_SHA = "80030de202298d2f868e07b027eab0fe647a411c4f050b9b95f91b32902c1ea3"
EXPECTED_SUITE_REQUESTS = [
    "PF Handle Suite v2", "AEGP Utility Suite v13", "PF ColorParamSuite v1",
]
RAY_HEX = (
    "8c5d9e3e0ca8853ec370563e118a223eb692e53dfa74b03ec86caf3ee4ecb23e"
    "661ca93ee2078c3e9dee313ec5147b3e95d5a73ec0b1b93ead7fc03e"
)
NATURAL_GLOW_HEX = (
    "0000803f70f9403e00000000a936673e0000803f93dd223e000000006e23433e"
    "0000803fe9a6023e00000000a38a1c3e0000803f780fc63d00000000b34eed3d"
    "0000803f31df8b3d000000009f96a73dffff7f3f0305573e0000000046d0803e"
    "0000803f15c3553e00000000690f803e0000803f06075a3e00000000929d823e"
    "0000803f75114e3e00000000e7e6763e0000803f08a22a3e00000000e9714c3e"
    "0000803f2fd1d83d00000000f3e3013e0000803fdef9183e000000000b4a373e"
    "0000803f38834c3e00000000c009753e0000803f9546623e000000008f8e873e"
    "0000803f30916a3e000000002a868c3e"
)
STOPS = (
    (0.0, 1.0, 1.0, 0.0, 0.0),
    (0.7799999713897705, 1.0, 1.0, 0.6510000228881836, 0.0),
    (1.0, 1.0, 1.0, 1.0, 1.0),
)
PARAMS = (
    "Blur Mode=2", "Vertical Length=0", "Horizontal Length=7",
    "Diagonal Length=0", "Diagonal 2 length=0", "Highlight Radius=0",
    "Merge mode=2", "Channel=1", "Brightness Gain=0.73",
    "Glow Rotation=fixed:22", "Use Ramp@19=1",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def load_aex_loader():
    spec = importlib.util.spec_from_file_location("kira_closure_aex_loader", LOADER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.AexLoader


def captured_hex(witness: dict, phase: str) -> str | None:
    item = witness.get(phase, {})
    return item.get("hex") if item.get("status") == "captured" else None


def trace_natural_owner(directory: Path) -> dict[str, object]:
    input_png = directory / "input.png"
    output_png = directory / "trace-output.png"
    rgba = tuple((i * 15, i * 11, i * 7, 64 + i * 11) for i in range(15))
    image = Image.new("RGBA", (5, 3)); image.putdata(rgba); image.save(input_png)
    command = [
        str(WORKER), "render-trace-png", str(AEX), str(input_png), str(output_png),
        "--pixel-format", "argb32f",
        "--watch", "function=0x114e860,arg=stack6,size=2136,occurrence=1",
        "--watch", "function=0x114d7f0,arg=stack5,size=128,occurrence=1",
        "--watch", "function=0x1150790,arg=r9,deref=16,size=60",
        "--watch", "function=0x1232080,arg=rdx,size=324",
        "--watch", "function=0x114e460,arg=rcx,deref=400,size=240",
        *PARAMS,
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    raw = result.stdout.encode()
    trace = json.loads(result.stdout)
    smart = next(item for item in trace["execution_traces"] if item["selector"] == "SMART_RENDER")
    witnesses = smart["memory_witnesses"]

    builder = next(w for w in witnesses if w["watch_id"] == "watch-1")
    builder_hex = captured_hex(builder, "after")
    if builder_hex is None:
        raise AssertionError("owner builder return was not captured")
    builder_bytes = bytes.fromhex(builder_hex)
    typed_owner = next(w for w in witnesses if w["watch_id"] == "watch-2")
    typed_hex = captured_hex(typed_owner, "before") or captured_hex(typed_owner, "after")
    if typed_hex is None:
        raise AssertionError("typed owner context was not captured")
    typed_bytes = bytes.fromhex(typed_hex)

    ray_witnesses = [w for w in witnesses if w["watch_id"] == "watch-3"]
    ray_matches = []
    for witness in ray_witnesses:
        for phase in ("before", "after"):
            if captured_hex(witness, phase) == RAY_HEX:
                ray_matches.append((witness, phase))
    helper = [w for w in witnesses if w["watch_id"] == "watch-4"]
    helper_target_rvas = {f"0x{w['function_rva']:x}" for w in helper}
    helper_callsite_rvas = {f"0x{w['pc_rva']:x}" for w in helper}
    if helper_target_rvas != {"0x1232080"}:
        raise AssertionError(f"unexpected Ramp helper target RVAs: {helper_target_rvas}")
    if helper_callsite_rvas != {"0x114fe9c"}:
        raise AssertionError(f"unexpected Ramp helper callsite RVAs: {helper_callsite_rvas}")
    helper_payloads = {
        captured_hex(w, "before") for w in helper if captured_hex(w, "before") is not None
    }
    writer = next(w for w in witnesses if w["watch_id"] == "watch-5")
    writer_hex = captured_hex(writer, "before")
    if writer_hex is None:
        raise AssertionError("writer glow was not captured")

    expected_ramp = struct.pack("<I", len(STOPS)) + b"".join(
        struct.pack("<5f", *stop) for stop in STOPS)
    expected_ramp += bytes(0x144 - len(expected_ramp))
    observations = {
        "trace_stdout_sha256": sha(raw),
        "input_png_sha256": sha(input_png.read_bytes()),
        "raw_pixel_sha256": trace["raw_pixel_sha256"],
        "render_error": trace["render_error"],
        "guards_intact": trace["guards_intact"],
        "trace_truncated": smart["truncated"],
        "dropped_memory_witnesses": smart["dropped_memory_witnesses"],
        "owner_builder": {
            "target_rva": "0x114e860",
            "brightness_f32_bits": f"0x{struct.unpack_from('<I', builder_bytes, 0x04)[0]:08x}",
            "public_merge_mode_at_0x44": struct.unpack_from("<i", builder_bytes, 0x44)[0],
            "aggregation_selector_at_0x48": struct.unpack_from("<i", builder_bytes, 0x48)[0],
            "blur_mode_at_0x4c": struct.unpack_from("<i", builder_bytes, 0x4C)[0],
        },
        "typed_owner": {
            "target_rva": "0x114d7f0",
            "public_merge_mode_at_0x44": struct.unpack_from("<i", typed_bytes, 0x44)[0],
            "aggregation_selector_at_0x48": struct.unpack_from("<i", typed_bytes, 0x48)[0],
            "blur_mode_at_0x4c": struct.unpack_from("<i", typed_bytes, 0x4C)[0],
        },
        "natural_ray": {
            "bytes": 60, "hex": RAY_HEX, "sha256": sha(bytes.fromhex(RAY_HEX)),
            "matching_witness_phases": len(ray_matches),
        },
        "ramp_helper": {
            "target_rva": "0x1232080", "callsite_rva": "0x114fe9c",
            "enclosing_aggregator_rva": "0x114fd90", "hits": len(helper),
            "observed_target_rvas": sorted(helper_target_rvas),
            "observed_callsite_rvas": sorted(helper_callsite_rvas),
            "unique_payloads": len(helper_payloads),
            "payload_sha256": sha(expected_ramp),
            "all_payloads_exact": helper_payloads == {expected_ramp.hex()},
        },
        "writer_glow": {
            "watch": "FUN_18114e460 RCX deref +400", "bytes": 240,
            "hex": writer_hex, "sha256": sha(bytes.fromhex(writer_hex)),
        },
    }
    return observations


def sample_ramp(amount: float) -> tuple[float, float, float]:
    lower, upper = STOPS[0], STOPS[1]
    if amount >= upper[0]:
        lower, upper = STOPS[1], STOPS[2]
    t = f32(f32(amount - f32(lower[0])) / f32(f32(upper[0]) - f32(lower[0])))
    result = []
    for channel in range(2, 5):
        delta = f32(f32(f32(upper[channel]) - f32(lower[channel])) * t)
        result.append(f32(f32(lower[channel]) + delta))
    return tuple(result)  # type: ignore[return-value]


def portable_fd90(ray_bytes: bytes) -> bytes:
    output = []
    for ray in struct.unpack("<15f", ray_bytes):
        if ray <= f32(0.001):
            output.extend((0.0, 0.0, 0.0, 0.0)); continue
        alpha = max(0.0, min(1.0, f32(ray * f32(0.73))))
        red, green, blue = sample_ramp(alpha)
        r = f32(alpha * red); g = f32(alpha * green); b = f32(alpha * blue)
        inverse = f32(f32(1.0) / alpha)
        output.extend((f32(r * inverse), f32(g * inverse), f32(b * inverse), alpha))
    return struct.pack("<60f", *output)


def direct_fd90_replay() -> dict[str, object]:
    AexLoader = load_aex_loader()
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    zero = loader.host_alloc(60); loader.write_bytes(zero, bytes(60))
    active = loader.host_alloc(60); loader.write_bytes(active, bytes.fromhex(RAY_HEX))
    rays = loader.host_alloc(40); loader.write_bytes(rays, struct.pack("<5Q", zero, active, zero, zero, zero))
    colors = loader.host_alloc(80); loader.write_bytes(colors, struct.pack("<20f", *([1.0] * 20)))
    flags = loader.host_alloc(5); loader.write_bytes(flags, bytes((0, 1, 0, 0, 0)))
    ramp_payload = struct.pack("<I", len(STOPS)) + b"".join(struct.pack("<5f", *s) for s in STOPS)
    ramp_payload += bytes(0x144 - len(ramp_payload))
    ramps = loader.host_alloc(0x144 * 5); loader.write_bytes(ramps, ramp_payload * 5)
    glow = loader.host_alloc(240); loader.write_bytes(glow, bytes(240))
    hits: list[int] = []
    loader.add_code_hook(0x181232080, lambda *_args: hits.append(1))
    call = loader.call_function(
        0x18114FD90,
        [0, rays, colors, flags, ramps, 0, glow, 15, 1, 0x3F3AE148],
        max_instructions=500_000,
    )
    actual = loader.read_bytes(glow, 240)
    portable = portable_fd90(bytes.fromhex(RAY_HEX))
    natural = bytes.fromhex(NATURAL_GLOW_HEX)
    return {
        "target": "0x18114fd90", "pre_scaled_by_harness": False,
        "brightness_f32_bits": "0x3f3ae148", "flags_hex": "0001000000",
        "ramp_helper_hits": len(hits), "instructions": call["instructions"],
        "bytes": 240, "actual_sha256": sha(actual), "portable_sha256": sha(portable),
        "natural_writer_sha256": sha(natural),
        "actual_equals_portable": actual == portable,
        "actual_equals_natural_writer": actual == natural,
        "mismatch_count": sum(a != b for a, b in zip(actual, natural)),
    }


def run_public_all_depths() -> dict[str, object]:
    env = os.environ.copy()
    env.update({
        "OLM_KIRA_EXPORTED_CASE": "mode2_rotation22",
        "OLM_KIRA_BLUR_MODE": "2", "OLM_KIRA_MERGE_MODE": "2",
        "OLM_KIRA_HORIZONTAL_LENGTH": "7", "OLM_KIRA_HORIZONTAL_USE_RAMP": "1",
        "OLM_KIRA_BRIGHTNESS_GAIN": "0.73", "OLM_KIRA_GLOW_ROTATION": "22",
        "OLM_KIRA_GLOW_ROTATION_RAW_FIXED": "22",
        "OLM_KIRA_EXPORTED_REPORT": str(PUBLIC.relative_to(ROOT)),
        "OLM_AEX_GUEST_WORKER": str(WORKER),
    })
    result = subprocess.run(["python3", str(BASE)], cwd=ROOT, env=env)
    if result.returncode:
        raise RuntimeError("public all-depth comparison did not close")
    public = json.loads(PUBLIC.read_text(encoding="utf-8"))
    public["aexcompat_worker"] = {
        "sha256": EXPECTED_WORKER_SHA,
        "known_commit": "28d535469f84f67236ef3425afe4291ea2fb0991",
        "required_capability": "typed raw-fixed ANGLE override (Glow Rotation=fixed:22)",
        "current_main_boundary": "AEXCompat main lacks the typed raw-fixed ANGLE override",
    }
    PUBLIC.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    return public


def validate_report(report: dict[str, object]) -> bool:
    try:
        identities = report["identities"]
        assert identities["aex_sha256"] == EXPECTED_AEX_SHA
        assert identities["aexcompat_worker_sha256"] == EXPECTED_WORKER_SHA
        assert identities["production_source_sha256"] == sha(SOURCE.read_bytes())
        assert identities["generator_sha256"] == sha(Path(__file__).read_bytes())
        assert report["status"] == "raw_exact"
        fixture = report["fixture"]
        assert fixture == {
            "dimensions": [5, 3], "padding": 12, "blur_mode": 2,
            "public_merge_mode": 2, "horizontal_length": 7,
            "horizontal_use_ramp": True, "brightness_gain": 0.73,
            "brightness_f32_bits": "0x3f3ae148", "rotation_raw_fixed": 22,
            "ordered_parameters": list(PARAMS),
            "ordered_parameters_sha256": sha("\0".join(PARAMS).encode()),
        }
        natural = report["natural_trace"]
        assert natural["render_error"] == 0 and natural["guards_intact"]
        assert not natural["trace_truncated"] and natural["dropped_memory_witnesses"] == 0
        assert natural["input_png_sha256"] == EXPECTED_INPUT_PNG_SHA
        assert natural["raw_pixel_sha256"] == EXPECTED_PUBLIC["PF32"][1]
        assert natural["owner_builder"]["target_rva"] == "0x114e860"
        assert natural["owner_builder"]["brightness_f32_bits"] == "0x3f3ae148"
        assert natural["owner_builder"]["public_merge_mode_at_0x44"] == 2
        assert natural["owner_builder"]["aggregation_selector_at_0x48"] == 1
        assert natural["owner_builder"]["blur_mode_at_0x4c"] == 2
        assert natural["typed_owner"]["target_rva"] == "0x114d7f0"
        assert natural["typed_owner"]["public_merge_mode_at_0x44"] == 2
        assert natural["typed_owner"]["aggregation_selector_at_0x48"] == 1
        assert natural["typed_owner"]["blur_mode_at_0x4c"] == 2
        assert natural["ramp_helper"] == {
            "target_rva": "0x1232080", "callsite_rva": "0x114fe9c",
            "enclosing_aggregator_rva": "0x114fd90", "hits": 15,
            "observed_target_rvas": ["0x1232080"],
            "observed_callsite_rvas": ["0x114fe9c"],
            "unique_payloads": 1,
            "payload_sha256": EXPECTED_RAMP_PAYLOAD_SHA,
            "all_payloads_exact": True,
        }
        assert natural["natural_ray"]["bytes"] == 60
        assert natural["natural_ray"]["hex"] == RAY_HEX
        assert natural["natural_ray"]["sha256"] == sha(bytes.fromhex(natural["natural_ray"]["hex"]))
        assert natural["natural_ray"]["matching_witness_phases"] >= 1
        assert natural["writer_glow"]["bytes"] == 240
        assert natural["writer_glow"]["hex"] == NATURAL_GLOW_HEX
        assert natural["writer_glow"]["sha256"] == EXPECTED_NATURAL_GLOW_SHA
        replay = report["direct_replay"]
        assert replay["target"] == "0x18114fd90" and not replay["pre_scaled_by_harness"]
        assert replay["brightness_f32_bits"] == "0x3f3ae148"
        assert replay["flags_hex"] == "0001000000"
        assert replay["ramp_helper_hits"] == 15 and replay["bytes"] == 240
        assert replay["actual_sha256"] == EXPECTED_NATURAL_GLOW_SHA
        assert replay["portable_sha256"] == EXPECTED_NATURAL_GLOW_SHA
        assert replay["natural_writer_sha256"] == EXPECTED_NATURAL_GLOW_SHA
        assert replay["actual_equals_portable"] and replay["actual_equals_natural_writer"]
        assert replay["mismatch_count"] == 0
        public = report["public_all_depths"]
        assert public["status"] == "exact"
        assert [row["depth"] for row in public["rows"]] == ["PF8", "PF16", "PF32"]
        for row in public["rows"]:
            size, expected = EXPECTED_PUBLIC[row["depth"]]
            assert row["pixel_format"] == {"PF8": "argb8", "PF16": "argb16", "PF32": "argb32f"}[row["depth"]]
            assert row["bytes"] == size and row["exact"]
            assert row["actual_exported_raw_sha256"] == expected
            assert row["mac_effectmain_raw_sha256"] == expected
            assert row["render_error"] == 0 and row["guards_intact"]
            assert row["input_unchanged"] and row["mac_padding_preserved"]
            assert row["suite_requests"] == EXPECTED_SUITE_REQUESTS
            assert row["unsupported_suite_calls"] == []
            for key in ("smart_pre_render", "smart_render"):
                assert row[key]["attempted"] and row[key]["completed"] and row[key]["error"] == 0
            assert row["smart_pre_render"]["selector"] == "SMART_PRE_RENDER"
            assert row["smart_render"]["selector"] == "SMART_RENDER"
        assert report["history"]["historical_seam_sha256"] == EXPECTED_HISTORICAL_SHA
        assert report["history"]["constructed_fd0_diagnostic_sha256"] == EXPECTED_CONSTRUCTED_FD0_SHA
        assert report["history"]["withdrawn_inference"] == "natural public Merge 2 dispatches FUN_18114ffd0"
        return True
    except (AssertionError, KeyError, TypeError):
        return False


def main() -> int:
    if sha(AEX.read_bytes()) != EXPECTED_AEX_SHA:
        raise RuntimeError("unexpected OLMKiraKira AEX identity")
    if sha(WORKER.read_bytes()) != EXPECTED_WORKER_SHA:
        raise RuntimeError("Rotation22 requires the pinned typed-angle worker")
    if sha(HISTORICAL.read_bytes()) != EXPECTED_HISTORICAL_SHA:
        raise RuntimeError("historical seam evidence changed")
    if sha(CONSTRUCTED_FD0.read_bytes()) != EXPECTED_CONSTRUCTED_FD0_SHA:
        raise RuntimeError("constructed fd0 diagnostic evidence changed")
    with tempfile.TemporaryDirectory(prefix="kira_rotation22_closure_") as raw:
        natural = trace_natural_owner(Path(raw))
    replay = direct_fd90_replay()
    public = run_public_all_depths()
    report = {
        "schema_version": 1,
        "kind": "olmkirakira_mode2_rotation22_closure",
        "date": "2026-08-12", "status": "raw_exact",
        "claim_boundary": "fixed 5x3 tuple, actual AEX Smart owner versus Mac public EffectMain, PF8/PF16/PF32 raw bytes",
        "identities": {
            "aex_sha256": EXPECTED_AEX_SHA,
            "aexcompat_worker_sha256": EXPECTED_WORKER_SHA,
            "aexcompat_commit": "28d535469f84f67236ef3425afe4291ea2fb0991",
            "production_source_sha256": sha(SOURCE.read_bytes()),
            "generator_sha256": sha(Path(__file__).read_bytes()),
        },
        "fixture": {
            "dimensions": [5, 3], "padding": 12, "blur_mode": 2,
            "public_merge_mode": 2, "horizontal_length": 7,
            "horizontal_use_ramp": True, "brightness_gain": 0.73,
            "brightness_f32_bits": "0x3f3ae148", "rotation_raw_fixed": 22,
            "ordered_parameters": list(PARAMS),
            "ordered_parameters_sha256": sha("\0".join(PARAMS).encode()),
        },
        "natural_trace": natural,
        "direct_replay": replay,
        "public_all_depths": {"status": public["status"], "rows": public["rows"]},
        "history": {
            "historical_seam_sha256": sha(HISTORICAL.read_bytes()),
            "constructed_fd0_diagnostic_sha256": sha(CONSTRUCTED_FD0.read_bytes()),
            "retained_observations": "natural ray exact; old Mac glow differed by 3 words and final PF32 by 1 word",
            "withdrawn_inference": "natural public Merge 2 dispatches FUN_18114ffd0",
            "replacement": "owner +0x48 is fixed to 1; natural FUN_18114fd90 replay equals writer glow and corrected production",
        },
        "claims_not_made": [
            "No arbitrary geometry or Ramp payload promotion",
            "No claim that current AEXCompat main supports the raw-fixed ANGLE fixture",
            "No Mac AE installed/loaded-binary claim in this hostless closure",
        ],
    }
    if not validate_report(report):
        raise AssertionError("closure report validation failed")
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    DOC.write_text(
        "# OLMKiraKira Mode 2 Rotation 22° closure（2026-08-12）\n\n"
        "Status: **raw exact**\n\n"
        "Natural Smart ownerはUI Merge modeを`+0x44=2`へ保持する一方、inner aggregation selectorを"
        "`+0x48=1`へ固定し、`FUN_18114fd90`でBrightnessとRampを処理する。natural writer glow 240 bytesは"
        "未スケールrayからのdirect fd90 replayと完全一致し、修正後のpublic EffectMainもPF8/PF16/PF32で"
        "actual AEXとraw exact。旧`public Mode 2 -> FUN_18114ffd0`推論は撤回し、historical seam JSONは保持する。\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "raw_exact", "depths": 3, "natural_glow_bytes": 240,
                      "fd90_replay_exact": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
