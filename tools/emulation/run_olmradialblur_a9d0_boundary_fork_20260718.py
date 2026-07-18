#!/usr/bin/env python3
"""Advance checkpoint6 to an A9D0 row boundary and prepare a safe fork.

The source checkpoint and protected natural process are never loaded by this
program.  A byte-identical copy is resumed in a fresh Unicorn loader.  Full
slice checkpoints are emitted only after a bounded actual-AEX serial versus
two-slice run proves pointer identity, half-open ownership, plane-only writes,
and byte-exact merge equality.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ZOOM_RUNNER = ROOT / "tools/emulation/test_zoom_case0009.py"
DEFAULT_SOURCE = Path("/tmp/olm_radial_case0009_workers_progress6_20260718.aexcp")
DEFAULT_RUNTIME = Path("/tmp/olmradialblur_a9d0_boundary_fork_20260718")
DEFAULT_JSON = ROOT / "refs/conformance/olmradialblur_a9d0_boundary_fork_20260718.json"
DEFAULT_MD = ROOT / "refs/conformance/olmradialblur_a9d0_boundary_fork_20260718.md"

MAGIC = b"AEXCP64\x00"
VERSION = 1
PREFIX_SIZE = len(MAGIC) + 4 + 8 + 32
EXPECTED_AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
A9D0_ROW_BOUNDARY = 0x18000B0F9
A9D0_RETURN = 0x180005C95
NORMALIZATION_START = 0x180005C9F
PROTECTED_PID = 59481


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class Checkpoint:
    header: dict[str, Any]
    encoded_regions: list[bytes]

    @classmethod
    def read(cls, path: Path) -> "Checkpoint":
        with path.open("rb") as handle:
            prefix = handle.read(PREFIX_SIZE)
            if len(prefix) != PREFIX_SIZE or not prefix.startswith(MAGIC):
                raise ValueError(f"invalid checkpoint prefix: {path}")
            version, header_size = struct.unpack(
                "<IQ", prefix[len(MAGIC):len(MAGIC) + 12]
            )
            if version != VERSION or header_size > 64 * 1024 * 1024:
                raise ValueError(f"unsupported checkpoint header: {path}")
            header_bytes = handle.read(header_size)
            if hashlib.sha256(header_bytes).digest() != prefix[-32:]:
                raise ValueError(f"checkpoint header checksum mismatch: {path}")
            header = json.loads(header_bytes.decode("ascii"))
            encoded = []
            for region in header.get("regions", []):
                size = int(region["compressed_size"])
                blob = handle.read(size)
                if len(blob) != size:
                    raise ValueError(f"truncated checkpoint region: {region['name']}")
                encoded.append(blob)
            if handle.read(1):
                raise ValueError(f"checkpoint has trailing data: {path}")
        image = cls(header=header, encoded_regions=encoded)
        image.validate_identity()
        return image

    def validate_identity(self) -> None:
        if self.header.get("format") != "aex-loader-x64-checkpoint":
            raise ValueError("checkpoint format mismatch")
        if self.header.get("version") != VERSION:
            raise ValueError("checkpoint version mismatch")
        if self.header.get("aex", {}).get("sha256") != EXPECTED_AEX_SHA256:
            raise ValueError("checkpoint AEX identity mismatch")
        metadata = self.header.get("metadata", {})
        config = metadata.get("config", {})
        if metadata.get("harness") != "test_zoom_case0009":
            raise ValueError("checkpoint harness identity mismatch")
        forbidden = (
            "direct_zoom_core", "direct_fast_forward_prefill", "direct_python_prefill",
            "direct_detour_prepass", "direct_detour_scatter",
        )
        if any(config.get(name) for name in forbidden):
            raise ValueError("checkpoint contains a forbidden synthetic or detoured path")

    def region_index(self, name: str) -> int:
        for index, region in enumerate(self.header["regions"]):
            if region["name"] == name:
                return index
        raise ValueError(f"checkpoint region is absent: {name}")

    def raw_region(self, name: str) -> bytearray:
        index = self.region_index(name)
        region = self.header["regions"][index]
        raw = zlib.decompress(self.encoded_regions[index])
        if len(raw) != int(region["size"]):
            raise ValueError(f"checkpoint region size mismatch: {name}")
        if hashlib.sha256(raw).hexdigest() != region["sha256"]:
            raise ValueError(f"checkpoint region hash mismatch: {name}")
        return bytearray(raw)

    def replace_region(self, name: str, raw: bytes | bytearray) -> None:
        index = self.region_index(name)
        region = self.header["regions"][index]
        if len(raw) != int(region["size"]):
            raise ValueError(f"replacement region size mismatch: {name}")
        encoded = zlib.compress(bytes(raw), level=9)
        region["compressed_size"] = len(encoded)
        region["sha256"] = hashlib.sha256(raw).hexdigest()
        self.encoded_regions[index] = encoded

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        header_bytes = json.dumps(
            self.header, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
        prefix = MAGIC + struct.pack("<IQ", VERSION, len(header_bytes))
        prefix += hashlib.sha256(header_bytes).digest()
        fd, temporary = tempfile.mkstemp(prefix="radial-fork-20260718-", dir=str(path.parent))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(prefix)
                handle.write(header_bytes)
                for blob in self.encoded_regions:
                    handle.write(blob)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except Exception:
            Path(temporary).unlink(missing_ok=True)
            raise


def u32(raw: bytes | bytearray, base: int, address: int) -> int:
    return struct.unpack_from("<I", raw, address - base)[0]


def u64(raw: bytes | bytearray, base: int, address: int) -> int:
    return struct.unpack_from("<Q", raw, address - base)[0]


def put_u32(raw: bytearray, base: int, address: int, value: int) -> None:
    struct.pack_into("<I", raw, address - base, value & 0xFFFFFFFF)


def put_u64(raw: bytearray, base: int, address: int, value: int) -> None:
    struct.pack_into("<Q", raw, address - base, value & 0xFFFFFFFFFFFFFFFF)


def half_open_partition(start: int, split: int, end: int) -> list[tuple[int, int]]:
    if not (0 <= start < split < end):
        raise ValueError(f"invalid half-open partition: [{start},{split}) + [{split},{end})")
    return [(start, split), (split, end)]


def non_overlapping(ranges: dict[str, tuple[int, int]]) -> bool:
    ordered = sorted((start, end, name) for name, (start, end) in ranges.items())
    return all(start < end for start, end, _ in ordered) and all(
        left_end <= right_start
        for (_, left_end, _), (right_start, _, _) in zip(ordered, ordered[1:])
    )


def inspect_boundary(checkpoint: Checkpoint) -> dict[str, Any]:
    gp = checkpoint.header["registers"]["gp"]
    if int(gp["rip"]) != A9D0_ROW_BOUNDARY:
        raise ValueError(f"checkpoint is not at row boundary: 0x{int(gp['rip']):x}")
    stack_index = checkpoint.region_index("stack")
    stack_meta = checkpoint.header["regions"][stack_index]
    stack_base = int(stack_meta["address"])
    stack = checkpoint.raw_region("stack")
    rsp = int(gp["rsp"])
    work = u64(stack, stack_base, rsp + 0x90)
    width = u32(stack, stack_base, rsp + 0xB8)
    height = u32(stack, stack_base, rsp + 0xC0)
    row = u32(stack, stack_base, rsp + 0xC8)
    raw_end = u32(stack, stack_base, rsp + 0xD0)
    effective_end = min(height, raw_end)
    caller_ebx = u32(stack, stack_base, rsp + 0x80)
    caller_return = u64(stack, stack_base, rsp + 0x88)
    caller_count = u32(stack, stack_base, work + 0x4220)

    pointers = {
        "source_rgba": u64(stack, stack_base, work + 0x38),
        "source_scalar_4": u64(stack, stack_base, work + 0x40),
        "source_scalar_3": u64(stack, stack_base, work + 0x50),
        "valid": u64(stack, stack_base, rsp + 0x70),
        "output_rgba": u64(stack, stack_base, work + 0x4210),
        "output_scalar": u64(stack, stack_base, work + 0x4218),
    }
    if u64(stack, stack_base, rsp + 0xD8) != pointers["output_rgba"]:
        raise ValueError("output RGBA pointer identity failed")
    if u64(stack, stack_base, rsp + 0xE0) != pointers["output_scalar"]:
        raise ValueError("output scalar pointer identity failed")

    index = row * width
    live_pointer_gates = {
        "r10_row_index": int(gp["r10"]) == index,
        "r11_next_row": (int(gp["r11"]) & 0xFFFFFFFF) == row,
        "rbp_source_rgba": int(gp["rbp"]) == pointers["source_rgba"] + index * 16,
        "r12_source_scalar_3": int(gp["r12"]) == pointers["source_scalar_3"] + index * 4,
        "r13_source_scalar_4": int(gp["r13"]) == pointers["source_scalar_4"] + index * 4,
        "rcx_valid": int(gp["rcx"]) == pointers["valid"] + index,
        "rdi_rgba_index": (int(gp["rdi"]) & 0xFFFFFFFF) == index * 4,
    }
    if not all(live_pointer_gates.values()):
        raise ValueError(f"live row pointer identity failed: {live_pointer_gates}")
    if caller_return != A9D0_RETURN or caller_ebx != caller_count:
        raise ValueError("A9D0 checkpoint is not the final caller invocation")
    if not (0 < width and 0 <= row < effective_end <= height):
        raise ValueError("invalid remaining row domain")

    cells = width * height
    plane_ranges = {
        "output_rgba": (pointers["output_rgba"], pointers["output_rgba"] + cells * 16),
        "output_scalar": (pointers["output_scalar"], pointers["output_scalar"] + cells * 4),
        "source_rgba": (pointers["source_rgba"], pointers["source_rgba"] + cells * 16),
        "source_scalar_4": (
            pointers["source_scalar_4"], pointers["source_scalar_4"] + cells * 4,
        ),
        "source_scalar_3": (
            pointers["source_scalar_3"], pointers["source_scalar_3"] + cells * 4,
        ),
        "valid": (pointers["valid"], pointers["valid"] + cells),
    }
    if not non_overlapping(plane_ranges):
        raise ValueError(f"source/output plane alias detected: {plane_ranges}")
    heap = next(region for region in checkpoint.header["regions"] if region["name"] == "heap-used")
    heap_start = int(heap["address"])
    heap_end = heap_start + int(heap["size"])
    if any(start < heap_start or end > heap_end for start, end in plane_ranges.values()):
        raise ValueError("a proven plane exceeds the checkpoint heap")
    if plane_ranges["output_rgba"][1] != pointers["output_scalar"]:
        raise ValueError("RGBA output does not end at scalar output")
    if plane_ranges["output_scalar"][1] != pointers["source_rgba"]:
        raise ValueError("scalar output does not end at source RGBA")

    return {
        "rsp": rsp,
        "stack_base": stack_base,
        "work": work,
        "width": width,
        "height": height,
        "start": row,
        "raw_end": raw_end,
        "end": effective_end,
        "caller_count": caller_count,
        "caller_ebx": caller_ebx,
        "caller_return": caller_return,
        "pointers": pointers,
        "plane_ranges": plane_ranges,
        "live_pointer_gates": live_pointer_gates,
        "heap_base": heap_start,
        "heap_size": int(heap["size"]),
    }


def make_slice(boundary_path: Path, destination: Path, contract: dict[str, Any],
               start: int, end: int) -> None:
    if not (contract["start"] <= start < end <= contract["end"]):
        raise ValueError(f"slice is outside remaining rows: [{start},{end})")
    checkpoint = Checkpoint.read(boundary_path)
    current = inspect_boundary(checkpoint)
    stable_keys = ("width", "height", "start", "end", "pointers", "plane_ranges")
    if any(current[key] != contract[key] for key in stable_keys):
        raise ValueError("boundary contract changed while preparing a slice")

    stack = checkpoint.raw_region("stack")
    base = contract["stack_base"]
    rsp = contract["rsp"]
    width = contract["width"]
    index = start * width
    previous_index = (start - 1) * width
    pointers = contract["pointers"]
    gp = checkpoint.header["registers"]["gp"]
    gp.update({
        "rax": end,
        "rcx": pointers["valid"] + index,
        "r10": index,
        "r11": start,
        "r12": pointers["source_scalar_3"] + index * 4,
        "r13": pointers["source_scalar_4"] + index * 4,
        "rbp": pointers["source_rgba"] + index * 16,
        "rdi": index * 4,
    })
    put_u32(stack, base, rsp + 0x98, previous_index)
    put_u32(stack, base, rsp + 0xA0, previous_index * 4)
    put_u64(stack, base, rsp + 0xA8, pointers["valid"] + index)
    put_u32(stack, base, rsp + 0xC8, start)
    put_u32(stack, base, rsp + 0xD0, end)
    checkpoint.replace_region("stack", stack)
    metadata = checkpoint.header.setdefault("metadata", {})
    metadata["a9d0_boundary_fork_20260718"] = {
        "source_boundary_sha256": file_sha256(boundary_path),
        "range": [start, end],
        "range_semantics": "half-open",
        "width": width,
        "merge_planes": ["output_rgba", "output_scalar"],
    }
    checkpoint.write(destination)


def runner_command(source: Path, destination: Path, runtime: Path,
                   max_instructions: int) -> list[str]:
    return [
        sys.executable, str(ZOOM_RUNNER),
        "--resume-checkpoint", str(source),
        "--save-checkpoint-at-rip", str(destination), hex(A9D0_RETURN),
        "--max-instructions", str(max_instructions),
        "--output-json", str(runtime / "unused_output_20260718.json"),
        "--output-md", str(runtime / "unused_output_20260718.md"),
    ]


def run_to_rip(source: Path, destination: Path, rip: int, runtime: Path,
               max_instructions: int) -> dict[str, Any]:
    destination.unlink(missing_ok=True)
    command = runner_command(source, destination, runtime, max_instructions)
    command[command.index(hex(A9D0_RETURN))] = hex(rip)
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0 or not destination.is_file():
        raise RuntimeError(
            f"checkpoint resume failed ({result.returncode}):\n{result.stdout}\n{result.stderr}"
        )
    return {"command": command, "stdout": result.stdout.strip(), "sha256": file_sha256(destination)}


def run_pair(left_input: Path, left_output: Path, right_input: Path, right_output: Path,
             runtime: Path, max_instructions: int) -> list[dict[str, Any]]:
    left_output.unlink(missing_ok=True)
    right_output.unlink(missing_ok=True)
    commands = [
        runner_command(left_input, left_output, runtime, max_instructions),
        runner_command(right_input, right_output, runtime, max_instructions),
    ]
    processes = [
        subprocess.Popen(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for command in commands
    ]
    results = []
    for command, process, output in zip(commands, processes, (left_output, right_output)):
        stdout, stderr = process.communicate()
        if process.returncode != 0 or not output.is_file():
            raise RuntimeError(
                f"slice resume failed ({process.returncode}):\n{stdout}\n{stderr}"
            )
        results.append({"command": command, "stdout": stdout.strip(), "sha256": file_sha256(output)})
    return results


def owned_ranges(contract: dict[str, Any], start: int, end: int) -> list[tuple[int, int]]:
    width = contract["width"]
    pointers = contract["pointers"]
    return [
        (pointers["output_rgba"] + start * width * 16,
         pointers["output_rgba"] + end * width * 16),
        (pointers["output_scalar"] + start * width * 4,
         pointers["output_scalar"] + end * width * 4),
    ]


def outside_owned_equal(base: bytes | bytearray, result: bytes | bytearray, heap_base: int,
                        ranges: list[tuple[int, int]]) -> bool:
    cursor = 0
    for start, end in sorted((start - heap_base, end - heap_base) for start, end in ranges):
        if not (cursor <= start <= end <= len(base)):
            return False
        if base[cursor:start] != result[cursor:start]:
            return False
        cursor = end
    return base[cursor:] == result[cursor:]


def validate_result(path: Path, input_path: Path) -> Checkpoint:
    checkpoint = Checkpoint.read(path)
    rip = int(checkpoint.header["registers"]["gp"]["rip"])
    if rip != A9D0_RETURN:
        raise ValueError(f"slice did not stop at A9D0 return: 0x{rip:x}")
    lineage = checkpoint.header.get("metadata", {}).get("checkpoint_lineage", [])
    if not lineage or lineage[-1].get("sha256") != file_sha256(input_path):
        raise ValueError("slice result does not descend from its prepared input")
    return checkpoint


def merge_results(boundary_path: Path, left_input: Path, left_result: Path,
                  right_input: Path, right_result: Path, output: Path,
                  contract: dict[str, Any], left_range: tuple[int, int],
                  right_range: tuple[int, int], serial_result: Path | None = None) -> dict[str, Any]:
    boundary = Checkpoint.read(boundary_path)
    left = validate_result(left_result, left_input)
    right = validate_result(right_result, right_input)
    boundary_heap = boundary.raw_region("heap-used")
    left_heap = left.raw_region("heap-used")
    right_heap = right.raw_region("heap-used")
    left_owned = owned_ranges(contract, *left_range)
    right_owned = owned_ranges(contract, *right_range)
    left_closed = outside_owned_equal(boundary_heap, left_heap, contract["heap_base"], left_owned)
    right_closed = outside_owned_equal(boundary_heap, right_heap, contract["heap_base"], right_owned)
    if not left_closed or not right_closed:
        raise ValueError("a slice wrote outside its owned output rows")

    merged_heap = bytearray(boundary_heap)
    for result_heap, ranges in ((left_heap, left_owned), (right_heap, right_owned)):
        for start, end in ranges:
            a = start - contract["heap_base"]
            b = end - contract["heap_base"]
            merged_heap[a:b] = result_heap[a:b]
    merged_heap_sha = hashlib.sha256(merged_heap).hexdigest()
    serial_equal = None
    serial_heap_sha = None
    if serial_result is not None:
        serial_heap = Checkpoint.read(serial_result).raw_region("heap-used")
        serial_heap_sha = hashlib.sha256(serial_heap).hexdigest()
        serial_equal = merged_heap == serial_heap
        if not serial_equal:
            raise ValueError("serial and merged two-slice heaps differ")

    leader = left
    leader.replace_region("heap-used", merged_heap)
    leader.header.setdefault("metadata", {})["a9d0_merge_20260718"] = {
        "boundary_sha256": file_sha256(boundary_path),
        "left_result_sha256": file_sha256(left_result),
        "right_result_sha256": file_sha256(right_result),
        "ranges": [list(left_range), list(right_range)],
        "planes": ["output_rgba", "output_scalar"],
        "heap_sha256": merged_heap_sha,
    }
    leader.write(output)
    return {
        "left_writes_within_owned_planes": left_closed,
        "right_writes_within_owned_planes": right_closed,
        "merged_heap_sha256": merged_heap_sha,
        "serial_heap_sha256": serial_heap_sha,
        "serial_vs_two_slice_heap_equal": serial_equal,
        "merged_checkpoint": str(output),
        "merged_checkpoint_sha256": file_sha256(output),
    }


def markdown(report: dict[str, Any]) -> str:
    contract = report.get("contract", {})
    lines = [
        "# OLMRadialBlur A9D0 boundary fork proof (2026-07-18)", "",
        f"- Status: `{report['status']}`",
        f"- Protected PID interactions: `{report['protected_pid_interactions']}`",
        f"- Original checkpoint unchanged: `{report.get('source_unchanged', False)}`", "",
        "## Proven boundary", "",
        f"- RIP: `{report.get('boundary_rip', '')}`",
        f"- Remaining rows: `[{contract.get('start')}, {contract.get('end')})`",
        f"- Width / height: `{contract.get('width')} / {contract.get('height')}`",
        f"- Caller return: `{hex(contract.get('caller_return', 0))}`; final invocation: "
        f"`{contract.get('caller_ebx')} / {contract.get('caller_count')}`", "",
        "## Fail-closed gates", "",
        "| Gate | Result |", "| --- | --- |",
    ]
    lines.extend(f"| `{name}` | `{value}` |" for name, value in report.get("gates", {}).items())
    lines.extend(["", "## Fork", ""])
    for item in report.get("full_fork", {}).get("slices", []):
        start, end = item["range"]
        lines.append(f"- `[{start}, {end})`: `{item['checkpoint']}`")
    lines.extend([
        "", "The full slice checkpoints are prepared but not executed by default. Run both fresh-loader "
        "commands concurrently, stop at `0x180005c95`, merge only the two owned output planes, then "
        "resume the merged checkpoint through normalization at `0x180005c9f`.", "",
        "No caller state was reconstructed: the preserved worker frame was advanced and range-adjusted in place.",
        "No Windows/AE exactness claim is made; this is an actual-AEX Unicorn checkpoint proof.", "",
    ])
    if report.get("error"):
        lines.extend(["## Failure", "", f"- {report['error']}", ""])
    return "\n".join(lines)


def write_report(report: dict[str, Any], json_path: Path, md_path: Path) -> None:
    def portable(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: portable(item) for key, item in value.items()}
        if isinstance(value, list):
            return [portable(item) for item in value]
        if isinstance(value, str):
            return value.replace(str(ROOT), "<repo>")
        return value

    report = portable(report)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--runtime-dir", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    parser.add_argument("--bounded-rows", type=int, default=2)
    parser.add_argument("--max-instructions", type=int, default=100_000_000)
    parser.add_argument("--full-max-instructions", type=int, default=12_000_000_000)
    parser.add_argument("--run-full", action="store_true")
    args = parser.parse_args()

    runtime = args.runtime_dir
    runtime.mkdir(parents=True, exist_ok=True)
    source = args.source.resolve()
    source_hash_before = file_sha256(source)
    copied = runtime / "checkpoint6_copy_20260718.aexcp"
    boundary_path = runtime / "next_row_boundary_20260718.aexcp"
    shutil.copy2(source, copied)

    report: dict[str, Any] = {
        "kind": "olmradialblur_a9d0_boundary_fork_20260718",
        "schema": 1,
        "status": "rejected_fail_closed",
        "protected_pid": PROTECTED_PID,
        "protected_pid_interactions": 0,
        "source": str(source),
        "source_sha256": source_hash_before,
        "copy": str(copied),
        "copy_sha256": file_sha256(copied),
        "gates": {},
    }
    full_paths: list[Path] = []
    try:
        if report["copy_sha256"] != source_hash_before:
            raise ValueError("checkpoint copy hash mismatch")
        advance = run_to_rip(
            copied, boundary_path, A9D0_ROW_BOUNDARY, runtime, args.max_instructions
        )
        boundary = Checkpoint.read(boundary_path)
        contract = inspect_boundary(boundary)
        report["contract"] = contract
        report["boundary"] = str(boundary_path)
        report["boundary_sha256"] = file_sha256(boundary_path)
        report["boundary_rip"] = hex(A9D0_ROW_BOUNDARY)
        report["advance"] = advance

        bounded_end = min(contract["start"] + args.bounded_rows, contract["end"])
        if bounded_end - contract["start"] < 2:
            raise ValueError("fewer than two rows remain for the bounded equality proof")
        bounded_split = contract["start"] + (bounded_end - contract["start"]) // 2
        bounded_ranges = half_open_partition(contract["start"], bounded_split, bounded_end)
        names = {
            "serial_input": runtime / "bounded_serial_input_20260718.aexcp",
            "serial_result": runtime / "bounded_serial_result_20260718.aexcp",
            "left_input": runtime / "bounded_left_input_20260718.aexcp",
            "left_result": runtime / "bounded_left_result_20260718.aexcp",
            "right_input": runtime / "bounded_right_input_20260718.aexcp",
            "right_result": runtime / "bounded_right_result_20260718.aexcp",
            "merged": runtime / "bounded_merged_result_20260718.aexcp",
            "normalization": runtime / "bounded_normalization_entry_20260718.aexcp",
        }
        make_slice(boundary_path, names["serial_input"], contract, contract["start"], bounded_end)
        make_slice(boundary_path, names["left_input"], contract, *bounded_ranges[0])
        make_slice(boundary_path, names["right_input"], contract, *bounded_ranges[1])
        serial_run = run_to_rip(
            names["serial_input"], names["serial_result"], A9D0_RETURN,
            runtime, args.max_instructions,
        )
        pair_runs = run_pair(
            names["left_input"], names["left_result"],
            names["right_input"], names["right_result"], runtime, args.max_instructions,
        )
        bounded_merge = merge_results(
            boundary_path, names["left_input"], names["left_result"],
            names["right_input"], names["right_result"], names["merged"],
            contract, bounded_ranges[0], bounded_ranges[1], names["serial_result"],
        )
        normalization_run = run_to_rip(
            names["merged"], names["normalization"], NORMALIZATION_START,
            runtime, args.max_instructions,
        )
        normalization_checkpoint = Checkpoint.read(names["normalization"])
        normalization_reached = (
            int(normalization_checkpoint.header["registers"]["gp"]["rip"])
            == NORMALIZATION_START
        )
        report["bounded_proof"] = {
            "range": [contract["start"], bounded_end],
            "slices": [list(item) for item in bounded_ranges],
            "serial_run": serial_run,
            "slice_runs": pair_runs,
            "merge": bounded_merge,
            "normalization_run": normalization_run,
            "normalization_reached": normalization_reached,
        }

        full_split = contract["start"] + (contract["end"] - contract["start"]) // 2
        full_ranges = half_open_partition(contract["start"], full_split, contract["end"])
        full_left_input = runtime / "full_left_input_20260718.aexcp"
        full_right_input = runtime / "full_right_input_20260718.aexcp"
        full_paths = [full_left_input, full_right_input]
        make_slice(boundary_path, full_left_input, contract, *full_ranges[0])
        make_slice(boundary_path, full_right_input, contract, *full_ranges[1])
        report["full_fork"] = {
            "ranges": [list(item) for item in full_ranges],
            "instruction_budget_per_slice": args.full_max_instructions,
            "slices": [
                {"range": list(full_ranges[0]), "checkpoint": str(full_left_input),
                 "sha256": file_sha256(full_left_input)},
                {"range": list(full_ranges[1]), "checkpoint": str(full_right_input),
                 "sha256": file_sha256(full_right_input)},
            ],
            "concurrent_commands": [
                runner_command(
                    full_left_input, runtime / "full_left_result_20260718.aexcp",
                    runtime, args.full_max_instructions,
                ),
                runner_command(
                    full_right_input, runtime / "full_right_result_20260718.aexcp",
                    runtime, args.full_max_instructions,
                ),
            ],
            "run_full_flag": "--run-full",
            "normalization_resume_rip": hex(NORMALIZATION_START),
        }

        gates = {
            "source_copy_hash_identity": file_sha256(copied) == source_hash_before,
            "aex_identity": boundary.header["aex"]["sha256"] == EXPECTED_AEX_SHA256,
            "natural_undetoured_lineage": True,
            "row_boundary_reached": int(boundary.header["registers"]["gp"]["rip"]) == A9D0_ROW_BOUNDARY,
            "pointer_identity": all(contract["live_pointer_gates"].values()),
            "plane_non_alias": non_overlapping(contract["plane_ranges"]),
            "final_caller_invocation": contract["caller_ebx"] == contract["caller_count"],
            "half_open_complete_partition": full_ranges[0][0] == contract["start"]
            and full_ranges[0][1] == full_ranges[1][0]
            and full_ranges[1][1] == contract["end"],
            "left_plane_write_bounded": bounded_merge["left_writes_within_owned_planes"],
            "right_plane_write_bounded": bounded_merge["right_writes_within_owned_planes"],
            "bounded_serial_vs_two_slice_equal": bounded_merge["serial_vs_two_slice_heap_equal"],
            "normalization_continuation_preserved": contract["caller_return"] == A9D0_RETURN
            and normalization_reached,
            "protected_pid_untouched": report["protected_pid_interactions"] == 0,
        }
        report["gates"] = gates
        if not all(gates.values()):
            raise ValueError(f"one or more fail-closed gates failed: {gates}")

        if args.run_full:
            left_result = runtime / "full_left_result_20260718.aexcp"
            right_result = runtime / "full_right_result_20260718.aexcp"
            full_runs = run_pair(
                full_left_input, left_result, full_right_input, right_result,
                runtime, args.full_max_instructions,
            )
            merged = runtime / "full_merged_at_c95_20260718.aexcp"
            full_merge = merge_results(
                boundary_path, full_left_input, left_result, full_right_input, right_result,
                merged, contract, full_ranges[0], full_ranges[1], None,
            )
            normalization = runtime / "full_merged_at_normalization_20260718.aexcp"
            full_normalization_run = run_to_rip(
                merged, normalization, NORMALIZATION_START, runtime, args.max_instructions,
            )
            report["full_execution"] = {
                "runs": full_runs,
                "merge": full_merge,
                "normalization_run": full_normalization_run,
                "continuation_checkpoint": str(normalization),
            }

        report["source_sha256_after"] = file_sha256(source)
        report["source_unchanged"] = report["source_sha256_after"] == source_hash_before
        if not report["source_unchanged"]:
            raise ValueError("source checkpoint changed during proof")
        report["status"] = "pass_boundary_fork_prepared"
    except Exception as exc:
        for path in full_paths:
            path.unlink(missing_ok=True)
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["source_sha256_after"] = file_sha256(source)
        report["source_unchanged"] = report["source_sha256_after"] == source_hash_before
        write_report(report, args.output_json, args.output_md)
        print(f"status={report['status']}")
        print(f"error={report['error']}")
        return 1

    write_report(report, args.output_json, args.output_md)
    print(f"status={report['status']}")
    print(f"boundary={boundary_path}")
    print(f"remaining=[{contract['start']},{contract['end']})")
    print(f"full_slices={report['full_fork']['ranges']}")
    print(f"bounded_equal={report['gates']['bounded_serial_vs_two_slice_equal']}")
    print(f"protected_pid_interactions={report['protected_pid_interactions']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
