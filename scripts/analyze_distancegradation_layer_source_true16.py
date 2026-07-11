#!/usr/bin/env python3
"""Analyze OLMDistanceGradation 16bpc Layer-source residuals as true 16-bit data."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST_DIR = (
    ROOT
    / "handoff"
    / "ae_pixel_validation_20260618"
    / "requests"
    / "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
)
DEFAULT_CANDIDATE_ROOT = ROOT / "refs" / "reports" / "ae_single_case_olmdistancegradation_case0012_depthgate_20260708"
DEFAULT_JSON = ROOT / "refs" / "conformance" / "olmdistancegradation_layer_source_true16_audit_20260708.json"
DEFAULT_MD = ROOT / "refs" / "conformance" / "olmdistancegradation_layer_source_true16_audit_20260708.md"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = load_module(ROOT / "refs" / "scripts" / "verify_manifest.py", "verify_manifest")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-dir", type=Path, default=DEFAULT_REQUEST_DIR)
    parser.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE_ROOT)
    parser.add_argument("--case-id", action="append", default=["olmdistancegradation_extended__case_0012"])
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def load_manifest(request_dir: Path) -> dict[str, Any]:
    path = request_dir / "reference_manifest.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def find_candidate(candidate_root: Path, case_id: str, frame: str) -> Path:
    direct = candidate_root / frame
    if direct.exists():
        return direct
    nested = candidate_root / case_id / frame
    if nested.exists():
        return nested
    matches = sorted(candidate_root.glob(f"**/{frame}"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"candidate frame not found under {candidate_root}: {frame}")


def quantiles(values: np.ndarray) -> list[float]:
    if values.size == 0:
        return []
    return [float(x) for x in np.quantile(values.astype(np.float64), [0, 0.01, 0.1, 0.5, 0.9, 0.99, 1])]


def common_values(values: np.ndarray, limit: int = 8) -> list[dict[str, int]]:
    return [
        {"value": int(value), "count": int(count)}
        for value, count in Counter(values.astype(np.int64).tolist()).most_common(limit)
    ]


def analyze_case(request_dir: Path, candidate_root: Path, case_ref: dict[str, Any]) -> dict[str, Any]:
    case_id = str(case_ref["id"])
    frame = str(case_ref["frame"])
    before_frame = str(case_ref["before_effects_frame"])
    candidate_path = find_candidate(candidate_root, case_id, frame)
    reference_path = request_dir / "expected" / frame
    input_path = request_dir / "input" / before_frame

    reference_raw = VERIFY.load_rgba(reference_path)
    candidate_raw = VERIFY.load_rgba(candidate_path)
    source_raw = VERIFY.load_rgba(input_path)
    if reference_raw.dtype == np.uint8 or candidate_raw.dtype == np.uint8 or source_raw.dtype == np.uint8:
        raise ValueError("expected true 16-bit RGBA inputs; got an 8-bit decode")
    reference = reference_raw.astype(np.int64)
    candidate = candidate_raw.astype(np.int64)
    source = source_raw.astype(np.int64)

    diff = candidate - reference
    changed = np.any(diff != 0, axis=-1)
    ys, xs = np.where(changed)
    abs_diff = np.abs(diff)
    same_alpha = changed & (diff[..., 3] == 0)
    selection = same_alpha & (candidate[..., 0] > 0) & (source[..., 3] > 0)

    examples: list[dict[str, Any]] = []
    if ys.size:
        mag = abs_diff.max(axis=-1)
        changed_mag = mag[changed]
        order = np.argsort(changed_mag)[-10:][::-1]
        for idx in order:
            y = int(ys[idx])
            x = int(xs[idx])
            examples.append(
                {
                    "xy": [x, y],
                    "source_rgba16": source[y, x].astype(int).tolist(),
                    "candidate_rgba16": candidate[y, x].astype(int).tolist(),
                    "reference_rgba16": reference[y, x].astype(int).tolist(),
                    "candidate_minus_reference": diff[y, x].astype(int).tolist(),
                }
            )

    ratios: dict[str, Any] = {}
    if np.any(selection):
        src_a = source[..., 3][selection].astype(np.float64)
        src_r = source[..., 0][selection].astype(np.float64)
        cand_a = candidate[..., 3][selection].astype(np.float64)
        ref_r = reference[..., 0][selection].astype(np.float64)
        cand_r = candidate[..., 0][selection].astype(np.float64)
        predicted_ref_from_straight_source = (src_r / src_a) * cand_a
        ratios = {
            "ref_minus_source_over_alpha_times_candidate_alpha_quantiles": quantiles(
                ref_r - predicted_ref_from_straight_source
            ),
            "reference_over_candidate_red_quantiles": quantiles(ref_r / np.maximum(cand_r, 1.0)),
            "source_red_over_source_alpha_quantiles": quantiles(src_r / src_a),
        }

    return {
        "case_id": case_id,
        "candidate_path": str(candidate_path.relative_to(ROOT)) if candidate_path.is_relative_to(ROOT) else str(candidate_path),
        "reference_path": str(reference_path.relative_to(ROOT)),
        "input_path": str(input_path.relative_to(ROOT)),
        "nonzero_pixels": int(changed.sum()),
        "max_abs_diff_true16": int(abs_diff.max()),
        "mean_abs_diff_true16": float(abs_diff.mean()),
        "max_abs_diff_byte_equivalent": float(abs_diff.max() / 256.0),
        "channel_abs_max_true16": [int(v) for v in abs_diff.reshape(-1, 4).max(axis=0).tolist()],
        "channel_nonzero": [int(np.count_nonzero(diff[..., ch])) for ch in range(4)],
        "same_alpha_changed_pixels": int(same_alpha.sum()),
        "diff_common_by_channel": {
            name: common_values(diff[..., ch][changed])
            for ch, name in enumerate(["R", "G", "B", "A"])
        },
        "ratios": ratios,
        "examples": examples,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDistanceGradation Layer-source True16 Audit",
        "",
        f"- Request dir: `{report['request_dir']}`",
        f"- Candidate root: `{report['candidate_root']}`",
        "",
        "## Cases",
        "",
        "| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for case in report["cases"]:
        lines.append(
            "| {case_id} | {nonzero_pixels} | {max_abs_diff_true16} | {max_abs_diff_byte_equivalent:.3f} | "
            "{mean_abs_diff_true16:.6f} | {same_alpha_changed_pixels} | `{channel_abs_max_true16}` |".format(**case)
        )
    lines.extend(["", "## Reading", ""])
    lines.extend(report["reading"])
    for case in report["cases"]:
        lines.extend(["", f"## {case['case_id']} Examples", ""])
        for item in case["examples"][:6]:
            lines.append(
                "- `{xy}` source=`{source_rgba16}` candidate=`{candidate_rgba16}` "
                "reference=`{reference_rgba16}` delta=`{candidate_minus_reference}`".format(**item)
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    request_dir = resolve(args.request_dir)
    candidate_root = resolve(args.candidate_root)
    manifest = load_manifest(request_dir)
    requested = set(args.case_id)
    by_id = {str(case["id"]): case for case in manifest["cases"]}
    missing = sorted(requested.difference(by_id))
    if missing:
        raise KeyError(f"case ids not in manifest: {missing}")
    cases = [analyze_case(request_dir, candidate_root, by_id[case_id]) for case_id in sorted(requested)]
    reading = [
        "The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.",
        "Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.",
        "If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.",
    ]
    report = {
        "kind": "olmdistancegradation_layer_source_true16_audit",
        "schema": 1,
        "request_dir": str(request_dir.relative_to(ROOT)) if request_dir.is_relative_to(ROOT) else str(request_dir),
        "candidate_root": str(candidate_root.relative_to(ROOT)) if candidate_root.is_relative_to(ROOT) else str(candidate_root),
        "cases": cases,
        "reading": reading,
    }
    output_json = resolve(args.output_json)
    output_md = resolve(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"report_json={output_json}")
    print(f"report_md={output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
