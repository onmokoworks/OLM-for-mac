#!/usr/bin/env python3
"""Audit a sequence of RadialBlur AexLoader checkpoints without restoring it."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAGIC = b"AEXCP64\x00"
PREFIX_SIZE = len(MAGIC) + 4 + 8 + 32
DEFAULT_JSON = ROOT / "refs/conformance/olmradialblur_natural_checkpoint_journey_20260717.json"
DEFAULT_MD = ROOT / "refs/conformance/olmradialblur_natural_checkpoint_journey_20260717.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_header(path: Path) -> dict:
    with path.open("rb") as source:
        prefix = source.read(PREFIX_SIZE)
        if len(prefix) != PREFIX_SIZE or not prefix.startswith(MAGIC):
            raise ValueError(f"invalid checkpoint magic: {path.name}")
        version, header_size = struct.unpack("<IQ", prefix[len(MAGIC):len(MAGIC) + 12])
        header_bytes = source.read(header_size)
    if hashlib.sha256(header_bytes).digest() != prefix[-32:]:
        raise ValueError(f"checkpoint header checksum mismatch: {path.name}")
    header = json.loads(header_bytes.decode("ascii"))
    if header.get("version") != version:
        raise ValueError(f"checkpoint version mismatch: {path.name}")
    return header


def parse_checkpoint(value: str) -> tuple[str, Path]:
    try:
        label, path = value.split("=", 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("checkpoint must be LABEL=PATH") from exc
    if not label or not path:
        raise argparse.ArgumentTypeError("checkpoint must be LABEL=PATH")
    return label, Path(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", action="append", type=parse_checkpoint, required=True)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    rows = []
    for label, path in args.checkpoint:
        header = read_header(path)
        metadata = header.get("metadata", {})
        registers = header.get("registers", {}).get("gp", {})
        rows.append(
            {
                "label": label,
                "file_sha256": sha256(path),
                "file_size": path.stat().st_size,
                "rip": f"0x{int(registers['rip']):x}",
                "instructions_executed": int(header["instructions_executed"]),
                "aex_sha256": header["aex"]["sha256"],
                "case_id": metadata.get("config", {}).get("case_id"),
                "input_sha256": metadata.get("config", {}).get("input_sha256"),
                "manifest_sha256": metadata.get("config", {}).get("manifest_sha256"),
                "synthetic_prefill": bool(metadata.get("config", {}).get("direct_fast_forward_prefill")),
                "python_prefill": bool(metadata.get("config", {}).get("direct_python_prefill")),
                "worker_detours": bool(
                    metadata.get("config", {}).get("direct_detour_prepass")
                    or metadata.get("config", {}).get("direct_detour_scatter")
                ),
            }
        )

    identity = {
        (row["aex_sha256"], row["case_id"], row["input_sha256"], row["manifest_sha256"])
        for row in rows
    }
    checks = {
        "single_case_identity": len(identity) == 1,
        "instruction_count_monotonic": all(
            left["instructions_executed"] <= right["instructions_executed"]
            for left, right in zip(rows, rows[1:])
        ),
        "no_prefill_or_worker_detour": all(
            not row["synthetic_prefill"] and not row["python_prefill"] and not row["worker_detours"]
            for row in rows
        ),
    }
    if not all(checks.values()):
        raise SystemExit(f"checkpoint journey failed: {checks}")

    report = {
        "kind": "olmradialblur_natural_checkpoint_journey_20260717",
        "status": "pass_local_natural_checkpoint_journey",
        "checkpoints": rows,
        "checks": checks,
        "claim_boundary": "actual-AEX checkpoint transport and reached RIPs only; no Windows or AE-exact claim",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# OLMRadialBlur natural checkpoint journey",
        "",
        f"- Status: `{report['status']}`",
        "- No Python/synthetic prefill and no worker detour were used.",
        "",
        "| Label | RIP | cumulative instructions | checkpoint SHA-256 |",
        "| --- | --- | ---: | --- |",
    ]
    lines.extend(
        f"| `{row['label']}` | `{row['rip']}` | `{row['instructions_executed']}` | `{row['file_sha256']}` |"
        for row in rows
    )
    lines.extend(["", f"Boundary: {report['claim_boundary']}.", ""])
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"PASS checkpoint journey: {len(rows)} stages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
