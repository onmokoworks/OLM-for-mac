#!/usr/bin/env python3
"""Fail-closed A9D0 row-slice acceleration harness.

This harness is deliberately conservative.  It copies a natural checkpoint,
checks that the copy is a safe A9D0-entry state, and only then has permission
to run the real AEX worker in fresh processes.  A checkpoint captured inside
the worker cannot be rewound into an entry state, so it is rejected without
loading, patching, or resuming it.

The current natural checkpoint6 is expected to take that rejection path.  The
future execution path is documented by the contract below, but is not
silently approximated here: serial-vs-two-slice equality, pointer non-alias,
the two phase barriers, and the post-A9D0 normalization continuation must all
be observed before a derived checkpoint can be emitted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHECKPOINT = Path("/tmp/olm_radial_case0009_workers_progress6_20260718.aexcp")
DEFAULT_COPY_DIR = Path("/tmp/olmradialblur_a9d0_row_slice_20260718")
DEFAULT_OUTPUT_JSON = ROOT / "refs/conformance/olmradialblur_a9d0_row_slice_acceleration_20260718.json"
DEFAULT_OUTPUT_MD = ROOT / "refs/conformance/olmradialblur_a9d0_row_slice_acceleration_20260718.md"

MAGIC = b"AEXCP64\x00"
PREFIX_SIZE = len(MAGIC) + 4 + 8 + 32
CALL_A9D0 = 0x180005C90
WORKER_A9D0 = 0x18000A9D0
NORMALIZATION_START = 0x180005C9F
EXPECTED_AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_checkpoint_header(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        prefix = handle.read(PREFIX_SIZE)
        if len(prefix) != PREFIX_SIZE or not prefix.startswith(MAGIC):
            raise ValueError(f"invalid checkpoint prefix: {path}")
        version = int.from_bytes(prefix[len(MAGIC):len(MAGIC) + 4], "little")
        header_size = int.from_bytes(prefix[len(MAGIC) + 4:len(MAGIC) + 12], "little")
        header_bytes = handle.read(header_size)
    if hashlib.sha256(header_bytes).digest() != prefix[-32:]:
        raise ValueError(f"checkpoint header checksum mismatch: {path}")
    header = json.loads(header_bytes.decode("ascii"))
    if header.get("version") != version:
        raise ValueError(f"checkpoint version mismatch: {path}")
    return header


def pid_state(pid: int) -> dict[str, Any]:
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "pid=,stat=,etime=,command="],
        capture_output=True,
        text=True,
        check=False,
    )
    line = result.stdout.strip()
    return {"pid": pid, "alive": bool(line), "ps_line": line}


def row_partition(height: int, slices: list[tuple[int, int]]) -> dict[str, Any]:
    if height <= 0 or not slices:
        raise ValueError("height and slices must be positive")
    ordered = sorted(slices)
    if any(start < 0 or start >= end or end > height for start, end in ordered):
        raise ValueError("slice range is outside the row domain")
    if ordered[0][0] != 0 or ordered[-1][1] != height:
        raise ValueError("slice partition is incomplete")
    if any(left[1] != right[0] for left, right in zip(ordered, ordered[1:])):
        raise ValueError("slice partition overlaps or has a gap")
    return {
        "height": height,
        "slices": [[start, end] for start, end in ordered],
        "complete": True,
        "disjoint": True,
    }


def classify_checkpoint(header: dict[str, Any]) -> dict[str, Any]:
    registers = header.get("registers", {}).get("gp", {})
    rip = int(registers.get("rip", 0))
    metadata = header.get("metadata", {})
    config = metadata.get("config", {})
    captured = metadata.get("captured", {})

    gates = {
        "checkpoint_format": header.get("format") == "aex-loader-x64-checkpoint",
        "aex_identity_pinned": header.get("aex", {}).get("sha256") == EXPECTED_AEX_SHA256,
        "natural_harness": metadata.get("harness") == "test_zoom_case0009",
        "no_direct_core": config.get("direct_zoom_core") is False,
        "no_prefill_detour": not config.get("direct_fast_forward_prefill", False)
        and not config.get("direct_python_prefill", False),
        "no_worker_detour": not config.get("direct_detour_prepass", False)
        and not config.get("direct_detour_scatter", False),
        "a9d0_entry_or_callsite": rip in {CALL_A9D0, WORKER_A9D0},
        "caller_state_available": False,
        "pointer_non_alias_proven": False,
        "complete_partition_proven": False,
        "two_phase_provenance_present": False,
        "post_a9d0_return_contract": False,
    }
    reasons: list[str] = []
    if rip not in {CALL_A9D0, WORKER_A9D0}:
        reasons.append(
            f"checkpoint RIP 0x{rip:x} is inside/after A9D0, not an A9D0 entry "
            f"(required 0x{WORKER_A9D0:x} or caller callsite 0x{CALL_A9D0:x})"
        )
    if not captured:
        reasons.append("checkpoint has no caller-state witness metadata")
    reasons.extend([
        "pointer non-alias cannot be proven from the supplied checkpoint",
        "complete row partition cannot be derived from a mid-worker checkpoint",
        "two-phase B150->A9D0 provenance is absent from the checkpoint",
        "post-return normalization continuation cannot be reconstructed without guessing",
    ])
    return {
        "rip": f"0x{rip:x}",
        "required_entry_rips": [f"0x{WORKER_A9D0:x}", f"0x{CALL_A9D0:x}"],
        "gates": gates,
        "reasons": reasons,
        "captured_keys": sorted(captured),
        "normalization_start": f"0x{NORMALIZATION_START:x}",
    }


def markdown(report: dict[str, Any]) -> str:
    gates = report["gates"]
    lines = [
        "# OLMRadialBlur A9D0 row-slice acceleration harness (2026-07-18)",
        "",
        f"- Status: `{report['status']}`",
        f"- Protected PID: `{report['protected_pid']}`; stopped: `{report['protected_pid_stopped']}`",
        f"- A9D0 invoked: `{report['a9d0_invoked']}`",
        f"- Derived checkpoint emitted: `{report['derived_checkpoint_emitted']}`",
        "",
        "## FACT",
        "",
        f"- Source checkpoint: `{report['source_checkpoint']}`",
        f"- Source SHA-256: `{report['source_sha256']}`",
        f"- Immutable copy: `{report['checkpoint_copy']}`",
        f"- Copy SHA-256: `{report['copy_sha256']}`",
        f"- Source unchanged after copy: `{report['source_unchanged_after_copy']}`",
        f"- Checkpoint RIP: `{report['checkpoint_classification']['rip']}`",
        "- The current checkpoint is not an A9D0 entry state, so no AEX worker was resumed.",
        "",
        "## Gates",
        "",
        "| Gate | Result |",
        "| --- | --- |",
    ]
    lines.extend(f"| `{name}` | `{value}` |" for name, value in gates.items())
    lines.extend(["", "## Rejection", ""])
    lines.extend(f"- {reason}" for reason in report["checkpoint_classification"]["reasons"])
    lines.extend([
        "",
        "## Required future proof",
        "",
        "- Load independent copies of a genuine A9D0-entry checkpoint.",
        "- Invoke the real AEX A9D0 with disjoint row ranges in separate loaders.",
        "- Prove pointer non-alias and a complete half-open partition.",
        "- Prove B150-all -> join -> A9D0-all -> join provenance.",
        "- Compare two-slice output with a serial bounded A9D0 replay byte-for-byte.",
        f"- Emit a checkpoint whose RIP is the proven normalization path `{NORMALIZATION_START:#x}`.",
        "",
        "No Windows/AE exactness claim is made by this fail-closed result.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--copy-dir", type=Path, default=DEFAULT_COPY_DIR)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--protected-pid", type=int, default=59481)
    args = parser.parse_args()

    source = args.checkpoint.resolve()
    if not source.is_file():
        raise SystemExit(f"source checkpoint does not exist: {source}")
    before_source_sha = sha256(source)
    pid_before = pid_state(args.protected_pid)
    args.copy_dir.mkdir(parents=True, exist_ok=True)
    copied = args.copy_dir / "natural_checkpoint6_copy.aexcp"
    shutil.copy2(source, copied)
    copy_sha = sha256(copied)
    after_source_sha = sha256(source)
    pid_after = pid_state(args.protected_pid)

    header = read_checkpoint_header(copied)
    classification = classify_checkpoint(header)
    source_unchanged = before_source_sha == after_source_sha
    pid_unchanged = pid_before == pid_after
    gates = {
        "checkpoint_copy_hash_equal": before_source_sha == copy_sha,
        "source_unchanged_after_copy": source_unchanged,
        "protected_pid_alive_before": pid_before["alive"],
        "protected_pid_alive_after": pid_after["alive"],
        "protected_pid_state_unchanged": pid_unchanged,
        **classification["gates"],
    }
    safe_entry = all(classification["gates"].values())
    report = {
        "kind": "olmradialblur_a9d0_row_slice_acceleration_20260718",
        "schema": 1,
        "status": "blocked_fail_closed_checkpoint_not_safe_for_a9d0_replay" if not safe_entry else "ready_for_execution_gate",
        "source_checkpoint": str(source),
        "checkpoint_copy": str(copied),
        "source_sha256": before_source_sha,
        "copy_sha256": copy_sha,
        "source_sha256_after_copy": after_source_sha,
        "source_unchanged_after_copy": source_unchanged,
        "protected_pid": args.protected_pid,
        "protected_pid_stopped": False,
        "protected_pid_before": pid_before,
        "protected_pid_after": pid_after,
        "a9d0_invoked": False,
        "serial_vs_two_slice": {"status": "not_attempted", "equal": False},
        "derived_checkpoint_emitted": False,
        "gates": gates,
        "checkpoint_classification": classification,
        "provenance": {
            "a9d0": f"0x{WORKER_A9D0:x}",
            "caller_a9d0_callsite": f"0x{CALL_A9D0:x}",
            "normalization_start": f"0x{NORMALIZATION_START:x}",
            "row_slice_contract": "refs/conformance/olmradialblur_row_slice_independence_20260718.json",
        },
        "claim_boundary": "No A9D0 execution or derived checkpoint is accepted until entry ABI, pointer non-alias, complete partition, two-phase provenance, serial equality, and normalization continuation are proven.",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(report), encoding="utf-8")
    print(f"status={report['status']}")
    print(f"checkpoint_copy={copied}")
    print(f"a9d0_invoked={report['a9d0_invoked']}")
    print(f"protected_pid_stopped={report['protected_pid_stopped']}")
    return 0 if report["status"].startswith("blocked_fail_closed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
