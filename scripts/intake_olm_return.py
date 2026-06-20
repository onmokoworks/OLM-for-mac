#!/usr/bin/env python3
"""Auto-route returned OLM artifacts to the right verifier/importer."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


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
    if rc != 0 or args.no_next_actions:
        return rc

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
    if package is None:
        package = root / "refs" / "runtime_trace_packages"
        packages = sorted(package.glob("*.zip"), key=lambda path: path.stat().st_mtime) if package.exists() else []
        package = packages[-1] if packages else None
    elif not package.is_absolute():
        package = root / package

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
    cmd = [
        sys.executable,
        "scripts/verify_runtime_trace_return.py",
        str(args.source.resolve()),
        "--require-all",
    ]
    if package:
        cmd.extend(["--package", str(package)])
    if summary_json:
        cmd.extend(["--summary-json", str(summary_json)])
    if summary_md:
        cmd.extend(["--summary-md", str(summary_md)])
    rc = run(cmd, root)
    if rc != 0:
        return rc
    if args.no_runtime_comparisons or summary_json is None:
        return 0
    compare_cmd = [
        sys.executable,
        "scripts/compare_runtime_trace_summary.py",
        "--runtime-summary-json",
        str(summary_json),
        "--output-dir",
        str(comparison_dir),
    ]
    return run(compare_cmd, root)


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
