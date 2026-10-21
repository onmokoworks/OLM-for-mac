#!/usr/bin/env python3
"""Bounded OLMBlur classic PF_Cmd_RENDER public-entry closure.

The actual export is called at selector 0x0b through the repository's x64
Unicorn loader.  The pinned AEXCompat worker independently supplies the
registered parameter/lifecycle ABI and its PF8/PF16/PF32 world-flag transport
is hash-bound.  Production is compiled through EffectMain(PF_Cmd_RENDER).
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmblur_fullentry import build_context, build_pf_suites  # noqa: E402
import test_olmblur_32bpc_source_aex_adapter_20260717 as production  # noqa: E402
import test_olmblur_amount_repeat_legacy_matrix_actual_aex_20260810 as fixture  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMBlur.aex"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
ENTRY = 0x18000A970
CLASSIC_OWNER = 0x18000A180
WORKER_CHECKOUT = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout")
WORKER = WORKER_CHECKOUT / "guest/target/release/aex-guest-worker"
WORKER_SHA256 = "46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61"
WORKER_COMMIT = "28d535469f84f67236ef3425afe4291ea2fb0991"
WORKER_PIXEL = WORKER_CHECKOUT / "guest/crates/aex-guest-worker/src/pixel.rs"
WORKER_CLASSIC = WORKER_CHECKOUT / "guest/crates/aex-guest-worker/src/classic.rs"
SOURCE = ROOT / "mac/OLMBlur/OLMBlur.cpp"
GENERATOR = Path(__file__).resolve()
REPORT = ROOT / "refs/conformance/olmblur_classic_public_entry_closure_20260812.json"
DOC = ROOT / "refs/conformance/olmblur_classic_public_entry_closure_20260812.md"
WIDTH = HEIGHT = 24
PADDING = {8: 17, 16: 23, 32: 32}
PIXEL_BYTES = {8: 4, 16: 8, 32: 16}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def qword(loader: AexLoader, address: int, value: int) -> None:
    loader.write_bytes(address, struct.pack("<Q", value))


def guarded_alloc(loader: AexLoader, size: int, fill: int) -> tuple[int, int]:
    base = loader.bump_alloc(size + 128, align=64)
    loader.write_bytes(base, bytes((0xCC,)) * 64 + bytes((fill,)) * size + bytes((0xCC,)) * 64)
    return base, base + 64


def actual_classic(depth: int, bias: int, legacy: int) -> dict[str, object]:
    pixel_bytes, padding = PIXEL_BYTES[depth], PADDING[depth]
    active = WIDTH * pixel_bytes
    rowbytes = active + padding
    source = fixture.source_bytes(depth)
    assert len(source) == active * HEIGHT

    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    loader.register_import_impl(
        "pow", lambda ld, _args: (ld.write_xmm_f64(0, math.pow(ld.read_xmm_f64(0), ld.read_xmm_f64(1))) or 0)
    )
    loader.register_import_impl(
        "powf", lambda ld, _args: (ld.write_xmm_f32(0, math.pow(ld.read_xmm_f32(0), ld.read_xmm_f32(1))) or 0)
    )
    spbasic, handle_events = build_pf_suites(loader)
    in_data = build_context(loader, spbasic)
    out_data = loader.host_alloc(0x300)
    loader.write_bytes(out_data, b"\0" * 0x300)
    qword(loader, in_data + 0xB8, 0x12345678)
    loader.write_bytes(in_data + 0xE0, struct.pack("<iii", 7, 1, 24))

    input_base, input_pixels = guarded_alloc(loader, rowbytes * HEIGHT, 0xA5)
    output_base, output_pixels = guarded_alloc(loader, rowbytes * HEIGHT, 0xEE)
    for y in range(HEIGHT):
        loader.write_bytes(input_pixels + y * rowbytes, source[y * active:(y + 1) * active])

    def world(data: int) -> int:
        address = loader.host_alloc(0x80)
        loader.write_bytes(address, b"\0" * 0x80)
        loader.write_bytes(address + 0x10, struct.pack("<I", 0 if depth == 8 else 1))
        qword(loader, address + 0x18, data)
        loader.write_bytes(address + 0x20, struct.pack("<IIIH", rowbytes, WIDTH, HEIGHT, depth))
        return address

    input_world, output_world = world(input_pixels), world(output_pixels)
    copy_calls = 0

    def copy_world(ld: AexLoader, args: list[int]) -> int:
        nonlocal copy_calls
        copy_calls += 1
        source_pointer = struct.unpack("<Q", ld.read_bytes(args[1] + 0x18, 8))[0]
        destination_pointer = struct.unpack("<Q", ld.read_bytes(args[2] + 0x18, 8))[0]
        ld.write_bytes(destination_pointer, ld.read_bytes(source_pointer, rowbytes * HEIGHT))
        return 0

    utils = loader.host_alloc(0x48)
    loader.write_bytes(utils, b"\0" * 0x48)
    qword(loader, utils + 0x40, loader.install_callback("PF/copy", copy_world))
    qword(loader, in_data + 0xB0, utils)

    definitions = []
    for _ in range(6):
        address = loader.host_alloc(0xB0)
        loader.write_bytes(address, b"\0" * 0xB0)
        definitions.append(address)
    loader.write_bytes(definitions[0] + 0x38, loader.read_bytes(input_world, 0x78))
    loader.write_bytes(definitions[1] + 0x38, struct.pack("<d", 5.0))
    loader.write_bytes(definitions[2] + 0x38, struct.pack("<i", 100 * 65536))
    loader.write_bytes(definitions[3] + 0x38, struct.pack("<i", 2))
    loader.write_bytes(definitions[4] + 0x38, struct.pack("<i", bias))
    loader.write_bytes(definitions[5] + 0x38, bytes((legacy,)))
    params = loader.host_alloc(8 * len(definitions))
    loader.write_bytes(params, b"".join(struct.pack("<Q", item) for item in definitions))

    input_before = loader.read_bytes(input_base, rowbytes * HEIGHT + 128)
    param_before = b"".join(loader.read_bytes(item, 0xB0) for item in definitions)
    world_before = loader.read_bytes(output_world, 0x80)
    selectors = []
    instructions = {}
    for selector, name, cap in ((5, "sequence_setup", 100_000), (10, "frame_setup", 100_000)):
        call = loader.call_function(ENTRY, int_args=[selector, in_data, out_data, params, output_world, 0], max_instructions=cap)
        assert call["rax"] == 0
        selectors.append(selector)
        instructions[name] = call["instructions"]
    render = loader.call_function(ENTRY, int_args=[11, in_data, out_data, params, output_world, 0], max_instructions=100_000_000)
    selectors.append(11)
    instructions["render"] = render["instructions"]
    for selector, name in ((12, "frame_setdown"), (8, "sequence_setdown")):
        call = loader.call_function(ENTRY, int_args=[selector, in_data, out_data, params, output_world, 0], max_instructions=100_000)
        assert call["rax"] == 0
        selectors.append(selector)
        instructions[name] = call["instructions"]

    actual = bytearray()
    padding_mismatches = 0
    for y in range(HEIGHT):
        row = loader.read_bytes(output_pixels + y * rowbytes, rowbytes)
        actual.extend(row[:active])
        padding_mismatches += sum(byte != 0xA5 for byte in row[active:])
    input_after = loader.read_bytes(input_base, rowbytes * HEIGHT + 128)
    output_lead = loader.read_bytes(output_base, 64)
    output_trail = loader.read_bytes(output_pixels + rowbytes * HEIGHT, 64)
    param_after = b"".join(loader.read_bytes(item, 0xB0) for item in definitions)
    world_after = loader.read_bytes(output_world, 0x80)
    assert render["rax"] == 0 and copy_calls == 1
    assert bytes(actual) == source and padding_mismatches == 0
    assert input_before == input_after and param_before == param_after and world_before == world_after
    assert output_lead == output_trail == bytes((0xCC,)) * 64
    return {
        "id": f"actual_pf{depth}_bias{bias}_legacy{legacy}", "depth": depth,
        "bias": bias, "legacy": legacy, "selectors": selectors,
        "return_code": render["rax"], "copy_calls": copy_calls,
        "source_sha256": sha256_bytes(source), "active_sha256": sha256_bytes(bytes(actual)),
        "active_mismatches": sum(a != b for a, b in zip(actual, source)),
        "padding_mismatches": padding_mismatches, "input_and_guards_immutable": True,
        "params_and_output_world_immutable": True, "instructions": instructions,
        "handle_suite_events": len(handle_events),
    }


def production_probe_source() -> str:
    text = production.probe_source()
    old = "struct PF_WorldSuite2 { PF_Err PF_GetPixelFormat(PF_LayerDef*, int *format) { *format = 3; return PF_Err_NONE; } };"
    new = "extern int g_input_format, g_output_format; extern PF_LayerDef *g_input_world, *g_output_world; struct PF_WorldSuite2 { PF_Err PF_GetPixelFormat(PF_LayerDef *world, int *format) { *format = world == g_output_world ? g_output_format : g_input_format; return PF_Err_NONE; } }; int g_input_format = 0, g_output_format = 0; PF_LayerDef *g_input_world = nullptr, *g_output_world = nullptr;"
    if old not in text:
        raise RuntimeError("production harness world-suite shape drift")
    text = text.replace(old, new)
    start = text.index("int main(int argc, char **argv) {")
    text = text[:start] + r'''int main(int argc, char **argv) {
  if (argc != 11) return 2;
  const int depth=std::atoi(argv[1]), width=std::atoi(argv[2]), height=std::atoi(argv[3]);
  const double amount=std::strtod(argv[4],nullptr), smoothness=std::strtod(argv[5],nullptr);
  const int repeat=std::atoi(argv[6]), bias=std::atoi(argv[7]), legacy=std::atoi(argv[8]), mutation=std::atoi(argv[10]);
  const int pixel_bytes=depth==8?4:(depth==16?8:16), padding=depth==8?17:(depth==16?23:32);
  const std::size_t active=static_cast<std::size_t>(width)*pixel_bytes; const int rowbytes=(int)active+padding;
  const std::vector<std::uint8_t> source=read_file(argv[9]);
  if(source.size()!=active*height) return 4;
  std::vector<std::uint8_t> input(rowbytes*height,0xA5), output(rowbytes*height,0xEE);
  for(int y=0;y<height;++y) std::memcpy(input.data()+y*rowbytes,source.data()+y*active,active);
  PF_EffectWorld in{input.data(),rowbytes,width,height,(A_short)depth,{0,0,width,height},0};
  PF_EffectWorld out{output.data(),rowbytes,width,height,(A_short)depth,{0,0,width,height},0};
  if(mutation==1) out.width=23; else if(mutation==2) out.height=23;
  else if(mutation==3) out.rowbytes=rowbytes-1; else if(mutation==4) in.width=23;
  else if(mutation==5) in.height=23; else if(mutation==6) in.rowbytes=rowbytes-1;
  else if(mutation==7) in.data=nullptr; else if(mutation==8) out.data=nullptr;
  else if(mutation==10) in.width=out.width=23; else if(mutation==11) in.height=out.height=23;
  else if(mutation==12) in.rowbytes=out.rowbytes=rowbytes-1;
  PF_ParamDef defs[6]{}; defs[0].u.ld=in; defs[1].u.fs_d.value=amount;
  defs[2].u.fd.value=(A_long)(smoothness*65536.0); defs[3].u.sd.value=repeat;
  defs[4].u.pd.value=bias; defs[5].u.bd.value=legacy; PF_ParamDef *params[6]={&defs[0],&defs[1],&defs[2],&defs[3],&defs[4],&defs[5]};
  if(mutation>=15&&mutation<=18) params[mutation-15]=nullptr;
  PF_InData id{}; id.downsample_x={1,1}; id.downsample_y={1,1}; PF_OutData od{};
  g_input_world=&in; g_output_world=&out;
  g_input_format=depth==8?PF_PixelFormat_ARGB32:(depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128);
  g_output_format=mutation==9?PF_PixelFormat_ARGB64:g_input_format;
  const auto input_before=input; const PF_Err err=EffectMain(PF_Cmd_RENDER,&id,&od,mutation==13?nullptr:params,mutation==14?nullptr:&out,nullptr);
  std::size_t active_mismatch=0,padding_mismatch=0,untouched_mismatch=0;
  for(int y=0;y<height;++y){const auto *row=output.data()+y*rowbytes;
    for(std::size_t i=0;i<active;++i){active_mismatch+=row[i]!=source[(std::size_t)y*active+i]; untouched_mismatch+=row[i]!=0xEE;}
    for(int i=0;i<padding;++i){padding_mismatch+=row[active+i]!=(depth==32||amount!=5.0||smoothness!=100.0||repeat!=2?0xEE:0xA5); untouched_mismatch+=row[active+i]!=0xEE;}}
  std::printf("{\"err\":%d,\"active_mismatches\":%zu,\"padding_mismatches\":%zu,\"untouched_mismatches\":%zu,\"input_immutable\":%s}\n",(int)err,active_mismatch,padding_mismatch,untouched_mismatch,input==input_before?"true":"false");
  const bool admitted=depth!=32&&amount==5.0&&smoothness==100.0&&repeat==2&&mutation==0;
  return (admitted?(err||active_mismatch||padding_mismatch):(err!=PF_Err_BAD_CALLBACK_PARAM||untouched_mismatch))?3:0;
}
'''
    return text


def compile_production(directory: Path) -> Path:
    source = directory / "probe.cpp"
    source.write_text(production_probe_source().replace(
        "__OLMBLUR_MAC_SOURCE__", str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')))
    executable = directory / "probe"
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
    command = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-DOLMBLUR_HOSTLESS_RENDER_HARNESS=1",
        "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk, "-I", str(ROOT/"Headers"),
        "-I", str(ROOT/"Headers/SP"), "-I", str(ROOT/"Util"), "-I", str(ROOT/"Resources"),
        "-I", str(ROOT/"core"), str(source), *[str(ROOT/item) for item in (
            "core/olmblur_helper.cpp", "core/olmblur_fullworker_helper.cpp", "core/olmblur_worker16_nonlegacy.cpp",
            "core/olmblur_worker16_legacy.cpp", "core/olmblur_worker32_nonlegacy.cpp", "core/olmblur_worker32_legacy.cpp",
            "core/olmblur_worker8_legacy.cpp", "core/olmblur_worker_orchestration.cpp")], "-framework", "Cocoa", "-o", str(executable)]
    subprocess.run(command, cwd=ROOT, check=True)
    return executable


def run_production(executable: Path, fixture_dir: Path, depth: int, amount: float, smoothness: float, repeat: int, bias: int, legacy: int, mutation: int = 0) -> dict[str, object]:
    source = fixture_dir / f"source_pf{depth}.bin"
    source.write_bytes(fixture.source_bytes(depth))
    run = subprocess.run([str(executable), str(depth), str(WIDTH), str(HEIGHT), str(amount), str(smoothness),
                          str(repeat), str(bias), str(legacy), str(source), str(mutation)], cwd=ROOT, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(f"production probe failed: {run.stdout}\n{run.stderr}")
    row = json.loads(run.stdout)
    row.update({"id": f"production_pf{depth}_a{amount}_s{smoothness}_r{repeat}_b{bias}_l{legacy}_m{mutation}",
                "depth": depth, "amount": amount, "smoothness": smoothness, "repeat": repeat,
                "bias": bias, "legacy": legacy, "mutation": mutation, "source_sha256": sha256(source)})
    return row


def main() -> int:
    assert sha256(AEX) == AEX_SHA256
    assert sha256(WORKER) == WORKER_SHA256
    commit = subprocess.run(["git", "-C", str(WORKER_CHECKOUT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    assert commit == WORKER_COMMIT
    setup_run = subprocess.run([str(WORKER), "setup", str(AEX)], capture_output=True, text=True, check=True)
    setup = json.loads(setup_run.stdout)
    assert setup["execution_backend"] == "unicorn-x86_64"
    assert [(row["slot"], row["param_type"], row["default_value"]) for row in setup["parameters"]] == [
        (1, 10, 5.0), (2, 2, 100.0), (3, 1, 2.0), (4, 7, 1.0), (5, 4, 0.0)]
    actual = [actual_classic(depth, bias, legacy) for depth in (8, 16, 32) for bias, legacy in ((1, 0), (2, 0), (1, 1), (2, 1))]
    with tempfile.TemporaryDirectory(prefix="olmblur_classic_public_") as name:
        temporary = Path(name)
        executable = compile_production(temporary)
        admitted = [run_production(executable, temporary, depth, 5, 100, 2, bias, legacy)
                    for depth in (8, 16) for bias, legacy in ((1, 0), (2, 0), (1, 1), (2, 1))]
        rejected = [run_production(executable, temporary, 32, 5, 100, 2, 1, 0)]
        rejected += [run_production(executable, temporary, 8, *values) for values in (
            (6, 100, 2, 1, 0), (5, 99, 2, 1, 0), (5, 100, 1, 1, 0))]
        rejected += [run_production(executable, temporary, 8, 5, 100, 2, 1, 0, mutation)
                     for mutation in range(1, 19)]
    report = {
        "schema": "olmblur.classic-public-entry-closure/1", "status": "bounded_exact_and_fail_closed",
        "plugin": "OLMBlur", "actual_aex_sha256": AEX_SHA256,
        "actual_export": f"0x{ENTRY:x}", "actual_selector": "0x0b PF_Cmd_RENDER",
        "actual_owner": f"0x{CLASSIC_OWNER:x} FUN_18000a180", "geometry": [WIDTH, HEIGHT],
        "padding_bytes": PADDING,
        "aexcompat": {"worker_path": str(WORKER), "worker_sha256": WORKER_SHA256, "commit": commit,
                      "pixel_transport_sha256": sha256(WORKER_PIXEL), "classic_lifecycle_sha256": sha256(WORKER_CLASSIC),
                      "setup": {key: setup[key] for key in ("execution_backend", "global_setup_error", "params_setup_error", "advertised_num_params", "out_flags", "out_flags2", "parameters")}},
        "identity": {"production_source_sha256": sha256(SOURCE), "generator_sha256": sha256(GENERATOR),
                     "aex_loader_sha256": sha256(ROOT/"tools/emulation/aex_loader.py"),
                     "decomp_sha256": sha256(ROOT/"decomp/OLMBlur.aex.c.txt"),
                     "disasm_sha256": sha256(ROOT/"disasm/OLMBlur.aex.asm.txt")},
        "actual_public_cases": actual, "actual_raw_exact_copy": sum(row["active_mismatches"] == 0 for row in actual),
        "production_admitted_cases": admitted, "production_admitted_exact": len(admitted),
        "production_rejected_cases": rejected, "production_rejected_fail_closed": len(rejected),
        "production_rejection_mutations": {"1": "output width 23", "2": "output height 23",
            "3": "output rowbytes minus one", "4": "input width 23", "5": "input height 23",
            "6": "input rowbytes minus one", "7": "null input data", "8": "null output data",
            "9": "input PF8/output PF16 format mismatch", "10": "both widths 23",
            "11": "both heights 23", "12": "both rowbytes minus one", "13": "null params array",
            "14": "null output world", "15": "null input slot", "16": "null amount slot",
            "17": "null smoothness slot", "18": "null repeat slot"},
        "owner_facts": [
            "FUN_18000a180 reads only parameter slots 1..3; Bias slot 4 and Legacy slot 5 are not read",
            "the current registered Blur Amount is PF_Param_FLOAT_SLIDER default 5.0; FUN_18000a180 reads its low int32 dword, which is zero for IEEE-754 double 5.0",
            "the zero amount makes the selected non-Legacy worker return after the initial PF copy",
            "classic selects PF8 when PF_WorldFlag_DEEP is clear and PF16 when set; AEXCompat uses DEEP for both PF16 and PF32",
        ],
        "decision": {"pf8_pf16_default": "copy-only exact for Bias 1/2 and Legacy 0/1",
                     "bias_legacy": "ignored at classic owner; production no longer consumes them",
                     "pf32": "fail closed because the actual classic owner cannot distinguish PF32 from PF16",
                     "other_amount_smoothness_repeat": "fail closed; no generalized malformed classic parameter ABI claim",
                     "layout": "only equal non-null 24x24 input/output with depth-specific admitted padded rowbytes",
                     "numerical_owner": "advertised SmartPreRender/SmartRender remains unchanged"},
        "boundary": "Actual AEX classic export is direct Unicorn execution with bounded synthetic suites. The pinned AEXCompat worker executes setup/default discovery; its pixel.rs and classic.rs world/lifecycle transport are identity-bound source context only because the worker automatically chooses the advertised Smart path for pixels. This does not claim worker/native-AE classic pixel execution.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(
        "# OLMBlur classic public-entry closure\n\n"
        "The retained 2025 export routes selector `0x0b` to `FUN_18000a180`. On the registered default tuple "
        "(Amount 5, Smoothness 100, Repeat 2), PF8 and PF16 are copy-only exact at padded 24x24. Bias 2 and "
        "Legacy 1 are counterexamples to the former Mac contract: the owner never reads either slot, so all four "
        "Bias/Legacy combinations have identical output. Production now admits only this bounded PF8/PF16 tuple, "
        "copies the world, and leaves numerical rendering on Smart Render.\n\n"
        "PF32 is fail-closed in classic Render. The actual owner tests only `PF_WorldFlag_DEEP`; AEXCompat sets that "
        "flag for both PF16 and PF32, so the classic export cannot identify a float owner and aliases its PF16 branch. "
        "Non-default Amount/Smoothness/Repeat values are also rejected rather than generalizing the malformed classic "
        "float-slider read. Input, parameter definitions, world headers, row padding, and guards are bound in the JSON.\n\n"
        "Evidence boundary: the actual classic export uses the repository Unicorn loader. The pinned AEXCompat worker "
        "executes setup/default discovery; pixel.rs/classic.rs are identity-bound source context only because the worker "
        "automatically chooses Smart for pixels. Worker classic pixels and native AE classic routing are not executed here.\n")
    print(f"PASS_OLMBLUR_CLASSIC_PUBLIC actual={len(actual)} admitted={len(admitted)} rejected={len(rejected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
