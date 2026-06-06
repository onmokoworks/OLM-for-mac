#!/usr/bin/env python3
"""Import returned Windows refs and run the post-import request checks."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Returned Windows reference zip or folder")
    parser.add_argument(
        "--set-id",
        default=None,
        help="Reference set directory name. Defaults to import_win_reference.py behavior.",
    )
    parser.add_argument(
        "--dest-root",
        type=Path,
        default=Path("refs/win_references"),
        help="Destination root for imported reference sets.",
    )
    parser.add_argument(
        "--requests-dir",
        type=Path,
        default=Path("refs/reference_requests"),
        help="Directory containing request JSON files for status/post-import checks.",
    )
    parser.add_argument(
        "--request",
        action="append",
        type=Path,
        default=[],
        help="Optional request JSON path to pass to import_win_reference.py. May be repeated.",
    )
    parser.add_argument("--replace", action="store_true", help="Replace existing destination directories.")
    parser.add_argument(
        "--require-optional-render-sets",
        action="store_true",
        help="Require optional render sets during post-import verification.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Also run smoke_all_algorithm_clis.py --profile quick after post-import checks.",
    )
    parser.add_argument(
        "--next-actions-json",
        type=Path,
        default=None,
        help="Write refs/scripts/next_reference_actions.py --json output after import checks.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], root: Path) -> int:
    print("$ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=root).returncode


def main() -> int:
    args = parse_args()
    root = repo_root()
    source = args.source.resolve()
    if not source.exists():
        print(f"source not found: {source}", file=sys.stderr)
        return 2

    import_cmd = [
        sys.executable,
        "refs/scripts/import_win_reference.py",
        str(source),
        "--dest-root",
        str(args.dest_root),
        "--allow-missing-optional-render-sets",
    ]
    if args.set_id:
        import_cmd.extend(["--set-id", args.set_id])
    if args.replace:
        import_cmd.append("--replace")
    for request in args.request:
        import_cmd.extend(["--request", str(request)])

    failures = 0
    if run(import_cmd, root) != 0:
        failures += 1

    status_cmd = [
        sys.executable,
        "refs/scripts/check_reference_request_status.py",
        "--requests",
        str(args.requests_dir),
        "--references",
        str(args.dest_root),
    ]
    if run(status_cmd, root) != 0:
        failures += 1

    post_cmd = [
        sys.executable,
        "refs/scripts/smoke_reference_requests_after_import.py",
        "--requests-dir",
        str(args.requests_dir),
        "--references-dir",
        str(args.dest_root),
    ]
    if args.require_optional_render_sets:
        post_cmd.append("--require-optional-render-sets")
    if run(post_cmd, root) != 0:
        failures += 1

    if args.quick:
        if run([sys.executable, "refs/scripts/smoke_all_algorithm_clis.py", "--profile", "quick"], root) != 0:
            failures += 1

    if args.next_actions_json:
        next_cmd = [
            sys.executable,
            "refs/scripts/next_reference_actions.py",
            "--requests",
            str(args.requests_dir),
            "--references",
            str(args.dest_root),
            "--json",
        ]
        print("$ " + " ".join(next_cmd) + f" > {args.next_actions_json}", flush=True)
        proc = subprocess.run(
            next_cmd,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if proc.returncode != 0:
            print(proc.stdout, end="")
            failures += 1
        else:
            args.next_actions_json.parent.mkdir(parents=True, exist_ok=True)
            args.next_actions_json.write_text(proc.stdout, encoding="utf-8")
            print(f"wrote next reference actions JSON: {args.next_actions_json}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
