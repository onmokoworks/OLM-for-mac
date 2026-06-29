#!/usr/bin/env python3
"""Compare the current Mac OLMBlur writer contract against Windows 16bpc asm facts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAC_SOURCE = ROOT / "mac" / "OLMBlur" / "OLMBlur.cpp"
DEFAULT_ASM_AUDIT = ROOT / "refs" / "conformance" / "olmblur_16bpc_asm_writer_audit_20260629.json"
DEFAULT_WORD_AUDIT = ROOT / "refs" / "conformance" / "olmblur_16bpc_word_delta_audit_20260628.json"
DEFAULT_JSON = ROOT / "refs" / "conformance" / "olmblur_16bpc_writer_contract_audit_20260629.json"
DEFAULT_MD = ROOT / "refs" / "conformance" / "olmblur_16bpc_writer_contract_audit_20260629.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mac-source", type=Path, default=DEFAULT_MAC_SOURCE)
    parser.add_argument("--asm-audit-json", type=Path, default=DEFAULT_ASM_AUDIT)
    parser.add_argument("--word-audit-json", type=Path, default=DEFAULT_WORD_AUDIT)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--summary-md", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_mac_writer(source_text: str) -> dict[str, Any]:
    round_match = re.search(
        r"static inline float round_blur_value\(float v, A_long legacy\)\s*\{\s*return legacy \? ([^:;]+) : ([^;]+);\s*\}",
        source_text,
        re.S,
    )
    if not round_match:
        raise RuntimeError("could not parse round_blur_value from mac source")
    legacy_expr = " ".join(round_match.group(1).split())
    nonlegacy_expr = " ".join(round_match.group(2).split())

    store16_match = re.search(
        r"static void store16\(.*?\)\s*\{(?P<body>.*?)\n\}",
        source_text,
        re.S,
    )
    if not store16_match:
        raise RuntimeError("could not parse store16 from mac source")
    body = store16_match.group("body")

    return {
        "legacy_round_expr": legacy_expr,
        "nonlegacy_round_expr": nonlegacy_expr,
        "clamps_to_32768": "if (r > 32768) r = 32768;" in body
        and "if (g > 32768) g = 32768;" in body
        and "if (b > 32768) b = 32768;" in body,
        "casts_to_u_short": "row[x].red   = (u_short)r;" in body
        and "row[x].green = (u_short)g;" in body
        and "row[x].blue  = (u_short)b;" in body,
        "uses_round_blur_value_for_store16": body.count("round_blur_value(") >= 3,
    }


def summarize(payload_mac: dict[str, Any], asm_payload: dict[str, Any], word_payload: dict[str, Any]) -> dict[str, Any]:
    windows = {row["name"]: row for row in asm_payload.get("windows", [])}
    standard = windows["standard_16bpc_word_writer"]
    alternate = windows["alternate_16bpc_direct_word_writer"]
    case_rows = {row["case_id"]: row for row in word_payload.get("cases", [])}
    nonlegacy_cases = [case_rows[f"case_{i:04d}"] for i in range(1, 7)]
    sign_mixed_cases = sum(1 for row in nonlegacy_cases if row.get("classification") == "sign-mixed-one-word")

    return {
        "kind": "olmblur_16bpc_writer_contract_audit",
        "date": "2026-06-29",
        "mac_source_writer": payload_mac,
        "windows_standard_writer": {
            "classification": standard["classification"],
            "loads_rounding_constant_0_5": standard["loads_rounding_constant_0_5"],
            "adds_rounding_constant": standard["adds_rounding_constant"],
            "calls_clamp_helper_18000ccb4": standard["calls_clamp_helper_18000ccb4"],
            "cvttss2si_from_xmm0": standard["cvttss2si_from_xmm0"],
            "word_stores": standard["word_stores"],
        },
        "windows_alternate_writer": {
            "classification": alternate["classification"],
            "cvttss2si_from_memory": alternate["cvttss2si_from_memory"],
            "word_stores": alternate["word_stores"],
        },
        "mac_vs_windows_standard": {
            "nonlegacy_rounding_expression_matches_standard_16bpc": payload_mac["nonlegacy_round_expr"] == "floorf(v + 0.5f)",
            "legacy_rounding_expression_matches_windows_add_half_family": payload_mac["legacy_round_expr"] == "floorf(v + 0.5f)",
            "nonlegacy_source_is_nearbyintf": "nearbyintf" in payload_mac["nonlegacy_round_expr"],
            "windows_standard_is_add_half_then_truncate": standard["classification"] == "round-add-helper-truncate-word-store",
        },
        "residual_context": {
            "nonlegacy_sign_mixed_one_word_cases": sign_mixed_cases,
            "nonlegacy_total_cases": len(nonlegacy_cases),
            "legacy_case_0007_classification": case_rows["case_0007"]["classification"],
        },
        "decision": "source-writer-mismatch-real-but-not-yet-sufficient-for-global-swap",
        "conclusion": [
            "The current Mac source uses `nearbyintf(v)` for non-legacy 16bpc store16, while Windows standard 16bpc asm is `+0.5 -> helper -> CVTTSS2SI -> word store`.",
            "This is a real source-vs-asm contract mismatch at the writer boundary.",
            "But the current 16bpc residual family is sign-mixed one-word across all non-legacy cases, so the evidence still does not support a blind global `nearbyintf -> floorf(v + 0.5f)` swap without proving pre-writeback/helper state.",
            "Legacy already matches the add-half family in source, so `case_0007` remains a separate border/seed/all-same investigation rather than proof for the non-legacy store path.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    mac = payload["mac_source_writer"]
    std = payload["windows_standard_writer"]
    alt = payload["windows_alternate_writer"]
    cmpv = payload["mac_vs_windows_standard"]
    ctx = payload["residual_context"]
    lines = [
        "# OLMBlur 16bpc Writer Contract Audit - 2026-06-29",
        "",
        "## Summary",
        "",
        "- Current Mac source non-legacy store16 path: "
        f"`{mac['nonlegacy_round_expr']}` then clamp `0..32768` then cast to `u_short`.",
        "- Current Mac source legacy store16 path: "
        f"`{mac['legacy_round_expr']}` then clamp `0..32768` then cast to `u_short`.",
        "- Windows standard 16bpc writer asm: "
        f"`{std['classification']}`.",
        "- Windows alternate 16bpc writer asm: "
        f"`{alt['classification']}`.",
        "",
        "## Contract Comparison",
        "",
        "| Question | Result |",
        "| --- | --- |",
        f"| Mac non-legacy source uses `nearbyintf` | `{cmpv['nonlegacy_source_is_nearbyintf']}` |",
        f"| Windows standard writer is add-half then truncate | `{cmpv['windows_standard_is_add_half_then_truncate']}` |",
        f"| Mac non-legacy source exactly matches Windows standard 16bpc rounding expression | `{cmpv['nonlegacy_rounding_expression_matches_standard_16bpc']}` |",
        f"| Mac legacy source matches Windows add-half family | `{cmpv['legacy_rounding_expression_matches_windows_add_half_family']}` |",
        "",
        "## Residual Context",
        "",
        f"- Non-legacy sign-mixed one-word cases: `{ctx['nonlegacy_sign_mixed_one_word_cases']}/{ctx['nonlegacy_total_cases']}`.",
        f"- Legacy `case_0007` classification: `{ctx['legacy_case_0007_classification']}`.",
        "",
        "## Decision",
        "",
        f"- `{payload['decision']}`",
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["conclusion"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    mac_payload = parse_mac_writer(read_text(args.mac_source))
    asm_payload = read_json(args.asm_audit_json)
    word_payload = read_json(args.word_audit_json)
    payload = summarize(mac_payload, asm_payload, word_payload)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.summary_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"summary_json={args.summary_json}")
    print(f"summary_md={args.summary_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
