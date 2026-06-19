#!/usr/bin/env python3
"""Import a reference folder/zip, run an algorithm CLI, and diff the result."""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def copy_reference(source_root, run_dir):
    manifest_src = source_root / "reference_manifest.json"
    if not manifest_src.exists():
        raise FileNotFoundError(f"reference_manifest.json not found in {source_root}")

    manifest_dst = run_dir / "reference_manifest.json"
    reference_dir = run_dir / "reference"
    reference_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(manifest_src, manifest_dst)

    with manifest_src.open(encoding="utf-8-sig") as handle:
        manifest = json.load(handle)

    missing = []
    copied = set()
    for index, case in enumerate(manifest.get("cases", []), start=1):
        case_id = case.get("id") or f"case_{index:04d}"
        frames = [case.get("frame") or f"{case_id}.png"]
        if case.get("before_effects_frame"):
            frames.append(case["before_effects_frame"])
        for frame in frames:
            if frame in copied:
                continue
            candidates = [source_root / frame, source_root / "png" / frame, source_root / "reference" / frame]
            source_png = next((path for path in candidates if path.exists()), None)
            if source_png is None:
                missing.append(frame)
                continue
            shutil.copy2(source_png, reference_dir / frame)
            copied.add(frame)

    if missing:
        raise FileNotFoundError("missing reference PNGs: " + ", ".join(missing))

    return manifest_dst, reference_dir


def run(command):
    print("+ " + " ".join(str(part) for part in command), flush=True)
    result = subprocess.run([str(part) for part in command])
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def run_from_root(source_root, args):
    run_name = args.name or f"reference_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir = Path(args.run_dir).resolve() if args.run_dir else ROOT / "refs" / "runs" / run_name
    if run_dir.exists() and any(run_dir.iterdir()):
        raise FileExistsError(f"run dir already exists and is not empty: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest_path, reference_dir = copy_reference(source_root, run_dir)
    candidate_dir = run_dir / "candidate"
    diff_dir = run_dir / "diff"
    report_dir = run_dir / "reports"

    run_cases_cmd = [
        sys.executable,
        ROOT / "refs" / "scripts" / "run_algorithm_cases.py",
        manifest_path,
        "--command",
        args.command,
        "--out-dir",
        candidate_dir,
    ]
    if args.input:
        input_path = Path(args.input)
        if not input_path.is_absolute():
            input_path = ROOT / input_path
        run_cases_cmd.extend(["--input", input_path])
    else:
        run_cases_cmd.extend(["--root", reference_dir, "--input-field", "before_effects_frame"])
    for case_id in args.case_id or []:
        run_cases_cmd.extend(["--case-id", case_id])
    if args.expected_effect:
        run_cases_cmd.extend(["--expected-effect", args.expected_effect])
    run(run_cases_cmd)

    verify_cmd = [
        sys.executable,
        ROOT / "refs" / "scripts" / "verify_manifest.py",
        manifest_path,
        "--reference-dir",
        reference_dir,
        "--candidate-dir",
        candidate_dir,
        "--diff-dir",
        diff_dir,
        "--report-dir",
        report_dir,
        "--report-name",
        "diff",
    ]
    for case_id in args.case_id or []:
        verify_cmd.extend(["--case-id", case_id])
    if args.expected_effect:
        verify_cmd.extend(["--expected-effect", args.expected_effect])
    # Pass-through tolerance gates so a known-good residual can be asserted as a
    # regression guard (verify_manifest defaults are all 0 = exact).
    if args.max_diff is not None:
        verify_cmd.extend(["--max-diff", str(args.max_diff)])
    if args.mean_diff is not None:
        verify_cmd.extend(["--mean-diff", str(args.mean_diff)])
    if args.nonzero_px_percent is not None:
        verify_cmd.extend(["--nonzero-px-percent", str(args.nonzero_px_percent)])
    run(verify_cmd)

    print(f"run_dir={run_dir}")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="reference folder or zip from Windows AE")
    parser.add_argument("--command", required=True, help="algorithm CLI command template")
    parser.add_argument("--input", default=None, help="override input image for all cases")
    parser.add_argument("--case-id", action="append", default=None, help="run/verify only this case id; may be repeated")
    parser.add_argument("--expected-effect", default=None, help="skip cases that do not contain this effect name/matchName")
    parser.add_argument("--run-dir", default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--max-diff", type=int, default=None, help="pass-pixel tolerance for verify_manifest (regression guard)")
    parser.add_argument("--mean-diff", type=float, default=None)
    parser.add_argument("--nonzero-px-percent", type=float, default=None)
    args = parser.parse_args()

    source = Path(args.source).resolve()
    if not source.exists():
        print(f"source not found: {source}", file=sys.stderr)
        return 2

    if source.is_dir():
        return run_from_root(source, args)

    if zipfile.is_zipfile(source):
        with tempfile.TemporaryDirectory(prefix="olm_reference_import_") as tmp:
            with zipfile.ZipFile(source) as archive:
                archive.extractall(tmp)
            return run_from_root(Path(tmp), args)

    print(f"source is neither a directory nor a zip: {source}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
