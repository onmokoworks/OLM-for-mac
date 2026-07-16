#!/usr/bin/env python3
"""Regression harness for the actual OLMDirectionalBlur 8bpc writer."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402


AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
ENTRY = 0x180006B30
DISASM_STOP = 0x180006BD0
REPORT_JSON = ROOT / "refs/conformance/olmdirectionalblur_direct_writer_actual_aex_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmdirectionalblur_direct_writer_actual_aex_20260716.md"
PARAM_SIZE = 0x8200
SENTINEL = bytes.fromhex("aabbccdd")

STATIC_EXPECTED = (
    "movq\t0x8090(%rcx), %r9",
    "movss\t0x28(%rcx), %xmm5",
    "imull\t0x80a0(%rcx), %eax",
    "addl\t0x809c(%rcx), %eax",
    "addl\t%edx, %eax",
    "shll\t$0x2, %eax",
    "minss\t%xmm0, %xmm5",
    "movss\t0xc(%r9,%rcx,4), %xmm3",
    "cvttss2si\t%xmm5, %eax",
    "cvttss2si\t%xmm3, %eax",
    "movb\t%al, 0x1(%rcx)",
    "movb\t%al, 0x3(%rcx)",
    "movb\t%al, 0x2(%rcx)",
    "movb\t%al, (%rcx)",
)

CASES = (
    {
        "id": "rgb_half_tie_truncation",
        "description": "0.5-byte boundaries truncate via CVTTSS2SI instead of rounding up.",
        "target_xy": [0, 0],
        "row0": 0,
        "col0": 0,
        "stride": 4,
        "gain": 1.0,
        "pixels": {
            (0, 0): (0.5, 0.5, 0.5, 171.0 / 255.0),
        },
        "expects": {
            "rgb_half_tie": True,
            "rgb_upper_clamp": False,
            "alpha_ungained": False,
            "biased_indexing": False,
            "complete_overwrite": True,
        },
    },
    {
        "id": "rgb_clamp_alpha_unclamped_store",
        "description": "RGB clamps after gain while alpha remains ungained and unclamped before byte store.",
        "target_xy": [0, 0],
        "row0": 0,
        "col0": 0,
        "stride": 4,
        "gain": 2.0,
        "pixels": {
            (0, 0): (0.75, 0.3, 0.9, 1.25),
        },
        "expects": {
            "rgb_half_tie": False,
            "rgb_upper_clamp": True,
            "alpha_ungained": True,
            "biased_indexing": False,
            "complete_overwrite": True,
        },
    },
    {
        "id": "biased_index_complete_overwrite",
        "description": "Non-zero row and column bias select the intended source cell and overwrite all four bytes.",
        "target_xy": [2, 4],
        "row0": 3,
        "col0": 5,
        "stride": 11,
        "gain": 1.0,
        "pixels": {
            (2, 4): (0.5, 1.0, 0.0, 0.25),
            (0, 0): (1.0, 0.0, 0.0, 1.0),
            (2, 3): (0.0, 1.0, 0.0, 1.0),
            (1, 4): (0.0, 0.0, 1.0, 1.0),
        },
        "expects": {
            "rgb_half_tie": False,
            "rgb_upper_clamp": False,
            "alpha_ungained": False,
            "biased_indexing": True,
            "complete_overwrite": True,
        },
    },
)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def f32_mul(left: float, right: float) -> float:
    return f32(f32(left) * f32(right))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guest_index(row0: int, col0: int, stride: int, x: int, y: int) -> int:
    return ((row0 + y) * stride + col0 + x)


def build_work_buffer(case: dict[str, object]) -> bytes:
    row0 = int(case["row0"])
    col0 = int(case["col0"])
    stride = int(case["stride"])
    pixels = case["pixels"]
    max_index = max(guest_index(row0, col0, stride, x, y) for x, y in pixels) + 1
    blob = bytearray(max_index * 16)
    for (x, y), rgba in pixels.items():
        offset = guest_index(row0, col0, stride, x, y) * 16
        blob[offset:offset + 16] = struct.pack("<4f", *(f32(value) for value in rgba))
    return bytes(blob)


def exact_output_argb(case: dict[str, object]) -> list[int]:
    x, y = case["target_xy"]
    rgba = case["pixels"][(x, y)]
    gain = f32(case["gain"])
    one = f32(1.0)
    channel_max = f32(255.0)
    rgb = []
    for component in rgba[:3]:
        gained = f32_mul(component, gain)
        clamped = min(gained, one)
        scaled = f32_mul(clamped, channel_max)
        rgb.append(int(scaled) & 0xFF)
    alpha_scaled = f32_mul(rgba[3], channel_max)
    alpha = int(alpha_scaled) & 0xFF
    return [alpha, *rgb]


def disassemble_writer() -> dict[str, object]:
    command = [
        "objdump",
        "-d",
        f"--start-address=0x{ENTRY:x}",
        f"--stop-address=0x{DISASM_STOP:x}",
        str(AEX),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    lines = [line.rstrip() for line in result.stdout.splitlines() if line.strip().startswith("180006b")]
    missing = [snippet for snippet in STATIC_EXPECTED if not any(snippet in line for line in lines)]
    if missing:
        raise AssertionError(f"writer disassembly drifted: missing {missing}")
    return {
        "command": f"objdump -d --start-address=0x{ENTRY:x} --stop-address=0x{DISASM_STOP:x} plugins_2025/OLMDirectionalBlur.aex",
        "matched_lines": list(STATIC_EXPECTED),
        "missing_lines": missing,
    }


def run_case(case: dict[str, object]) -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    params = loader.host_alloc(PARAM_SIZE)
    work = loader.host_alloc(len(build_work_buffer(case)))
    output = loader.host_alloc(4)
    payload = build_work_buffer(case)
    row0 = int(case["row0"])
    col0 = int(case["col0"])
    stride = int(case["stride"])
    target_x, target_y = case["target_xy"]

    loader.write_bytes(params, b"\x00" * PARAM_SIZE)
    loader.write_bytes(work, payload)
    loader.write_bytes(output, SENTINEL)
    loader.write_bytes(params + 0x28, struct.pack("<f", f32(case["gain"])))
    loader.write_bytes(params + 0x8090, struct.pack("<Q", work))
    loader.write_bytes(params + 0x8098, struct.pack("<I", row0))
    loader.write_bytes(params + 0x809C, struct.pack("<I", col0))
    loader.write_bytes(params + 0x80A0, struct.pack("<I", stride))

    result = loader.call_function(
        ENTRY,
        int_args=[params, target_x, target_y, 0, output],
        max_instructions=1000,
    )
    observed = list(loader.read_bytes(output, 4))
    expected = exact_output_argb(case)
    target_offset = guest_index(row0, col0, stride, target_x, target_y) * 16
    target_rgba = list(struct.unpack("<4f", payload[target_offset:target_offset + 16]))

    decoys = []
    if case["expects"]["biased_indexing"]:
        for other_xy, rgba in case["pixels"].items():
            if list(other_xy) == case["target_xy"]:
                continue
            decoys.append({"xy": list(other_xy), "rgba": list(rgba), "expected_argb": exact_output_argb({
                **case,
                "target_xy": list(other_xy),
            })})

    return {
        "id": case["id"],
        "description": case["description"],
        "target_xy": case["target_xy"],
        "bias": {"row0": row0, "col0": col0, "stride": stride},
        "gain": f32(case["gain"]),
        "target_guest_pixel_index": guest_index(row0, col0, stride, target_x, target_y),
        "target_guest_byte_offset": target_offset,
        "target_rgba_f32": target_rgba,
        "expected_argb8": expected,
        "observed_argb8": observed,
        "matches_expected": observed == expected,
        "all_four_bytes_overwritten": loader.read_bytes(output, 4) != SENTINEL and all(
            loader.read_bytes(output, 4)[i] != SENTINEL[i] for i in range(4)
        ),
        "instructions": result["instructions"],
        "coverage": case["expects"],
        "decoy_pixels": decoys,
    }


def markdown(report: dict[str, object]) -> str:
    lines = [
        "# OLMDirectionalBlur direct-writer actual-AEX regression",
        "",
        f"- Status: `{report['status']}`",
        f"- Binary: `plugins_2025/OLMDirectionalBlur.aex` (`{report['binary_sha256']}`)",
        f"- Entry: `0x{ENTRY:x}`",
        "- Scope: isolated 8bpc output callback semantics only; not AE exact.",
        "",
        "## Static FACT",
        "",
        "- `objdump` of the real binary matches the expected `0x180006b30..0x180006bc9` writer body.",
        "- The callback reads `params+0x8090`, `params+0x28`, `params+0x8098`, `params+0x809c`, and `params+0x80a0`.",
        "- RGB channels hit `MINSS` before `*255` and `CVTTSS2SI`; alpha skips `MINSS` and is stored with `MOVB` too.",
        "- The store order is `A/R/G/B` at byte offsets `+0/+1/+2/+3`.",
        "",
        "### Exact static lines",
        "",
    ]
    for line in report["static"]["matched_lines"]:
        lines.append(f"- `{line}`")
    lines.extend([
        "",
        "## Actual-AEX FACT",
        "",
    ])
    for case in report["cases"]:
        lines.append(
            f"- `{case['id']}`: observed `{case['observed_argb8']}` from target RGBA `{case['target_rgba_f32']}` "
            f"at biased index `{case['target_guest_pixel_index']}` after `{case['instructions']}` instructions."
        )
    lines.extend([
        "",
        "## Coverage",
        "",
        "- `rgb_half_tie_truncation`: `0.5 * 255 = 127.5` stores `127`, proving truncation.",
        "- `rgb_clamp_alpha_unclamped_store`: RGB above `1.0` clamps to `255`, while alpha `1.25` stores the low byte of `318` (`62`) because it is not RGB-gained or clamped first.",
        "- `biased_index_complete_overwrite`: non-zero `row0=3`, `col0=5`, `stride=11` selects the intended source cell and overwrites all four destination bytes.",
        "",
        "## Remaining Windows Same-Run Blocker",
        "",
        "- This harness proves the isolated callback rule only. The remaining missing same-run Windows fact is a live writer-entry capture at `OLMDirectionalBlur+0x6b30` on the real residual lane, so we can prove which RGBA floats the full render passes into the callback before the byte stores.",
        "- Until that same-run writer-entry witness exists, this direct-writer pass does not close the full-render row-755 / host-column-1308 residual lane and does not justify any production change.",
        "",
        "Reproduction: `python3 tools/emulation/test_dblur_direct_writer_actual_aex_20260716.py`",
        "",
    ])
    return "\n".join(lines)


def run() -> dict[str, object]:
    static = disassemble_writer()
    cases = [run_case(case) for case in CASES]
    if not all(case["matches_expected"] for case in cases):
        raise AssertionError("actual-AEX writer output drifted from the modeled contract")
    if not all(case["all_four_bytes_overwritten"] for case in cases):
        raise AssertionError("writer did not overwrite all four output bytes")
    report = {
        "schema": 1,
        "kind": "olmdirectionalblur_direct_writer_actual_aex_regression",
        "date": "2026-07-16",
        "status": "pass_actual_aex_writer_contract",
        "scope": "isolated actual-AEX 8bpc output callback only; not AE exact",
        "binary": str(AEX.relative_to(ROOT)),
        "binary_sha256": sha256(AEX),
        "entry": hex(ENTRY),
        "static": static,
        "cases": cases,
        "remaining_windows_same_run_blocker": {
            "status": "open",
            "required_live_site": "OLMDirectionalBlur+0x6b30",
            "missing_fact": "same-run live writer-entry RGBA floats for the real residual lane",
            "why_it_matters": "the microfixture proves callback semantics but not the full-render values that reach the callback",
            "current_lane": "row-755 / host-column-1308 residual family remains upstream-boundary blocked",
        },
        "production_changed": False,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(markdown(report), encoding="utf-8")
    return report


def main() -> int:
    report = run()
    print(json.dumps({
        "status": report["status"],
        "report_json": str(REPORT_JSON),
        "report_md": str(REPORT_MD),
        "cases": {case["id"]: case["observed_argb8"] for case in report["cases"]},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
