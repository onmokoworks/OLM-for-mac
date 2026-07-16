#!/usr/bin/env python3
"""Compare the actual-AEX PF16 callback fixture to the Mac source RenderBits path.

The source side is compiled from the current production
``mac/OLMDistanceGradation/OLMDistanceGradation.cpp`` and calls
``RenderBits<PF_Pixel16>`` directly.  It does not contain expected output words
or a hand-written compose model.  The current degenerate AEX control is retained
as a fail-closed non-discriminating control; the comparison uses the smallest
branch change, ``refcon+0x90 = 0``, to exercise the non-degenerate compose path.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import probe_dg_pf16_wrapper_entry_20260717 as actual  # noqa: E402

WIDTH, HEIGHT, PAD = 8, 5, 12
ROWBYTES = WIDTH * 8 + PAD
CANARY = 0xA5
MAC_SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
SOURCE_BRIDGE = HERE / "dg_pf16_source_oracle_20260717.cpp"
SHIM_DIR = HERE / "dg_renderbits_real_harness_20260716"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_source_oracle(tmp: Path) -> tuple[ctypes.CDLL, list[str]]:
    compiler = shutil.which("clang++")
    if not compiler:
        raise RuntimeError("clang++ is required for the independent Mac source oracle")
    dylib = tmp / "libdg_pf16_source_oracle_20260717.dylib"
    command = [
        compiler,
        "-std=c++17",
        "-O0",
        "-fno-fast-math",
        "-ffp-contract=off",
        "-dynamiclib",
        "-I",
        str(SHIM_DIR),
        str(SOURCE_BRIDGE),
        str(ROOT / "core/olmdistancegradation_fieldgen.cpp"),
        "-o",
        str(dylib),
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    library = ctypes.CDLL(str(dylib))
    word_pointer = ctypes.POINTER(ctypes.c_uint16)
    function = library.dg_pf16_source_oracle_20260717
    contract = library.dg_pf16_source_oracle_contract_20260717
    contract.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
    contract.restype = ctypes.c_int
    field = library.dg_pf16_source_field_20260717
    field.argtypes = [word_pointer, ctypes.c_size_t,
                      ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
                      word_pointer, ctypes.c_size_t]
    field.restype = ctypes.c_int
    function.argtypes = [word_pointer, ctypes.c_size_t, word_pointer, ctypes.c_size_t,
                         ctypes.c_size_t, ctypes.c_size_t]
    function.restype = ctypes.c_int
    recorded = [
        Path(compiler).name,
        "-std=c++17", "-O0", "-fno-fast-math", "-ffp-contract=off", "-dynamiclib",
        "-I", "tools/emulation/dg_renderbits_real_harness_20260716",
        "tools/emulation/dg_pf16_source_oracle_20260717.cpp",
        "core/olmdistancegradation_fieldgen.cpp",
        "-o", "<temporary>/libdg_pf16_source_oracle_20260717.dylib",
    ]
    return library, recorded


def source_input() -> bytearray:
    data = bytearray([CANARY] * (ROWBYTES * HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            struct.pack_into("<4H", data, y * ROWBYTES + x * 8, 32768, 0, 0, 0)
    return data


def padding(data: bytes) -> bytes:
    return b"".join(data[y * ROWBYTES + WIDTH * 8 : (y + 1) * ROWBYTES]
                     for y in range(HEIGHT))


def active(data: bytes) -> bytes:
    return b"".join(data[y * ROWBYTES : y * ROWBYTES + WIDTH * 8]
                     for y in range(HEIGHT))


def run() -> dict[str, object]:
    control = actual.run(degenerate=True)
    if control["status"] != "PASS":
        return {"status": "blocked", "blocker": "actual-AEX degenerate control did not complete", "control": control}

    # The degenerate branch is not a useful equality oracle: it bypasses field
    # reads and emits the same use-background branch for every pixel. Keep it
    # recorded, then change only the branch flag for the discriminating run.
    actual_run = actual.run(degenerate=False)
    if actual_run["status"] != "PASS":
        return {
            "status": "blocked",
            "blocker": "actual-AEX non-degenerate branch did not complete",
            "control_degenerate": control,
            "actual_non_degenerate": actual_run,
        }

    actual_contract = actual_run["parameter_contract"]["values"]
    assert actual_contract["invert"] == 1
    assert actual_contract["inout_mode"] == 3
    assert actual_contract["render_mode"] == 1
    assert actual_contract["use_bg"] == 1
    assert actual_contract["interp_mode"] == 1
    assert actual_contract["grad_rgb"] == [28.0 / 255.0, 0.0, 238.0 / 255.0]
    assert actual_contract["bg_rgb"] == [0.0, 0.0, 0.0]

    with tempfile.TemporaryDirectory(prefix="dg_pf16_source_oracle_20260717.") as directory:
        library, command = build_source_oracle(Path(directory))
        source = source_input()
        source_before = bytes(source)
        output = bytearray([CANARY] * (ROWBYTES * HEIGHT))
        source_buffer = (ctypes.c_uint16 * (len(source) // 2)).from_buffer(source)
        output_buffer = (ctypes.c_uint16 * (len(output) // 2)).from_buffer(output)
        contract_values = (ctypes.c_float * 9)()
        contract_rc = library.dg_pf16_source_oracle_contract_20260717(contract_values, 9)
        assert contract_rc == 0
        expected_source_contract = [1.0, 3.0, 1.0, 1.0, 2.0, 1.0,
                                    28.0 / 255.0, 0.0, 238.0 / 255.0]
        assert b"".join(struct.pack("<f", value) for value in contract_values) == b"".join(
            struct.pack("<f", value) for value in expected_source_contract
        )
        rc = library.dg_pf16_source_oracle_20260717(
            source_buffer, ROWBYTES, output_buffer, ROWBYTES, WIDTH, HEIGHT)
        field_x = (ctypes.c_float * (WIDTH * HEIGHT))()
        d_alpha = (ctypes.c_float * (WIDTH * HEIGHT))()
        field_words = (ctypes.c_uint16 * (WIDTH * HEIGHT))()
        field_rc = library.dg_pf16_source_field_20260717(
            source_buffer, ROWBYTES, field_x, d_alpha, field_words, WIDTH * HEIGHT)
        assert field_rc == 0
        source_active = active(output)
        aex_active = b"".join(
            struct.pack("<4H", *words) for words in actual_run["output_active_words_agrb"]
        )
        source_padding = padding(output)
        source_field_words = [[0, int(field_words[i]), 0, 0] for i in range(WIDTH * HEIGHT)]
        source_field_active = b"".join(struct.pack("<4H", *words) for words in source_field_words)
        actual_observation = actual_run["compose_observation"]
        actual_refcon = actual_observation["refcon"]
        compose_semantic_match = (
            actual_refcon["degenerate"] == 0 and
            actual_refcon["inout_mode"] == 3 and actual_refcon["use_bg"] == 1 and
            actual_refcon["invert"] == 1 and actual_refcon["render_mode"] == 1 and
            actual_refcon["power"] == 1.0 and
            actual_observation["source_pixel_agrb"] == [32768, 0, 0, 0] and
            actual_refcon["bg_rgb"] == [0.0, 0.0, 0.0] and
            b"".join(struct.pack("<f", value) for value in actual_refcon["grad_rgb"]) ==
            b"".join(struct.pack("<f", value) for value in (28.0 / 255.0, 0.0, 238.0 / 255.0))
        )
        result = {
            "status": "PASS" if rc == 0 and source_active == aex_active and
                      source_padding == bytes([CANARY]) * (PAD * HEIGHT) else "blocked",
            "control_degenerate": {
                "status": control["status"],
                "compose_entries": control["compose_entry_hook_hits"],
                "equality_discriminating": False,
            },
            "actual_non_degenerate": {
                "status": actual_run["status"],
                "compose_entries": actual_run["compose_entry_hook_hits"],
                "active_sha256": actual_run["output_active_sha256"],
                "padding_preserved": actual_run["padding_canary"]["preserved"],
            },
            "source_oracle": {
                "return_code": rc,
                "field_return_code": field_rc,
                "contract_return_code": contract_rc,
                "contract_values": list(contract_values),
                "implementation": "production RenderBits<PF_Pixel16> -> shade_scanline<PF_Pixel16> -> compose_pixel",
                "mac_source_sha256": sha256(MAC_SOURCE),
                "bridge_sha256": sha256(SOURCE_BRIDGE),
                "compile_command": command,
                "active_sha256": hashlib.sha256(source_active).hexdigest(),
                "padding_sha256": hashlib.sha256(source_padding).hexdigest(),
                "padding_preserved": source_padding == bytes([CANARY]) * (PAD * HEIGHT),
                "input_unchanged": bytes(source) == source_before,
                "input_active_sha256": hashlib.sha256(active(source_before)).hexdigest(),
                "field_raw_words_agrb": source_field_words,
                "field_active_sha256": hashlib.sha256(source_field_active).hexdigest(),
                "field_x_values": list(field_x),
                "field_d_alpha_values": list(d_alpha),
            },
            "parameter_contract": {
                "actual_aex": actual_run["parameter_contract"],
                "source_semantics": {
                    "invert": 1, "inout_mode": 3, "render_mode": 1,
                    "use_bg": 1, "interp_mode": "linear", "power": 1.0,
                    "grad_rgb": [28.0 / 255.0, 0.0, 238.0 / 255.0],
                    "bg_rgb": [0.0, 0.0, 0.0],
                },
                "semantic_match": True,
            },
            "world_contract": {
                "actual_aex": actual_run["world_contract"],
                "source": {"width": WIDTH, "height": HEIGHT, "rowbytes": ROWBYTES,
                            "input_active_sha256": hashlib.sha256(active(source_before)).hexdigest()},
                "source_input_matches_actual": actual_run["world_contract"]["source_active_sha256"] == hashlib.sha256(active(source_before)).hexdigest(),
            },
            "first_divergence": {
                "actual_aex_field": actual_run["field_capture"],
                "source_field_input_to_shade": {
                    "active_sha256": hashlib.sha256(source_field_active).hexdigest(),
                    "raw_words_agrb": source_field_words,
                    "x_values": list(field_x),
                    "d_alpha_values": list(d_alpha),
                },
                "raw_field_words_equal": actual_run["field_capture"]["raw_words_agrb"] == source_field_words,
                "field_x_equal": all(abs(a - b) <= 1.0 / 32768.0 for a, b in zip(actual_run["field_capture"]["x_values"], field_x)),
                "classification": "fieldgen_or_staging" if actual_run["field_capture"]["raw_words_agrb"] != source_field_words else "compose_layout_or_later",
            },
            "compose_observation": {
                "actual_aex": actual_run["compose_observation"],
                "source": {
                    "refcon": {
                        "degenerate": 0, "inout_mode": 3, "use_bg": 1, "invert": 1,
                        "render_mode": 1, "interp_mode": "linear", "power": 1.0,
                        "grad_rgb": [28.0 / 255.0, 0.0, 238.0 / 255.0],
                        "bg_rgb": [0.0, 0.0, 0.0],
                    },
                    "source_pixel_agrb": [32768, 0, 0, 0],
                },
                "semantic_match": compose_semantic_match,
            },
            "comparison": {
                "active_byte_equal": source_active == aex_active,
                "active_byte_count": len(aex_active),
                "byte_mismatch_count": sum(a != b for a, b in zip(source_active, aex_active)),
                "first_mismatch_byte": next((i for i, (a, b) in enumerate(zip(source_active, aex_active)) if a != b), None),
                "source_active_words_agrb": [list(struct.unpack("<4H", source_active[i:i + 8]))
                                             for i in range(0, len(source_active), 8)],
                "actual_aex_active_words_agrb": actual_run["output_active_words_agrb"],
            },
            "claims": {
                "mac_source_oracle_execution": rc == 0,
                "windows_claim": False,
                "ae_exact_claim": False,
            },
        }
        return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
