#!/usr/bin/env python3
"""Classify the 2026-07-15 DG8 exact-coordinate Windows return."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ("case_0001", "case_0015", "case_0029")
TARGET = [397, 281]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def png_size(data: bytes) -> list[int]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("invalid PNG header")
    return list(struct.unpack(">II", data[16:24]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    raw_zip = args.source.read_bytes()
    with zipfile.ZipFile(args.source) as archive:
        names = {name.replace("\\", "/"): name for name in archive.namelist()}

        def read(name: str) -> bytes:
            if name not in names:
                raise ValueError(f"missing archive entry: {name}")
            return archive.read(names[name])

        readme = read("README.md").decode("utf-8")
        queue = read("AE_TYPED_QUEUE.log").decode("utf-8")
        trace = read("exact_trace.txt").decode("utf-8")
        stdout = read("exact_stdout.txt").decode("utf-8", errors="replace")

        if "Status: `exact_bind_failure`" not in readme:
            raise ValueError("README does not classify exact_bind_failure")
        if "EXACT_FIXED_BREAKPOINTS_ARMED" not in trace:
            raise ValueError("PF8/PF32 breakpoints were not armed")
        if "edx==397" not in trace or "r8d==281" not in trace:
            raise ValueError("target condition is not the requested coordinate")
        if "DG8_EXACT_PF8" in trace.split("EXACT_FIXED_BREAKPOINTS_ARMED", 1)[-1]:
            raise ValueError("return unexpectedly contains a target PF8 hit")

        case_records = []
        for case in CASES:
            result = json.loads(read(f"AE_SINGLE_CASE_{case}.json"))
            if result.get("case_id") != case or result.get("status") != "ok":
                raise ValueError(f"AE case did not complete: {case}")
            expected_project = {
                "bits_per_channel": 8,
                "working_space": "None",
                "linear_blending": False,
            }
            observed_project = {
                "bits_per_channel": result.get("project_bits_per_channel"),
                "working_space": result.get("project_working_space"),
                "linear_blending": result.get("project_linear_blending"),
            }
            if observed_project != expected_project:
                raise ValueError(f"project contract drift: {case}: {observed_project}")
            for marker in (
                f"OLMDG8_CASE_START run_id=dg8-exact-fixed-probe-20260715 case_id={case}",
                f"OLMDG8_CASE_END run_id=dg8-exact-fixed-probe-20260715 case_id={case}",
            ):
                if marker not in queue:
                    raise ValueError(f"missing queue marker: {marker}")
            png = read(f"single_case_output/{case}/{case}.png")
            case_records.append(
                {
                    "case_id": case,
                    "ae_status": "ok",
                    "ae_version": result.get("ae_version"),
                    "project": observed_project,
                    "output_png": {
                        "width_height": png_size(png),
                        "sha256": sha256_bytes(png),
                        "size_bytes": len(png),
                    },
                }
            )

    hash_present = "aex_sha256=" in trace or "aex_sha256=" in stdout
    report = {
        "schema": "olmdg8-exact-fixed-failure-classification.v1",
        "source": {"path": display_path(args.source), "sha256": sha256_bytes(raw_zip)},
        "status": "accepted_exact_bind_failure",
        "classification": "target-coordinate-not-observed-and-aex-hash-unbound",
        "algorithm_evidence": False,
        "request_satisfied": False,
        "target_xy": TARGET,
        "callback": {
            "pf8_rva": "0x1170870",
            "pf32_rva": "0x1170c90",
            "breakpoints_armed": True,
            "target_hit_count": 0,
            "aex_sha256_present": hash_present,
        },
        "cases": case_records,
        "FACT": [
            "AE 25.2 rendered all three named cases successfully at 8bpc with working space None and linear blending disabled.",
            "CDB armed absolute PF8 and PF32 callback breakpoints and continued execution.",
            "The PF8 entry condition EDX=397 and R8D=281 emitted no target marker.",
            "The return does not retain an AEX SHA-256 or a complete typed field/compose/store chain.",
        ],
        "INFERENCE": [
            "Static callback ABI evidence identifies EDX/R8D as x/y at PF8 entry, but this return cannot decide whether AE skipped the target through its iterate ROI or whether host coordinate mapping differs.",
            "A broad coordinate-liveness census is required before another exact-coordinate capture.",
        ],
        "next_action": "run a hash-pinned PF8 coordinate-liveness census for the same three cases; collect total/min/max/first hits, target-neighborhood hits, output pointers, PF32 count, and same-run identity",
    }
    if hash_present:
        raise ValueError("classifier expected the known return to lack a retained AEX hash")

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# OLMDistanceGradation 8bpc Exact-Coordinate Return",
        "",
        f"- Status: `{report['status']}`",
        f"- Classification: `{report['classification']}`",
        "- Request satisfied: no",
        "- Algorithm evidence: no",
        f"- Source ZIP SHA-256: `{report['source']['sha256']}`",
        "",
        "## Facts",
        "",
        *[f"- {item}" for item in report["FACT"]],
        "",
        "## Boundary",
        "",
        *[f"- {item}" for item in report["INFERENCE"]],
        "",
        "## Next Action",
        "",
        report["next_action"],
        "",
    ]
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"status={report['status']}")
    print(f"classification={report['classification']}")
    print(f"json={args.output_json}")
    print(f"md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
