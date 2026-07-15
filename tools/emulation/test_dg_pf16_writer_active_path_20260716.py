#!/usr/bin/env python3
"""Census the DG PF16 writer leaves while running the actual-AEX compose path.

The existing case_0023 compose fixture is the largest runnable DG path in this
repository: it executes the real compose callback and checks its final words.
This script installs entry hooks for compose and both PF16 writer leaves in
one Unicorn loader session.  It does not call the writer leaves as controls;
that would turn an active-path census into a direct-leaf probe.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from datetime import UTC, datetime
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from test_dg_compose import (  # noqa: E402
    FIELD_X_BY_PIXEL,
    WINDOWS_FINAL_RGBA16,
    build_case0023_refcon,
    build_world,
    make_loader,
)

FUN_RGB = 0x181458030
FUN_RGBA = 0x1814581A0
FUN_COMPOSE = 0x181170480
AEX = ROOT / "aex" / "OLMDistanceGradation" / "Plugins" / "64" / "2025" / "DistanceGradation.aex"
OUTPUT_JSON = ROOT / "refs" / "conformance" / "dg_pf16_writer_active_path_20260716.json"
OUTPUT_MD = ROOT / "refs" / "conformance" / "dg_pf16_writer_active_path_20260716.md"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def u64(loader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def f32_words(loader, address: int, count: int) -> tuple[list[float], str]:
    count = max(0, min(count, 16))
    raw = loader.read_bytes(address, count * 4)
    return list(struct.unpack("<%df" % count, raw)), raw.hex()


def run_census() -> dict[str, object]:
    loader = make_loader()
    entry_log: list[dict[str, object]] = []
    writer_entries: list[dict[str, object]] = []

    def capture_compose(ld, address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        entry_log.append({
            "function": hex(address),
            "rcx": hex(ld.uc.reg_read(UC_X86_REG_RCX)),
            "rdx": hex(ld.uc.reg_read(UC_X86_REG_RDX)),
            "r8d": ld.uc.reg_read(UC_X86_REG_R8) & 0xFFFFFFFF,
            "return_address": hex(u64(ld, rsp)),
        })

    def capture_writer(ld, address: int, _size: int) -> None:
        rcx = ld.uc.reg_read(UC_X86_REG_RCX)
        rdx = ld.uc.reg_read(UC_X86_REG_RDX)
        count = ld.uc.reg_read(UC_X86_REG_R8) & 0xFFFFFFFF
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        floats, raw_hex = f32_words(ld, rcx, count)
        record = {
            "function": hex(address),
            "rcx": hex(rcx),
            "rcx_float32": floats,
            "rcx_float32_raw_hex": raw_hex,
            "rdx": hex(rdx),
            "r8d": count,
            "return_address": hex(u64(ld, rsp)),
            "destination_words_before_return": list(struct.unpack("<4H", ld.read_bytes(rdx, 8))),
            "destination": rdx,
        }
        entry_log.append({k: v for k, v in record.items() if k != "destination"})
        writer_entries.append(record)

    loader.add_code_hook(FUN_COMPOSE, capture_compose)
    loader.add_code_hook(FUN_RGB, capture_writer)
    loader.add_code_hook(FUN_RGBA, capture_writer)

    points = sorted(WINDOWS_FINAL_RGBA16)
    field_pixels = {
        xy: (0, int(round(field_x * 32768.0)), 0, 0)
        for xy, field_x in FIELD_X_BY_PIXEL.items()
    }
    field_world = build_world(loader, 420, 400, field_pixels)
    source_world = build_world(loader, 420, 400, {})
    refcon = build_case0023_refcon(loader, field_world, source_world)
    output_addresses: list[int] = []
    final_outputs: list[dict[str, object]] = []

    for x, y in points:
        output = loader.bump_alloc(8, align=16)
        loader.write_bytes(output, b"\xee" * 8)
        output_addresses.append(output)
        loader.call_function(FUN_COMPOSE, int_args=[refcon, x, y, 0, output], max_instructions=200_000)
        words = list(struct.unpack("<4H", loader.read_bytes(output, 8)))
        if words == [0xEEEE] * 4:
            raise AssertionError(f"compose produced no final words at {(x, y)}")
        final_outputs.append({
            "xy": [x, y],
            "output_address": hex(output),
            "final_words_agrb": words,
            "final_output_written": True,
        })

    for record in writer_entries:
        destination = int(record.pop("destination"))
        record["final_words_after_return"] = list(struct.unpack("<4H", loader.read_bytes(destination, 8)))
        record["final_words_captured"] = True

    return {
        "schema": "olmdistancegradation.pf16-writer-active-path-census/1",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "inactive_for_fixture" if not writer_entries else "writer_hit",
        "classification": "bounded Mac-local Unicorn actual-AEX census; no AE-exact claim",
        "binary": {"path": str(AEX.relative_to(ROOT)), "sha256": sha256_file(AEX)},
        "fixture": {
            "source": "tools/emulation/test_dg_compose.py case_0023 compose fixture",
            "path_kind": "compose_to_final_output",
            "compose_reached": any(item["function"] == hex(FUN_COMPOSE) for item in entry_log),
            "final_output_reached": bool(final_outputs),
            "points": [list(point) for point in points],
            "active_path_limit": "The fixture does not establish an AE host/full effect entry or a compose-to-writer dispatch callback.",
        },
        "hooks": {
            "FUN_181458030": hex(FUN_RGB),
            "FUN_1814581a0": hex(FUN_RGBA),
            "FUN_181170480": hex(FUN_COMPOSE),
            "same_loader_session": True,
        },
        "entry_log": entry_log,
        "writer_hits": writer_entries,
        "final_outputs": final_outputs,
        "conclusion": {
            "writer_leaf_hit_counts": {
                "FUN_181458030": sum(item["function"] == hex(FUN_RGB) for item in writer_entries),
                "FUN_1814581a0": sum(item["function"] == hex(FUN_RGBA) for item in writer_entries),
            },
            "interpretation": (
                "Neither writer leaf hit on this runnable compose-to-final-output fixture; this is inactive_for_fixture, "
                "not a global dead-code conclusion."
                if not writer_entries else
                "At least one requested writer leaf hit; records include the requested ABI and final destination words."
            ),
            "ae_exact_claim": False,
            "production_edits": False,
        },
    }


def render_md(report: dict[str, object]) -> str:
    hits = report["writer_hits"]
    lines = [
        "# DG PF16 writer active-path census",
        "",
        f"- Status: `{report['status']}`",
        "- Scope: one same-loader actual-AEX run using the existing case_0023 compose fixture.",
        "- Hooks: `0x181458030`, `0x1814581a0`, and compose `0x181170480`.",
        "- No AE-exact claim and no production edits.",
        "",
        "## Path proof",
        "",
        f"- Compose reached: `{report['fixture']['compose_reached']}`.",
        f"- Final output reached: `{report['fixture']['final_output_reached']}`.",
        f"- Compose calls: `{len(report['final_outputs'])}`.",
        f"- Writer hits: `{len(hits)}`.",
        "",
        "## Writer census",
        "",
        "Each hit would retain RCX float32 values/raw bytes, RDX, R8D, the stack return address, and final destination words.",
        "",
    ]
    if hits:
        for hit in hits:
            lines.append(f"- `{hit['function']}` RCX=`{hit['rcx']}`, RDX=`{hit['rdx']}`, R8D=`{hit['r8d']}`, return=`{hit['return_address']}`, final=`{hit['final_words_after_return']}`.")
    else:
        lines.append("- No writer hit was observed. The leaves are `inactive_for_fixture`; this does not claim they are globally dead.")
    lines.extend(["", "## Final words", ""])
    for item in report["final_outputs"]:
        lines.append(f"- `{tuple(item['xy'])}`: AGRB16 `{item['final_words_agrb']}`.")
    lines.extend(["", "## Commands", "", "```sh", "python3 -m py_compile tools/emulation/test_dg_pf16_writer_active_path_20260716.py", "python3 tools/emulation/test_dg_pf16_writer_active_path_20260716.py", "```", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=OUTPUT_JSON)
    parser.add_argument("--md", type=Path, default=OUTPUT_MD)
    args = parser.parse_args()
    report = run_census()
    args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "writer_hits": len(report["writer_hits"]), "compose_calls": len(report["final_outputs"])}, indent=2))
    print(f"wrote_json={args.json}")
    print(f"wrote_md={args.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
