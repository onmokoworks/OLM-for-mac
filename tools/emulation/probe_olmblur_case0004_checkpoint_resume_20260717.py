#!/usr/bin/env python3
"""Natural AEX checkpoint/resume probe for OLMBlur case_0004.

This probe deliberately keeps the worker and both helper bodies live.  A
checkpoint is taken at a real guest RIP and resumed in a fresh process; no
Python image prefill, helper detour, crop replay, or exactness claim is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_R9, UC_X86_REG_RDI, UC_X86_REG_R15, UC_X86_REG_RIP, UC_X86_REG_RSP

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader, RETURN_TRAMPOLINE  # noqa: E402
from test_olmblur_fullentry import build_context, build_pf_suites  # noqa: E402
import test_olmblur_case0006_fullentry as fullworker  # noqa: E402

AEX = ROOT / "plugins_2025/OLMBlur.aex"
MANIFEST = ROOT / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json"
INPUT_DIR = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625/input"
CASE_ID = "olmblur__case_0004"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
MANIFEST_SHA256 = "c4378358c8b4db2b2d5d12d0bf0b4142f141963538ca5ec4d86a49eeb8b9e71e"
INPUT_SHA256 = "930317e23068ea93bfd72961c2215e755e73cfd4ec784d97bccca223ed94e30a"
WIDTH, HEIGHT = 960, 540
FUN_ENTRY = 0x180002280
FUN_HORIZONTAL = 0x180001000
FUN_VERTICAL = 0x180001980
STAGING_DONE = 0x1800028DB
WRITER_PRE = 0x1800030E2
WRITER_POST = 0x180003123


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_sha(path: Path, expected: str) -> None:
    if not path.is_file():
        raise AssertionError(f"required dependency is missing: {path}")
    actual = sha256(path.read_bytes())
    if actual != expected:
        raise AssertionError(f"dependency hash mismatch for {path}: {actual}")


def load_case_input() -> tuple[bytes, dict[str, str]]:
    require_sha(AEX, AEX_SHA256)
    require_sha(MANIFEST, MANIFEST_SHA256)
    manifest = json.loads(MANIFEST.read_text())
    case = next((item for item in manifest.get("cases", []) if item.get("id") == CASE_ID), None)
    if case is None:
        raise AssertionError(f"manifest case is missing: {CASE_ID}")
    input_path = INPUT_DIR / case["before_effects_frame"]
    require_sha(input_path, INPUT_SHA256)
    width, height, rgba = fullworker.png_rgba16(input_path)
    if (width, height) != (WIDTH, HEIGHT):
        raise AssertionError(f"case_0004 dimensions differ: {(width, height)!r}")
    # This is the pinned input ABI conversion, performed before the guest
    # worker.  The guest staging code remains responsible for float planes.
    pf16 = bytearray(len(rgba))
    for offset in range(0, len(rgba), 8):
        r, g, b, a = struct.unpack_from(">4H", rgba, offset)
        struct.pack_into("<4H", pf16, offset, *((word + 1) // 2 for word in (a, r, g, b)))
    return bytes(pf16), {
        "path": str(input_path.relative_to(ROOT)),
        "png_sha256": INPUT_SHA256,
        "pf16_sha256": sha256(pf16),
    }


def _world(loader: AexLoader, data: int) -> int:
    address = loader.host_alloc(0x80)
    loader.write_bytes(address, b"\x00" * 0x80)
    loader.write_bytes(address + 0x18, struct.pack("<Q", data))
    loader.write_bytes(address + 0x20, struct.pack("<I", WIDTH * 8))
    loader.write_bytes(address + 0x24, struct.pack("<I", WIDTH))
    loader.write_bytes(address + 0x28, struct.pack("<I", HEIGHT))
    loader.write_bytes(address + 0x2C, struct.pack("<H", 16))
    return address


def _stable_release(_loader: AexLoader, _args: list[int]) -> int:
    return 0


def _params(loader: AexLoader) -> int:
    block = loader.host_alloc(0x40)
    loader.write_bytes(block, b"\x00" * 0x40)
    for offset, value in ((0x18, struct.pack("<I", 16)),
                          (0x20, struct.pack("<f", 125.599998474121)),
                          (0x24, struct.pack("<f", 100.0)),
                          (0x28, struct.pack("<I", 4)),
                          (0x2C, struct.pack("<I", 1))):
        loader.write_bytes(block + offset, value)
    return block


def setup_loader(pf16: bytes) -> tuple[AexLoader, int, int, int, dict]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    spbasic, events = build_pf_suites(loader)
    # The shared fixture's nested ReleaseSuite closure has an unstable
    # marshal fingerprint across fresh interpreter processes.  Keep the
    # checkpoint topology strict while using a module-level equivalent.
    release_stub = struct.unpack("<Q", loader.read_bytes(spbasic + 8, 8))[0]
    release_callback = next(address for address, (label, _handler) in loader.callbacks.items()
                            if label == "SPBasic.ReleaseSuite")
    if release_stub != release_callback:
        raise AssertionError("SPBasic.ReleaseSuite callback pointer is inconsistent")
    loader.callbacks[release_callback] = ("SPBasic.ReleaseSuite", _stable_release)
    context = build_context(loader, spbasic)
    source_data = loader.bump_alloc(len(pf16), align=64)
    output_data = loader.bump_alloc(len(pf16), align=64)
    loader.write_bytes(source_data, pf16)
    loader.write_bytes(output_data, pf16)
    params = _params(loader)
    return loader, context, _world(loader, source_data), _world(loader, output_data), {
        "callbacks": events, "source_data": source_data, "output_data": output_data,
        "params": params,
    }


def _parse_rip(value: str) -> int:
    try:
        rip = int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid RIP: {value}") from exc
    if not (0x180000000 <= rip < 0x190000000):
        raise argparse.ArgumentTypeError(f"RIP is outside the AEX image: {value}")
    return rip


def _helper_observer(capture: dict, direction: str):
    def hook(loader: AexLoader, address: int, _size: int) -> None:
        rsp = loader.uc.reg_read(UC_X86_REG_RSP)
        values = [struct.unpack("<i", loader.read_bytes(rsp + offset, 4))[0]
                  for offset in (0x28, 0x30, 0x38, 0x40, 0x48)]
        width, height, passes, offset, radius = values
        if radius < 0 or radius > max(WIDTH, HEIGHT):
            raise AssertionError(f"invalid {direction} helper radius: {radius}")
        weights = loader.uc.reg_read(UC_X86_REG_R9)
        capture["helpers"].append({
            "rip": hex(address), "direction": direction, "width": width,
            "height": height, "passes": passes, "offset": offset, "radius": radius,
            "caller_r15": hex(loader.uc.reg_read(UC_X86_REG_R15)),
            "weights_pointer": hex(weights),
        })
    return hook


def run(args: argparse.Namespace) -> dict:
    pf16, identity = load_case_input()
    loader, context, source, output, setup = setup_loader(pf16)
    capture = {"helpers": [], "writer": [], "staging": [], "checkpoint_saved": False}

    def staging(loader_: AexLoader, address: int, _size: int) -> None:
        capture["staging"].append(hex(address))

    def writer(label: str):
        def hook(loader_: AexLoader, address: int, _size: int) -> None:
            rsp = loader_.uc.reg_read(UC_X86_REG_RSP)
            capture["writer"].append({"label": label, "rip": hex(address),
                                      "rsp": hex(rsp), "rdi": hex(loader_.uc.reg_read(UC_X86_REG_RDI))})
        return hook

    loader.add_code_hook(STAGING_DONE, staging)
    loader.add_code_hook(FUN_HORIZONTAL, _helper_observer(capture, "horizontal"))
    loader.add_code_hook(FUN_VERTICAL, _helper_observer(capture, "vertical"))
    loader.add_code_hook(WRITER_PRE, writer("pre-store"))
    loader.add_code_hook(WRITER_POST, writer("post-store"))

    if args.resume_checkpoint:
        header = loader.load_checkpoint(args.resume_checkpoint)
        result = loader.resume_execution(args.max_instructions)
        capture["checkpoint_loaded"] = str(args.resume_checkpoint)
        capture["checkpoint_metadata"] = header.get("metadata", {})
        capture["resume"] = result
        if result["rip"] != RETURN_TRAMPOLINE:
            raise AssertionError(f"resume did not return before instruction cap: RIP=0x{result['rip']:x}")
        if not capture["helpers"]:
            raise AssertionError("resume did not reach a natural H/V helper")
        if not any(item["label"] == "pre-store" for item in capture["writer"]):
            raise AssertionError("resume did not reach writer pre-store")
        if not any(item["label"] == "post-store" for item in capture["writer"]):
            raise AssertionError("resume did not reach writer post-store")
    else:
        if not args.save_checkpoint_at_rip:
            raise AssertionError("one of --save-checkpoint-at-rip or --resume-checkpoint is required")
        checkpoint_path, checkpoint_rip = args.save_checkpoint_at_rip

        def save_at_rip(loader_: AexLoader, address: int, _size: int) -> None:
            if address != checkpoint_rip:
                return
            loader_.save_checkpoint(checkpoint_path, metadata={
                "probe": "olmblur.case0004.natural-helper-checkpoint",
                "checkpoint_rip": hex(checkpoint_rip),
                "entry": hex(FUN_ENTRY), "helper": hex(FUN_HORIZONTAL),
            })
            capture["checkpoint_saved"] = True
            loader_.uc.emu_stop()

        loader.add_code_hook(checkpoint_rip, save_at_rip)
        result = loader.call_function(FUN_ENTRY, int_args=[context, source, output, setup["params"]],
                                       max_instructions=args.max_instructions)
        capture["save"] = {key: result[key] for key in ("rax", "instructions")}
        capture["save"]["rip"] = hex(loader.uc.reg_read(UC_X86_REG_RIP))
        capture["checkpoint_path"] = str(checkpoint_path)
        capture["checkpoint_rip"] = hex(checkpoint_rip)
        if not capture["checkpoint_saved"]:
            raise AssertionError(f"checkpoint RIP was not reached: 0x{checkpoint_rip:x}")

    return {
        "schema": "olmblur.case0004.natural-helper-checkpoint/1",
        "status": "pass",
        "identity": {"case_id": CASE_ID, "aex_sha256": AEX_SHA256, "input": identity,
                      "entry": hex(FUN_ENTRY), "helpers": [hex(FUN_HORIZONTAL), hex(FUN_VERTICAL)]},
        "observed": capture,
        "claim_limit": "Natural AEX control-flow checkpoint/resume evidence only; no AE exactness claim.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save-checkpoint-at-rip", nargs=2, metavar=("PATH", "RIP"),
                        help="save at a natural guest RIP and stop")
    parser.add_argument("--resume-checkpoint", type=Path,
                        help="load a checkpoint into a fresh loader and continue")
    parser.add_argument("--max-instructions", type=int, default=30_000_000)
    args = parser.parse_args()
    if args.max_instructions <= 0:
        parser.error("--max-instructions must be positive")
    if bool(args.save_checkpoint_at_rip) == bool(args.resume_checkpoint):
        parser.error("choose exactly one checkpoint mode")
    if args.save_checkpoint_at_rip:
        args.save_checkpoint_at_rip = (Path(args.save_checkpoint_at_rip[0]),
                                       _parse_rip(args.save_checkpoint_at_rip[1]))
    try:
        print(json.dumps(run(args), indent=2, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "fail-closed", "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
