#!/usr/bin/env python3
"""Verify returned macOS AE-host PNGs against a pixel validation request zip or directory."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "request",
        type=Path,
        help="Request zip from package_ae_pixel_validation_request.py, or a materialized request directory.",
    )
    parser.add_argument(
        "result",
        type=Path,
        help="Returned AE result directory/zip. PNGs may be at root, candidate/, rendered/, or png/.",
    )
    parser.add_argument("--run-dir", type=Path, default=None, help="Directory for reports/diffs")
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def extract_zip(path: Path, dest: Path) -> Path:
    if not zipfile.is_zipfile(path):
        raise ValueError(f"not a zip file: {path}")
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            normalized = member.filename.replace("\\", "/")
            if not normalized or normalized.endswith("/"):
                continue
            if normalized.startswith("/") or ".." in Path(normalized).parts:
                raise ValueError(f"unsafe zip member: {member.filename}")
            target = dest / normalized
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as src, target.open("wb") as out:
                shutil.copyfileobj(src, out)
    roots = [child for child in dest.iterdir() if child.is_dir() and child.name != "__MACOSX"]
    if len(roots) == 1:
        return roots[0]
    return dest


def materialize_source(source: Path, dest: Path) -> Path:
    source = source.resolve()
    if source.is_dir():
        return source
    if source.exists() and zipfile.is_zipfile(source):
        return extract_zip(source, dest)
    raise ValueError(f"result is neither a directory nor a zip: {source}")


def materialize_request(source: Path, dest: Path) -> Path:
    source = source.resolve()
    if source.is_dir():
        return find_request_root(source)
    if source.exists() and zipfile.is_zipfile(source):
        return find_request_root(extract_zip(source, dest))
    raise ValueError(f"request is neither a directory nor a zip: {source}")


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def find_request_root(root: Path) -> Path:
    if (root / "request_manifest.json").exists():
        return root
    matches = list(root.rglob("request_manifest.json"))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one request_manifest.json, found {len(matches)}")
    return matches[0].parent


def candidate_png(result_root: Path, frame: str) -> Path | None:
    candidates = [
        result_root / frame,
        result_root / "candidate" / frame,
        result_root / "rendered" / frame,
        result_root / "png" / frame,
        result_root / "output" / frame,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = list(result_root.rglob(frame))
    if len(matches) == 1:
        return matches[0]
    return None


def verify_group(
    repo: Path,
    request_root: Path,
    candidate_dir: Path,
    run_dir: Path,
    group: dict,
    effect_name: str,
) -> int:
    cmd = [
        sys.executable,
        str(repo / "refs" / "scripts" / "verify_manifest.py"),
        str(request_root / "reference_manifest.json"),
        "--reference-dir",
        str(request_root / "expected"),
        "--candidate-dir",
        str(candidate_dir),
        "--diff-dir",
        str(run_dir / "diff" / group["name"]),
        "--report-dir",
        str(run_dir / "reports"),
        "--report-name",
        f"ae_pixel_{group['name']}",
        "--expected-effect",
        effect_name,
        "--max-diff",
        str(group["max_diff"]),
        "--mean-diff",
        str(group["mean_diff"]),
        "--nonzero-px-percent",
        str(group["nonzero_px_percent"]),
    ]
    for case_id in group["case_ids"]:
        cmd.extend(["--case-id", case_id])
    proc = subprocess.run(cmd, cwd=repo, text=True)
    return proc.returncode


def main() -> int:
    args = parse_args()
    repo = repo_root()
    request = args.request.resolve()
    result = args.result.resolve()
    if not request.exists():
        return fail(f"request not found: {request}")
    if not result.exists():
        return fail(f"result not found: {result}")

    with tempfile.TemporaryDirectory(prefix="olm_ae_pixel_verify_") as tmp:
        tmp_path = Path(tmp)
        try:
            request_root = materialize_request(request, tmp_path / "request")
            result_root = materialize_source(result, tmp_path / "result")
            request_manifest = load_json(request_root / "request_manifest.json")
        except Exception as exc:  # noqa: BLE001
            return fail(str(exc))

        if request_manifest.get("kind") != "olm_ae_pixel_validation_request":
            return fail("request_manifest.kind must be 'olm_ae_pixel_validation_request'")

        run_dir = args.run_dir.resolve() if args.run_dir else Path("/tmp") / request_manifest["request_id"]
        if run_dir.exists():
            shutil.rmtree(run_dir)
        candidate_dir = run_dir / "candidate"
        candidate_dir.mkdir(parents=True)

        missing: list[str] = []
        for case in request_manifest.get("cases", []):
            frame = case.get("frame")
            if not isinstance(frame, str) or not frame:
                return fail("each request case must have a frame")
            source_png = candidate_png(result_root, frame)
            if source_png is None:
                missing.append(frame)
                continue
            shutil.copy2(source_png, candidate_dir / frame)

        if missing:
            return fail("missing returned candidate PNGs: " + ", ".join(missing))

        rc = 0
        for group in request_manifest.get("threshold_groups", []):
            rc = verify_group(
                repo,
                request_root,
                candidate_dir,
                run_dir,
                group,
                request_manifest["effect_name"],
            ) or rc

        if rc == 0:
            print(f"[OK] AE pixel validation passed: {request_manifest['request_id']}")
            print(f"run_dir={run_dir}")
        return rc


if __name__ == "__main__":
    raise SystemExit(main())
