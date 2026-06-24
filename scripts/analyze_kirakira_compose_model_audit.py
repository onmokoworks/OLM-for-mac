#!/usr/bin/env python3
"""Audit OLMKiraKira compose model candidates against BT.709 Software refs."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = (
    ROOT
    / "refs"
    / "reports"
    / "olmkirakira_remeasure_20260624_bt709_software"
    / "reference_manifest.json"
)
DEFAULT_OUT_DIR = ROOT / "refs" / "reports" / "olmkirakira_compose_model_audit_20260625"


VARIANTS: list[dict[str, Any]] = [
    {
        "id": "current_gain_0_62",
        "label": "current aex-screen-over gain 0.62",
        "args": "--compose-mode aex-screen-over --scale-mode aex-screen-over --gain-scale 0.62",
        "expectation": "current baseline; preserve unless a candidate improves without breaking strength0",
    },
    {
        "id": "gain_0_60",
        "label": "aex-screen-over gain 0.60",
        "args": "--compose-mode aex-screen-over --scale-mode aex-screen-over --gain-scale 0.60",
        "expectation": "prior broad probe said total mean worsens",
    },
    {
        "id": "gain_0_5811",
        "label": "aex-screen-over gain 0.5811 from center/right implied scale",
        "args": "--compose-mode aex-screen-over --scale-mode aex-screen-over --gain-scale 0.5811",
        "expectation": "tests whether traced grayscale implied scale can generalize",
    },
    {
        "id": "gain_0_5436",
        "label": "aex-screen-over gain 0.5436 from colored up implied scale",
        "args": "--compose-mode aex-screen-over --scale-mode aex-screen-over --gain-scale 0.5436",
        "expectation": "tests whether colored witness implied scale can generalize",
    },
    {
        "id": "scale_override_1_0",
        "label": "direct scale override 1.0",
        "args": "--compose-mode aex-screen-over --scale-mode aex-screen-over --gain-scale 0.62 --scale-override 1.0",
        "expectation": "negative control; should break strength0 anchors",
    },
    {
        "id": "premul_gain_0_62",
        "label": "aex-premul compose gain 0.62",
        "args": "--compose-mode aex-premul --scale-mode aex --gain-scale 0.62",
        "expectation": "negative control for merge-mode-1 screen-over vs premul blend",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--work-dir", type=Path, default=None)
    parser.add_argument(
        "--python",
        type=Path,
        default=Path(os.environ.get("OLM_PROBE_PYTHON", "/tmp/olm_cv455_probe_venv/bin/python")),
        help="Python with cv2 installed.",
    )
    parser.add_argument("--keep-work", action="store_true")
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: manifest must be a JSON object")
    return data


def software_cases(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for case in manifest.get("cases", []):
        render_set = str(case.get("render_set_id") or case.get("render_set") or "").lower()
        frame = str(case.get("frame") or "").lower()
        if "software" in render_set or "__software__" in frame:
            cases.append(case)
    return cases


def write_software_manifest(manifest: dict[str, Any], source: Path, work_dir: Path) -> Path:
    filtered = dict(manifest)
    filtered["cases"] = software_cases(manifest)
    filtered["source_manifest"] = str(source)
    path = work_dir / "software_reference_manifest.json"
    path.write_text(json.dumps(filtered, indent=2, sort_keys=True), encoding="utf-8")
    return path


def classify_case(case_id: str) -> str:
    if "strength0" in case_id:
        return "strength0_anchor"
    if "rotation13" in case_id:
        return "rotation13"
    return "strength100_single_ray"


def run_command(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        print(result.stdout, file=sys.stderr)
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}")


def run_variant(
    variant: dict[str, Any],
    manifest_path: Path,
    reference_root: Path,
    work_dir: Path,
    python: Path,
) -> dict[str, Any]:
    variant_dir = work_dir / variant["id"]
    candidate_dir = variant_dir / "candidate"
    diff_dir = variant_dir / "diff"
    report_dir = variant_dir / "reports"
    command = (
        f'"{python}" "refs/scripts/olmkirakira_cli.py" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--seed-mode aex --falloff box3 "
        "--ray-mode opencv-two-temp "
        "--auto-length-scale --comp-width 1920 "
        "--zero-ray-skip "
        f"{variant['args']}"
    )
    run_args = [
        sys.executable,
        str(ROOT / "refs" / "scripts" / "run_algorithm_cases.py"),
        str(manifest_path),
        "--command",
        command,
        "--root",
        str(reference_root),
        "--input-field",
        "before_effects_frame",
        "--out-dir",
        str(candidate_dir),
        "--expected-effect",
        "OLM Kira Kira",
    ]
    run_command(run_args, ROOT)

    verify_args = [
        sys.executable,
        str(ROOT / "refs" / "scripts" / "verify_manifest.py"),
        str(manifest_path),
        "--reference-dir",
        str(reference_root),
        "--candidate-dir",
        str(candidate_dir),
        "--diff-dir",
        str(diff_dir),
        "--report-dir",
        str(report_dir),
        "--report-name",
        "diff",
        "--expected-effect",
        "OLM Kira Kira",
        "--max-diff",
        "255",
        "--mean-diff",
        "255",
        "--nonzero-px-percent",
        "100",
    ]
    run_command(verify_args, ROOT)

    report = json.loads((report_dir / "diff.json").read_text(encoding="utf-8"))
    cases = report.get("cases", [])
    groups: dict[str, dict[str, Any]] = {}
    for row in cases:
        group = classify_case(str(row["id"]))
        current = groups.setdefault(
            group,
            {"case_count": 0, "exact_count": 0, "mean_sum": 0.0, "max_diff": 0},
        )
        current["case_count"] += 1
        current["exact_count"] += 1 if int(row.get("max_diff", 0)) == 0 else 0
        current["mean_sum"] += float(row.get("mean_diff", 0.0))
        current["max_diff"] = max(int(current["max_diff"]), int(row.get("max_diff", 0)))

    total = {
        "case_count": len(cases),
        "exact_count": sum(1 for row in cases if int(row.get("max_diff", 0)) == 0),
        "mean_sum": sum(float(row.get("mean_diff", 0.0)) for row in cases),
        "max_diff": max((int(row.get("max_diff", 0)) for row in cases), default=0),
    }
    return {
        "id": variant["id"],
        "label": variant["label"],
        "args": variant["args"],
        "expectation": variant["expectation"],
        "total": total,
        "groups": groups,
        "report_json": str(report_dir / "diff.json"),
        "candidate_dir": str(candidate_dir),
    }


def decision(rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline = next(row for row in rows if row["id"] == "current_gain_0_62")
    better = [
        row
        for row in rows
        if row["total"]["mean_sum"] < baseline["total"]["mean_sum"]
        and row["total"]["max_diff"] <= baseline["total"]["max_diff"]
        and row["groups"].get("strength0_anchor", {}).get("max_diff", 999) <= baseline["groups"].get("strength0_anchor", {}).get("max_diff", 999)
    ]
    if len(better) <= 1:
        status = "preserve-current-compose-model"
        reason = "No audited candidate improves total mean and max while preserving strength0 anchors."
    else:
        status = "candidate-needs-binary-proof"
        reason = "At least one candidate improves aggregate metrics; do not promote without compose/writeback proof."
    return {
        "status": status,
        "reason": reason,
        "baseline_id": baseline["id"],
        "best_by_mean": min(rows, key=lambda row: row["total"]["mean_sum"])["id"],
        "best_by_max": min(rows, key=lambda row: row["total"]["max_diff"])["id"],
    }


def write_outputs(out_dir: Path, report: dict[str, Any]) -> tuple[Path, Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "compose_model_audit.json"
    md_path = out_dir / "compose_model_audit.md"
    csv_path = out_dir / "compose_model_audit.csv"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["variant", "group", "cases", "exact", "max_diff", "mean_sum"])
        for row in report["variants"]:
            writer.writerow(
                [
                    row["id"],
                    "total",
                    row["total"]["case_count"],
                    row["total"]["exact_count"],
                    row["total"]["max_diff"],
                    f"{row['total']['mean_sum']:.6f}",
                ]
            )
            for group, stats in sorted(row["groups"].items()):
                writer.writerow(
                    [
                        row["id"],
                        group,
                        stats["case_count"],
                        stats["exact_count"],
                        stats["max_diff"],
                        f"{stats['mean_sum']:.6f}",
                    ]
                )

    lines = [
        "# OLMKiraKira Compose Model Audit",
        "",
        f"- Decision: `{report['decision']['status']}`",
        f"- Reason: {report['decision']['reason']}",
        f"- Best by mean: `{report['decision']['best_by_mean']}`",
        f"- Best by max: `{report['decision']['best_by_max']}`",
        "",
        "## Total Metrics",
        "",
        "| Variant | Exact | Max | Mean sum | Notes |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in report["variants"]:
        total = row["total"]
        lines.append(
            f"| `{row['id']}` | {total['exact_count']}/{total['case_count']} | "
            f"{total['max_diff']} | {total['mean_sum']:.6f} | {row['expectation']} |"
        )
    lines.extend(["", "## Group Metrics", ""])
    for row in report["variants"]:
        lines.extend(
            [
                f"### {row['id']}",
                "",
                "| Group | Exact | Max | Mean sum |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for group, stats in sorted(row["groups"].items()):
            lines.append(
                f"| `{group}` | {stats['exact_count']}/{stats['case_count']} | "
                f"{stats['max_diff']} | {stats['mean_sum']:.6f} |"
            )
        lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path, csv_path


def main() -> int:
    args = parse_args()
    python = args.python
    cv2_check = subprocess.run(
        [str(python), "-c", "import cv2; print(cv2.__version__)"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if cv2_check.returncode != 0:
        print(cv2_check.stdout, file=sys.stderr)
        raise RuntimeError(f"missing cv2 for {python}")

    if args.work_dir:
        work_dir = args.work_dir.resolve()
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir(parents=True)
        cleanup = False
    else:
        work_dir = Path(tempfile.mkdtemp(prefix="olmkirakira_compose_audit_"))
        cleanup = not args.keep_work

    try:
        source_manifest_path = args.manifest.resolve()
        reference_root = source_manifest_path.parent / "reference"
        manifest = load_manifest(source_manifest_path)
        software_only = software_cases(manifest)
        case_ids = [str(case.get("id")) for case in software_only]
        if len(software_only) != 9:
            raise RuntimeError(f"expected 9 Software cases, found {len(software_only)}: {case_ids}")
        manifest_path = write_software_manifest(manifest, source_manifest_path, work_dir)
        rows = [run_variant(variant, manifest_path, reference_root, work_dir, python) for variant in VARIANTS]
        report = {
            "kind": "olmkirakira_compose_model_audit",
            "manifest": str(source_manifest_path),
            "filtered_manifest": str(manifest_path),
            "python": str(python),
            "cv2_version": cv2_check.stdout.strip(),
            "case_ids": case_ids,
            "variants": rows,
        }
        report["decision"] = decision(rows)
        json_path, md_path, csv_path = write_outputs(args.out_dir.resolve(), report)
        print(f"report_json={json_path}")
        print(f"report_md={md_path}")
        print(f"report_csv={csv_path}")
        return 0
    finally:
        if cleanup:
            shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
