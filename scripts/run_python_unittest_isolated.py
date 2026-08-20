#!/usr/bin/env python3
"""Run every tests/test*.py in an isolated process and emit JSON summary."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests-dir", type=Path, default=Path("tests"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    tests_dir = (root / args.tests_dir).resolve() if not args.tests_dir.is_absolute() else args.tests_dir
    paths = sorted(tests_dir.glob("test*.py"))
    started = time.monotonic()

    def run_one(path: Path) -> dict[str, object]:
        case_started = time.monotonic()
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", str(path)], cwd=root,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=args.timeout,
            )
            status = "pass" if proc.returncode == 0 else "fail"
            return {"file": str(path.relative_to(root)), "status": status,
                    "returncode": proc.returncode,
                    "duration_seconds": round(time.monotonic() - case_started, 3),
                    "stdout": proc.stdout, "stderr": proc.stderr}
        except subprocess.TimeoutExpired as exc:
            return {"file": str(path.relative_to(root)), "status": "timeout",
                    "returncode": None,
                    "duration_seconds": round(time.monotonic() - case_started, 3),
                    "stdout": exc.stdout or "", "stderr": exc.stderr or ""}

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        rows = list(executor.map(run_one, paths))
    counts = {status: sum(row["status"] == status for row in rows)
              for status in ("pass", "fail", "timeout")}
    summary = {"schema": "olm.python-unittest-isolated/1", "python": sys.version,
               "test_file_count": len(rows), "counts": counts,
               "duration_seconds": round(time.monotonic() - started, 3), "results": rows}
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output), **counts, "test_file_count": len(rows)}))
    return 0 if not counts["fail"] and not counts["timeout"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
