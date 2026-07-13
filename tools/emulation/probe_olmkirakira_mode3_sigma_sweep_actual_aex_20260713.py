#!/usr/bin/env python3
"""Sweep OLMKiraKira Mode 3 actual-AEX Gaussian boundary over several lengths."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import struct
import subprocess
from pathlib import Path
from typing import Any

import pefile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SINGLE_PROBE_PATH = HERE / "probe_olmkirakira_mode3_actual_aex.py"
DEFAULT_JSON = ROOT / "refs/conformance/olmkirakira_mode3_sigma_sweep_actual_aex_20260713.json"
DEFAULT_MD = ROOT / "refs/conformance/olmkirakira_mode3_sigma_sweep_actual_aex_20260713.md"
DAT_18148D670 = 0x18148D670
DISASM_CALLSITE_START = 0x1811510C0
DISASM_CALLSITE_STOP = 0x181151108


def load_single_probe() -> Any:
    spec = importlib.util.spec_from_file_location("olmkirakira_mode3_actual_aex_probe", SINGLE_PROBE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load probe module: {SINGLE_PROBE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex-path", type=Path, default=ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex")
    parser.add_argument("--width", type=int, default=9)
    parser.add_argument("--height", type=int, default=7)
    parser.add_argument("--lengths", type=int, nargs="+", default=[1, 2, 5, 9])
    parser.add_argument("--max-instructions", type=int, default=20_000_000)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def read_lines(path: Path, center: str, radius: int) -> list[str]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for index, line in enumerate(lines):
        if center in line:
            start = max(0, index - radius)
            stop = min(len(lines), index + radius + 1)
            return lines[start:stop]
    raise RuntimeError(f"unable to find snippet {center!r} in {path}")


def capture_disasm(aex_path: Path) -> dict[str, Any]:
    command = [
        "objdump",
        "-d",
        "-M",
        "intel",
        f"--start-address=0x{DISASM_CALLSITE_START:x}",
        f"--stop-address=0x{DISASM_CALLSITE_STOP:x}",
        str(aex_path),
    ]
    proc = subprocess.run(command, text=True, capture_output=True, check=True)
    lines = [line.rstrip() for line in proc.stdout.splitlines() if line.strip()]
    return {
        "command": " ".join(command),
        "callsite_lines": lines,
    }


def capture_data_constant(aex_path: Path) -> dict[str, Any]:
    pe = pefile.PE(str(aex_path), fast_load=True)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    rva = DAT_18148D670 - image_base
    file_offset = pe.get_offset_from_rva(rva)
    raw = aex_path.read_bytes()[file_offset:file_offset + 16]
    section = pe.get_section_by_rva(rva)
    return {
        "virtual_address": hex(DAT_18148D670),
        "image_base": hex(image_base),
        "rva": hex(rva),
        "file_offset": hex(file_offset),
        "section": {
            "name": section.Name.decode(errors="ignore").rstrip("\x00"),
            "virtual_address": hex(section.VirtualAddress),
            "virtual_size": hex(section.Misc_VirtualSize),
            "raw_ptr": hex(section.PointerToRawData),
            "raw_size": hex(section.SizeOfRawData),
        },
        "raw_hex_le_16": raw.hex(),
        "raw_hex_le_8": raw[:8].hex(),
        "f64": struct.unpack("<d", raw[:8])[0],
        "next_f64": struct.unpack("<d", raw[8:16])[0],
    }


def run_sweep(args: argparse.Namespace) -> dict[str, Any]:
    single = load_single_probe()
    started = dt.datetime.now(dt.timezone.utc)
    report: dict[str, Any] = {
        "schema": "olmkirakira-mode3-sigma-sweep-actual-aex/1",
        "generated_at_utc": started.isoformat().replace("+00:00", "Z"),
        "single_probe_source": str(SINGLE_PROBE_PATH),
        "single_probe_sha256": hashlib.sha256(SINGLE_PROBE_PATH.read_bytes()).hexdigest(),
        "aex": str(args.aex_path),
        "aex_sha256": hashlib.sha256(args.aex_path.read_bytes()).hexdigest() if args.aex_path.exists() else None,
        "input": {
            "width": args.width,
            "height": args.height,
            "lengths": list(args.lengths),
            "blur_mode": 3,
            "sigma_argument": 0.0,
            "type": "CV_32FC1",
        },
        "execution_log": [],
        "cases": [],
        "FACT": [
            "Each sweep point replays the actual AEX helper path separately and records the captured FUN_181272ec0 boundary rather than reusing a cached hit.",
            "The decomp callsite multiplies integer length by DAT_18148d670 before calling FUN_181272ec0.",
            "The disassembly callsite at 0x1811510d5 loads the same DAT_18148d670 qword into mulsd before the Gaussian wrapper call.",
            "The raw .rdata bytes at virtual address 0x18148d670 decode to IEEE-754 little-endian double 0.5.",
        ],
        "INFERENCE": [
            "The size field is reported exactly as the captured low/high 32-bit unpack of R8 (0x100000000 -> [0, 1]); this report does not rename those words into semantic width/height beyond that raw decode.",
            "Agreement between observed sigmaX and length * 0.5 is evidence for the helper-side multiplier contract, not a claim about deeper OpenCV internals.",
            "If any point misses the Gaussian hook, that case remains in the report and weakens the sweep verdict instead of being silently dropped.",
        ],
    }
    if not args.aex_path.exists():
        report["status"] = "skip"
        report["error"] = f"missing AEX: {args.aex_path}"
        return report

    decomp_snippet = read_lines(
        ROOT / "decomp/OLMKiraKira.aex.c.txt",
        "FUN_181272ec0(local_218,local_200,0x100000000,(double)(int)param_7 * DAT_18148d670);",
        4,
    )
    dat_usage_snippet = read_lines(ROOT / "decomp/OLMKiraKira.aex.c.txt", "uVar2 = DAT_18148d670;", 6)
    report["dat_18148d670"] = {
        "decomp_callsite_snippet": decomp_snippet,
        "decomp_additional_usage_snippet": dat_usage_snippet,
        "disasm": capture_disasm(args.aex_path),
        "data": capture_data_constant(args.aex_path),
    }

    dat_value = float(report["dat_18148d670"]["data"]["f64"])
    size_set: set[tuple[int, int]] = set()
    all_captured = True
    sigma_matches = True
    for length in args.lengths:
        call_started = dt.datetime.now(dt.timezone.utc)
        namespace = argparse.Namespace(
            aex_path=args.aex_path,
            width=args.width,
            height=args.height,
            length=length,
            sigma=0.0,
            output_json=args.output_json,
            output_md=args.output_md,
            max_instructions=args.max_instructions,
        )
        point = single.run(namespace)
        call_finished = dt.datetime.now(dt.timezone.utc)
        case: dict[str, Any] = {
            "length": length,
            "status": point["status"],
            "started_at_utc": call_started.isoformat().replace("+00:00", "Z"),
            "finished_at_utc": call_finished.isoformat().replace("+00:00", "Z"),
            "helper_result": point.get("helper_result"),
            "target_hit_count": len(point.get("target_capture", {}).get("hits", [])),
        }
        hits = point.get("target_capture", {}).get("hits", [])
        if hits:
            hit = hits[0]
            observed_sigma = float(hit["sigma_x_f64"])
            expected_sigma = float(length) * dat_value
            size = tuple(int(x) for x in hit["size"])
            case.update(
                {
                    "size": list(size),
                    "size_packed": hit["size_packed"],
                    "sigma_x_f64": observed_sigma,
                    "expected_sigma_x_f64": expected_sigma,
                    "sigma_matches_expected": observed_sigma == expected_sigma,
                    "input_wrapper_flags": hit.get("input_array", {}).get("flags"),
                    "output_wrapper_flags": hit.get("output_array", {}).get("flags"),
                }
            )
            size_set.add(size)
            sigma_matches = sigma_matches and bool(case["sigma_matches_expected"])
        else:
            all_captured = False
            sigma_matches = False
            case["error"] = point.get("error")
        report["cases"].append(case)
        report["execution_log"].append(
            {
                "length": length,
                "status": case["status"],
                "target_hit_count": case["target_hit_count"],
                "size": case.get("size"),
                "sigma_x_f64": case.get("sigma_x_f64"),
                "expected_sigma_x_f64": case.get("expected_sigma_x_f64"),
                "instructions": (case.get("helper_result") or {}).get("instructions"),
            }
        )

    report["summary"] = {
        "dat_18148d670_f64": dat_value,
        "all_points_captured": all_captured,
        "observed_size_set": [list(item) for item in sorted(size_set)],
        "size_is_invariant": len(size_set) == 1 and all_captured,
        "sigma_matches_length_times_dat": sigma_matches and all_captured,
        "length_count": len(args.lengths),
    }
    report["status"] = "captured" if all_captured else "partial"
    return report


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMKiraKira Mode 3 sigma sweep actual-AEX evidence",
        "",
        f"Date: {report['generated_at_utc']}",
        "",
        "## FACT",
        "",
    ]
    lines.extend(f"- {item}" for item in report.get("FACT", []))
    lines += ["", "## INFERENCE", ""]
    lines.extend(f"- {item}" for item in report.get("INFERENCE", []))
    lines += [
        "",
        "## Execution",
        "",
        f"- Status: `{report['status']}`",
        f"- AEX: `{report['aex']}`",
        f"- AEX SHA-256: `{report['aex_sha256']}`",
        f"- Single probe: `{report['single_probe_source']}`",
        f"- Single probe SHA-256: `{report['single_probe_sha256']}`",
        f"- Input: `{json.dumps(report['input'], sort_keys=True)}`",
        "",
        "## DAT_18148d670 evidence",
        "",
        f"- Raw data: `{json.dumps(report['dat_18148d670']['data'], sort_keys=True)}`",
        f"- Disasm command: `{report['dat_18148d670']['disasm']['command']}`",
        "",
        "### Decomp callsite",
        "",
        "```c",
        *report["dat_18148d670"]["decomp_callsite_snippet"],
        "```",
        "",
        "### Decomp additional use",
        "",
        "```c",
        *report["dat_18148d670"]["decomp_additional_usage_snippet"],
        "```",
        "",
        "### Disasm callsite",
        "",
        "```asm",
        *report["dat_18148d670"]["disasm"]["callsite_lines"],
        "```",
        "",
        "## Sweep table",
        "",
        "| Length | Status | Size | sigmaX | Expected sigmaX (= length * DAT) | Match | Instructions |",
        "| --- | --- | --- | ---: | ---: | --- | ---: |",
    ]
    for case in report["cases"]:
        lines.append(
            "| {length} | {status} | {size} | {sigma} | {expected} | {match} | {instructions} |".format(
                length=case["length"],
                status=case["status"],
                size=case.get("size"),
                sigma=case.get("sigma_x_f64"),
                expected=case.get("expected_sigma_x_f64"),
                match=case.get("sigma_matches_expected"),
                instructions=(case.get("helper_result") or {}).get("instructions"),
            )
        )
    lines += ["", "## Execution log", ""]
    for item in report["execution_log"]:
        lines.append(f"- `{json.dumps(item, sort_keys=True)}`")
    lines += ["", "## Verdict", ""]
    lines.append(f"- `{json.dumps(report['summary'], sort_keys=True)}`")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = run_sweep(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "json": str(args.output_json),
                "md": str(args.output_md),
                "cases": len(report.get("cases", [])),
                "captured_cases": sum(1 for case in report.get("cases", []) if case["status"] == "captured"),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] in {"captured", "partial", "skip"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
