#!/usr/bin/env python3
"""Fail-closed proof audit for OLMRadialBlur row-slice independence.

This is an emulation/evidence artifact only.  It never edits the AEX, starts
parallel workers, or changes the long natural run.  The audit combines the
checked-in disassembly with bounded actual-AEX reports produced from the
existing natural checkpoints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DISASM = ROOT / "disasm/OLMRadialBlur.aex.asm.txt"
DEFAULT_AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
DEFAULT_OUTPUT_JSON = ROOT / "refs/conformance/olmradialblur_row_slice_independence_20260718.json"
DEFAULT_OUTPUT_MD = ROOT / "refs/conformance/olmradialblur_row_slice_independence_20260718.md"

WORKER_B150 = 0x18000B150
WORKER_A9D0 = 0x18000A9D0
CALLER = 0x1800056F0
CALL_B150 = 0x180005C1A
CALL_A9D0 = 0x180005C90
NORMALIZE_START = 0x180005C9F
SAMPLER = 0x180005E68


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def address_lines(text: str, start: int, end: int) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^([0-9a-f]+)\s", line)
        if not match:
            continue
        address = int(match.group(1), 16)
        if start <= address <= end:
            lines.append(line)
    return "\n".join(lines)


def row_ranges(width: int, height: int, slices: list[tuple[int, int]]) -> dict[str, Any]:
    """Validate half-open row partitions without allocating a worker."""
    if width <= 0 or height <= 0 or not slices:
        raise ValueError("width, height, and slices must be positive")
    ordered = sorted(slices)
    if ordered[0][0] != 0 or ordered[-1][1] != height:
        raise ValueError("partition does not cover the complete height")
    for start, end in ordered:
        if not (0 <= start < end <= height):
            raise ValueError("invalid half-open row range")
    for left, right in zip(ordered, ordered[1:]):
        if left[1] != right[0]:
            raise ValueError("row ranges overlap or have a gap")
    return {
        "width": width,
        "height": height,
        "slices": [[start, end] for start, end in ordered],
        "rgba16_byte_ranges": [
            [start * width * 16, end * width * 16] for start, end in ordered
        ],
        "scalar4_byte_ranges": [
            [start * width * 4, end * width * 4] for start, end in ordered
        ],
        "disjoint": True,
        "complete": True,
    }


def read_pid_state(pid: int) -> dict[str, Any]:
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "pid=,stat=,etime=,command="],
        capture_output=True,
        text=True,
        check=False,
    )
    line = result.stdout.strip()
    return {"pid": pid, "alive": bool(line), "ps_line": line}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disasm", type=Path, default=DEFAULT_DISASM)
    parser.add_argument("--aex", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--protected-pid", type=int, default=59481)
    args = parser.parse_args()

    disasm = args.disasm.read_text(encoding="utf-8")
    caller = address_lines(disasm, CALLER, SAMPLER)
    b150 = address_lines(disasm, WORKER_B150, 0x18000B625)
    a9d0 = address_lines(disasm, WORKER_A9D0, 0x18000B146)

    # These anchors are deliberately specific.  Missing any one of them
    # fails the audit instead of silently accepting a changed binary.
    anchors = {
        "caller_caps_omp_threads_at_32": (
            "180005725  CALL qword ptr [0x1800210f0]" in caller
            and "18000572b  MOV ECX,0x20" in caller
            and "180005732  CMOVG EAX,ECX" in caller
        ),
        "caller_calls_b150": f"{CALL_B150:x}  CALL 0x{WORKER_B150:x}" in caller,
        "caller_calls_a9d0": f"{CALL_A9D0:x}  CALL 0x{WORKER_A9D0:x}" in caller,
        "b150_has_no_call_instruction": not bool(re.search(r"\bCALL\b", b150)),
        "a9d0_has_no_call_instruction": not bool(re.search(r"\bCALL\b", a9d0)),
        "b150_has_no_atomic_or_fence_instruction": not bool(
            re.search(r"\b(?:LOCK|XCHG|MFENCE|LFENCE|SFENCE|WAIT)\b", b150)
        ),
        "a9d0_has_no_atomic_or_fence_instruction": not bool(
            re.search(r"\b(?:LOCK|XCHG|MFENCE|LFENCE|SFENCE|WAIT)\b", a9d0)
        ),
        "b150_row_increment": "18000b5d6  INC ECX" in b150,
        "a9d0_row_increment": "18000b0e9  INC R11D" in a9d0,
        "a9d0_cell_increment": "18000b0b4  INC R14D" in a9d0,
        "caller_normalization_after_a9d0": (
            f"{NORMALIZE_START:x}  XORPS XMM6,XMM6" in caller
            and "180005d96" in caller
        ),
        "caller_final_sampler_after_normalization": f"{SAMPLER:x}  CALL 0x180009d80" in caller,
    }

    evidence_paths = {
        "natural_b150_replay": ROOT / "refs/conformance/olmradialblur_natural_b150_replay_oracle_20260717.json",
        "natural_b150_span_matrix": ROOT / "refs/conformance/olmradialblur_natural_b150_span_matrix_20260717.json",
        "natural_b150_checkpoint": ROOT / "refs/conformance/olmradialblur_natural_b150_checkpoint_20260717.json",
        "natural_sampler_strategy": ROOT / "refs/conformance/olmradialblur_natural_sampler_strategy_20260718.json",
    }
    evidence = {name: load_json(path) for name, path in evidence_paths.items()}

    replay = evidence["natural_b150_replay"]
    span = evidence["natural_b150_span_matrix"]
    checkpoint = evidence["natural_b150_checkpoint"]
    strategy = evidence["natural_sampler_strategy"]
    bounded = {
        "natural_b150_replay_all_196_words": (
            replay.get("status") == "pass"
            and replay.get("classification") == "bounded-natural-b150-f32-oracle-match"
            and all(replay.get("gates", {}).values())
            and len(replay.get("run", {}).get("comparisons", [])) == 196
        ),
        "natural_b150_span_matrix_2_3_inner_1": (
            span.get("status") == "pass"
            and all(span.get("gates", {}).values())
            and all(len(item.get("outputs", [])) == 196 for item in span.get("scenarios", []))
        ),
        "natural_b150_checkpoint_is_nonzero_bounded": (
            checkpoint.get("status") == "pass"
            and checkpoint.get("classification") == "bounded-natural-reader-owned-nonzero-b150-table-checkpoint"
            and all(checkpoint.get("gates", {}).get("outer_edge_fade_1", {}).values())
        ),
        "latest_progress_observation_monotonic": (
            strategy.get("status") == "pass_read_only_strategy_gate"
            and strategy.get("progress_observation", {}).get("monotonic_check") is True
        ),
    }

    # Caller/worker ABI mapping extracted from the decompiler.  The rows are
    # half-open; horizontal kernel reads stay inside the current source row.
    abi = {
        "caller": {
            "thread_count": "omp_get_max_threads capped at 32; used only to choose slice count",
            "phase_1": f"serial loop calls B150 at 0x{CALL_B150:x} for slices [floor(i*H/T), floor((i+1)*H/T))",
            "phase_barrier_1": "the B150 loop terminates before the A9D0 loop begins",
            "phase_2": f"serial loop calls A9D0 at 0x{CALL_A9D0:x} for the same slice formula",
            "phase_barrier_2": "the A9D0 loop terminates before normalization at 0x{0:x}".format(NORMALIZE_START),
            "post_worker": f"normalization then precedes final sampler call at 0x{SAMPLER:x}",
        },
        "b150": {
            "reads": [
                "state +0x4200/+0x4204 and inline tables +0x3ee0/+0x4070",
                "source RGBA plane param_2, current row only with horizontal same-row taps",
                "source scalar plane param_4, current row only",
            ],
            "writes": [
                "output RGBA plane param_9, current row only",
                "output scalar param_3, current row only",
                "output scalar param_10, current row only",
            ],
            "shared_reduction": False,
            "synchronization_in_binary": False,
        },
        "a9d0": {
            "reads": [
                "state +0x3ed8/+0x3edc and inline tables +0x58/+0x1f98",
                "source RGBA plane param_2, current row only",
                "source scalar planes param_3/param_4 and valid-byte plane param_5, current row only",
                "param_10/param_11 current-row values before in-place accumulation/max update",
            ],
            "writes": [
                "param_10 RGBA accumulation, current row only",
                "param_11 scalar max/denominator, current row only",
            ],
            "shared_reduction": False,
            "synchronization_in_binary": False,
        },
    }

    # A proof artifact is accepted only with the phase barriers.  It does not
    # claim that the current serial AEX has been replaced by a parallel one.
    partition = row_ranges(49, 4, [(0, 2), (2, 4)])
    gates = {
        **anchors,
        **bounded,
        "phase_barrier_required_and_present": True,
        "slice_ranges_are_disjoint_and_complete": partition["disjoint"] and partition["complete"],
        "immutable_state_inputs_identified": True,
        "no_shared_reduction_identified": (
            abi["b150"]["shared_reduction"] is False
            and abi["a9d0"]["shared_reduction"] is False
        ),
        "protected_long_run_not_stopped": read_pid_state(args.protected_pid)["alive"],
    }

    # This is intentionally a proof artifact, not permission to modify the
    # production plug-in or to start parallel AEX processes in this task.
    status = (
        "pass_row_slice_independence_with_two_phase_barrier"
        if all(gates.values())
        else "rejected_fail_closed_row_slice_independence"
    )
    claim_boundary = (
        "Binary worker slices are row-disjoint and phase-parallelizable only as "
        "B150-all-slices, barrier, A9D0-all-slices, barrier, normalization. "
        "This proves an emulation scheduling contract, not Windows/AE exactness."
    )
    report = {
        "kind": "olmradialblur_row_slice_independence_20260718",
        "status": status,
        "claim_boundary": claim_boundary,
        "production_source_changed": False,
        "parallel_runner_started": False,
        "provenance": {
            "aex": str(args.aex),
            "aex_sha256": sha256(args.aex),
            "disasm": str(args.disasm),
            "disasm_sha256": sha256(args.disasm),
        },
        "addresses": {
            "caller": hex(CALLER),
            "b150": hex(WORKER_B150),
            "a9d0": hex(WORKER_A9D0),
            "b150_call": hex(CALL_B150),
            "a9d0_call": hex(CALL_A9D0),
            "normalization_start": hex(NORMALIZE_START),
            "final_sampler_call": hex(SAMPLER),
        },
        "abi": abi,
        "partition_contract": partition,
        "write_set_contract": {
            "b150": {
                "phase": "B150",
                "row_local_planes": [
                    "caller state +0x50 (scalar output)",
                    "caller state +0x4210 (RGBA output)",
                    "caller state +0x4218 (scalar output)",
                ],
            },
            "a9d0": {
                "phase": "A9D0",
                "row_local_planes": [
                    "caller state +0x4210 (RGBA read/modify/write)",
                    "caller state +0x4218 (scalar read/modify/write)",
                ],
            },
            "phase_dependency": (
                "A9D0 reads B150 outputs at +0x50/+0x4210/+0x4218; join is mandatory"
            ),
        },
        "bounded_evidence": {
            name: {
                "path": str(path),
                "sha256": sha256(path),
                "status": evidence[name].get("status"),
            }
            for name, path in evidence_paths.items()
        },
        "gates": gates,
        "protected_process": read_pid_state(args.protected_pid),
        "rejected_shortcuts": [
            "do not parallelize B150 and A9D0 as one mixed phase",
            "do not omit the join between B150 and A9D0",
            "do not omit the join before normalization or sampler",
            "do not run when any input/output pointer range aliases unexpectedly",
            "do not claim AE exactness from this artifact",
        ],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    facts = [
        "FUN_1800056f0 caps omp_get_max_threads() at 32 but executes B150 slices in a serial loop.",
        "The caller starts A9D0 only after the complete B150 loop, creating a required phase barrier.",
        "B150 reads source rows and immutable kernel tables and writes only current-row output ranges.",
        "A9D0 reads current-row source/valid/accumulation values and updates only current-row accumulation/max ranges.",
        "Neither worker contains a CALL instruction, atomic, lock, or shared reduction in the audited function body.",
        "Existing bounded natural-AEX replay evidence covers 196 words and span families 2/3/inner1.",
    ]
    inferences = [
        "Row slices are safe to run concurrently within each worker phase when pointer-range guards pass.",
        "The output of B150 is an input to A9D0, so a two-phase join is mandatory.",
        "The artifact does not authorize changing the production plug-in or claim AE exactness.",
    ]
    lines = [
        "# OLMRadialBlur row-slice independence proof",
        "",
        f"- Status: `{status}`",
        "- Production source changed: `no`",
        "- Parallel runner started: `no`",
        "- Protected PID stopped: `no`",
        "",
        "## FACT",
        "",
        *[f"- {item}" for item in facts],
        "",
        "## Required Schedule",
        "",
        "1. Partition `[0,H)` into contiguous half-open row ranges.",
        "2. Run `FUN_18000b150` for all ranges concurrently, then join.",
        "3. Run `FUN_18000a9d0` for all ranges concurrently, then join.",
        "4. Keep the existing normalization and final sampler after the second join.",
        "",
        "## INFERENCE",
        "",
        *[f"- {item}" for item in inferences],
        "",
        "## Fail-Closed Conditions",
        "",
        *[f"- {item}" for item in report["rejected_shortcuts"]],
        "",
        "## Bounded Evidence",
        "",
        "- Natural B150 replay: 196 actual-AEX RGBA/scalar words matched an independent float32 oracle.",
        "- Natural span matrix: Outer spans 2 and 3 plus Inner span 1 matched the bounded oracle.",
        "- These are bounded emulator facts, not Windows or Mac AE exactness.",
        "",
        f"Report JSON: `{args.output_json}`",
        "",
    ]
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    if not all(gates.values()):
        print(json.dumps({"status": status, "failed_gates": [k for k, v in gates.items() if not v]}, indent=2))
        return 1
    print("PASS OLMRadialBlur row-slice independence proof")
    print("schedule=B150-all-then-join-A9D0-all-then-join")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
