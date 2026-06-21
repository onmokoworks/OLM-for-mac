#!/usr/bin/env python3
"""Measure OLMSmoother2 legacy cases against the current-AEX recapture.

This is not an AE-exact completion gate. It preserves the current important
facts from the 2026-06-21 Windows Software recapture:

- legacy case 0001 is closest when the returned source input is used.
- legacy cases 0002 and 0003 are exact when the AE-saved premultiplied
  before-effects PNGs are used.
- the remaining legacy key/gamma cases are localized residual measurements.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from check_reference_request_status import load_status_rows


REQUEST_ID = "smoother2_legacy_full_current_aex_recapture_20260621"
EXPECTED_EFFECT = "OLM Smoother v2"

SOURCE_GATE = {
    "legacy_case_0001_current_aex": {"max_diff": 43, "mean_diff": 0.0021},
}
BEFORE_EXACT_GATE = {
    "legacy_case_0002_current_aex",
    "legacy_case_0003_current_aex",
}
BEFORE_RESIDUAL_CASES = [
    "legacy_case_0004_current_aex",
    "legacy_case_0005_current_aex",
    "legacy_case_0006_current_aex",
    "legacy_case_0007_current_aex",
    "legacy_case_0008_current_aex",
    "legacy_case_0009_v1mode_current_aex",
    "legacy_case_0010_gamma3_current_aex",
    "legacy_case_0011_gamma5_blue_current_aex",
    "legacy_case_0012_gamma5_red_blue_current_aex",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def covered_manifest(root: Path) -> Path | None:
    rows = load_status_rows(root / "refs" / "reference_requests", root / "refs" / "win_references")
    for row in rows:
        if row.get("request_id") != REQUEST_ID or row.get("status") != "covered":
            continue
        manifest = (row.get("best") or {}).get("manifest")
        if isinstance(manifest, str) and manifest:
            path = Path(manifest)
            return path if path.is_absolute() else (root / path).resolve()
    return None


def source_input_path(manifest_path: Path) -> Path:
    manifest = load_json(manifest_path)
    for entry in manifest.get("source_inputs", []):
        if not isinstance(entry, dict):
            continue
        name = entry.get("file")
        if not isinstance(name, str) or not name:
            continue
        candidates = [
            manifest_path.parent / name,
            manifest_path.parent / name.replace("/", "\\"),
            manifest_path.parent / name.replace("\\", "/"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
    matches = [path for path in manifest_path.parent.iterdir() if path.name.startswith("input")]
    if matches:
        return matches[0]
    raise FileNotFoundError(f"could not find source input PNG for {manifest_path}")


def run_probe(root: Path, manifest_dir: Path, label: str, case_ids: list[str], input_override: Path | None) -> Path:
    run_dir = Path(f"/tmp/olmsmoother2_legacy_current_aex_{label}")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = '"cli/OLMSmoother2/olmsmoother2_cli" --input "{input}" --params "{params}" --output "{output}"'
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(manifest_dir),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        EXPECTED_EFFECT,
        "--command",
        command,
        "--max-diff",
        "255",
        "--mean-diff",
        "255",
        "--nonzero-px-percent",
        "100",
    ]
    if input_override is not None:
        args.extend(["--input", str(input_override)])
    for case_id in case_ids:
        args.extend(["--case-id", case_id])

    result = subprocess.run(args, cwd=root)
    if result.returncode != 0:
        raise RuntimeError(f"{label} probe failed with exit {result.returncode}")
    csv_path = run_dir / "reports" / "diff.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"{label} probe did not produce {csv_path}")
    return csv_path


def read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def row_by_id(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["id"]: row for row in rows}


def print_rows(title: str, rows: list[dict[str, str]]) -> None:
    print(f"=== {title} ===")
    for row in rows:
        print(
            f"{row['id']}: max={row['max_diff']} "
            f"mean={float(row['mean_diff']):.4f} "
            f"nz%={float(row['nonzero_px_percent']):.4f}"
        )


def check_source_gate(rows: list[dict[str, str]]) -> int:
    by_id = row_by_id(rows)
    failures = 0
    for case_id, gate in SOURCE_GATE.items():
        row = by_id.get(case_id)
        if row is None:
            print(f"[FAIL] missing source-gate row: {case_id}", file=sys.stderr)
            failures += 1
            continue
        max_diff = int(row["max_diff"])
        mean_diff = float(row["mean_diff"])
        if max_diff > gate["max_diff"] or mean_diff > gate["mean_diff"]:
            print(
                f"[FAIL] {case_id}: max={max_diff} mean={mean_diff:.6f} "
                f"exceeds gate max<={gate['max_diff']} mean<={gate['mean_diff']}",
                file=sys.stderr,
            )
            failures += 1
    return failures


def check_before_exact(rows: list[dict[str, str]]) -> int:
    by_id = row_by_id(rows)
    failures = 0
    for case_id in sorted(BEFORE_EXACT_GATE):
        row = by_id.get(case_id)
        if row is None:
            print(f"[FAIL] missing before-exact row: {case_id}", file=sys.stderr)
            failures += 1
            continue
        max_diff = int(row["max_diff"])
        mean_diff = float(row["mean_diff"])
        if max_diff != 0 or mean_diff != 0.0:
            print(f"[FAIL] {case_id}: expected exact, got max={max_diff} mean={mean_diff}", file=sys.stderr)
            failures += 1
    return failures


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    manifest_path = covered_manifest(root)
    if manifest_path is None:
        print(f"[SKIP] {REQUEST_ID} is still pending; import the Windows recapture first.")
        return 0

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmsmoother2_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    source_png = source_input_path(manifest_path)
    source_csv = run_probe(root, manifest_path.parent, "source_input", list(SOURCE_GATE), source_png)
    before_cases = sorted(BEFORE_EXACT_GATE) + BEFORE_RESIDUAL_CASES
    before_csv = run_probe(root, manifest_path.parent, "before_frames", before_cases, None)

    source_rows = read_rows(source_csv)
    before_rows = read_rows(before_csv)
    print_rows("source input gate", source_rows)
    print_rows("AE-saved before frame gate/measurements", before_rows)

    failures = check_source_gate(source_rows)
    failures += check_before_exact(before_rows)
    if failures:
        return 1
    print("[OK] OLMSmoother2 legacy current-AEX CLI smoke")
    print(f"source_csv={source_csv}")
    print(f"before_csv={before_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
