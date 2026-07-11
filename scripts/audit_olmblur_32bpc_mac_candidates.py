#!/usr/bin/env python3
"""Materialize a fail-closed OLMBlur 32bpc Mac/Windows EXR audit report.

The report compares exact FLOAT RGBA semantic planes.  There is deliberately
no tolerance, epsilon, or numeric normalization in this audit.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_float_exr import read_planes  # noqa: E402
from verify_32bpc_float_return import VerificationError  # noqa: E402


CHANNELS = ("A", "B", "G", "R")
CASE_TOKENS = ("id", "source_case_id")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def case_tokens(case: dict[str, Any]) -> set[str]:
    tokens = {str(case[key]) for key in CASE_TOKENS if case.get(key)}
    tokens.update({token.replace("__", "_") for token in list(tokens)})
    return tokens


def find_artifact(root: Path, case: dict[str, Any], no_op: bool) -> Path:
    if not root.is_dir():
        raise VerificationError(f"artifact root does not exist or is not a directory: {root}")
    tokens = case_tokens(case)
    suffixes = ("_before_effects", "_no_op", "_noop") if no_op else ("_effect", "_effects")
    matches = []
    for path in sorted(root.rglob("*.exr")):
        stem = path.stem.lower()
        token_match = any(token.lower() in stem for token in tokens)
        if no_op:
            kind_match = any(stem.endswith(suffix) for suffix in suffixes)
        else:
            kind_match = not any(stem.endswith(suffix) for suffix in ("_before_effects", "_no_op", "_noop"))
        if token_match and kind_match:
            matches.append(path)
    if len(matches) != 1:
        label = "no-op" if no_op else "effect"
        raise VerificationError(f"{root}: expected exactly one {label} EXR for {sorted(tokens)!r}, found {len(matches)}")
    return matches[0]


def provenance_hash(root: Path) -> str | None:
    """Read only explicit AEX hash fields from JSON provenance sidecars."""
    keys = {"aex_sha256", "plugin_aex_sha256", "plugin_binary_sha256", "binary_sha256"}
    for path in sorted(root.rglob("*.json")):
        try:
            value = load_json(path)
        except (OSError, ValueError):
            continue
        stack = [value]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                for key, candidate in item.items():
                    if key.lower() in keys and isinstance(candidate, str) and len(candidate) == 64:
                        return candidate.lower()
                    stack.append(candidate)
            elif isinstance(item, list):
                stack.extend(item)
    return None


def inspect(path: Path) -> tuple[dict[str, bytes], int, int]:
    planes, width, height = read_planes(path)
    return planes, width, height


def compare(left: Path, right: Path) -> dict[str, Any]:
    left_planes, left_w, left_h = inspect(left)
    right_planes, right_w, right_h = inspect(right)
    dimensions_match = (left_w, left_h) == (right_w, right_h)
    counts: dict[str, int] = {}
    max_delta: dict[str, int] = {}
    if dimensions_match:
        for channel in CHANNELS:
            count = 0
            delta = 0
            for offset in range(0, len(left_planes[channel]), 4):
                a = left_planes[channel][offset:offset + 4]
                b = right_planes[channel][offset:offset + 4]
                if a != b:
                    count += 1
                    delta = max(delta, abs(int.from_bytes(a, "little") - int.from_bytes(b, "little")))
            counts[channel] = count
            max_delta[channel] = delta
    else:
        counts = {channel: None for channel in CHANNELS}  # type: ignore[assignment]
        max_delta = {channel: None for channel in CHANNELS}  # type: ignore[assignment]
    return {
        "match": dimensions_match and all(value == 0 for value in counts.values()),
        "dimensions": {"reference": [left_w, left_h], "candidate": [right_w, right_h], "match": dimensions_match},
        "mismatched_values_by_channel": counts,
        "max_raw_u32_delta_by_channel": max_delta,
        "alpha_mismatch": counts["A"],
    }


def audit(spec_path: Path, windows_root: Path, mac_effect_root: Path, mac_noop_root: Path) -> dict[str, Any]:
    spec = load_json(spec_path)
    if spec.get("scope", {}).get("bit_depth") != "32bpc" or spec.get("effect", {}).get("match_name") != "OLM OLM Blur":
        raise VerificationError("focused spec is not the OLMBlur 32bpc spec")
    cases = spec.get("cases")
    if not isinstance(cases, list) or not cases:
        raise VerificationError("focused spec has no cases")
    windows_aex_hash = provenance_hash(windows_root)
    mac_aex_hash = provenance_hash(mac_effect_root)
    mac_noop_hash = provenance_hash(mac_noop_root)
    rows = []
    for case in cases:
        case_id = case.get("id")
        if not isinstance(case_id, str):
            raise VerificationError("every focused-spec case must have a string id")
        win_effect = find_artifact(windows_root, case, False)
        win_noop = find_artifact(windows_root, case, True)
        mac_effect = find_artifact(mac_effect_root, case, False)
        mac_noop = find_artifact(mac_noop_root, case, True)
        noop = compare(win_noop, mac_noop)
        effect = compare(win_effect, mac_effect)
        rows.append({
            "case_id": case_id,
            "windows": {"effect": str(win_effect), "no_op": str(win_noop)},
            "mac": {"effect": str(mac_effect), "no_op": str(mac_noop)},
            "no_op": noop,
            "effect": effect,
            "effect_attributable": noop["match"],
        })
    no_op_exact = all(row["no_op"]["match"] for row in rows)
    effect_exact = all(row["effect"]["match"] for row in rows)
    provenance_exact = bool(windows_aex_hash and mac_aex_hash and mac_noop_hash)
    ae_exact = no_op_exact and effect_exact and provenance_exact
    return {
        "schema": "olmblur_32bpc_mac_candidate_audit.v1",
        "focused_spec": str(spec_path),
        "plugin": "OLMBlur",
        "bit_depth": "32bpc",
        "comparison": {"mode": "exact_float_semantic_planes", "tolerance": None, "tolerance_used": False},
        "provenance": {
            "windows_aex_sha256": windows_aex_hash,
            "mac_effect_aex_sha256": mac_aex_hash,
            "mac_no_op_aex_sha256": mac_noop_hash,
            "aex_hashes_present": provenance_exact,
        },
        "gates": {
            "no_op_exact": no_op_exact,
            "effect_exact": effect_exact,
            "aex_hashes_present": provenance_exact,
            "ae_exact": ae_exact,
            "ae_exact_refused": not ae_exact,
            "refusal_reasons": [
                reason for reason, failed in (
                    ("no-op mismatch", not no_op_exact),
                    ("effect mismatch", not effect_exact),
                    ("AEX hash missing from provenance", not provenance_exact),
                ) if failed
            ],
        },
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--focused-spec", required=True, type=Path)
    parser.add_argument("--windows-reference-dir", required=True, type=Path)
    parser.add_argument("--mac-effect-result-root", required=True, type=Path)
    parser.add_argument("--mac-no-op-result-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="JSON report path; a Markdown sibling is also written")
    args = parser.parse_args()
    try:
        report = audit(args.focused_spec, args.windows_reference_dir, args.mac_effect_result_root, args.mac_no_op_result_root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        md = args.output.with_suffix(".md")
        lines = ["# OLMBlur 32bpc Mac candidate audit", "", f"Verdict: `{('AE exact' if report['gates']['ae_exact'] else 'AE exact refused')}`", "", "| case | no-op | effect | alpha effect mismatches |", "|---|---:|---:|---:|"]
        for row in report["cases"]:
            lines.append(f"| `{row['case_id']}` | {row['no_op']['match']} | {row['effect']['match']} | {row['effect']['alpha_mismatch']} |")
        lines.extend(["", "Refusal reasons: " + (", ".join(report["gates"]["refusal_reasons"]) or "none") + ".", ""])
        md.write_text("\n".join(lines), encoding="utf-8")
        print(f"[OK] wrote {args.output}")
        print(f"[OK] wrote {md}")
        return 0 if report["gates"]["ae_exact"] else 1
    except (OSError, ValueError, KeyError, VerificationError) as exc:
        print(f"[FAIL] {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
