#!/usr/bin/env python3
"""Audit a natural RadialBlur checkpoint and plan sampler reachability.

This is a read-only strategy gate.  It does not resume Unicorn, alter a
checkpoint, enter direct Zoom, fill any plane, or detour a worker.  Its job is
to turn the current natural checkpoint into explicit facts before spending a
multi-hour resume run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAGIC = b"AEXCP64\x00"
PREFIX_SIZE = len(MAGIC) + 4 + 8 + 32
WORKER_START = 0x18000A9D0
WORKER_END = 0x18000B14F
CELL_COMPLETION_BEFORE_INCREMENT = 0x18000B0B4
CELL_PROGRESS_AFTER_INCREMENT = 0x18000B0B7
ROW_STORE = 0x18000B0F1
ROW_PROGRESS_AFTER_STORE = 0x18000B0F9
SAMPLER = 0x180005E68
WORKER_ROW_START = 181
WORKER_ROW_END = 1800
WORKER_WIDTH = 1104


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_checkpoint(path: Path) -> dict:
    raw = path.read_bytes()
    if len(raw) < PREFIX_SIZE or not raw.startswith(MAGIC):
        raise ValueError(f"invalid checkpoint: {path}")
    version, header_size = struct.unpack_from("<IQ", raw, len(MAGIC))
    digest_start = len(MAGIC) + 4 + 8
    expected_digest = raw[digest_start:digest_start + 32]
    header_start = PREFIX_SIZE
    header_bytes = raw[header_start:header_start + header_size]
    if hashlib.sha256(header_bytes).digest() != expected_digest:
        raise ValueError(f"checkpoint header checksum mismatch: {path}")
    header = json.loads(header_bytes.decode("ascii"))
    if header.get("version") != version:
        raise ValueError(f"checkpoint version mismatch: {path}")
    return header


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("/tmp/olm_radial_case0009_workers_progress3_20260717.aexcp"),
    )
    parser.add_argument(
        "--aex",
        type=Path,
        default=ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex",
    )
    parser.add_argument(
        "--disasm",
        type=Path,
        default=ROOT / "disasm/OLMRadialBlur.aex.asm.txt",
    )
    parser.add_argument(
        "--worker-row",
        type=int,
        required=True,
        help=(
            "Current outer worker row from an external checkpoint stack witness. "
            "The checkpoint header does not contain this value."
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / "refs/conformance/olmradialblur_natural_sampler_strategy_20260718.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=ROOT / "refs/conformance/olmradialblur_natural_sampler_strategy_20260718.md",
    )
    parser.add_argument(
        "--progress-json",
        type=Path,
        help="Optional live/final progress sidecar from the natural runner.",
    )
    args = parser.parse_args()

    header = read_checkpoint(args.checkpoint)
    metadata = header.get("metadata", {})
    config = metadata.get("config", {})
    regs = header.get("registers", {}).get("gp", {})
    checkpoint_callbacks = header.get("callbacks", [])
    rip = int(regs["rip"])
    aex_sha = sha256(args.aex)
    checkpoint_aex_sha = header.get("aex", {}).get("sha256")
    disasm_text = args.disasm.read_text(encoding="utf-8")
    progress_observation: dict[str, Any] = {
        "path": str(args.progress_json) if args.progress_json else None,
        "present": bool(args.progress_json and args.progress_json.exists()),
    }
    if progress_observation["present"]:
        sidecar = json.loads(args.progress_json.read_text(encoding="utf-8"))
        progress_observation.update(
            {
                "hook": sidecar.get("hook"),
                "hook_mode": sidecar.get("hook_mode"),
                "monotonic_check": sidecar.get("monotonic_check"),
                "boundary_hits": sidecar.get("total_boundary_hits", 0),
                "samples": sidecar.get("total_samples", 0),
                "live_run": "live_run" in sidecar,
            }
        )

    # R11D is the current inner-loop bound at this RIP, not the outer row.
    # The outer row is recovered from the checkpoint stack witness supplied by
    # the natural-run auditor; keep it explicit instead of guessing from R11.
    current_row = args.worker_row
    current_cell = int(regs.get("r14", 0))
    remaining_cells = max(0, (WORKER_ROW_END - current_row) * WORKER_WIDTH - current_cell)
    total_cells = (WORKER_ROW_END - WORKER_ROW_START) * WORKER_WIDTH
    reached_cells = total_cells - remaining_cells

    checks = {
        "checkpoint_header_valid": True,
        "aex_sha_matches_checkpoint": aex_sha == checkpoint_aex_sha,
        "natural_render_config": not any(
            config.get(key, False)
            for key in (
                "direct_zoom_core",
                "direct_fast_forward_prefill",
                "direct_python_prefill",
                "direct_detour_prepass",
                "direct_detour_scatter",
            )
        ),
        "rip_inside_scatter_worker": WORKER_START <= rip <= WORKER_END,
        "cell_completion_before_increment_in_disassembly": f"{CELL_COMPLETION_BEFORE_INCREMENT:x}" in disasm_text,
        "cell_progress_after_increment_in_disassembly": f"{CELL_PROGRESS_AFTER_INCREMENT:x}" in disasm_text,
        "sampler_in_disassembly": f"{SAMPLER:x}" in disasm_text,
        "boundary_increments_cell": "18000b0b4  INC R14D" in disasm_text,
        "progress_hook_is_after_increment": "18000b0b7  DEC R15D" in disasm_text,
        "boundary_updates_row": "18000b0f1  MOV dword ptr [RSP + 0xc8],R11D" in disasm_text,
        "row_progress_hook_is_after_store": "18000b0f9  MOV dword ptr [RSP + 0x98],R10D" in disasm_text,
        "progress_code_hooks_not_serialized": not any(
            int(callback.get("address", -1))
            in (CELL_PROGRESS_AFTER_INCREMENT, ROW_PROGRESS_AFTER_STORE)
            for callback in checkpoint_callbacks
        ),
        "bounded_progress_observation_monotonic": (
            not progress_observation["present"]
            or progress_observation.get("monotonic_check") is True
        ),
    }
    if not all(checks.values()):
        raise SystemExit(f"RadialBlur strategy gate failed: {checks}")

    report = {
        "kind": "olmradialblur_natural_sampler_strategy_20260718",
        "status": "pass_read_only_strategy_gate",
        "claim_boundary": (
            "Natural checkpoint state and worker boundary are verified; this is not "
            "sampler reachability, Windows equivalence, or AE exactness."
        ),
        "checkpoint": {
            "path": str(args.checkpoint),
            "sha256": sha256(args.checkpoint),
            "instructions_executed": int(header["instructions_executed"]),
            "rip": f"0x{rip:x}",
            "aex_sha256": checkpoint_aex_sha,
            "config": config,
            "registers": regs,
        },
        "worker_state": {
            "row_range": [WORKER_ROW_START, WORKER_ROW_END],
            "width": WORKER_WIDTH,
            "current_row": current_row,
            "current_cell": current_cell,
            "row_source": "external witness supplied via --worker-row; not stored in checkpoint header",
            "r11_inner_bound": int(regs.get("r11", 0)),
            "total_cells": total_cells,
            "reached_cells_estimate": reached_cells,
            "remaining_cells_estimate": remaining_cells,
        },
        "progress_observation": progress_observation,
        "addresses": {
            "worker": [f"0x{WORKER_START:x}", f"0x{WORKER_END:x}"],
            "cell_completion_before_increment": f"0x{CELL_COMPLETION_BEFORE_INCREMENT:x}",
            "cell_progress_after_increment": f"0x{CELL_PROGRESS_AFTER_INCREMENT:x}",
            "row_store": f"0x{ROW_STORE:x}",
            "row_progress_after_store": f"0x{ROW_PROGRESS_AFTER_STORE:x}",
            "final_sampler": f"0x{SAMPLER:x}",
        },
        "checks": checks,
        "facts": [
            "The checkpoint uses the natural full render path.",
            "The current RIP is inside the scatter worker, not the final sampler.",
            "The worker increments R14D at 0x18000b0b4; the runner observes at 0x18000b0b7 after that increment and before DEC R15D.",
            "The worker stores the next outer row at 0x18000b0f1; the low-overhead row mode observes at 0x18000b0f9 after that store and before the next row-loop compare.",
            "The final sampler callsite is downstream of worker completion and is present in the disassembly.",
            "The checkpoint header does not contain the outer worker row; the row used for the estimate is an external witness supplied to this audit.",
            "The checkpoint callback list contains no progress code-hook address; AexLoader validates host callbacks, while the cell/row observation hook is installed by the fresh runner.",
        ],
        "inferences": [
            "A single uninterrupted resume is the only direct route to an unmodified final sampler call.",
            "Checkpoint frequency alone cannot reduce CPU work; it only improves restartability.",
            "A safe acceleration candidate is row-slice parallelism, but it requires a new proof that worker slices write disjoint planes and have no shared reduction or synchronization.",
            "The natural runner can reduce its own callback overhead with --hook-mode row, which observes 0x18000b0f9 once per outer-row transition; this changes observability only and does not accelerate the AEX algorithm itself.",
            "Because the observation code hook is not serialized in the checkpoint callback list, switching from cell to row mode on a compatible checkpoint is a loader-topology-neutral observation change; the AEX memory/register state remains the checkpoint source of truth.",
            "Until row-slice independence is proven, no worker detour, state rewrite, or parallel fresh process is safe.",
        ],
        "recommended_sequence": [
            {
                "stage": "A",
                "status": "completed_in_runner",
                "action": "Use the Radial-only runner's read-only hook at 0x18000b0b7 for cell witnesses, or --hook-mode row at 0x18000b0f9 for low-overhead progress; both use the existing checkpoint mechanism for any stop.",
                "preserves_algorithm": True,
                "requires_existing_runner_edit": False,
            },
            {
                "stage": "B",
                "status": (
                    "completed"
                    if progress_observation["present"]
                    and progress_observation.get("monotonic_check") is True
                    else "next"
                ),
                "action": "Run a short continuation from this checkpoint to confirm the post-increment hook sees monotonically increasing row/cell state and does not change memory or registers.",
                "preserves_algorithm": True,
                "requires_existing_runner_edit": False,
            },
            {
                "stage": "C",
                "status": "blocked_on_B",
                "action": "Use disassembly plus two bounded differential runs to prove whether row slices are disjoint. Only then consider parallel fresh processes from the same natural pre-worker checkpoint.",
                "preserves_algorithm": "conditional",
                "requires_existing_runner_edit": False,
            },
            {
                "stage": "D",
                "status": "blocked_on_B_C",
                "action": "Resume the natural path to 0x180005e68 only after A-C pass; record the sampler call arguments and final writer separately.",
                "preserves_algorithm": True,
                "requires_existing_runner_edit": False,
            },
        ],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(
        "\n".join(
            [
                "# OLMRadialBlur natural sampler strategy",
                "",
                f"- Status: `{report['status']}`",
                f"- Checkpoint RIP: `{report['checkpoint']['rip']}`",
                f"- Instructions executed: `{report['checkpoint']['instructions_executed']}`",
                f"- Estimated remaining worker cells: `{remaining_cells}`",
                f"- Final sampler: `{report['addresses']['final_sampler']}`",
                f"- Progress sidecar: `{progress_observation.get('path') or 'not supplied'}`",
                f"- Bounded progress observation: `{progress_observation.get('boundary_hits', 'not run')} hook hits`, monotonic=`{progress_observation.get('monotonic_check', 'not run')}`",
                "",
                "## FACT",
                "",
                *[f"- {item}" for item in report["facts"]],
                "",
                "## INFERENCE",
                "",
                *[f"- {item}" for item in report["inferences"]],
                "",
                "## Safe Sequence",
                "",
                *[
                    f"{item['stage']} [{item['status']}]. {item['action']}"
                    for item in report["recommended_sequence"]
                ],
                "",
                "Row estimate source: external checkpoint-stack witness supplied via `--worker-row`; it is not present in the checkpoint header.",
                "",
                f"Boundary: {report['claim_boundary']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("PASS RadialBlur natural sampler strategy gate")
    print(f"checkpoint_rip=0x{rip:x}")
    print(f"instructions_executed={header['instructions_executed']}")
    print(f"remaining_worker_cells={remaining_cells}")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
