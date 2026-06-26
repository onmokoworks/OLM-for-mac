#!/usr/bin/env python3
"""Verify a directory of AE pixel validation returns against request zips."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import zipfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request_dir", type=Path, help="Directory containing request zip files.")
    parser.add_argument("result_dir", type=Path, help="Directory containing returned result zips or directories.")
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Batch report directory. Defaults to /tmp/olm_ae_pixel_batch_<timestamp>.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Return success when some requests have no matching result yet.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def load_request_manifest(request_zip: Path) -> dict:
    with zipfile.ZipFile(request_zip) as archive:
        matches = [name for name in archive.namelist() if name.endswith("request_manifest.json")]
        if len(matches) != 1:
            raise ValueError(f"{request_zip} expected one request_manifest.json, found {len(matches)}")
        data = json.loads(archive.read(matches[0]))
    if not isinstance(data, dict):
        raise ValueError(f"{request_zip} request_manifest.json top-level JSON must be an object")
    return data


def normalize_name(value: str) -> str:
    keep = []
    for char in value.lower():
        keep.append(char if char.isalnum() else "_")
    while "__" in "".join(keep):
        value = "".join(keep).replace("__", "_")
        keep = list(value)
    return "".join(keep).strip("_")


def aliases_for(request_zip: Path, manifest: dict) -> set[str]:
    request_id = normalize_name(str(manifest.get("request_id", "")))
    stem = normalize_name(request_zip.stem)
    aliases = {stem}
    if request_id:
        aliases.add(request_id)
        if request_id.startswith("ae_pixel_"):
            aliases.add(request_id.removeprefix("ae_pixel_"))
        parts = request_id.split("_")
        if len(parts) > 1 and parts[-1].isdigit():
            aliases.add("_".join(parts[:-1]))
            if "_".join(parts[:-1]).startswith("ae_pixel_"):
                aliases.add("_".join(parts[:-1]).removeprefix("ae_pixel_"))
    return {alias for alias in aliases if alias}


def result_candidates(result_dir: Path) -> list[Path]:
    candidates = []
    for child in sorted(result_dir.iterdir()):
        if child.name.startswith("."):
            continue
        if child.is_dir() or zipfile.is_zipfile(child):
            candidates.append(child)
    return candidates


def match_result(aliases: set[str], candidates: list[Path], used: set[Path]) -> Path | None:
    for candidate in candidates:
        if candidate in used:
            continue
        name = normalize_name(candidate.stem if candidate.is_file() else candidate.name)
        if any(alias in name or name in alias for alias in aliases):
            return candidate
    return None


def main() -> int:
    args = parse_args()
    repo = repo_root()
    request_dir = args.request_dir.resolve()
    result_dir = args.result_dir.resolve()
    if not request_dir.is_dir():
        return fail(f"request dir not found: {request_dir}")
    if not result_dir.is_dir():
        return fail(f"result dir not found: {result_dir}")

    requests = sorted(path for path in request_dir.glob("*.zip") if zipfile.is_zipfile(path))
    if not requests:
        return fail(f"no request zips found in {request_dir}")
    candidates = result_candidates(result_dir)
    if not candidates:
        return fail(f"no result zips/directories found in {result_dir}")

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = args.run_dir.resolve() if args.run_dir else Path("/tmp") / f"olm_ae_pixel_batch_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    used: set[Path] = set()
    rc = 0
    for request_zip in requests:
        try:
            manifest = load_request_manifest(request_zip)
            aliases = aliases_for(request_zip, manifest)
        except Exception as exc:  # noqa: BLE001
            rows.append({"request": str(request_zip), "status": "invalid-request", "error": str(exc)})
            rc = 1
            continue

        result = match_result(aliases, candidates, used)
        if result is None:
            rows.append(
                {
                    "request": str(request_zip),
                    "request_id": manifest.get("request_id"),
                    "status": "missing-result",
                    "aliases": sorted(aliases),
                }
            )
            if not args.allow_missing:
                rc = 1
            continue

        used.add(result)
        request_run_dir = run_dir / request_zip.stem
        proc = subprocess.run(
            [
                sys.executable,
                str(repo / "scripts" / "verify_ae_pixel_validation_result.py"),
                str(request_zip),
                str(result),
                "--run-dir",
                str(request_run_dir),
            ],
            cwd=repo,
            text=True,
        )
        status = "pass" if proc.returncode == 0 else "fail"
        rows.append(
            {
                "request": str(request_zip),
                "request_id": manifest.get("request_id"),
                "result": str(result),
                "run_dir": str(request_run_dir),
                "status": status,
                "returncode": proc.returncode,
            }
        )
        rc = proc.returncode or rc

    summary = {
        "request_dir": str(request_dir),
        "result_dir": str(result_dir),
        "run_dir": str(run_dir),
        "total_requests": len(requests),
        "pass": sum(1 for row in rows if row["status"] == "pass"),
        "fail": sum(1 for row in rows if row["status"] == "fail"),
        "missing": sum(1 for row in rows if row["status"] == "missing-result"),
        "rows": rows,
    }
    summary_path = run_dir / "batch_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for row in rows:
        label = row.get("request_id") or Path(row["request"]).stem
        print(f"{row['status'].upper():14} {label}")
    print(f"summary={summary_path}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
