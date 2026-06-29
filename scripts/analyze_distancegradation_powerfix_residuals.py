#!/usr/bin/env python3
"""Classify OLMDistanceGradation 16bpc residuals after the Power param fix."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
DEFAULT_RUN = ROOT / "refs/reports/ae_pixel_validation_16bpc_distancegradation_extended_powerfix_20260629_1424"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-dir", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=ROOT / "refs/conformance/olmdistancegradation_16bpc_powerfix_residual_families_20260629.json",
    )
    parser.add_argument(
        "--summary-md",
        type=Path,
        default=ROOT / "refs/conformance/olmdistancegradation_16bpc_powerfix_residual_families_20260629.md",
    )
    return parser.parse_args()


def load_verify_manifest_module():
    path = ROOT / "refs/scripts/verify_manifest.py"
    spec = importlib.util.spec_from_file_location("verify_manifest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def param_values(case: dict) -> dict[str, object]:
    effects = case.get("effects") or []
    if not effects:
        return {}
    return {
        p.get("name"): p.get("value")
        for p in effects[0].get("params", [])
        if p.get("name") and p.get("value") is not None
    }


def classify(params: dict[str, object], max_diff: int, nonzero_px: int) -> str:
    interp = int(params.get("Interpolation Mode", 0))
    render_mode = int(params.get("Render Mode", 0))
    use_bg = int(params.get("Use Background Color", 0))
    in_out = int(params.get("In/Out", 0))
    inside = int(params.get("Inside Threshold", 0))
    outside = int(params.get("Outside Threshold", 0))
    if max_diff == 0:
        return "ae-exact"
    if interp == 1 and use_bg:
        return "constant-bg-binary-sparse-full-color"
    if interp == 4 and render_mode == 1 and use_bg:
        return "power-rgb-bg-boundary-quantization"
    if interp == 4 and render_mode == 2 and use_bg:
        return "power-layer-bg-source-or-premultiply"
    if interp == 3 and use_bg:
        return "sphere-bg-boundary-quantization"
    if render_mode == 2 and not use_bg:
        return "layer-no-bg-source-or-alpha-ownership"
    if in_out == 3 and not use_bg and (inside == 0 or outside == 0):
        return "both-no-bg-zero-threshold-edge-case"
    if nonzero_px < 20000:
        return "sparse-boundary-quantization"
    return "broad-field-or-compose-residual"


def main() -> int:
    args = parse_args()
    verify = load_verify_manifest_module()
    request_dir = args.request_dir.resolve()
    run_dir = args.run_dir.resolve()
    report_path = run_dir / "reports/ae_pixel_16bpc_extended_powerfix.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    reference_manifest = json.loads((request_dir / "reference_manifest.json").read_text(encoding="utf-8"))
    case_by_id = {case["id"]: case for case in reference_manifest["cases"]}

    rows: list[dict] = []
    for case_report in report["cases"]:
        cid = case_report["id"]
        case = case_by_id[cid]
        params = param_values(case)
        frame = case_report["frame"]
        ref = verify.load_rgba(request_dir / "expected" / frame)
        cand = verify.load_rgba(run_dir / "candidate" / frame)
        delta = cand.astype(np.int64) - ref.astype(np.int64)
        absd = np.abs(delta)
        max_diff = int(case_report["max_diff"])
        ys, xs, cs = np.where(absd == max_diff)
        witnesses = []
        for i in range(min(5, len(xs))):
            y, x, ch = int(ys[i]), int(xs[i]), int(cs[i])
            witnesses.append(
                {
                    "x": x,
                    "y": y,
                    "channel": ch,
                    "reference": [int(v) for v in ref[y, x]],
                    "candidate": [int(v) for v in cand[y, x]],
                    "delta": [int(v) for v in delta[y, x]],
                }
            )
        nonzero_px = int(case_report.get("nonzero_px") or 0)
        rows.append(
            {
                "case_id": cid,
                "pass": bool(case_report["pass"]),
                "max_diff": max_diff,
                "mean_diff": float(case_report["mean_diff"]),
                "nonzero_px": nonzero_px,
                "params": {
                    key: params.get(key)
                    for key in (
                        "Invert",
                        "In/Out",
                        "Inside Threshold",
                        "Outside Threshold",
                        "Render Mode",
                        "Use Background Color",
                        "Interpolation Mode",
                        "Power",
                    )
                },
                "family": classify(params, max_diff, nonzero_px),
                "max_witnesses": witnesses,
            }
        )

    family_counts: dict[str, int] = {}
    for row in rows:
        family_counts[row["family"]] = family_counts.get(row["family"], 0) + 1

    payload = {
        "kind": "olmdistancegradation_16bpc_powerfix_residual_families",
        "source_report": str(report_path.relative_to(ROOT)),
        "exact": sum(1 for row in rows if row["pass"]),
        "fail": sum(1 for row in rows if not row["pass"]),
        "total": len(rows),
        "family_counts": family_counts,
        "cases": rows,
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# OLMDistanceGradation 16bpc Power-Fix Residual Families (2026-06-29)",
        "",
        f"- Source report: `{payload['source_report']}`",
        f"- Exact: `{payload['exact']}/{payload['total']}`",
        "",
        "## Families",
        "",
        "| Family | Count |",
        "| --- | ---: |",
    ]
    for family, count in sorted(family_counts.items()):
        lines.append(f"| `{family}` | {count} |")
    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| Case | Family | max | mean | nonzero_px | Params | First max witness |",
            "| --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in rows:
        witness = row["max_witnesses"][0] if row["max_witnesses"] else {}
        params = row["params"]
        compact_params = (
            f"inv={params.get('Invert')} inout={params.get('In/Out')} "
            f"in={params.get('Inside Threshold')} out={params.get('Outside Threshold')} "
            f"mode={params.get('Render Mode')} bg={params.get('Use Background Color')} "
            f"interp={params.get('Interpolation Mode')} power={params.get('Power')}"
        )
        witness_text = ""
        if witness:
            witness_text = (
                f"({witness['x']},{witness['y']}) ch{witness['channel']} "
                f"ref={witness['reference']} cand={witness['candidate']} delta={witness['delta']}"
            )
        lines.append(
            f"| `{row['case_id']}` | `{row['family']}` | {row['max_diff']} | "
            f"{row['mean_diff']:.4f} | {row['nonzero_px']} | `{compact_params}` | `{witness_text}` |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- The Power parameter collapse is fixed and should not be revisited.",
            "- Remaining work should be split by family rather than tuned from all failures together.",
            "- `constant-bg-binary-sparse-full-color` is still a full-color branch mismatch on sparse pixels.",
            "- `power-layer-bg-source-or-premultiply` needs source/premultiply ownership evidence.",
            "- `power-rgb-bg-boundary-quantization` and `sphere-bg-boundary-quantization` need final field quantization / writeback proof.",
        ]
    )
    args.summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary_json={args.summary_json}")
    print(f"summary_md={args.summary_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
