#!/usr/bin/env python3
"""Bound the OLMSmoother2 case_0004 float-to-PF8 boundary on Mac.

This uses the checked-in actual AEX typed worker only.  It does not modify the
plug-in or claim that a Windows writer-frame tuple is the true worker input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))
import test_olmsmoother2_typed_writeback_20260717 as typed  # noqa: E402

REPORT_JSON = ROOT / "refs/conformance/olmsmoother2_case0004_writeback_rule_20260718.json"
REPORT_MD = ROOT / "refs/conformance/olmsmoother2_case0004_writeback_rule_20260718.md"
EXPECTED_AEX_SHA256 = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"

CASE4_FRAME = (0.80824906, 0.80824906, 0.80824906, 0.44156867)
CASE4_EXPECTED_MEMORY = bytes.fromhex("71e8e8e8")
CASE12_FRAME = (1.0, 1.0, 1.0, 0.0)
CASE12_EXPECTED_MEMORY = bytes.fromhex("00ffffff")


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', f32(value)))[0]:08x}"


def quantize(value: float) -> int:
    return max(0, min(255, int(f32(f32(value * 255.0) + 0.5))))


def run_frame(frame: tuple[float, float, float, float]) -> dict[str, Any]:
    typed.SRC = frame
    observed = typed.run_depth("PF8")
    return {
        "input_rgba_f32": list(frame),
        "input_rgba_f32_bits": [bits(value) for value in frame],
        "aex_memory_hex": observed["actual_raw_hex"],
        "aex_argb_hex": bytes.fromhex(observed["actual_raw_hex"])[::-1].hex(),
        "dynamic_ranges": observed["dynamic_ranges"],
        "dynamic_next_calls": observed["dynamic_next_calls"],
    }


def expected_memory(frame: tuple[float, float, float, float]) -> bytes:
    alpha, red, green, blue = frame[3], frame[0], frame[1], frame[2]
    return bytes((quantize(alpha), quantize(red), quantize(green), quantize(blue)))


def candidate_frames() -> dict[str, tuple[float, float, float, float]]:
    alpha = CASE4_FRAME[3]
    rgb = CASE4_FRAME[:3]
    return {
        "straight": CASE4_FRAME,
        "premultiplied_rgb": tuple((*[f32(value * alpha) for value in rgb], alpha)),
        "unpremultiplied_rgb_clamped": tuple((*[min(1.0, f32(value / alpha)) for value in rgb], alpha)),
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# OLMSmoother2 case_0004 float-to-packed boundary - 2026-07-18",
        "",
        "## Verdict",
        "",
        f"`{report['verdict']}`",
        "",
        "The Mac-local actual-AEX PF8 worker has a bounded typed-store rule, but the retained case_0004 Windows writer-frame tuple does not explain the retained PF8 bytes under straight, premultiplied, or unpremultiplied RGB interpretations.",
        "",
        "## FACT",
        "",
        f"- AEX SHA-256: `{report['aex_sha256']}`.",
        "- The actual PF8 worker emits A,R,G,B bytes using float32 `value * 255 + 0.5`, truncation, and clamp to `0..255`.",
        f"- Case_0004 retained frame `{CASE4_FRAME}` emits memory bytes `{report['straight_case']['aex_memory_hex']}`.",
        f"- The retained case_0004 Windows PF8 record is memory bytes `{CASE4_EXPECTED_MEMORY.hex()}` (`0xe8e8e871` as the logged little-endian integer).",
        f"- Case_0012 retained frame emits `{report['case0012']['aex_memory_hex']}`, matching its retained Windows record `{CASE12_EXPECTED_MEMORY.hex()}`.",
        "",
        "## BOUNDED RESULT",
        "",
        "| Interpretation of case_0004 frame | Actual-AEX memory | Expected memory |",
        "| --- | --- | --- |",
    ]
    for name, row in report["candidate_replays"].items():
        lines.append(f"| `{name}` | `{row['aex_memory_hex']}` | `{CASE4_EXPECTED_MEMORY.hex()}` |")
    lines += [
        "",
        f"To emit the expected RGB byte `232`, the actual worker input must lie in `{report['required_writer_input']['rgb_interval']}` per channel. The expected alpha byte `113` requires `{report['required_writer_input']['alpha_interval']}`.",
        "",
        "## NEXT MISSING WITNESS",
        "",
        "A same-run writer-entry float4 witness is required: bind the exact case_0004 render identity and capture the four float32 bit patterns immediately at the typed PF8 worker input, alongside the final raw bytes. A post-cce0 tuple that is not the worker input cannot close this boundary.",
        "",
        "No production source was changed and no global writeback rule was inferred from PNGs.",
        "",
        "## Reproduction",
        "",
        "```sh",
        "python3 tools/emulation/audit_olmsmoother2_case0004_writeback_rule_20260718.py",
        "python3 tools/emulation/test_olmsmoother2_case0004_writeback_rule_20260718.py",
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, default=REPORT_JSON)
    parser.add_argument("--output-md", type=Path, default=REPORT_MD)
    args = parser.parse_args()
    actual_hash = hashlib.sha256(typed.AEX_PATH.read_bytes()).hexdigest()
    if actual_hash != EXPECTED_AEX_SHA256:
        raise RuntimeError("FAIL CLOSED: AEX hash drift")

    straight = run_frame(CASE4_FRAME)
    case12 = run_frame(CASE12_FRAME)
    expected = expected_memory(CASE4_FRAME)
    if bytes.fromhex(straight["aex_memory_hex"]) != expected:
        raise RuntimeError("FAIL CLOSED: straight replay disagrees with independent quantizer")

    candidates = {name: run_frame(frame) for name, frame in candidate_frames().items()}
    rgb_low = f32(231.5 / 255.0)
    rgb_high = f32(232.5 / 255.0)
    alpha_low = f32(112.5 / 255.0)
    alpha_high = f32(113.5 / 255.0)
    report = {
        "verdict": "PASS_BOUNDED_WRITER_RULE_NEXT_SAME_RUN_FLOAT_WITNESS",
        "scope": "Mac-local checked-in actual-AEX PF8 typed worker replay",
        "aex_sha256": actual_hash,
        "worker": "0x180003370",
        "rule": {
            "channel_order": "A,R,G,B memory bytes from RGBA float4",
            "formula": "clamp(trunc(float32(float32(value * 255.0) + 0.5)), 0, 255)",
        },
        "straight_case": straight,
        "case0012": {
            **case12,
            "expected_memory_hex": CASE12_EXPECTED_MEMORY.hex(),
            "matches_retained_windows_record": case12["aex_memory_hex"] == CASE12_EXPECTED_MEMORY.hex(),
        },
        "candidate_replays": candidates,
        "retained_case0004": {
            "windows_writer_frame_rgba_f32": list(CASE4_FRAME),
            "windows_pf8_memory_hex": CASE4_EXPECTED_MEMORY.hex(),
            "straight_replay_matches": straight["aex_memory_hex"] == CASE4_EXPECTED_MEMORY.hex(),
        },
        "required_writer_input": {
            "rgb_interval": f"[{rgb_low!r}, {rgb_high!r})",
            "alpha_interval": f"[{alpha_low!r}, {alpha_high!r})",
            "representative_rgba": [rgb_low, rgb_low, rgb_low, alpha_low],
            "representative_bits": [bits(rgb_low), bits(rgb_low), bits(rgb_low), bits(alpha_low)],
        },
        "next_missing_witness": "same-run case_0004 typed PF8 worker-entry float4 bits bound to final packed raw bytes",
        "claims_not_made": ["Windows live execution", "AE host equivalence", "upstream c280/cce0 producer identity", "global production writeback change"],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render(report) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
