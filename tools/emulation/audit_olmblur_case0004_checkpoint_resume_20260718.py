#!/usr/bin/env python3
"""Classify the Mac-only actual-AEX case_0004 checkpoint boundaries.

The first process is delegated to the retained natural checkpoint probe.  A
fresh loader then resumes that checkpoint and records the same-run helper
plane values and PF16 writer values.  No helper body, writer, image plane, or
production source is detoured or rewritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RDI, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_RSP

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools" / "emulation"
sys.path.insert(0, str(TOOLS))
from aex_loader import AexLoader  # noqa: E402
from probe_olmblur_case0004_checkpoint_resume_20260717 import (  # noqa: E402
    FUN_HORIZONTAL,
    FUN_ENTRY,
    FUN_VERTICAL,
    INPUT_SHA256,
    MANIFEST_SHA256,
    AEX_SHA256,
    STAGING_DONE,
    WRITER_POST,
    WRITER_PRE,
    WIDTH,
    HEIGHT,
    load_case_input,
    setup_loader,
    run as retained_probe_run,
)

CASE_ID = "olmblur__case_0004"
CHECKPOINT_RIP = FUN_HORIZONTAL
RETURN_ADDRESSES = (
    0x1800029F5, 0x180002A27, 0x180002A5C, 0x180002A91,
    0x180002AC6, 0x180002AFA, 0x180002B30, 0x180002B62,
    0x180002B97, 0x180002BCC, 0x180002C01, 0x180002C35,
)
WITNESSES = ((411, 258), (458, 314))
SOURCE_PROBE = TOOLS / "probe_olmblur_case0004_checkpoint_resume_20260717.py"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def f32_record(loader: AexLoader, address: int) -> dict[str, object]:
    raw = loader.read_bytes(address, 12)
    values = struct.unpack("<3f", raw)
    words = struct.unpack("<3I", raw)
    return {"values": list(values), "bits_hex": [f"0x{x:08x}" for x in words]}


def u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def point(loader: AexLoader, plane: int, x: int, y: int) -> dict[str, object]:
    return f32_record(loader, plane + (y * WIDTH + x) * 12)


def save_natural_checkpoint(path: Path, cap: int) -> dict[str, object]:
    # Keep save and resume in this interpreter so the retained callback
    # fingerprint is stable.  This is the same retained probe entry point,
    # not a second checkpoint implementation.
    report = retained_probe_run(argparse.Namespace(
        resume_checkpoint=None,
        save_checkpoint_at_rip=(path, CHECKPOINT_RIP),
        max_instructions=cap,
    ))
    if report.get("status") != "pass" or not report.get("observed", {}).get("checkpoint_saved"):
        raise RuntimeError("natural checkpoint was not proven saved")
    if not path.is_file():
        raise RuntimeError("natural checkpoint file was not created")
    return {
        "status": report["status"],
        "instructions": report["observed"]["save"]["instructions"],
        "checkpoint_rip": report["observed"]["checkpoint_rip"],
        "checkpoint_sha256": digest(path.read_bytes()),
    }


def capture_resume(checkpoint: Path, cap: int) -> dict[str, object]:
    pf16, identity = load_case_input()
    loader, _context, _source, _output, _setup = setup_loader(pf16)
    capture: dict[str, object] = {
        "helpers": [], "writer": [], "staging_hits": [],
        "return_addresses": list(map(hex, RETURN_ADDRESSES)),
    }
    pending: dict[str, object] | None = None
    writer_pending: dict[str, object] | None = None

    def staging(loader_: AexLoader, address: int, _size: int) -> None:
        capture["staging_hits"].append(hex(address))

    def helper_entry(direction: str):
        def hook(loader_: AexLoader, address: int, _size: int) -> None:
            nonlocal pending
            rsp = loader_.uc.reg_read(UC_X86_REG_RSP)
            width, height, passes, offset, radius = [
                struct.unpack("<i", loader_.read_bytes(rsp + off, 4))[0]
                for off in (0x28, 0x30, 0x38, 0x40, 0x48)
            ]
            src = loader_.uc.reg_read(UC_X86_REG_RDX)
            dst = loader_.uc.reg_read(UC_X86_REG_R8)
            selected = {}
            for x, y in WITNESSES:
                axis = y if direction == "horizontal" else x
                if offset <= axis < offset + passes:
                    selected[f"({x},{y})"] = {
                        "src": point(loader_, src, x, y),
                        "dst_before": point(loader_, dst, x, y),
                    }
            record = {
                "call_index": len(capture["helpers"]),
                "direction": direction,
                "rip": hex(address),
                "return_address": hex(u64(loader_, rsp)),
                "abi": {"width": width, "height": height, "passes": passes,
                        "offset": offset, "radius": radius},
                "planes": {"src": hex(src), "dst": hex(dst)},
                "witnesses_before": selected,
            }
            capture["helpers"].append(record)
            pending = record
        return hook

    def helper_return(loader_: AexLoader, address: int, _size: int) -> None:
        nonlocal pending
        if pending is None or pending["return_address"] != hex(address):
            return
        dst = int(pending["planes"]["dst"], 16)
        pending["witnesses_after"] = {
            key: point(loader_, dst, *tuple(int(value) for value in key.strip("()").split(",")))
            for key in pending["witnesses_before"]
        }
        pending = None

    def writer_pre(loader_: AexLoader, _address: int, _size: int) -> None:
        nonlocal writer_pending
        destination = loader_.uc.reg_read(UC_X86_REG_RBX)
        source = loader_.uc.reg_read(UC_X86_REG_RDI) - 8
        entry = {
            "destination": hex(destination),
            "source": hex(source),
            "pre_store_rgb": f32_record(loader_, source),
            "stored_argb16_before": list(struct.unpack("<4H", loader_.read_bytes(destination, 8))),
        }
        capture["writer"].append(entry)
        writer_pending = entry

    def writer_post(loader_: AexLoader, _address: int, _size: int) -> None:
        if writer_pending is not None:
            writer_pending["stored_argb16_after"] = list(
                struct.unpack("<4H", loader_.read_bytes(int(writer_pending["destination"], 16), 8))
            )

    loader.add_code_hook(STAGING_DONE, staging)
    loader.add_code_hook(FUN_HORIZONTAL, helper_entry("horizontal"))
    loader.add_code_hook(FUN_VERTICAL, helper_entry("vertical"))
    for address in RETURN_ADDRESSES:
        loader.add_code_hook(address, helper_return)
    loader.add_code_hook(WRITER_PRE, writer_pre)
    loader.add_code_hook(WRITER_POST, writer_post)

    header = loader.load_checkpoint(checkpoint)
    result = loader.resume_execution(cap)
    return {
        "identity": identity,
        "checkpoint_metadata": header.get("metadata", {}),
        "resume": result,
        "helpers": capture["helpers"],
        "staging_hits": capture["staging_hits"],
        "writer": capture["writer"],
        "returned_to_trampoline": result["rip"] == 0xDEADC0DE,
    }


def classify(saved: dict[str, object], resumed: dict[str, object]) -> str:
    helpers = resumed["helpers"]
    writer = resumed["writer"]
    if not helpers:
        return "blocked_before_helper_output"
    if not all("witnesses_after" in item for item in helpers):
        return "helper_entry_observed_helper_output_incomplete"
    if not writer:
        return "helper_output_observed_writer_unreached"
    if not all("stored_argb16_after" in item for item in writer):
        return "writer_pre_store_observed_writer_post_store_incomplete"
    return "actual_aex_boundaries_observed_mac_comparison_pending"


def build_report(checkpoint: Path, saved: dict[str, object], resumed: dict[str, object], cap: int) -> dict[str, object]:
    return {
        "schema": "olmblur.case0004.checkpoint-resume-boundary-audit/1",
        "status": "pass" if resumed["helpers"] else "fail-closed",
        "classification": classify(saved, resumed),
        "scope": "Mac-only actual-AEX checkpoint/resume boundary evidence",
        "fact": {
            "aex_sha256": AEX_SHA256,
            "manifest_sha256": MANIFEST_SHA256,
            "input_png_sha256": INPUT_SHA256,
            "checkpoint_rip": hex(CHECKPOINT_RIP),
            "checkpoint_path": "<temporary>/olmblur_case0004_helper_entry.aexcp",
            "resume_instruction_cap": cap,
            "saved": saved,
            "resumed": resumed,
        },
        "inference": {
            "helper_entry": bool(resumed["helpers"]),
            "helper_output": bool(resumed["helpers"])
            and all("witnesses_after" in item for item in resumed["helpers"]),
            "writer_pre_store": bool(resumed["writer"]),
            "writer_post_store": bool(resumed["writer"]) and all("stored_argb16_after" in item for item in resumed["writer"]),
            "mac_comparison": "not performed by this audit; no AE exactness claim",
        },
        "claim_limit": "FACT is actual-AEX Unicorn boundary observation only. INFERENCE is classification of the observed boundary. This report does not claim AE exact, Windows exact, or production-source correctness.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/olmblur_case0004_checkpoint_resume_boundary_audit_20260718.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/conformance/olmblur_case0004_checkpoint_resume_boundary_audit_20260718.md")
    parser.add_argument("--checkpoint-cap", type=int, default=100_000_000)
    parser.add_argument("--resume-cap", type=int, default=100_000_000)
    args = parser.parse_args()
    checkpoint = Path("/tmp/olmblur_case0004_boundary_audit_20260718.aexcp")
    try:
        saved = save_natural_checkpoint(checkpoint, args.checkpoint_cap)
        resumed = capture_resume(checkpoint, args.resume_cap)
        report = build_report(checkpoint, saved, resumed, args.resume_cap)
        args.output_json.write_text(json.dumps(report, indent=2) + "\n")
        md = [
            "# OLMBlur case_0004 checkpoint/resume boundary audit (2026-07-18)", "",
            "## Result", "",
            f"- Classification: `{report['classification']}`.",
            "- This is Mac-only actual-AEX Unicorn evidence; it is not AE exact or Windows conformance evidence.",
            "",
            "## FACT", "",
            f"- Pinned AEX SHA-256: `{AEX_SHA256}`.",
            f"- Natural checkpoint reached `{hex(CHECKPOINT_RIP)}` after `{saved['instructions']}` instructions.",
            f"- Resume cap: `{args.resume_cap}` instructions; observed helper calls: `{len(resumed['helpers'])}`; writer pre-store hits: `{len(resumed['writer'])}`.",
            f"- Completed helper calls retain source/destination float32 words before and after the actual helper body: `{sum('witnesses_after' in item for item in resumed['helpers'])}/{len(resumed['helpers'])}`.",
            "- Each recorded writer retains pre-store RGB float32 words and destination ARGB16 words before/after the actual writer body.",
            "",
            "## INFERENCE", "",
            f"- The bounded classification is `{report['classification']}`.",
            "- Helper entry/output and writer boundaries are separated by same-run observations; this does not identify the first Mac-vs-Windows divergence.",
            "- No production source edit is justified by this audit alone.",
            "",
            "## Reproduction", "",
            "```text",
            "python3 tools/emulation/audit_olmblur_case0004_checkpoint_resume_20260718.py",
            "python3 tools/emulation/test_olmblur_case0004_checkpoint_resume_boundary_audit_20260718.py",
            "```",
            "",
            "## Changed files", "",
            "- `tools/emulation/audit_olmblur_case0004_checkpoint_resume_20260718.py`",
            "- `tools/emulation/test_olmblur_case0004_checkpoint_resume_boundary_audit_20260718.py`",
            "- `refs/conformance/olmblur_case0004_checkpoint_resume_boundary_audit_20260718.json`",
            "- `refs/conformance/olmblur_case0004_checkpoint_resume_boundary_audit_20260718.md`",
        ]
        args.output_md.write_text("\n".join(md) + "\n")
        print(json.dumps({"status": report["status"], "classification": report["classification"], "helpers": len(resumed["helpers"]), "writer": len(resumed["writer"]), "output_json": str(args.output_json)}, indent=2))
        return 0 if report["status"] == "pass" else 1
    except Exception as exc:
        failure = {"schema": "olmblur.case0004.checkpoint-resume-boundary-audit/1", "status": "fail-closed", "error": f"{type(exc).__name__}: {exc}", "claim_limit": "No exactness claim."}
        args.output_json.write_text(json.dumps(failure, indent=2) + "\n")
        print(json.dumps(failure, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
