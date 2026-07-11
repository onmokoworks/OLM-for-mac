#!/usr/bin/env python3
"""Auto-route returned OLM artifacts to the right verifier/importer."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


RUNTIME_SUMMARY_KIND = "olm_runtime_trace_return_summary"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Returned zip/folder from AE host or Windows reference renderer.")
    parser.add_argument(
        "--kind",
        choices=("auto", "ae-host", "ae-pixel-validation", "win-reference", "runtime-trace"),
        default="auto",
        help="Artifact kind. auto detects from JSON contents.",
    )
    parser.add_argument(
        "--package",
        type=Path,
        default=None,
        help="Mac plug-in or OLM handoff package for AE-host returns. Defaults to the newest valid package in /tmp.",
    )
    parser.add_argument(
        "--package-search-dir",
        action="append",
        type=Path,
        default=[],
        help="AE-host: directory to search for a package when --package is omitted. May be repeated.",
    )
    parser.add_argument("--require-all-pass", action="store_true", help="AE-host: require all plugins to pass.")
    parser.add_argument(
        "--require-all-pixel-requests",
        action="store_true",
        help="AE-host: require every packaged pixel request to have a returned PNG group.",
    )
    parser.add_argument("--run-dir", type=Path, default=None, help="AE-host pixel report directory.")
    parser.add_argument(
        "--ae-pixel-requests-dir",
        action="append",
        type=Path,
        default=[],
        help="AE pixel validation: directory containing request zips. May be repeated.",
    )
    parser.add_argument("--set-id", default=None, help="Windows refs: destination set id.")
    parser.add_argument(
        "--dest-root",
        type=Path,
        default=Path("refs/win_references"),
        help="Windows refs: destination root.",
    )
    parser.add_argument(
        "--requests-dir",
        type=Path,
        default=Path("refs/reference_requests"),
        help="Windows refs: request directory for status/post-import checks.",
    )
    parser.add_argument(
        "--request",
        action="append",
        type=Path,
        default=[],
        help="Windows refs: request JSON path. May be repeated.",
    )
    parser.add_argument("--replace", action="store_true", help="Windows refs: replace existing import dirs.")
    parser.add_argument(
        "--require-optional-render-sets",
        action="store_true",
        help="Windows refs: require optional render sets during post-import checks.",
    )
    parser.add_argument("--quick", action="store_true", help="Windows refs: run quick aggregate after import.")
    parser.add_argument(
        "--no-next-actions",
        action="store_true",
        help="Windows refs: do not print next prioritized reference action after import.",
    )
    parser.add_argument(
        "--next-actions-json",
        type=Path,
        default=None,
        help="Windows refs: write next_reference_actions.py --json output after import.",
    )
    parser.add_argument(
        "--dispatch-dir",
        type=Path,
        default=None,
        help="Windows refs: write per-action sub-agent dispatch files after import.",
    )
    parser.add_argument(
        "--runtime-package",
        type=Path,
        default=None,
        help="Runtime trace: request package zip. Defaults to newest refs/runtime_trace_packages/*.zip.",
    )
    parser.add_argument(
        "--runtime-summary-json",
        type=Path,
        default=None,
        help="Runtime trace: write normalized summary JSON.",
    )
    parser.add_argument(
        "--runtime-summary-md",
        type=Path,
        default=None,
        help="Runtime trace: write a human-readable Markdown summary.",
    )
    parser.add_argument(
        "--runtime-comparison-dir",
        type=Path,
        default=None,
        help=(
            "Runtime trace: run known comparison routers after summary generation "
            "and write their outputs to this directory."
        ),
    )
    parser.add_argument(
        "--runtime-report-dir",
        type=Path,
        default=None,
        help="Runtime trace: default directory for auto-named summary JSON/Markdown.",
    )
    parser.add_argument(
        "--no-runtime-comparisons",
        action="store_true",
        help="Runtime trace: skip automatic comparison routing after writing a summary.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def fail(message: str, code: int = 1) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return code


def slug(value: str, fallback: str = "reference") -> str:
    value = value.strip().replace(" ", "")
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value or fallback


def extract_if_zip(source: Path, dest: Path) -> Path:
    source = source.resolve()
    if source.is_dir():
        return source
    if not source.exists() or not zipfile.is_zipfile(source):
        raise ValueError(f"source is neither a directory nor zip: {source}")
    with zipfile.ZipFile(source) as archive:
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
    visible = [
        child
        for child in dest.iterdir()
        if child.name != "__MACOSX" and not child.name.startswith("._")
    ]
    roots = [child for child in visible if child.is_dir()]
    return roots[0] if len(visible) == 1 and len(roots) == 1 else dest


def load_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def load_runtime_summary(path: Path) -> dict[str, Any] | None:
    data = load_json(path)
    if not isinstance(data, dict) or data.get("kind") != RUNTIME_SUMMARY_KIND:
        return None
    return data


def merge_runtime_summaries(existing: dict[str, Any] | None, incoming: dict[str, Any]) -> dict[str, Any]:
    merged_results: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for summary in (existing, incoming):
        if not isinstance(summary, dict):
            continue
        for row in summary.get("results", []):
            if not isinstance(row, dict):
                continue
            request_id = str(row.get("request_id") or "")
            status = str(row.get("status") or "")
            source_file = str(row.get("source_file") or "")
            summary_text = str(row.get("summary") or "")
            key = (request_id, status, source_file, summary_text)
            if key in seen:
                continue
            seen.add(key)
            merged_results.append(row)

    by_id: dict[str, list[dict[str, Any]]] = {}
    for row in merged_results:
        request_id = row.get("request_id")
        if isinstance(request_id, str) and request_id:
            by_id.setdefault(request_id, []).append(row)

    required: list[dict[str, Any]] = []
    for request_id in sorted(by_id):
        rows = by_id[request_id]
        statuses = sorted({str(row.get("status") or "") for row in rows if str(row.get("status") or "")})
        answered = any(
            status in {"answered", "ok", "done", "complete", "completed"} or status.startswith("answered")
            for status in statuses
        )
        required.append(
            {
                "request_id": request_id,
                "count": len(rows),
                "answered": answered,
                "statuses": statuses,
            }
        )

    source_roots = []
    packages = []
    for summary in (existing, incoming):
        if not isinstance(summary, dict):
            continue
        source_root = summary.get("source_root")
        package = summary.get("package")
        if isinstance(source_root, str) and source_root and source_root not in source_roots:
            source_roots.append(source_root)
        if isinstance(package, str) and package and package not in packages:
            packages.append(package)

    return {
        "kind": RUNTIME_SUMMARY_KIND,
        "schema": 1,
        "source_root": " + ".join(source_roots) if source_roots else "runtime-trace-return-merged",
        "package": packages[0] if len(packages) == 1 else None,
        "required": required,
        "extra_request_ids": [],
        "results": merged_results,
    }


def render_runtime_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# OLM Runtime Trace Return Summary",
        "",
        "| Request | Count | Answered | Statuses |",
        "| --- | ---: | --- | --- |",
    ]
    for row in summary.get("required", []):
        request_id = row.get("request_id", "-")
        count = int(row.get("count", 0) or 0)
        answered = "yes" if row.get("answered") else "no"
        statuses = ", ".join(row.get("statuses") or []) or "-"
        lines.append(f"| `{request_id}` | {count} | {answered} | `{statuses}` |")
    lines.append("")
    return "\n".join(lines)


def package_kind(path: Path) -> str | None:
    if path.is_dir():
        data = load_json(path / "manifest.json")
        if data:
            kind = data.get("kind")
            if kind in {"olm_port_handoff_package", "olm_mac_plugin_package"}:
                return kind
        return None

    if not path.exists() or not zipfile.is_zipfile(path):
        return None
    try:
        with zipfile.ZipFile(path) as archive:
            manifests = [
                name
                for name in archive.namelist()
                if name.endswith("manifest.json")
                and "__MACOSX" not in Path(name).parts
                and not any(part.startswith("._") for part in Path(name).parts)
            ]
            top_manifests = [name for name in manifests if len(Path(name).parts) == 2]
            for name in top_manifests:
                data = json.loads(archive.read(name).decode("utf-8-sig"))
                if isinstance(data, dict):
                    kind = data.get("kind")
                    if kind in {"olm_port_handoff_package", "olm_mac_plugin_package"}:
                        return kind
    except Exception:
        return None
    return None


def verify_package_candidate(root: Path, path: Path, verifier: str) -> str | None:
    cmd = [sys.executable, verifier, str(path)]
    proc = subprocess.run(cmd, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode == 0:
        return None
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return lines[-1] if lines else f"{verifier} exited {proc.returncode}"


def sorted_candidates(search_dirs: list[Path], pattern: str) -> list[Path]:
    candidates: list[Path] = []
    for search_dir in search_dirs:
        if not search_dir.exists() or not search_dir.is_dir():
            continue
        candidates.extend(search_dir.glob(pattern))
    return sorted(set(candidates), key=lambda path: path.stat().st_mtime, reverse=True)


def find_latest_ae_package(root: Path, search_dirs: list[Path]) -> Path | None:
    for pattern, verifier in (
        ("olm_port_handoff*.zip", "scripts/verify_olm_handoff_package.py"),
        ("olm_mac_plugins*.zip", "scripts/verify_mac_plugin_package.py"),
    ):
        for candidate in sorted_candidates(search_dirs, pattern):
            if not package_kind(candidate):
                print(f"[INFO] skipping AE-host package candidate: {candidate} (unrecognized package kind)")
                continue
            problem = verify_package_candidate(root, candidate, verifier)
            if problem:
                print(f"[INFO] skipping AE-host package candidate: {candidate} ({problem})")
                continue
            return candidate.resolve()
    return None


def detect_kind(root: Path) -> str | None:
    for path in root.rglob("*.json"):
        if "__MACOSX" in path.parts or path.name.startswith("._"):
            continue
        data = load_json(path)
        if not data:
            continue
        if data.get("kind") in {"olm_runtime_trace_result", "olm_runtime_trace_return"}:
            return "runtime-trace"
        if isinstance(data.get("runtime_trace_results"), list):
            return "runtime-trace"
        if isinstance(data.get("results"), list):
            return "runtime-trace"
        if data.get("request_id") and data.get("status"):
            return "runtime-trace"

    if list(root.rglob("AE_VALIDATION_EXACT_REPORT.json")):
        return "ae-pixel-validation"
    if list(root.rglob("*_return.zip")) and any("ae_pixel_validation_return" in path.parts for path in root.rglob("*_return.zip")):
        return "ae-pixel-validation"

    ae_jsons = [
        path
        for path in root.rglob("AE_VALIDATION_RESULT*.json")
        if "__MACOSX" not in path.parts and not path.name.startswith("._")
    ]
    for path in ae_jsons:
        data = load_json(path)
        if data and data.get("kind") == "olm_ae_host_validation_result":
            return "ae-host"

    for path in root.rglob("reference_manifest.json"):
        if "__MACOSX" in path.parts or path.name.startswith("._"):
            continue
        data = load_json(path)
        if data and data.get("kind") == "ae_effect_reference_manifest":
            return "win-reference"
    return None


def run(cmd: list[str], root: Path) -> int:
    print("$ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=root).returncode


def manifest_request_ids(manifest_path: Path) -> set[str]:
    data = load_json(manifest_path)
    if not data:
        return set()
    ids: set[str] = set()
    value = data.get("request_id")
    if isinstance(value, str) and value:
        ids.add(value)
    for item in data.get("requests", []):
        if isinstance(item, dict):
            value = item.get("request_id")
            if isinstance(value, str) and value:
                ids.add(value)
    for case in data.get("cases", []):
        if isinstance(case, dict):
            for key in ("request_id",):
                value = case.get(key)
                if isinstance(value, str) and value:
                    ids.add(value)
    return ids


def imported_reference_set_dir(args: argparse.Namespace, root: Path) -> Path:
    set_id = slug(args.set_id or args.source.stem, "returned_reference")
    return (root / args.dest_root / set_id).resolve()


def run_fresh_default_audits(args: argparse.Namespace, root: Path) -> int:
    request_id = "olm_fresh_instance_defaults_20260629"
    set_dir = imported_reference_set_dir(args, root)
    if not set_dir.exists():
        print(f"[INFO] no imported reference set dir for fresh-default audit: {set_dir}")
        return 0

    manifests = []
    for path in sorted(set_dir.rglob("reference_manifest.json")):
        if request_id in manifest_request_ids(path):
            manifests.append(path)
    if not manifests:
        print("[INFO] no fresh-default manifest found in imported set")
        return 0

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    failures = 0
    for manifest in manifests:
        stem = slug(manifest.parent.name or "fresh_defaults", "fresh_defaults")
        out_json = root / "refs" / "reports" / f"windows_fresh_defaults_audit_{stem}_{stamp}.json"
        out_md = root / "refs" / "reports" / f"windows_fresh_defaults_audit_{stem}_{stamp}.md"
        cmd = [
            sys.executable,
            "scripts/audit_windows_fresh_defaults.py",
            str(manifest),
            "--output-json",
            str(out_json),
            "--output-md",
            str(out_md),
        ]
        failures += run(cmd, root) != 0
    return 1 if failures else 0


def runtime_package_manifest(path: Path) -> dict | None:
    try:
        with zipfile.ZipFile(path) as archive:
            data = json.loads(archive.read("runtime_trace_package_manifest.json").decode("utf-8-sig"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def runtime_report_slug(package: Path | None) -> str:
    if package is None:
        return "runtime_trace"
    manifest = runtime_package_manifest(package)
    if manifest:
        profile = str(manifest.get("profile") or "").strip()
        if profile:
            return profile.replace("-", "_")
        actions = manifest.get("runtime_actions", [])
        if isinstance(actions, list):
            ids = [
                str(action.get("request_id"))
                for action in actions
                if isinstance(action, dict) and action.get("request_id")
            ]
            if len(ids) == 1:
                return ids[0].replace("-", "_")
    return package.stem.replace("-", "_")


def default_runtime_report_paths(root: Path, package: Path | None, report_dir: Path | None) -> tuple[Path, Path, Path]:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = runtime_report_slug(package)
    if report_dir is None:
        report_dir = root / "refs" / "reports"
    elif not report_dir.is_absolute():
        report_dir = root / report_dir
    summary_json = report_dir / f"runtime_trace_summary_{slug}_{stamp}.json"
    summary_md = report_dir / f"runtime_trace_summary_{slug}_{stamp}.md"
    comparison_dir = report_dir / "runtime_trace_comparisons" / f"{slug}_{stamp}"
    return summary_json, summary_md, comparison_dir


def run_ae_host(args: argparse.Namespace, root: Path) -> int:
    package = args.package.resolve() if args.package else None
    if package is None:
        search_dirs = [path.resolve() for path in args.package_search_dir] or [Path("/tmp")]
        package = find_latest_ae_package(root, search_dirs)
        if package is None:
            rendered_dirs = ", ".join(str(path) for path in search_dirs)
            return fail(f"could not auto-detect AE-host package in: {rendered_dirs}; pass --package", 2)
        print(f"[INFO] using AE-host package: {package}")
    if not package.exists():
        return fail(f"AE-host package not found: {package}", 2)
    cmd = [
        sys.executable,
        "scripts/verify_ae_host_return.py",
        str(package),
        str(args.source.resolve()),
    ]
    if args.require_all_pass:
        cmd.append("--require-all-pass")
    if args.require_all_pixel_requests:
        cmd.append("--require-all-pixel-requests")
    if args.run_dir:
        cmd.extend(["--run-dir", str(args.run_dir)])
    return run(cmd, root)


def request_id_from_zip(path: Path) -> str | None:
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                normalized = name.replace("\\", "/")
                if not normalized.endswith("request_manifest.json"):
                    continue
                data = json.loads(archive.read(name).decode("utf-8-sig"))
                if isinstance(data, dict) and isinstance(data.get("request_id"), str):
                    return data["request_id"]
    except Exception:
        return None
    return None


def runtime_package_manifest_request_ids(path: Path) -> set[str]:
    try:
        with zipfile.ZipFile(path) as archive:
            data = json.loads(archive.read("runtime_trace_package_manifest.json").decode("utf-8"))
    except Exception:
        return set()
    ids: set[str] = set()
    for action in data.get("runtime_actions", []):
        if isinstance(action, dict) and isinstance(action.get("request_id"), str):
            ids.add(str(action["request_id"]))
    return ids


def runtime_trace_request_ids_from_json(data: dict) -> list[str]:
    ids: list[str] = []
    direct = data.get("request_id")
    if isinstance(direct, str):
        ids.append(direct)
    for key in ("results", "runtime_trace_results", "requests_answered"):
        rows = data.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            status = str(row.get("status") or "").lower()
            if status == "diagnostic":
                continue
            if isinstance(row.get("request_id"), str):
                ids.append(str(row["request_id"]))
    seen: set[str] = set()
    unique: list[str] = []
    for request_id in ids:
        if request_id in seen:
            continue
        seen.add(request_id)
        unique.append(request_id)
    return unique


def find_matching_runtime_package(root: Path, source: Path) -> Path | None:
    package_dir = root / "refs" / "runtime_trace_packages"
    if not package_dir.is_dir():
        return None
    with tempfile.TemporaryDirectory(prefix="olm_runtime_package_match_") as tmp:
        try:
            materialized = extract_if_zip(source, Path(tmp) / "source")
        except Exception:
            return None
        request_ids: list[str] = []
        for path in sorted(materialized.rglob("*.json")) if materialized.is_dir() else [materialized]:
            if "__MACOSX" in path.parts or path.name.startswith("._"):
                continue
            data = load_json(path)
            if not isinstance(data, dict):
                continue
            request_ids.extend(runtime_trace_request_ids_from_json(data))
        request_ids = sorted(set(request_ids))
    if not request_ids:
        return None
    if len(request_ids) == 1:
        request_id = request_ids[0]
    else:
        source_name = source.name.lower()
        matched = next((rid for rid in request_ids if rid.lower() in source_name), None)
        if matched is None:
            return None
        request_id = matched
    candidates = sorted(package_dir.glob("*.zip"), key=lambda path: (path.stat().st_mtime, path.name), reverse=True)
    for package in candidates:
        try:
            with zipfile.ZipFile(package) as archive:
                data = json.loads(archive.read("runtime_trace_package_manifest.json").decode("utf-8"))
        except Exception:
            continue
        actions = data.get("runtime_actions", [])
        for action in actions:
            if isinstance(action, dict) and action.get("request_id") == request_id:
                return package
    return None


def find_ae_pixel_requests(root: Path, args: argparse.Namespace, materialized: Path) -> dict[str, Path]:
    search_dirs = [path.resolve() for path in args.ae_pixel_requests_dir]
    search_dirs.extend(
        [
            root / "refs" / "ae_pixel_validation_packages",
            materialized / "ae_pixel_validation",
        ]
    )
    requests: dict[str, Path] = {}
    for search_dir in search_dirs:
        if not search_dir.exists() or not search_dir.is_dir():
            continue
        for path in sorted(search_dir.glob("*.zip")):
            request_id = request_id_from_zip(path)
            if request_id and request_id not in requests:
                requests[request_id] = path.resolve()
    return requests


def ae_pixel_request_dirs(root: Path, args: argparse.Namespace, materialized: Path) -> list[Path]:
    search_dirs = [path.resolve() for path in args.ae_pixel_requests_dir]
    if not search_dirs:
        search_dirs.extend(
            [
                root / "refs" / "ae_pixel_validation_packages",
                materialized / "ae_pixel_validation",
                materialized / "requests",
            ]
        )
    dirs: list[Path] = []
    seen: set[Path] = set()
    for search_dir in search_dirs:
        if not search_dir.exists() or not search_dir.is_dir():
            continue
        if not any(path.is_file() and zipfile.is_zipfile(path) for path in search_dir.glob("*.zip")):
            continue
        resolved = search_dir.resolve()
        if resolved not in seen:
            dirs.append(resolved)
            seen.add(resolved)
    return dirs


def ae_pixel_return_id(path: Path) -> str | None:
    name = path.name
    if name.endswith("_return.zip"):
        return name[: -len("_return.zip")]
    if path.is_dir():
        return name
    return None


def find_ae_pixel_returns(materialized: Path) -> list[Path]:
    returns_dir = materialized / "ae_pixel_validation_return" / "returns"
    if returns_dir.exists():
        nested = sorted(path for path in returns_dir.glob("*_return.zip") if path.is_file())
        if nested:
            return nested
    roots = [
        path
        for path in materialized.rglob("AE_VALIDATION_RESULT.json")
        if "ae_pixel_validation_staging" not in path.parts
    ]
    return sorted(path.parent for path in roots)


def run_ae_pixel_validation(args: argparse.Namespace, root: Path, materialized: Path | None = None) -> int:
    with tempfile.TemporaryDirectory(prefix="olm_ae_pixel_intake_") as tmp:
        tmp_path = Path(tmp)
        materialized_root = materialized or extract_if_zip(args.source, tmp_path / "source")
        request_zips = find_ae_pixel_requests(root, args, materialized_root)
        return_paths = find_ae_pixel_returns(materialized_root)
        if not return_paths:
            request_dirs = ae_pixel_request_dirs(root, args, materialized_root)
            if request_dirs:
                run_root = (
                    args.run_dir.resolve()
                    if args.run_dir
                    else root / "refs" / "reports" / "ae_pixel_validation_intake"
                )
                failures = 0
                for request_dir in request_dirs:
                    label = request_dir.name or "requests"
                    cmd = [
                        sys.executable,
                        "scripts/verify_ae_pixel_validation_batch.py",
                        str(request_dir),
                        str(materialized_root),
                        "--run-dir",
                        str(run_root / label),
                    ]
                    failures += run(cmd, root) != 0
                if failures:
                    return 1
                print(f"[OK] AE pixel validation batch return verified with {len(request_dirs)} request dir(s)")
                print(f"run_dir={run_root}")
                return 0
            return fail("no AE pixel validation return zips/folders found", 2)
        if not request_zips:
            return fail("no AE pixel validation request zips found; pass --ae-pixel-requests-dir", 2)

        run_root = (
            args.run_dir.resolve()
            if args.run_dir
            else root / "refs" / "reports" / "ae_pixel_validation_intake"
        )
        failures = 0
        checks = 0
        for result_path in return_paths:
            request_id = ae_pixel_return_id(result_path)
            if not request_id:
                continue
            request_zip = request_zips.get(request_id)
            if request_zip is None:
                print(f"[SKIP] {request_id}: no matching request zip")
                continue
            cmd = [
                sys.executable,
                "scripts/verify_ae_pixel_validation_result.py",
                str(request_zip),
                str(result_path),
                "--run-dir",
                str(run_root / request_id),
            ]
            failures += run(cmd, root) != 0
            checks += 1
        if checks == 0:
            return fail("no AE pixel validation return matched a request zip", 2)
        if failures:
            return 1
        print(f"[OK] AE pixel validation return verified with {checks} check(s)")
        print(f"run_dir={run_root}")
        return 0


def run_win_reference(args: argparse.Namespace, root: Path) -> int:
    cmd = [
        sys.executable,
        "refs/scripts/import_and_check_win_reference.py",
        str(args.source.resolve()),
        "--dest-root",
        str(args.dest_root),
        "--requests-dir",
        str(args.requests_dir),
    ]
    if args.set_id:
        cmd.extend(["--set-id", args.set_id])
    if args.replace:
        cmd.append("--replace")
    if args.require_optional_render_sets:
        cmd.append("--require-optional-render-sets")
    if args.quick:
        cmd.append("--quick")
    if args.next_actions_json:
        cmd.extend(["--next-actions-json", str(args.next_actions_json)])
    if args.dispatch_dir:
        cmd.extend(["--dispatch-dir", str(args.dispatch_dir)])
    for request in args.request:
        cmd.extend(["--request", str(request)])
    rc = run(cmd, root)
    if rc != 0:
        return rc

    fresh_audit_rc = run_fresh_default_audits(args, root)
    if fresh_audit_rc != 0:
        return fresh_audit_rc
    if args.no_next_actions:
        return 0

    next_cmd = [
        sys.executable,
        "refs/scripts/next_reference_actions.py",
        "--requests",
        str(args.requests_dir),
        "--references",
        str(args.dest_root),
    ]
    return run(next_cmd, root)


def run_runtime_trace(args: argparse.Namespace, root: Path) -> int:
    package = args.runtime_package
    exact_package_match = False
    if package is None:
        package = find_matching_runtime_package(root, args.source.resolve())
        if package is None:
            package_dir = root / "refs" / "runtime_trace_packages"
            packages = sorted(package_dir.glob("*.zip"), key=lambda path: path.stat().st_mtime) if package_dir.exists() else []
            package = packages[-1] if packages else None
    elif not package.is_absolute():
        package = root / package
    if package and package.exists():
        with tempfile.TemporaryDirectory(prefix="olm_runtime_trace_match_") as tmp:
            try:
                materialized = extract_if_zip(args.source.resolve(), Path(tmp) / "source")
            except Exception:
                materialized = None
            source_request_ids: set[str] = set()
            if materialized is not None:
                for path in sorted(materialized.rglob("*.json")) if materialized.is_dir() else [materialized]:
                    if "__MACOSX" in path.parts or path.name.startswith("._"):
                        continue
                    data = load_json(path)
                    if isinstance(data, dict):
                        source_request_ids.update(runtime_trace_request_ids_from_json(data))
            exact_package_match = bool(source_request_ids & runtime_package_manifest_request_ids(package))

    summary_json = args.runtime_summary_json
    summary_md = args.runtime_summary_md
    comparison_dir = args.runtime_comparison_dir
    if summary_json is None:
        summary_json, default_summary_md, default_comparison_dir = default_runtime_report_paths(
            root,
            package,
            args.runtime_report_dir,
        )
        if summary_md is None:
            summary_md = default_summary_md
        if comparison_dir is None and not args.no_runtime_comparisons:
            comparison_dir = default_comparison_dir
    if comparison_dir is None and not args.no_runtime_comparisons:
        comparison_dir = root / "refs" / "reports" / "runtime_trace_comparisons"
    with tempfile.TemporaryDirectory(prefix="olm_runtime_trace_intake_") as tmp:
        tmp_dir = Path(tmp)
        tmp_summary_json = tmp_dir / "runtime_trace_summary.json"
        tmp_summary_md = tmp_dir / "runtime_trace_summary.md"
        cmd = [
            sys.executable,
            "scripts/verify_runtime_trace_return.py",
            str(args.source.resolve()),
        ]
        if package and exact_package_match:
            cmd.append("--require-all")
            cmd.extend(["--package", str(package)])
        else:
            cmd.extend(["--package", "none"])
        cmd.extend(["--summary-json", str(tmp_summary_json)])
        cmd.extend(["--summary-md", str(tmp_summary_md)])
        rc = run(cmd, root)

        if summary_json and tmp_summary_json.exists():
            existing = load_runtime_summary(summary_json) if summary_json.exists() else None
            incoming = load_runtime_summary(tmp_summary_json)
            if incoming is not None:
                merged = merge_runtime_summaries(existing, incoming)
                summary_json.parent.mkdir(parents=True, exist_ok=True)
                summary_json.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                if summary_md:
                    summary_md.parent.mkdir(parents=True, exist_ok=True)
                    summary_md.write_text(render_runtime_summary_markdown(merged), encoding="utf-8")
    if args.no_runtime_comparisons or summary_json is None:
        return rc
    compare_cmd = [
        sys.executable,
        "scripts/compare_runtime_trace_summary.py",
        "--runtime-summary-json",
        str(summary_json),
        "--output-dir",
        str(comparison_dir),
    ]
    compare_rc = run(compare_cmd, root)
    if rc != 0:
        return rc
    return compare_rc


def main() -> int:
    args = parse_args()
    root = repo_root()
    if not args.source.exists():
        return fail(f"source not found: {args.source}", 2)

    kind = args.kind
    if kind == "auto":
        with tempfile.TemporaryDirectory(prefix="olm_return_intake_") as tmp:
            try:
                materialized = extract_if_zip(args.source, Path(tmp) / "source")
            except Exception as exc:  # noqa: BLE001
                return fail(str(exc), 2)
            detected = detect_kind(materialized)
        if detected is None:
            return fail("could not detect return kind; pass --kind ae-host or --kind win-reference", 2)
        kind = detected
        print(f"[INFO] detected return kind: {kind}")

    if kind == "ae-host":
        return run_ae_host(args, root)
    if kind == "ae-pixel-validation":
        return run_ae_pixel_validation(args, root)
    if kind == "win-reference":
        return run_win_reference(args, root)
    if kind == "runtime-trace":
        return run_runtime_trace(args, root)
    return fail(f"unsupported kind: {kind}", 2)


if __name__ == "__main__":
    raise SystemExit(main())
