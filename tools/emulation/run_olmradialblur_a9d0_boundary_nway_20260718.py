#!/usr/bin/env python3
"""Run a fail-closed N-way fork from the proven RadialBlur A9D0 boundary.

The default operation only prepares fresh slice checkpoints.  ``--run-full``
is intentionally opt-in because a full AEX execution is expensive.  Every
slice starts from the same immutable boundary, owns half-open row ranges, and
gets unique runner output files so it cannot collide with the older two-slice
run.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "tools/emulation/run_olmradialblur_a9d0_boundary_fork_20260718.py"
DEFAULT_BOUNDARY = Path(
    "/tmp/olmradialblur_a9d0_boundary_fork_20260718/"
    "next_row_boundary_20260718.aexcp"
)
DEFAULT_RUNTIME = Path("/tmp/olmradialblur_a9d0_boundary_nway_20260718")
DEFAULT_JSON = ROOT / "refs/conformance/olmradialblur_a9d0_boundary_nway_20260718.json"
DEFAULT_MD = ROOT / "refs/conformance/olmradialblur_a9d0_boundary_nway_20260718.md"
STOP_RIP = 0x180005C95
NORMALIZATION_RIP = 0x180005C9F


def load_base():
    spec = importlib.util.spec_from_file_location("radial_boundary_fork_20260718", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base runner: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def portable(value: Any) -> Any:
    """Remove workstation-specific absolute paths from checked-in evidence."""
    if isinstance(value, dict):
        return {key: portable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [portable(item) for item in value]
    if isinstance(value, str):
        root = str(ROOT)
        value = value.replace(root + "/", "")
        value = value.replace(str(Path(sys.executable)), "<python>")
        value = value.replace("/private/tmp/", "<temporary>/")
        value = value.replace("/tmp/", "<temporary>/")
        if value == root:
            return "."
        return value
    return value


def partition_rows(start: int, end: int, count: int) -> list[tuple[int, int]]:
    if count < 1 or start < 0 or start >= end:
        raise ValueError(f"invalid partition request: [{start},{end}) into {count}")
    length = end - start
    if count > length:
        raise ValueError("partition count exceeds remaining row count")
    quotient, remainder = divmod(length, count)
    ranges: list[tuple[int, int]] = []
    cursor = start
    for index in range(count):
        next_cursor = cursor + quotient + (1 if index < remainder else 0)
        ranges.append((cursor, next_cursor))
        cursor = next_cursor
    if ranges[0][0] != start or ranges[-1][1] != end:
        raise AssertionError("partition endpoints changed")
    if any(left[1] != right[0] for left, right in zip(ranges, ranges[1:])):
        raise AssertionError("partition has a gap or overlap")
    return ranges


def nway_runner_command(base: Any, source: Path, destination: Path,
                        runtime: Path, index: int, max_instructions: int,
                        stop_rip: int = STOP_RIP) -> list[str]:
    runtime.mkdir(parents=True, exist_ok=True)
    output_json = runtime / f"slice_{index:02d}_runner_20260718.json"
    output_md = runtime / f"slice_{index:02d}_runner_20260718.md"
    return [
        sys.executable, str(base.ZOOM_RUNNER),
        "--resume-checkpoint", str(source),
        "--save-checkpoint-at-rip", str(destination), hex(stop_rip),
        "--max-instructions", str(max_instructions),
        "--output-json", str(output_json),
        "--output-md", str(output_md),
    ]


def prepare_slices(base: Any, boundary: Path, runtime: Path,
                   contract: dict[str, Any], count: int) -> list[dict[str, Any]]:
    ranges = partition_rows(contract["start"], contract["end"], count)
    boundary_hash = base.file_sha256(boundary)
    items = []
    for index, (start, end) in enumerate(ranges):
        input_path = runtime / f"nway_slice_{index:02d}_input_20260718.aexcp"
        base.make_slice(boundary, input_path, contract, start, end)
        items.append({
            "index": index,
            "range": [start, end],
            "input": str(input_path),
            "input_sha256": base.file_sha256(input_path),
            "boundary_sha256": boundary_hash,
            "result": str(runtime / f"nway_slice_{index:02d}_result_20260718.aexcp"),
        })
    return items


def run_slices(base: Any, items: list[dict[str, Any]], runtime: Path,
               max_instructions: int) -> list[dict[str, Any]]:
    processes = []
    for item in items:
        result = Path(item["result"])
        result.unlink(missing_ok=True)
        command = nway_runner_command(
            base, Path(item["input"]), result, runtime, item["index"], max_instructions
        )
        processes.append((item, result, command, subprocess.Popen(
            command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )))

    completed = []
    for item, result, command, process in processes:
        stdout, stderr = process.communicate()
        if process.returncode != 0 or not result.is_file():
            raise RuntimeError(
                f"slice {item['index']} failed ({process.returncode}):\n{stdout}\n{stderr}"
            )
        completed.append({
            **item,
            "command": command,
            "stdout": stdout.strip(),
            "result_sha256": base.file_sha256(result),
        })
    return completed


def merge_nway(base: Any, boundary: Path, items: list[dict[str, Any]],
               contract: dict[str, Any], output: Path) -> dict[str, Any]:
    boundary_image = base.Checkpoint.read(boundary)
    boundary_heap = boundary_image.raw_region("heap-used")
    merged_heap = bytearray(boundary_heap)
    checked = []
    seen_ranges: list[tuple[int, int]] = []
    for item in items:
        start, end = item["range"]
        result_path = Path(item["result"])
        input_path = Path(item["input"])
        if not result_path.is_file():
            raise ValueError(f"missing slice result: {result_path}")
        result = base.validate_result(result_path, input_path)
        result_heap = result.raw_region("heap-used")
        owned = base.owned_ranges(contract, start, end)
        for owned_start, owned_end in owned:
            if any(left < owned_end and owned_start < right for left, right in seen_ranges):
                raise ValueError("slice ownership ranges overlap")
            seen_ranges.append((owned_start, owned_end))
        bounded = base.outside_owned_equal(
            boundary_heap, result_heap, contract["heap_base"], owned
        )
        if not bounded:
            raise ValueError(f"slice {item['index']} wrote outside owned output planes")
        for owned_start, owned_end in owned:
            a = owned_start - contract["heap_base"]
            b = owned_end - contract["heap_base"]
            merged_heap[a:b] = result_heap[a:b]
        checked.append({"index": item["index"], "range": item["range"], "bounded": bounded})

    leader = base.Checkpoint.read(Path(items[0]["result"]))
    leader.replace_region("heap-used", merged_heap)
    leader.header.setdefault("metadata", {})["a9d0_nway_merge_20260718"] = {
        "boundary_sha256": base.file_sha256(boundary),
        "slice_count": len(items),
        "ranges": [item["range"] for item in items],
        "planes": ["output_rgba", "output_scalar"],
        "heap_sha256": hashlib.sha256(merged_heap).hexdigest(),
    }
    leader.write(output)
    return {
        "output": str(output),
        "output_sha256": base.file_sha256(output),
        "slice_checks": checked,
        "merged_heap_sha256": hashlib.sha256(merged_heap).hexdigest(),
    }


def run_to_rip(base: Any, source: Path, destination: Path, runtime: Path,
               max_instructions: int, index: int, rip: int) -> dict[str, Any]:
    destination.unlink(missing_ok=True)
    command = nway_runner_command(base, source, destination, runtime, index, max_instructions, rip)
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0 or not destination.is_file():
        raise RuntimeError(f"continuation failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
    return {"command": command, "sha256": base.file_sha256(destination), "stdout": result.stdout.strip()}


def write_report(report: dict[str, Any], json_path: Path, md_path: Path) -> None:
    report = portable(report)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# OLMRadialBlur A9D0 boundary N-way proof (2026-07-18)",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Partitions: `{report.get('partitions')}`",
        f"- Boundary SHA-256: `{report.get('boundary_sha256')}`",
        f"- Protected PID interactions: `{report.get('protected_pid_interactions')}`",
        f"- Exact claim: `{not report.get('no_exact_claim', True)}`",
        "",
        "## Gates",
        "",
        "| Gate | Result |",
        "| --- | --- |",
    ]
    lines.extend(
        f"| `{name}` | `{value}` |"
        for name, value in report.get("gates", {}).items()
    )
    lines.extend(["", "## Slices", "", "| Index | Rows | Input |", "| ---: | --- | --- |"])
    for item in report.get("slices", []):
        lines.append(f"| {item['index']} | `[{item['range'][0]},{item['range'][1]})` | `{item['input']}` |")
    lines.extend([
        "",
        "This report covers checkpoint preparation and optional bounded execution only.",
        "It makes no Windows, After Effects, or AE-exactness claim.",
        "",
    ])
    if report.get("error"):
        lines.extend(["## Failure", "", f"`{report['error']}`", ""])
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundary", type=Path, default=DEFAULT_BOUNDARY)
    parser.add_argument("--runtime-dir", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--partitions", type=int, default=8)
    parser.add_argument("--max-instructions", type=int, default=12_000_000_000)
    parser.add_argument("--run-full", action="store_true")
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    base = load_base()
    boundary = args.boundary.resolve()
    runtime = args.runtime_dir.resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    source_hash = base.file_sha256(boundary)
    report: dict[str, Any] = {
        "kind": "olmradialblur_a9d0_boundary_nway_20260718",
        "status": "rejected_fail_closed",
        "boundary": str(boundary),
        "boundary_sha256": source_hash,
        "partitions": args.partitions,
        "protected_pid_interactions": 0,
        "full_execution_requested": args.run_full,
        "no_exact_claim": True,
    }
    try:
        image = base.Checkpoint.read(boundary)
        contract = base.inspect_boundary(image)
        items = prepare_slices(base, boundary, runtime, contract, args.partitions)
        ranges = [item["range"] for item in items]
        report["contract"] = contract
        report["slices"] = items
        report["gates"] = {
            "boundary_rip": int(image.header["registers"]["gp"]["rip"]) == base.A9D0_ROW_BOUNDARY,
            "half_open_complete_partition": ranges == [list(pair) for pair in partition_rows(contract["start"], contract["end"], args.partitions)],
            "fresh_unique_slice_inputs": len({item["input"] for item in items}) == args.partitions,
            "fresh_unique_slice_results": len({item["result"] for item in items}) == args.partitions,
            "source_hash_unchanged": base.file_sha256(boundary) == source_hash,
            "protected_pid_untouched": True,
        }
        if not all(report["gates"].values()):
            raise ValueError(f"preparation gate failed: {report['gates']}")
        if args.run_full:
            results = run_slices(base, items, runtime, args.max_instructions)
            merged = runtime / "nway_merged_at_c95_20260718.aexcp"
            merge = merge_nway(base, boundary, results, contract, merged)
            normalization = runtime / "nway_merged_at_normalization_20260718.aexcp"
            continuation = run_to_rip(base, merged, normalization, runtime, args.max_instructions, 99, NORMALIZATION_RIP)
            report["full_execution"] = {"results": results, "merge": merge, "continuation": continuation}
        report["status"] = "pass_nway_prepared" if not args.run_full else "pass_nway_merged_to_normalization"
        if base.file_sha256(boundary) != source_hash:
            raise ValueError("boundary checkpoint changed")
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["status"] = "rejected_fail_closed"
        write_report(report, args.output_json, args.output_md)
        print(f"status={report['status']}")
        print(f"error={report['error']}")
        return 1
    write_report(report, args.output_json, args.output_md)
    print(f"status={report['status']}")
    print(f"partitions={args.partitions}")
    print(f"boundary_sha256={source_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
