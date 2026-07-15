#!/usr/bin/env python3
"""Run scripts/ae_pixel_validation_render.jsx through a live After Effects instance."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", action="append", default=[], help="Request id directory to render. May be repeated.")
    parser.add_argument(
        "--request-ids-file",
        type=Path,
        default=None,
        help="Optional newline-delimited request id list. Ignored when --request-id is supplied.",
    )
    parser.add_argument("--base-dir", type=Path, default=None, help="AE validation handoff base. Defaults to handoff/ae_pixel_validation_20260618.")
    parser.add_argument("--requests-base", type=Path, default=None, help="Directory containing request subdirectories.")
    parser.add_argument("--results-base", type=Path, default=None, help="Directory where AE should write candidate PNGs.")
    parser.add_argument("--progress-log", type=Path, default=None)
    parser.add_argument("--batch-result-json", type=Path, default=None)
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--dump-js", type=Path, default=None)
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def js_string(value: str) -> str:
    return json.dumps(value)


def build_request_ids(args: argparse.Namespace) -> list[str]:
    if args.request_id:
        return args.request_id
    if args.request_ids_file:
        return [line.strip() for line in args.request_ids_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    return []


def main() -> int:
    args = parse_args()
    root = repo_root()
    base_dir = (args.base_dir or (root / "handoff" / "ae_pixel_validation_20260618")).resolve()
    requests_base = (args.requests_base or (base_dir / "requests")).resolve()
    results_base = (args.results_base or (base_dir / "results")).resolve()
    run_dir = results_base.parent / f"batch_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    progress_log = (args.progress_log or (run_dir / "AE_PIXEL_VALIDATION_PROGRESS.log")).resolve()
    batch_result_json = (args.batch_result_json or (run_dir / "AE_PIXEL_VALIDATION_BATCH_RESULT.json")).resolve()
    wrapper_jsx = run_dir / "AE_VALIDATION_BATCH_WRAPPER.jsx"
    jsx_path = root / "scripts" / "ae_pixel_validation_render.jsx"

    request_ids = build_request_ids(args)
    env_lines = [
        f"$.setenv('OLM_AE_BASE_DIR', {js_string(str(base_dir))});",
        f"$.setenv('OLM_AE_REQUESTS_BASE', {js_string(str(requests_base))});",
        f"$.setenv('OLM_AE_RESULTS_BASE', {js_string(str(results_base))});",
        f"$.setenv('OLM_AE_PROGRESS_LOG', {js_string(str(progress_log))});",
        f"$.setenv('OLM_AE_BATCH_RESULT_JSON', {js_string(str(batch_result_json))});",
    ]
    if request_ids:
        env_lines.append(f"$.setenv('OLM_AE_REQUEST_IDS_JSON', {js_string(json.dumps(request_ids))});")
    elif args.request_ids_file:
        env_lines.append(f"$.setenv('OLM_AE_REQUEST_IDS_FILE', {js_string(str(args.request_ids_file.resolve()))});")

    js = "\n".join(
        [
            *env_lines,
            f"$.evalFile(new File({js_string(str(jsx_path))}));",
        ]
    )
    if args.dump_js:
        args.dump_js.parent.mkdir(parents=True, exist_ok=True)
        args.dump_js.write_text(js, encoding="utf-8")
        print(f"[OK] wrote ExtendScript wrapper: {args.dump_js}")
        return 0

    wrapper_jsx.write_text(js, encoding="utf-8")
    apple_script = (
        f"with timeout of {int(args.timeout)} seconds\n"
        f"tell application {js_string(args.app_name)} to DoScriptFile POSIX file {js_string(str(wrapper_jsx))} with override\n"
        "end timeout\n"
    )
    proc = subprocess.run(
        ["osascript"],
        input=apple_script,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=args.timeout + 30,
    )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
    if proc.returncode != 0:
        print(f"[FAIL] osascript exited {proc.returncode}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return proc.returncode
    if not batch_result_json.exists():
        print(f"[FAIL] AE did not write batch result JSON: {batch_result_json}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    result = json.loads(batch_result_json.read_text(encoding="utf-8-sig"))
    print("[OK] AE batch render finished")
    print(f"[INFO] run_dir: {run_dir}")
    print(f"[INFO] batch_result_json: {batch_result_json}")
    print(f"[INFO] requests_rendered: {len(result.get('requests', []))}")
    observations = [
        observation
        for request in result.get("requests", [])
        for observation in (request.get("png_observations") or {}).values()
    ]
    if observations:
        stable = sum(1 for observation in observations if observation.get("status") == "stable")
        print(f"[INFO] png_observations: {stable}/{len(observations)} stable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
