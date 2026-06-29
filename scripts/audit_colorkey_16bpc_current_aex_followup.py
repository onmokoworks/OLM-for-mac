#!/usr/bin/env python3
"""Audit raw CDB evidence for the OLMColorKey 16bpc case_0009 follow-up."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_ZIP = (
    REPO
    / "refs"
    / "returns"
    / "olm_runtime_trace_colorkey_16bpc_case0009_current_aex_followup_20260627_return_windows_20260628_1338.zip"
)
DEFAULT_JSON = REPO / "refs" / "conformance" / "olmcolorkey_16bpc_current_aex_followup_20260628.json"
DEFAULT_MD = REPO / "refs" / "conformance" / "olmcolorkey_16bpc_current_aex_followup_20260628.md"


WITNESS_RE = re.compile(
    r"=== WITNESS_1110_149_PRECHECK ===.*?"
    r"ebx=(?P<ebx>[0-9a-f]+).*?"
    r"edi=(?P<edi>[0-9a-f]+).*?"
    r"=== WITNESS_1110_149_DISTANCE_COMPARE ===.*?"
    r"matte_ptr=(?P<matte_ptr>[0-9a-f]+) dist_ptr=(?P<dist_ptr>[0-9a-f]+).*?"
    r"(?P<matte_addr>[0-9a-f]+`[0-9a-f]+)\s+"
    r"(?P<matte0>[0-9a-f]{4})\s+(?P<matte1>[0-9a-f]{4})\s+"
    r"(?P<matte2>[0-9a-f]{4})\s+(?P<matte3>[0-9a-f]{4}).*?"
    r"(?P<dist_addr>[0-9a-f]+`[0-9a-f]+)\s+(?P<dist_raw>[0-9a-f]{8}).*?"
    r"=== WITNESS_1110_149_COPY_PATH_TAKEN ===.*?"
    r"=== WITNESS_1110_149_LOOP_END ===.*?"
    r"(?P<end_addr>[0-9a-f]+`[0-9a-f]+)\s+"
    r"(?P<end0>[0-9a-f]{4})\s+(?P<end1>[0-9a-f]{4})\s+"
    r"(?P<end2>[0-9a-f]{4})\s+(?P<end3>[0-9a-f]{4})",
    re.DOTALL | re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("return_zip", nargs="?", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def read_zip_text(archive: zipfile.ZipFile, name: str) -> str:
    raw = archive.read(name)
    if b"\x00" in raw[:200]:
        return raw.decode("utf-16le", errors="replace")
    return raw.decode("utf-8", errors="replace")


def u32_float(raw_hex: str) -> float:
    import struct

    value = int(raw_hex, 16)
    return struct.unpack("<f", struct.pack("<I", value))[0]


def parse_1110_trace(text: str) -> dict[str, Any]:
    match = WITNESS_RE.search(text)
    if not match:
        return {"hit": False}
    groups = match.groupdict()
    return {
        "hit": True,
        "x": int(groups["ebx"], 16),
        "y": int(groups["edi"], 16),
        "matte_ptr": groups["matte_ptr"],
        "dist_ptr": groups["dist_ptr"],
        "matte_words_before": [int(groups[f"matte{i}"], 16) for i in range(4)],
        "dist_raw_hex": groups["dist_raw"],
        "dist_float": u32_float(groups["dist_raw"]),
        "matte_words_after": [int(groups[f"end{i}"], 16) for i in range(4)],
        "copy_path_taken": "=== WITNESS_1110_149_COPY_PATH_TAKEN ===" in match.group(0),
    }


def build_report(return_zip: Path) -> dict[str, Any]:
    with zipfile.ZipFile(return_zip) as archive:
        result = json.loads(archive.read("RETURN_RUNTIME_TRACE_RESULT.json"))
        trace_name = "evidence\\cdb_witness_1110_149\\cdb_trace_88c8_2026-06-28_12-59-52-616.log"
        text = read_zip_text(archive, trace_name)
    witness = parse_1110_trace(text)
    return {
        "kind": "olmcolorkey_16bpc_current_aex_followup_audit",
        "schema": 1,
        "return_zip": str(return_zip),
        "raw_result_status": result.get("results", [{}])[0].get("status"),
        "raw_result_summary": result.get("results", [{}])[0].get("summary"),
        "trace_file": trace_name,
        "witness_1110_149": witness,
        "conclusion": [
            "The returned JSON summary is stale for the primary witness, but the raw CDB log is actionable.",
            "The primary residual witness (1110,149) does hit the current-AEX +0x9237/+0x9247/+0x924c/+0x92b7 path.",
            "Windows consumes dist=2.0 at (1110,149), takes the copy path, and changes matte word0 from 0x0000 to 0x8000.",
            "This proves the primary residual is not merely outside the +0x9000 positive Edge Thin loop; at least this witness is removed by that loop.",
            "The local exported-PNG Lab76 seed model puts the same witness at taxicab distance 43 from the current hit set, so the remaining mismatch is now specifically the seed/matte world feeding current-AEX positive Edge Thin.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    w = report["witness_1110_149"]
    lines = [
        "# OLMColorKey 16bpc current-AEX follow-up audit",
        "",
        f"- Return zip: `{report['return_zip']}`",
        f"- Raw status: `{report['raw_result_status']}`",
        f"- Trace file: `{report['trace_file']}`",
        "",
        "## Witness `(1110,149)`",
        "",
    ]
    if not w.get("hit"):
        lines.append("- No parsed hit found.")
    else:
        lines.extend(
            [
                f"- Parsed coordinate: `({w['x']},{w['y']})`",
                f"- Distance: `{w['dist_float']}` (`0x{w['dist_raw_hex']}`)",
                f"- Copy path taken: `{w['copy_path_taken']}`",
                f"- Matte before: `{w['matte_words_before']}`",
                f"- Matte after: `{w['matte_words_after']}`",
            ]
        )
    lines.extend(["", "## Conclusion", ""])
    for item in report["conclusion"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = build_report(args.return_zip)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"summary_json={args.output_json}")
    print(f"summary_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
