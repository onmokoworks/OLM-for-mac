#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import list_olm_return_candidates


RETURN_KINDS = {
    "runtime-trace-return",
    "win-reference-return",
    "ae-host-return",
    "ae-pixel-validation-return",
    "windows-action-bundle-return",
    "olmblur-standalone-witness",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--share-root",
        type=Path,
        default=Path("/Volumes/onmk/olm_pr"),
        help="Shared exchange root. Defaults to /Volumes/onmk/olm_pr",
    )
    parser.add_argument(
        "--kind",
        choices=(
            "auto",
            "runtime-trace-return",
            "win-reference-return",
            "ae-host-return",
            "ae-pixel-validation-return",
            "windows-action-bundle-return",
            "olmblur-standalone-witness",
        ),
        default="auto",
        help="Optional kind filter. Defaults to auto (any recognized return kind).",
    )
    parser.add_argument(
        "--intake-arg",
        action="append",
        default=[],
        help="Extra argument appended to the intake_olm_return.py invocation. May be repeated.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the chosen return and intake command without running it.",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Do not archive files from share/new into share/old after a successful intake.",
    )
    return parser.parse_args()


def choose_return(new_dir: Path, kind_filter: str) -> dict:
    rows = [list_olm_return_candidates.build_row(path) for path in list_olm_return_candidates.candidate_paths([new_dir])]
    filtered = [row for row in rows if row.get("kind") in RETURN_KINDS]
    if kind_filter != "auto":
        filtered = [row for row in filtered if row.get("kind") == kind_filter]
    if not filtered:
        raise SystemExit(f"no ingestible Windows return found in {new_dir}")
    return max(filtered, key=lambda row: float(row.get("mtime", 0)))


def build_intake_command(root: Path, row: dict, extra_args: list[str]) -> list[str]:
    suggested = row.get("suggested_command", "")
    if not isinstance(suggested, str) or not suggested:
        raise SystemExit(f"no suggested intake command for kind={row.get('kind')}")
    cmd = shlex.split(suggested)
    if not cmd:
        raise SystemExit(f"failed to parse suggested command: {suggested}")
    if cmd[0] == "python3":
        cmd[0] = sys.executable
    elif cmd[0] == "python":
        cmd[0] = sys.executable
    cmd.extend(extra_args)
    return cmd


def extract_flag_value(cmd: list[str], flag: str) -> str | None:
    found: str | None = None
    for index, part in enumerate(cmd):
        if part == flag and index + 1 < len(cmd):
            found = cmd[index + 1]
        if part.startswith(flag + "="):
            found = part.split("=", 1)[1]
    return found


def archive_paths(paths: list[Path], old_dir: Path) -> list[Path]:
    timestamp = subprocess.run(
        ["date", "+%Y%m%d_%H%M%S"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    archived: list[Path] = []
    for path in sorted({path.resolve() for path in paths}):
        if not path.is_file():
            continue
        target = old_dir / f"{timestamp}__{path.name}"
        shutil.move(str(path), str(target))
        archived.append(target)
    return archived


def archive_targets_for_chosen(new_dir: Path, chosen_path: Path) -> list[Path]:
    targets = [chosen_path]
    stem_prefix = chosen_path.stem + "__"
    name_prefix = chosen_path.name + "__"
    for path in sorted(new_dir.iterdir()):
        if not path.is_file() or path.resolve() == chosen_path.resolve():
            continue
        if path.name.startswith(stem_prefix) or path.name.startswith(name_prefix):
            targets.append(path)
    return targets


def package_manifest(path: Path) -> dict | None:
    try:
        with zipfile.ZipFile(path) as archive:
            name = next(
                (
                    member
                    for member in archive.namelist()
                    if member.replace("\\", "/").endswith("runtime_trace_package_manifest.json")
                ),
                None,
            )
            if name is None:
                return None
            data = json.loads(archive.read(name).decode("utf-8-sig"))
    except Exception:
        return None
    return data if isinstance(data, dict) and data.get("kind") == "olm_runtime_trace_request_package" else None


def extract_if_zip(source: Path, dest: Path) -> Path:
    source = source.resolve()
    if source.is_dir():
        return source
    if not source.exists() or not zipfile.is_zipfile(source):
        raise ValueError(f"not a directory or zip: {source}")
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
    visible_children = [
        path
        for path in dest.iterdir()
        if path.name != "__MACOSX" and not path.name.startswith("._")
    ]
    roots = [path for path in visible_children if path.is_dir()]
    return roots[0] if len(visible_children) == 1 and len(roots) == 1 else dest


def default_report_paths(root: Path, kind: str, chosen_path: Path) -> tuple[Path, Path]:
    stem = chosen_path.stem if chosen_path.suffix else chosen_path.name
    report_dir = root / "refs" / "reports"
    suffix = {
        "ae-host-return": "ae_host_summary",
        "win-reference-return": "win_reference_summary",
    }.get(kind, "summary")
    return (
        report_dir / f"{stem}_{suffix}.json",
        report_dir / f"{stem}_{suffix}.md",
    )


def bundle_return_pairs(bundle_root: Path) -> list[tuple[Path, Path]]:
    package_dir = next((path for path in bundle_root.rglob("runtime_trace") if path.is_dir()), None)
    returns_dir = next((path for path in bundle_root.rglob("runtime_trace_returns") if path.is_dir()), None)
    if package_dir is not None and returns_dir is not None:
        package_by_stem = {path.stem: path for path in sorted(package_dir.glob("*.zip"))}
        pairs: list[tuple[Path, Path]] = []
        for returned in sorted(returns_dir.glob("*.zip")):
            stem = returned.stem
            request_stem = stem
            if request_stem.endswith("_return_windows"):
                request_stem = request_stem[: -len("_return_windows")]
            if request_stem.endswith("_windows_partial_return"):
                request_stem = request_stem[: -len("_windows_partial_return")]
            package = package_by_stem.get(request_stem)
            if package is None:
                raise ValueError(f"no matching runtime trace package for bundled return: {returned.name}")
            pairs.append((returned, package))
        if not pairs:
            raise ValueError("bundle return did not include any runtime_trace_returns/*.zip")
        return pairs

    raise ValueError("bundle return is missing runtime_trace or runtime_trace_returns directories")


def load_request_id_from_manifest(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    actions = data.get("runtime_actions")
    if not isinstance(actions, list):
        return None
    for action in actions:
        if isinstance(action, dict) and isinstance(action.get("request_id"), str):
            return str(action["request_id"])
    return None


def load_request_id_from_return(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    for key in ("results", "runtime_trace_results"):
        rows = data.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("request_id"), str):
                return str(row["request_id"])
    return None


def collect_request_ids_from_return(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    request_ids: list[str] = []
    seen: set[str] = set()
    for key in ("results", "runtime_trace_results"):
        rows = data.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            request_id = row.get("request_id")
            if isinstance(request_id, str) and request_id not in seen:
                seen.add(request_id)
                request_ids.append(request_id)
    return request_ids


def find_repo_runtime_package(root: Path, request_id: str) -> Path | None:
    package_dir = root / "refs" / "runtime_trace_packages"
    candidates = sorted(
        package_dir.glob("*.zip"),
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )
    for package in candidates:
        manifest = package_manifest(package)
        if not isinstance(manifest, dict):
            continue
        for action in manifest.get("runtime_actions", []):
            if isinstance(action, dict) and action.get("request_id") == request_id:
                return package
    return None


def resolve_runtime_package_for_return(root: Path, source: Path) -> Path | None:
    with tempfile.TemporaryDirectory(prefix="olm_return_pkg_resolve_") as tmp:
        extracted = extract_if_zip(source, Path(tmp) / "return")
        result_jsons = sorted(extracted.rglob("RETURN_RUNTIME_TRACE_RESULT.json"))
        if not result_jsons:
            return None
        request_ids: list[str] = []
        seen: set[str] = set()
        for result_json in result_jsons:
            for request_id in collect_request_ids_from_return(result_json):
                if request_id not in seen:
                    seen.add(request_id)
                    request_ids.append(request_id)
        if len(request_ids) != 1:
            return None
        return find_repo_runtime_package(root, request_ids[0])


def nested_folder_bundle_return_pairs(root: Path, bundle_root: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for child in sorted(bundle_root.iterdir()):
        if not child.is_dir():
            continue
        result_json = child / "RETURN_RUNTIME_TRACE_RESULT.json"
        manifest_json = child / "request_package" / "runtime_trace_package_manifest.json"
        if not result_json.is_file() or not manifest_json.is_file():
            continue
        request_id = load_request_id_from_manifest(manifest_json) or load_request_id_from_return(result_json)
        if not request_id:
            raise ValueError(f"could not determine request_id for bundled return folder: {child}")
        package = find_repo_runtime_package(root, request_id)
        if package is None:
            raise ValueError(f"no matching repo runtime trace package for bundled return folder: {child.name} ({request_id})")
        pairs.append((child, package))
    return pairs


def intake_windows_action_bundle_return(root: Path, source: Path, env: dict[str, str]) -> int:
    with tempfile.TemporaryDirectory(prefix="olm_windows_bundle_return_") as tmp:
        bundle_root = extract_if_zip(source, Path(tmp) / "bundle")
        bundle_stem = source.stem if source.suffix else source.name
        report_dir = root / "refs" / "reports" / "runtime_trace_bundle" / bundle_stem
        report_dir.mkdir(parents=True, exist_ok=True)
        try:
            pairs = bundle_return_pairs(bundle_root)
        except ValueError:
            pairs = nested_folder_bundle_return_pairs(root, bundle_root)
        if not pairs:
            raise ValueError("bundle return did not include any recognized runtime return/package pairs")
        for returned, package in pairs:
            before_summaries = set(report_dir.glob("runtime_trace_summary_*.json"))
            cmd = [
                sys.executable,
                str(root / "scripts" / "intake_olm_return.py"),
                str(returned),
                "--runtime-package",
                str(package),
                "--runtime-report-dir",
                str(report_dir),
            ]
            proc = subprocess.run(
                cmd,
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
            print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
            if proc.returncode != 0:
                return proc.returncode
            after_summaries = set(report_dir.glob("runtime_trace_summary_*.json"))
            new_summaries = sorted(after_summaries - before_summaries, key=lambda path: path.stat().st_mtime)
            if new_summaries:
                summary_proc = subprocess.run(
                    [
                        sys.executable,
                        str(root / "scripts" / "summarize_runtime_trace_proof_lanes.py"),
                        "--runtime-summary-json",
                        str(new_summaries[-1]),
                    ],
                    cwd=root,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=env,
                )
                print(summary_proc.stdout, end="" if summary_proc.stdout.endswith("\n") else "\n")
                if summary_proc.returncode != 0:
                    return summary_proc.returncode
        print(f"[OK] processed bundled runtime returns into {report_dir}")
    return 0


def main() -> int:
    args = parse_args()
    root = repo_root()
    share_root = args.share_root
    new_dir = share_root / "new"
    old_dir = share_root / "old"

    if not new_dir.is_dir():
        raise SystemExit(f"share/new not available: {new_dir}")
    old_dir.mkdir(parents=True, exist_ok=True)

    chosen = choose_return(new_dir, args.kind)
    cmd = build_intake_command(root, chosen, args.intake_arg)
    if chosen.get("kind") == "runtime-trace-return" and extract_flag_value(cmd, "--runtime-package") is None:
        resolved_package = resolve_runtime_package_for_return(root, Path(str(chosen["path"])))
        if resolved_package is not None:
            cmd.extend(["--runtime-package", str(resolved_package)])
    if chosen.get("kind") == "win-reference-return" and extract_flag_value(cmd, "--next-actions-json") is None:
        auto_next_actions = root / "refs" / "reports" / f"{Path(str(chosen['path'])).stem}_next_actions.json"
        cmd.extend(["--next-actions-json", str(auto_next_actions)])

    if args.dry_run:
        print(f"chosen: {chosen['kind']} {chosen['path']}")
        print("command:")
        if chosen.get("kind") == "windows-action-bundle-return":
            print("python3 scripts/intake_latest_windows_return_from_share.py --share-root ... --kind windows-action-bundle-return")
        else:
            print(" ".join(shlex.quote(part) for part in cmd))
        return 0

    env = os.environ.copy()
    if chosen.get("kind") == "windows-action-bundle-return":
        rc = intake_windows_action_bundle_return(root, Path(str(chosen["path"])), env)
        if rc != 0:
            return rc
        if not args.no_archive:
            archived = archive_paths(archive_targets_for_chosen(new_dir, Path(str(chosen["path"]))), old_dir)
            for path in archived:
                print(f"[INFO] archived after intake: {path}")
        return 0

    proc = subprocess.run(
        cmd,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.returncode != 0:
        return proc.returncode

    if chosen.get("kind") == "runtime-trace-return":
        summary_json_arg = extract_flag_value(cmd, "--runtime-summary-json")
        summary_json = Path(summary_json_arg) if summary_json_arg else (root / "refs" / "reports" / "runtime_trace_summary.json")
        if not summary_json.is_absolute():
            summary_json = root / summary_json
        if summary_json.exists():
            summary_proc = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "summarize_runtime_trace_proof_lanes.py"),
                    "--runtime-summary-json",
                    str(summary_json),
                ],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
            print(summary_proc.stdout, end="" if summary_proc.stdout.endswith("\n") else "\n")
            if summary_proc.returncode != 0:
                return summary_proc.returncode

    if chosen.get("kind") == "ae-host-return":
        output_json, output_md = default_report_paths(root, "ae-host-return", Path(str(chosen["path"])))
        summary_cmd = [
            sys.executable,
            str(root / "scripts" / "summarize_ae_host_return.py"),
            str(chosen["path"]),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
        package_arg = extract_flag_value(cmd, "--package")
        if package_arg:
            summary_cmd.extend(["--package", str(package_arg)])
        summary_proc = subprocess.run(
            summary_cmd,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
        )
        print(summary_proc.stdout, end="" if summary_proc.stdout.endswith("\n") else "\n")
        if summary_proc.returncode != 0:
            return summary_proc.returncode

    if chosen.get("kind") == "win-reference-return":
        next_actions_arg = extract_flag_value(cmd, "--next-actions-json")
        set_id_arg = extract_flag_value(cmd, "--set-id")
        dest_root_arg = extract_flag_value(cmd, "--dest-root")
        imported_set_dir = Path(dest_root_arg) if dest_root_arg else (root / "refs" / "win_references")
        if not imported_set_dir.is_absolute():
            imported_set_dir = root / imported_set_dir
        imported_set_dir = imported_set_dir / (set_id_arg or Path(str(chosen["path"])).stem)
        output_json, output_md = default_report_paths(root, "win-reference-return", Path(str(chosen["path"])))
        summary_cmd = [
            sys.executable,
            str(root / "scripts" / "summarize_win_reference_return.py"),
            str(chosen["path"]),
            "--imported-set-dir",
            str(imported_set_dir),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
        if next_actions_arg:
            summary_cmd.extend(["--next-actions-json", str(next_actions_arg)])
        summary_proc = subprocess.run(
            summary_cmd,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
        )
        print(summary_proc.stdout, end="" if summary_proc.stdout.endswith("\n") else "\n")
        if summary_proc.returncode != 0:
            return summary_proc.returncode
        summary_data = load_json(output_json)
        if isinstance(summary_data, dict):
            source_summary = summary_data.get("source_summary")
            request_ids = source_summary.get("request_ids") if isinstance(source_summary, dict) else None
            print(
                "[INFO] win-reference quality: "
                f"{summary_data.get('reference_quality', 'unknown')} "
                f"(requests={request_ids or []}, "
                f"float_preserving={source_summary.get('float_preserving_present') if isinstance(source_summary, dict) else None}, "
                f"preferred_exr={source_summary.get('preferred_exr_present') if isinstance(source_summary, dict) else None})"
            )
            reason = summary_data.get("reference_quality_reason")
            if isinstance(reason, str) and reason:
                print(f"[INFO] win-reference quality reason: {reason}")

    if not args.no_archive:
        archived = archive_paths(archive_targets_for_chosen(new_dir, Path(str(chosen["path"]))), old_dir)
        for path in archived:
            print(f"[INFO] archived after intake: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
