#!/usr/bin/env python3
"""Compare natural actual-AEX writer words with the production Mac source path."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from unicorn import UC_PROT_READ, UC_PROT_WRITE
from unicorn.x86_const import (
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RAX,
    UC_X86_REG_RIP,
    UC_X86_REG_RSP,
)

ROOT = Path(__file__).resolve().parents[2]
NATURAL_HARNESS_DIR = ROOT / "tools/emulation"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
PRODUCTION = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_nonzero_writer_oracle_20260717.json"
NOTE = ROOT / "refs/conformance/olmdirectionalblur_nonzero_writer_oracle_20260717.md"
CROP = (556, 316, 572, 332)
WIDTH = HEIGHT = 16
POPULATE = 0x180006980
ROTATE = 0x180001EC0
WRITER = 0x180006B30
PRIVATE_STACK = 0x61000000
PRIVATE_STACK_SIZE = 0x10000
PRIVATE_RETURN = 0x821FFFF0


class ContractError(RuntimeError):
    """An exact execution contract needed by this comparison is unavailable."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_natural_harness():
    sys.path.insert(0, str(NATURAL_HARNESS_DIR))
    import test_olmdirectionalblur_iterate8_natural_prerender_followup_20260717 as natural

    return natural


def compile_oracle(directory: Path) -> tuple[Path, dict]:
    compiler_name = os.environ.get("CXX", "clang++")
    compiler = shutil.which(compiler_name)
    if not compiler:
        raise ContractError(f"production source execution requires compiler {compiler_name!r}")
    xcrun = shutil.which("xcrun")
    if not xcrun:
        raise ContractError("production source execution requires xcrun and a macOS SDK")
    sdk = subprocess.run(
        [xcrun, "--show-sdk-path"], capture_output=True, text=True, check=False
    )
    if sdk.returncode or not sdk.stdout.strip():
        raise ContractError(
            "production source execution requires a resolvable macOS SDK: "
            + sdk.stderr.strip()
        )

    helper = directory / "olmdirectionalblur_nonzero_writer_oracle.cpp"
    executable = directory / "olmdirectionalblur_nonzero_writer_oracle"
    production = str(PRODUCTION).replace("\\", "\\\\").replace('"', '\\"')
    helper.write_text(
        f'''#define OLM_DBLUR_TEST_SEAM 1
#include "{production}"

#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <vector>

int main(int argc, char **argv) {{
    if (argc != 3) return 2;
    std::ifstream input_file(argv[1], std::ios::binary);
    std::vector<std::uint8_t> rgba((std::istreambuf_iterator<char>(input_file)),
                                   std::istreambuf_iterator<char>());
    if (rgba.size() != {WIDTH * HEIGHT * 4}) return 3;
    std::vector<PF_Pixel8> input({WIDTH * HEIGHT});
    std::vector<PF_Pixel8> output({WIDTH * HEIGHT});
    for (std::size_t i = 0; i < input.size(); ++i) {{
        input[i].red = rgba[i * 4 + 0];
        input[i].green = rgba[i * 4 + 1];
        input[i].blue = rgba[i * 4 + 2];
        input[i].alpha = rgba[i * 4 + 3];
    }}
    PF_EffectWorld in{{}};
    PF_EffectWorld out{{}};
    in.data = reinterpret_cast<PF_PixelPtr>(input.data());
    out.data = reinterpret_cast<PF_PixelPtr>(output.data());
    in.rowbytes = out.rowbytes = {WIDTH} * sizeof(PF_Pixel8);
    in.width = out.width = {WIDTH};
    in.height = out.height = {HEIGHT};
    in.extent_hint = out.extent_hint = {{0, 0, {WIDTH}, {HEIGHT}}};
    OLMDirectionalBlurInfo info{{}};
    info.angle_deg = 0.0;
    info.brightness_gain = 1.0;
    info.front_strength = 8;
    info.render_scale_x = info.render_scale_y = 1.0;
    int used_exact = 0;
    const PF_Err error = OLMDirectionalBlurTestRenderWorld(
        &in, &out, &info, 8, &used_exact);
    if (error != PF_Err_NONE || used_exact != 1) return 4;
    std::ofstream output_file(argv[2], std::ios::binary);
    for (const PF_Pixel8 &pixel : output) {{
        const std::uint8_t argb[4] = {{pixel.alpha, pixel.red, pixel.green, pixel.blue}};
        output_file.write(reinterpret_cast<const char *>(argb), sizeof(argb));
    }}
    return output_file ? 0 : 5;
}}
''',
        encoding="utf-8",
    )
    command = [
        compiler,
        "-std=c++17",
        "-arch",
        "arm64",
        "-O2",
        "-fno-fast-math",
        "-ffp-contract=off",
        "-ffunction-sections",
        "-fdata-sections",
        "-Wno-unused-function",
        "-Wno-unused-parameter",
        "-isysroot",
        sdk.stdout.strip(),
        "-I",
        str(ROOT / "Headers"),
        "-I",
        str(ROOT / "Headers/SP"),
        "-I",
        str(ROOT / "Util"),
        "-I",
        str(ROOT / "Resources"),
        str(helper),
        str(ROOT / "core/dblur_frontonly.cpp"),
        str(ROOT / "core/dblur_rotate.cpp"),
        str(ROOT / "core/dblur_rowdriver.cpp"),
        str(ROOT / "core/dblur_field.cpp"),
        "-Wl,-dead_strip",
        "-framework",
        "Cocoa",
        "-o",
        str(executable),
    ]
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if build.returncode:
        raise ContractError(
            "production source-included OLMDirectionalBlurTestRenderWorld helper must compile: "
            + build.stderr.strip()
        )
    root_text = str(ROOT)
    temp_text = str(directory)
    sdk_text = sdk.stdout.strip()
    portable_flags = [
        value.replace(temp_text, "<temporary>").replace(root_text, ".").replace(sdk_text, "<sdk>")
        for value in command[1:]
    ]
    return executable, {
        "compiler": compiler,
        "architecture": "arm64",
        "flags": portable_flags,
        "helper_lifetime": "temporary",
    }


def run_oracle(directory: Path, rgba: bytes) -> tuple[bytes, dict]:
    executable, build = compile_oracle(directory)
    source_raw = directory / "source.rgba8"
    output_raw = directory / "production.argb8"
    source_raw.write_bytes(rgba)
    run = subprocess.run(
        [str(executable), str(source_raw), str(output_raw)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if run.returncode:
        raise ContractError(
            "production source dispatcher must accept the exact PF8 front-only contract; "
            f"helper exit={run.returncode}, stderr={run.stderr.strip()!r}"
        )
    output = output_raw.read_bytes()
    if len(output) != WIDTH * HEIGHT * 4:
        raise ContractError(
            "production source helper must return one typed PF_Pixel8 word per fixture pixel"
        )
    return output, build


def run_aex(source_png: Path) -> tuple[bytes, list[dict], dict]:
    natural = load_natural_harness()
    fixture = natural.load_fixture()
    state = {"private_calls": 0, "populate_calls": 0, "writer_calls": 0}
    writer_words: list[dict] = []
    checkpoints: list[str] = []

    class NaturalLoader(fixture.AexLoader):
        last = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.uc.mem_map(PRIVATE_STACK, PRIVATE_STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
            self.add_code_hook(ROTATE, lambda _ld, _address, _size: checkpoints.append(hex(ROTATE)))
            self.add_code_hook(0x180005628, lambda _ld, _address, _size: checkpoints.append("0x180005628"))
            NaturalLoader.last = self

    def call_actual(loader, address: int, args: list[int], limit: int) -> dict:
        saved = loader.uc.context_save()
        outer_rsp = loader.uc.reg_read(UC_X86_REG_RSP)
        outer_frame = loader.read_bytes(outer_rsp, 0x68)
        stack_pointer = (PRIVATE_STACK + PRIVATE_STACK_SIZE - 0x108) & ~0xF
        loader.write_bytes(stack_pointer, struct.pack("<Q", PRIVATE_RETURN))
        for index, value in enumerate(args[4:]):
            loader.write_bytes(stack_pointer + 0x28 + index * 8, struct.pack("<Q", value))
        for register, value in zip(
            (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9), args
        ):
            loader.uc.reg_write(register, value)
        loader.uc.reg_write(UC_X86_REG_RSP, stack_pointer)
        loader.uc.reg_write(UC_X86_REG_RIP, address)
        before = loader.instructions_executed
        try:
            loader.uc.emu_start(address, PRIVATE_RETURN, count=limit)
            result = {
                "entry": hex(address),
                "instructions": loader.instructions_executed - before,
                "rax": loader.uc.reg_read(UC_X86_REG_RAX),
                "return_rip": hex(loader.uc.reg_read(UC_X86_REG_RIP)),
            }
            if loader.uc.reg_read(UC_X86_REG_RIP) != PRIVATE_RETURN:
                raise ContractError(
                    f"actual AEX callback {address:#x} must return to the private sentinel"
                )
        finally:
            loader.uc.context_restore(saved)
        if loader.read_bytes(outer_rsp, 0x68) != outer_frame:
            raise ContractError(
                f"actual AEX callback {address:#x} must preserve the natural Iterate8 frame"
            )
        state["private_calls"] += 1
        return result

    def actual_populate(loader, params: int, y: int, x: int, pixel: bytes) -> None:
        pixel_ptr = loader.bump_alloc(4, align=4)
        loader.write_bytes(pixel_ptr, pixel)
        call_actual(loader, POPULATE, [params, x, y, pixel_ptr], 10000)
        if fixture.u32(loader, params + 0x80A0) == 26:
            state["populate_calls"] += 1

    def actual_writer(
        loader, params: int, y: int, x: int, out: bytearray, out_ptr: int, width: int
    ) -> None:
        stride = fixture.u32(loader, params + 0x80A0)
        row0 = fixture.u32(loader, params + 0x8098)
        col0 = fixture.u32(loader, params + 0x809C)
        base = fixture.u64(loader, params + 0x8090)
        index = (row0 + y) * stride + col0 + x
        typed_rgba = list(struct.unpack("<4f", loader.read_bytes(base + index * 16, 16)))
        callback = call_actual(loader, WRITER, [params, x, y, 0, out_ptr], 1000)
        packed = loader.read_bytes(out_ptr, 4)
        out_offset = (y * width + x) * 4
        out[out_offset:out_offset + 4] = packed
        if stride == 26:
            writer_words.append(
                {
                    "xy": [x, y],
                    "writer_input_rgba_f32": typed_rgba,
                    "pf_pixel8_argb": list(packed),
                    "pf_pixel8_word_le": f"0x{struct.unpack('<I', packed)[0]:08x}",
                    "callback_instructions": callback["instructions"],
                }
            )
            state["writer_calls"] += 1

    fixture.AexLoader = NaturalLoader
    fixture.model_populate = actual_populate
    fixture.model_output = actual_writer
    fixture_report_path = source_png.parent / "natural_fixture.json"
    old_argv = sys.argv
    sys.argv = [
        str(natural.FIXTURE_PATH),
        "--source", str(source_png),
        "--output", str(fixture_report_path),
        "--angle", "0",
        "--brightness-gain", "1",
        "--downsample-num", "1",
        "--downsample-den", "1",
        "--front-strength", "8",
        "--size-variation", "0",
        "--front-alpha-fade", "0",
        "--front-sharp-tail", "0",
        "--back-strength", "0",
        "--back-alpha-fade", "0",
        "--back-sharp-tail", "0",
        "--noise-variation", "0",
        "--world-area", "0", "0", str(WIDTH), str(HEIGHT),
        "--row-padding", "12",
        "--no-detour-rotate",
        "--max-instructions", "20000000",
    ]
    try:
        fixture_status = fixture.main()
    finally:
        sys.argv = old_argv
    continuations = []
    loader = NaturalLoader.last
    if loader is None:
        raise ContractError("natural harness must construct an AEX loader")
    for attempt in range(1, 5):
        start = loader.uc.reg_read(UC_X86_REG_RIP)
        if start == natural.GLOBAL_RETURN:
            break
        record = {"attempt": attempt, "start_rip": hex(start)}
        try:
            loader.uc.emu_start(start, natural.GLOBAL_RETURN, count=20000000)
            record["end_rip"] = hex(loader.uc.reg_read(UC_X86_REG_RIP))
        except Exception as exc:
            record.update({"error": type(exc).__name__, "message": str(exc)})
        continuations.append(record)
        if "error" in record or loader.uc.reg_read(UC_X86_REG_RIP) == natural.GLOBAL_RETURN:
            break
    fixture_report = json.loads(fixture_report_path.read_text(encoding="utf-8"))
    execution = fixture_report["execution"]
    callbacks = [hex(POPULATE), hex(WRITER)] if state["writer_calls"] else [hex(POPULATE)]
    if fixture_status != 0 or not checkpoints:
        raise ContractError(
            "natural harness must reach populate, real FUN_180001ec0, rotateback, and writer: "
            + json.dumps(fixture_report.get("blocked", {}), sort_keys=True)
        )
    if callbacks != [hex(POPULATE), hex(WRITER)]:
        raise ContractError(
            "natural Iterate8 callback order must be 0x180006980 then 0x180006b30: "
            + json.dumps(callbacks)
        )
    if (hex(ROTATE) not in checkpoints or "0x180005628" not in checkpoints or
            state["populate_calls"] != WIDTH * HEIGHT or state["writer_calls"] != WIDTH * HEIGHT):
        raise ContractError(
            "actual AEX path must invoke populate and writer once per fixture pixel and enter "
            f"FUN_180001ec0: state={state}, checkpoints={checkpoints}, continuations={continuations}"
        )
    output = b"".join(bytes(item["pf_pixel8_argb"]) for item in writer_words)
    return output, writer_words, {
        "fixture_status": fixture_report["status"],
        "fixture_blocked_reason": fixture_report.get("blocked", {}).get("reason"),
        "iterate_callbacks": callbacks,
        "natural_checkpoints_before_continuation": execution["checkpoints"],
        "continuations": continuations,
        "actual_rotate_hook_count": checkpoints.count(hex(ROTATE)),
        "actual_rotateback_hook_count": checkpoints.count("0x180005628"),
        "actual_callback_calls": state,
        "output_complete": fixture_report["output"]["complete"],
    }


def render_note(report: dict) -> str:
    comparison = report.get("comparison", {})
    if report["status"] == "blocked":
        result = f"Blocked fail-closed: {report['blocked']['missing_contract']}"
    else:
        result = (
            f"Exact match: `{comparison['exact']}` across "
            f"`{comparison['word_count']}` typed `PF_Pixel8` words."
        )
    return f"""# OLMDirectionalBlur nonzero writer oracle (2026-07-17)

- Status: `{report['status']}`
- {result}
- Fixture: checked-in `case_0001_before_effects.png` crop `{list(CROP)}`; no host pixels were fabricated.
- AEX chain: real `0x180006980` populate callback, real `FUN_180001ec0`, then real `0x180006b30` writer callback under the existing natural followup harness.
- Oracle: temporary source-included helper calling the production Mac `OLMDirectionalBlurTestRenderWorld` dispatcher with the same decoded RGBA bytes and parameter contract.
- Scope: local executable differential only; no Windows/AE claim and no production or ledger edits.
"""


def blocked_report(message: str) -> dict:
    return {
        "schema": 1,
        "kind": "olmdirectionalblur_nonzero_writer_oracle",
        "status": "blocked",
        "blocked": {"reason": "missing-equivalent-production-contract", "missing_contract": message},
        "fail_closed": {
            "production_source_edited": False,
            "ledger_edited": False,
            "host_pixels_fabricated": False,
            "windows_or_ae_claim": False,
        },
    }


def main() -> int:
    try:
        source_image = Image.open(SOURCE).convert("RGBA")
        crop = source_image.crop(CROP)
        rgba = crop.tobytes()
        interior = [crop.getpixel((x, y)) for y in range(4, 12) for x in range(4, 12)]
        if crop.size != (WIDTH, HEIGHT) or crop.getpixel((8, 8)) == (0, 0, 0, 0):
            raise ContractError("binary-grounded fixture must have a nonzero center pixel")
        if len(set(interior)) < 2:
            raise ContractError("binary-grounded fixture must discriminate interior geometry")

        with tempfile.TemporaryDirectory(prefix="olm_dblur_nonzero_writer_oracle_") as name:
            directory = Path(name)
            source_png = directory / "source_16x16.png"
            crop.save(source_png)
            aex_output, words, natural = run_aex(source_png)
            production_output, build = run_oracle(directory, rgba)

        mismatches = []
        for index, (actual, expected) in enumerate(zip(
            (aex_output[i:i + 4] for i in range(0, len(aex_output), 4)),
            (production_output[i:i + 4] for i in range(0, len(production_output), 4)),
        )):
            if actual != expected:
                mismatches.append({
                    "xy": [index % WIDTH, index // WIDTH],
                    "aex_argb": list(actual),
                    "production_argb": list(expected),
                })
        exact = not mismatches and len(aex_output) == len(production_output)
        report = {
            "schema": 1,
            "kind": "olmdirectionalblur_nonzero_writer_oracle",
            "status": "pass" if exact else "mismatch",
            "scope": "Local actual-AEX versus source-included production Mac algorithm; no Windows/AE claim",
            "fixture": {
                "source": str(SOURCE.relative_to(ROOT)),
                "source_sha256": sha256_path(SOURCE),
                "crop_ltrb": list(CROP),
                "dimensions": [WIDTH, HEIGHT],
                "decoded_rgba_sha256": sha256_bytes(rgba),
                "unique_interior_rgba": [list(pixel) for pixel in sorted(set(interior))],
                "center_xy": [8, 8],
                "center_rgba": list(crop.getpixel((8, 8))),
                "origin": "decoded crop of checked-in binary reference; no generated host pixels",
            },
            "aex": {
                "binary": str(AEX.relative_to(ROOT)),
                "binary_sha256": sha256_path(AEX),
                "natural_harness": str(natural_module_path().relative_to(ROOT)),
                "chain": [hex(POPULATE), "FUN_180001ec0", hex(WRITER)],
                "execution": natural,
                "typed_writer_words": words,
                "argb8_sha256": sha256_bytes(aex_output),
            },
            "production_oracle": {
                "source": str(PRODUCTION.relative_to(ROOT)),
                "source_sha256": sha256_path(PRODUCTION),
                "entry": "OLMDirectionalBlurTestRenderWorld -> RenderWorld -> RenderExactFrontOnly8",
                "parameters": {
                    "bitdepth": 8,
                    "angle_degrees": 0,
                    "brightness_gain": 1.0,
                    "front_strength": 8,
                    "front_alpha_fade": 0,
                    "render_scale": [1.0, 1.0],
                },
                "build": build,
                "argb8_sha256": sha256_bytes(production_output),
            },
            "comparison": {
                "exact": exact,
                "word_count": len(words),
                "mismatch_count": len(mismatches),
                "first_mismatches": mismatches[:16],
            },
            "fail_closed": {
                "production_source_edited": False,
                "ledger_edited": False,
                "host_pixels_fabricated": False,
                "windows_or_ae_claim": False,
                "equivalent_source_contract_exercised": True,
            },
            "command": "python3 tools/emulation/test_olmdirectionalblur_nonzero_writer_oracle_20260717.py",
        }
    except ContractError as exc:
        report = blocked_report(str(exc))
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    NOTE.write_text(render_note(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "report": str(REPORT.relative_to(ROOT)),
        "exact": report.get("comparison", {}).get("exact"),
        "missing_contract": report.get("blocked", {}).get("missing_contract"),
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def natural_module_path() -> Path:
    return NATURAL_HARNESS_DIR / "test_olmdirectionalblur_iterate8_natural_prerender_followup_20260717.py"


if __name__ == "__main__":
    raise SystemExit(main())
