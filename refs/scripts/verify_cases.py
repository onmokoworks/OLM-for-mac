#!/usr/bin/env python3
"""Verify rendered PNGs against a parameterized case manifest.

This compares Windows reference renders and macOS candidate renders case by
case, writes amplified diff images, and records machine-readable reports.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def load_rgba(path):
    return np.asarray(Image.open(path).convert("RGBA"))


def compare_images(reference_path, candidate_path, diff_path):
    reference = load_rgba(reference_path)
    candidate = load_rgba(candidate_path)
    if reference.shape != candidate.shape:
        return {
            "status": "shape_mismatch",
            "reference_shape": list(reference.shape),
            "candidate_shape": list(candidate.shape),
        }

    delta = np.abs(reference.astype(np.int32) - candidate.astype(np.int32))
    nonzero_mask = delta.any(axis=-1)
    nonzero_px = int(nonzero_mask.sum())
    total_px = int(reference.shape[0] * reference.shape[1])
    max_diff = int(delta.max())
    mean_diff = float(delta.mean())

    samples = []
    if nonzero_px:
        ys, xs = np.where(nonzero_mask)
        for index in range(min(10, len(xs))):
            x = int(xs[index])
            y = int(ys[index])
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
        "shape": list(reference.shape),
        "max_diff": max_diff,
        "mean_diff": mean_diff,
        "nonzero_px": nonzero_px,
        "total_px": total_px,
        "nonzero_px_percent": 100.0 * nonzero_px / total_px,
        "samples": samples,
    }


def passes_thresholds(metrics, thresholds):
    if metrics["status"] != "compared":
        return False
    return (
        metrics["max_diff"] <= thresholds["max_diff"]
        and metrics["mean_diff"] <= thresholds["mean_diff"]
        and metrics["nonzero_px_percent"] <= thresholds["nonzero_px_percent"]
    )


def case_thresholds(manifest, case):
    thresholds = dict(manifest.get("default_thresholds", {}))
    thresholds.update(case.get("thresholds", {}))
    thresholds.setdefault("max_diff", 0)
    thresholds.setdefault("mean_diff", 0.0)
    thresholds.setdefault("nonzero_px_percent", 0.0)
    return thresholds


def resolve_path(root, value):
    path = Path(value)
    return path if path.is_absolute() else root / path


def write_reports(report_dir, report_name, rows, manifest, summary):
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / f"{report_name}.json"
    csv_path = report_dir / f"{report_name}.csv"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "manifest": {
                    "plugin": manifest.get("plugin"),
                    "variant": manifest.get("variant"),
                    "input": manifest.get("input"),
                },
                "summary": summary,
                "cases": rows,
            },
            handle,
            indent=2,
            sort_keys=True,
        )

    fieldnames = [
        "id",
        "frame",
        "pass",
        "status",
        "max_diff",
        "mean_diff",
        "nonzero_px",
        "total_px",
        "nonzero_px_percent",
        "params",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    return json_path, csv_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "manifest",
        nargs="?",
        default="refs/cases/olmsmoother_v1_minimal.json",
        help="case manifest JSON",
    )
    parser.add_argument("--root", default=None, help="refs root; defaults to manifest parent/..")
    parser.add_argument("--report-name", default=None)
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)

    root = Path(args.root).resolve() if args.root else manifest_path.parent.parent
    reference_dir = resolve_path(root, manifest["reference_dir"])
    candidate_dir = resolve_path(root, manifest["candidate_dir"])
    diff_dir = resolve_path(root, manifest.get("diff_dir", "diff"))
    report_dir = resolve_path(root, manifest.get("report_dir", "reports"))
    report_name = args.report_name or manifest_path.stem

    rows = []
    ok = fail = missing = 0
    print(f"=== {manifest.get('plugin', 'render')} {manifest.get('variant', '')} ===")
    for case in manifest["cases"]:
        case_id = case["id"]
        frame = case["frame"]
        reference_path = reference_dir / frame
        candidate_path = candidate_dir / frame
        diff_path = diff_dir / f"{Path(frame).stem}_{case_id}_diff.png"
        thresholds = case_thresholds(manifest, case)

        row = {
            "id": case_id,
            "frame": frame,
            "params": json.dumps(case.get("params", {}), sort_keys=True),
            "thresholds": thresholds,
        }

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

        metrics = compare_images(reference_path, candidate_path, diff_path)
        passed = passes_thresholds(metrics, thresholds)
        row.update(metrics)
        row["pass"] = passed
        rows.append(row)

        if passed:
            ok += 1
            print(f"[OK]      {case_id:20s} max={metrics['max_diff']} mean={metrics['mean_diff']:.4f}")
        else:
            fail += 1
            if metrics["status"] == "compared":
                print(
                    f"[DIFF]    {case_id:20s} "
                    f"max={metrics['max_diff']} mean={metrics['mean_diff']:.4f} "
                    f"nz={metrics['nonzero_px']}/{metrics['total_px']} "
                    f"({metrics['nonzero_px_percent']:.4f}%)"
                )
            else:
                print(f"[DIFF]    {case_id:20s} {metrics['status']}")

    summary = {"ok": ok, "fail": fail, "missing": missing, "total": len(rows)}
    json_path, csv_path = write_reports(report_dir, report_name, rows, manifest, summary)
    print("---")
    print(f"ok={ok} fail={fail} missing={missing} total={len(rows)}")
    print(f"report_json={json_path}")
    print(f"report_csv={csv_path}")

    return 0 if fail == 0 and missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
