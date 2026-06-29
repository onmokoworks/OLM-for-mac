#!/usr/bin/env python3
"""Extract OLMBlur writer facts from the Windows AEX disassembly."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DISASM = ROOT / "disasm" / "OLMBlur.aex.asm.txt"
DEFAULT_JSON = ROOT / "refs" / "conformance" / "olmblur_16bpc_asm_writer_audit_20260629.json"
DEFAULT_MD = ROOT / "refs" / "conformance" / "olmblur_16bpc_asm_writer_audit_20260629.md"


WINDOWS = {
    "standard_16bpc_word_writer": ("180002fad", "18000302e"),
    "alternate_16bpc_direct_word_writer": ("1800031d0", "180003256"),
    "legacy_8bpc_byte_writer_family": ("180007f8c", "18000800c"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disasm", type=Path, default=DEFAULT_DISASM)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--summary-md", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def read_lines(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    pattern = re.compile(r"^(?P<addr>[0-9a-fA-F]{9})\s+(?P<text>.*)$")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if not match:
            continue
        rows.append({"addr": match.group("addr").lower(), "text": match.group("text").strip()})
    return rows


def window_rows(rows: list[dict[str, str]], start: str, end: str) -> list[dict[str, str]]:
    start_i = int(start, 16)
    end_i = int(end, 16)
    return [row for row in rows if start_i <= int(row["addr"], 16) <= end_i]


def count_contains(rows: list[dict[str, str]], needle: str) -> int:
    return sum(1 for row in rows if needle in row["text"])


def count_regex(rows: list[dict[str, str]], pattern: str) -> int:
    rx = re.compile(pattern)
    return sum(1 for row in rows if rx.search(row["text"]))


def summarize_window(name: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "name": name,
        "start": rows[0]["addr"] if rows else "",
        "end": rows[-1]["addr"] if rows else "",
        "line_count": len(rows),
        "loads_rounding_constant_0_5": count_contains(rows, "MOVSS XMM6,dword ptr [0x18000d24c]"),
        "adds_rounding_constant": count_contains(rows, "ADDSS XMM0,XMM6"),
        "calls_clamp_helper_18000ccb4": count_contains(rows, "CALL 0x18000ccb4"),
        "cvttss2si_total": count_contains(rows, "CVTTSS2SI"),
        "cvttss2si_from_xmm0": count_contains(rows, "CVTTSS2SI EAX,XMM0"),
        "cvttss2si_from_memory": count_regex(rows, r"CVTTSS2SI EAX,dword ptr"),
        "word_stores": count_regex(rows, r"MOV word ptr"),
        "byte_stores": count_regex(rows, r"MOV byte ptr"),
        "branch_to_direct_writer": count_regex(rows, r"J(GE|S) 0x1800031f9"),
        "excerpt": [f"{row['addr']}  {row['text']}" for row in rows],
    }


def classify(window: dict[str, Any]) -> str:
    if (
        window["word_stores"] >= 3
        and window["loads_rounding_constant_0_5"] >= 1
        and window["adds_rounding_constant"] >= 3
        and window["calls_clamp_helper_18000ccb4"] >= 3
        and window["cvttss2si_from_xmm0"] >= 3
    ):
        return "round-add-helper-truncate-word-store"
    if window["word_stores"] >= 3 and window["cvttss2si_from_memory"] >= 3 and window["adds_rounding_constant"] == 0:
        return "direct-memory-truncate-word-store"
    if (
        window["byte_stores"] >= 3
        and window["loads_rounding_constant_0_5"] >= 1
        and window["adds_rounding_constant"] >= 3
        and window["calls_clamp_helper_18000ccb4"] >= 3
    ):
        return "round-add-helper-truncate-byte-store"
    return "review"


def build_payload(rows: list[dict[str, str]], disasm: Path) -> dict[str, Any]:
    windows = []
    for name, (start, end) in WINDOWS.items():
        summary = summarize_window(name, window_rows(rows, start, end))
        summary["classification"] = classify(summary)
        windows.append(summary)
    return {
        "kind": "olmblur_16bpc_asm_writer_audit",
        "date": "2026-06-29",
        "disasm": str(disasm),
        "windows": windows,
        "conclusion": [
            "The standard 16bpc word writer adds the 0.5 constant, calls helper 0x18000ccb4, truncates with CVTTSS2SI, then stores 16-bit channel words.",
            "The nearby alternate 16bpc word writer branches to a direct memory CVTTSS2SI word-store family, so Legacy/edge witnesses must keep writer family separate from the standard path.",
            "The known 8bpc legacy byte writer at 0x180007fdf is a byte-store analogue of the round-add-helper path and should not be confused with the 16bpc word-store family.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OLMBlur 16bpc ASM Writer Audit - 2026-06-29",
        "",
        "## Summary",
        "",
        "This audit extracts the relevant writer windows from",
        "`disasm/OLMBlur.aex.asm.txt` so the 16bpc residual discussion is tied",
        "to reproducible binary evidence rather than a hand-copied note.",
        "",
        "## Writer Windows",
        "",
        "| Window | Classification | 0.5 loads | ADDSS | helper calls | CVTTSS2SI XMM0 | CVTTSS2SI memory | word stores | byte stores |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["windows"]:
        lines.append(
            f"| `{row['name']}` | `{row['classification']}` | "
            f"{row['loads_rounding_constant_0_5']} | {row['adds_rounding_constant']} | "
            f"{row['calls_clamp_helper_18000ccb4']} | {row['cvttss2si_from_xmm0']} | "
            f"{row['cvttss2si_from_memory']} | {row['word_stores']} | {row['byte_stores']} |"
        )
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {item}" for item in payload["conclusion"])
    lines.extend(["", "## Excerpts", ""])
    for row in payload["windows"]:
        lines.extend([f"### {row['name']}", "", "```asm"])
        lines.extend(row["excerpt"])
        lines.extend(["```", ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    rows = read_lines(args.disasm)
    if not rows:
        raise SystemExit(f"[FAIL] no disassembly rows parsed from {args.disasm}")
    payload = build_payload(rows, args.disasm)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.summary_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"summary_json={args.summary_json}")
    print(f"summary_md={args.summary_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
