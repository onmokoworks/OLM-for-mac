#!/usr/bin/env python3
"""Compare reference and candidate PNGs using any manifest with cases[].frame."""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def load_rgba(path):
    return np.asarray(Image.open(path).convert("RGBA"))


def compare(reference_path, candidate_path, diff_path):
    reference = load_rgba(reference_path)
    candidate = load_rgba(candidate_path)
    if reference.shape != candidate.shape:
        return {
            "status": "shape_mismatch",
            "reference_shape": list(reference.shape),
            "candidate_shape": list(candidate.shape),
        }

    delta = np.abs(reference.astype(np.int32) - candidate.astype(np.int32))
    mask = delta.any(axis=-1)
    nonzero_px = int(mask.sum())
    total_px = int(reference.shape[0] * reference.shape[1])
    max_diff = int(delta.max())
    mean_diff = float(delta.mean())

    samples = []
    if nonzero_px:
        ys, xs = np.where(mask)
        for i in range(min(10, len(xs))):
            x = int(xs[i])
            y = int(ys[i])
            samples.append(
                {
                    "x": x,
                    "y": y,
                    "reference": [int(v) for v in reference[y, x]],
                    "candidate": [int(v) for v in candidate[y, x]],
                    "delta": [int(v) for v in delta[y, x]],
                }
            )

        diff_path.parent.mkdir(parents=True, exist_ok=True)
        amplified = np.minimum(delta * 32, 255).astype(np.uint8)
        amplified[..., 3] = 255
        Image.fromarray(amplified, "RGBA").save(diff_path)

    return {
        "status": "compared",
        "max_diff": max_diff,
        "mean_diff": mean_diff,
        "nonzero_px": nonzero_px,
        "total_px": total_px,
        "nonzero_px_percent": 100.0 * nonzero_px / total_px,
        "samples": samples,
    }


def passes(metrics, max_diff, mean_diff, nonzero_px_percent):
    if metrics["status"] != "compared":
        return False
    return (
        metrics["max_diff"] <= max_diff
        and metrics["mean_diff"] <= mean_diff
        and metrics["nonzero_px_percent"] <= nonzero_px_percent
    )


def write_reports(report_dir, report_name, rows, summary):
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"{report_name}.json"
    csv_path = report_dir / f"{report_name}.csv"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump({"summary": summary, "cases": rows}, handle, indent=2, sort_keys=True)

    fields = [
        "id",
        "frame",
        "pass",
        "status",
        "max_diff",
        "mean_diff",
        "nonzero_px",
        "total_px",
        "nonzero_px_percent",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})

    return json_path, csv_path


def case_has_effect(case, expected_effect):
    if not expected_effect:
        return True
    for effect in case.get("effects", []):
        if effect.get("name") == expected_effect or effect.get("match_name") == expected_effect:
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--reference-dir", required=True)
    parser.add_argument("--candidate-dir", required=True)
    parser.add_argument("--diff-dir", default="refs/diff")
    parser.add_argument("--report-dir", default="refs/reports")
    parser.add_argument("--report-name", default="manifest_diff")
    parser.add_argument("--case-id", action="append", default=None, help="verify only this case id; may be repeated")
    parser.add_argument("--expected-effect", default=None, help="skip cases that do not contain this effect name/matchName")
    parser.add_argument("--max-diff", type=int, default=0)
    parser.add_argument("--mean-diff", type=float, default=0.0)
    parser.add_argument("--nonzero-px-percent", type=float, default=0.0)
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    reference_dir = Path(args.reference_dir).resolve()
    candidate_dir = Path(args.candidate_dir).resolve()
    diff_dir = Path(args.diff_dir).resolve()
    report_dir = Path(args.report_dir).resolve()

    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)

    ok = fail = missing = 0
    rows = []
    allow_cases = set(args.case_id or [])
    print(f"=== verify {manifest_path.name} ===")
    for index, case in enumerate(manifest.get("cases", []), start=1):
        case_id = case.get("id") or f"case_{index:04d}"
        if allow_cases and case_id not in allow_cases:
            continue
        if not case_has_effect(case, args.expected_effect):
            print(f"[SKIP] {case_id:20s} missing effect {args.expected_effect}")
            continue
        frame = case.get("frame") or f"{case_id}.png"
        reference_path = reference_dir / frame
        candidate_path = candidate_dir / frame
        diff_path = diff_dir / f"{Path(frame).stem}_{case_id}_diff.png"
        row = {"id": case_id, "frame": frame}

        if not reference_path.exists() or not candidate_path.exists():
            row.update(
                {
                    "pass": False,
                    "status": "missing",
                    "missing_reference": not reference_path.exists(),
                    "missing_candidate": not candidate_path.exists(),
                }
            )
            missing += 1
            print(f"[MISSING] {case_id:20s} {frame}")
            rows.append(row)
            continue

        metrics = compare(reference_path, candidate_path, diff_path)
        row.update(metrics)
        row["pass"] = passes(metrics, args.max_diff, args.mean_diff, args.nonzero_px_percent)
        rows.append(row)
        if row["pass"]:
            ok += 1
            print(f"[OK]      {case_id:20s} max={metrics['max_diff']} mean={metrics['mean_diff']:.4f}")
        else:
            fail += 1
            if metrics["status"] == "compared":
                print(
                    f"[DIFF]    {case_id:20s} "
                    f"max={metrics['max_diff']} mean={metrics['mean_diff']:.4f} "
                    f"nz={metrics['nonzero_px']}/{metrics['total_px']}"
                )
            else:
                print(f"[DIFF]    {case_id:20s} {metrics['status']}")

    summary = {"ok": ok, "fail": fail, "missing": missing, "total": len(rows)}
    json_path, csv_path = write_reports(report_dir, args.report_name, rows, summary)
    print("---")
    print(f"ok={ok} fail={fail} missing={missing} total={len(rows)}")
    print(f"report_json={json_path}")
    print(f"report_csv={csv_path}")
    return 0 if fail == 0 and missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
