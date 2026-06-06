#!/usr/bin/env python3
"""Auto-route returned OLM artifacts to the right verifier/importer."""

from __future__ import annotations

import argparse
import json
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
        choices=("auto", "ae-host", "win-reference"),
        default="auto",
        help="Artifact kind. auto detects from JSON contents.",
    )
    parser.add_argument(
        "--package",
        type=Path,
        default=Path("/tmp/olm_port_handoff_20260606.zip"),
        help="Mac plug-in or OLM handoff package for AE-host returns.",
    )
    parser.add_argument("--require-all-pass", action="store_true", help="AE-host: require all plugins to pass.")
    parser.add_argument(
        "--require-all-pixel-requests",
        action="store_true",
        help="AE-host: require every packaged pixel request to have a returned PNG group.",
    )
    parser.add_argument("--run-dir", type=Path, default=None, help="AE-host pixel report directory.")
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
        archive.extractall(dest)
    visible = [
        child
        for child in dest.iterdir()
        if child.name != "__MACOSX" and not child.name.startswith("._")
    ]
    roots = [child for child in visible if child.is_dir()]
    return roots[0] if len(visible) == 1 and len(roots) == 1 else dest


def load_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def detect_kind(root: Path) -> str | None:
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


def run_ae_host(args: argparse.Namespace, root: Path) -> int:
    package = args.package.resolve()
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
    if kind == "win-reference":
        return run_win_reference(args, root)
    return fail(f"unsupported kind: {kind}", 2)


if __name__ == "__main__":
    raise SystemExit(main())
