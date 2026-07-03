#!/usr/bin/env python3
"""Score whether OLMBlur residual witnesses are explained by writer-only rounding swaps."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE_JSON = ROOT / "refs" / "conformance" / "olmblur_current_word_baseline_20260629.json"
DEFAULT_OUT_JSON = ROOT / "refs" / "conformance" / "olmblur_writer_only_hypothesis_20260630.json"
DEFAULT_OUT_MD = ROOT / "refs" / "conformance" / "olmblur_writer_only_hypothesis_20260630.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-json", type=Path, default=DEFAULT_BASELINE_JSON)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def as_int_list(values: list[Any]) -> list[int]:
    return [int(v) for v in values]


def parse_float_triplet(probe: dict[str, Any], key: str) -> list[float]:
    return [float(v) for v in probe[key]]


def parse_int_triplet(probe: dict[str, Any], key: str) -> list[int]:
    return [int(v) for v in probe[key]]


TRACE_RE = re.compile(
    r"rgb=\((?P<rgb>[^)]*)\).*?floor05=\((?P<floor05>[^)]*)\)\s+nearby=\((?P<nearby>[^)]*)\)"
)


def parse_trace(line: str) -> dict[str, list[float] | list[int]]:
    match = TRACE_RE.search(line)
    if not match:
        raise ValueError(f"unable to parse trace line: {line}")
    rgb = [float(part.strip()) for part in match.group("rgb").split(",")]
    floor05 = [int(part.strip()) for part in match.group("floor05").split(",")]
    nearby = [int(part.strip()) for part in match.group("nearby").split(",")]
    return {"raw": rgb, "floor05": floor05, "nearby": nearby}


def export16(words: list[int]) -> list[int]:
    out: list[int] = []
    for word in words:
        out.append(0 if word <= 0 else word * 2 - 1)
    return out


def abs_sum_delta(a: list[int], b: list[int]) -> int:
    return sum(abs(int(x) - int(y)) for x, y in zip(a, b))


def build_witness(case_id: str, bit_depth: str, sample_row: dict[str, Any]) -> dict[str, Any]:
    reference = as_int_list(sample_row["reference"])
    candidate = as_int_list(sample_row["candidate"])
    source = sample_row.get("probe")
    if source is not None:
        floor05_words = parse_int_triplet(source, "floor05")
        nearby_words = parse_int_triplet(source, "nearby")
        raw = parse_float_triplet(source, "raw")
    else:
        trace = parse_trace(sample_row["trace"])
        floor05_words = [int(v) for v in trace["floor05"]]
        nearby_words = [int(v) for v in trace["nearby"]]
        raw = [float(v) for v in trace["raw"]]

    if bit_depth == "16bpc":
        predicted_floor05 = export16(floor05_words) + [65535]
        predicted_nearby = export16(nearby_words) + [65535]
    elif bit_depth == "8bpc-old-normalized":
        predicted_floor05 = floor05_words + [255]
        predicted_nearby = nearby_words + [255]
    else:
        raise ValueError(f"unsupported bit depth {bit_depth}")

    nearby_error = abs_sum_delta(reference, predicted_nearby)
    floor05_error = abs_sum_delta(reference, predicted_floor05)
    candidate_error = abs_sum_delta(reference, candidate)

    if floor05_error < nearby_error:
        best = "floor05"
    elif nearby_error < floor05_error:
        best = "nearby"
    else:
        best = "tie"

    return {
        "case_id": case_id,
        "bit_depth": bit_depth,
        "xy": [int(sample_row["x"]), int(sample_row["y"])],
        "reference": reference,
        "candidate": candidate,
        "raw": raw,
        "predicted_nearby": predicted_nearby,
        "predicted_floor05": predicted_floor05,
        "candidate_error_l1": candidate_error,
        "nearby_error_l1": nearby_error,
        "floor05_error_l1": floor05_error,
        "best_writer_only_rule": best,
        "writer_only_can_match_reference": nearby_error == 0 or floor05_error == 0,
        "writer_only_diagnosis": diagnose(reference, candidate, predicted_nearby, predicted_floor05, best),
    }


def diagnose(
    reference: list[int],
    candidate: list[int],
    predicted_nearby: list[int],
    predicted_floor05: list[int],
    best: str,
) -> str:
    if predicted_nearby == reference and predicted_floor05 != reference:
        return "nearby-only-match"
    if predicted_floor05 == reference and predicted_nearby != reference:
        return "floor05-only-match"
    if predicted_floor05 == reference and predicted_nearby == reference:
        return "both-writer-rules-match"
    if best == "tie":
        if candidate == predicted_floor05 == predicted_nearby:
            return "writer-rule-irrelevant-at-this-witness"
        return "writer-rule-tie-no-exact-match"
    return "neither-writer-rule-exact"


def build_payload(baseline: dict[str, Any]) -> dict[str, Any]:
    witnesses: list[dict[str, Any]] = []
    for case in baseline.get("cases", []):
        for sample_row in case.get("samples", []):
            witnesses.append(build_witness(case["case_id"], case["bit_depth"], sample_row))

    counts: dict[str, int] = {}
    for row in witnesses:
        key = row["writer_only_diagnosis"]
        counts[key] = counts.get(key, 0) + 1

    return {
        "kind": "olmblur_writer_only_hypothesis",
        "date": "2026-06-30",
        "baseline_json": str(DEFAULT_BASELINE_JSON.relative_to(ROOT)),
        "witnesses": witnesses,
        "diagnosis_counts": counts,
        "decision": "writer-only-swap-cannot-explain-all-active-witnesses",
        "conclusion": [
            "A pure non-Legacy writer swap from nearbyint to floor05 would fix the 16bpc witness (314,14), but it leaves (29,71) unchanged and does not explain the sign-mixed family by itself.",
            "The surviving 16bpc Legacy witness (345,672) actually prefers nearbyint at the exact Mac-side raw=12544.5 value, so its remaining mismatch is more consistent with a slight pre-store float delta on Windows than with a different local Legacy writer rule.",
            "The surviving old 8bpc Legacy witness (488,941) is not solved by either local floor05 or nearbyint because the current raw value is already below 250.5; Windows must either reach a slightly larger pre-store float or differ earlier in state.",
            "This audit is now historical context for the OLMBlur closeout gate: it explains why a blind source-side writer rewrite stayed forbidden before the later provenance/export lane narrowed the remaining reopen condition.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OLMBlur Writer-Only Hypothesis Audit",
        "",
        f"- Date: `{payload['date']}`",
        f"- Baseline: `{payload['baseline_json']}`",
        f"- Diagnosis counts: `{payload['diagnosis_counts']}`",
        "",
        "## Witness Matrix",
        "",
        "| Case | Bit depth | XY | Reference | Candidate | nearby | floor05 | Best | Diagnosis |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["witnesses"]:
        lines.append(
            f"| `{row['case_id']}` | `{row['bit_depth']}` | `({row['xy'][0]},{row['xy'][1]})` | "
            f"`{row['reference']}` | `{row['candidate']}` | `{row['predicted_nearby']}` | "
            f"`{row['predicted_floor05']}` | `{row['best_writer_only_rule']}` | "
            f"`{row['writer_only_diagnosis']}` |"
        )
    lines.extend(["", "## Decision", "", f"- `{payload['decision']}`", "", "## Interpretation", ""])
    lines.extend(f"- {item}" for item in payload["conclusion"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    baseline = read_json(args.baseline_json)
    payload = build_payload(baseline)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"output_json={args.output_json}")
    print(f"output_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
