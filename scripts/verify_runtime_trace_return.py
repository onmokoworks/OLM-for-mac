#!/usr/bin/env python3
"""Verify and summarize returned OLM runtime trace facts."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


RUNTIME_KIND = "olm_runtime_trace_result"
RUNTIME_RETURN_KIND = "olm_runtime_trace_return"
DEFAULT_REQUIRED_IDS = [
    "radialblur_inner_runtime_trace_20260618",
    "kirakira_opencv455_primitive_fact_20260618",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Returned runtime trace result zip, folder, or JSON file.")
    parser.add_argument(
        "--package",
        type=Path,
        default=None,
        help=(
            "Runtime trace request package zip. If omitted, uses the newest "
            "refs/runtime_trace_packages/*.zip. Pass `none` to disable package matching."
        ),
    )
    parser.add_argument(
        "--require-all",
        action="store_true",
        help="Require every runtime action from the request package to have an answered result.",
    )
    parser.add_argument("--summary-json", type=Path, default=None, help="Write normalized summary JSON.")
    parser.add_argument("--summary-md", type=Path, default=None, help="Write a human-readable Markdown summary.")
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def display_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def archive_relative_path(source_root: Path, path: Path) -> str:
    try:
        return path.relative_to(source_root).as_posix()
    except ValueError:
        return path.name


def fail(message: str, code: int = 1) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return code


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def extract_if_zip(source: Path, dest: Path) -> Path:
    source = source.resolve()
    if source.is_dir() or source.suffix.lower() == ".json":
        return source
    if not source.exists() or not zipfile.is_zipfile(source):
        raise ValueError(f"source is neither a directory, JSON, nor zip: {source}")
    with zipfile.ZipFile(source) as archive:
        for member in archive.infolist():
            normalized = member.filename.replace("\\", "/")
            parts = [
                part
                for part in normalized.split("/")
                if part and part not in {".", ".."} and not part.startswith("._")
            ]
            if not parts or "__MACOSX" in parts:
                continue
            target = dest.joinpath(*parts)
            if member.is_dir() or normalized.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as src, target.open("wb") as dst:
                dst.write(src.read())
    visible = [
        child
        for child in dest.iterdir()
        if child.name != "__MACOSX" and not child.name.startswith("._")
    ]
    roots = [child for child in visible if child.is_dir()]
    return roots[0] if len(visible) == 1 and len(roots) == 1 else dest


def latest_package(root: Path) -> Path | None:
    package_dir = root / "refs" / "runtime_trace_packages"
    packages = sorted(package_dir.glob("*.zip"), key=lambda path: path.stat().st_mtime)
    return packages[-1] if packages else None


def runtime_action_ids(package: Path | None) -> list[str]:
    if package is None:
        return list(DEFAULT_REQUIRED_IDS)
    if not package.exists() or not zipfile.is_zipfile(package):
        raise ValueError(f"runtime trace package not found or not zip: {package}")
    with zipfile.ZipFile(package) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.replace("\\", "/").split("/")[-1] == "runtime_trace_package_manifest.json"
            and "__MACOSX" not in name.split("/")
            and not name.split("/")[-1].startswith("._")
        ]
        if len(names) != 1:
            raise ValueError(f"expected exactly one runtime trace package manifest, found {len(names)}")
        data = json.loads(archive.read(names[0]).decode("utf-8-sig"))
    actions = data.get("runtime_actions", [])
    ids = [str(action.get("request_id")) for action in actions if isinstance(action, dict) and action.get("request_id")]
    if not ids and isinstance(data.get("request_id"), str):
        ids = [str(data["request_id"])]
    return ids or list(DEFAULT_REQUIRED_IDS)


def is_trace_result(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    if data.get("kind") in {RUNTIME_KIND, RUNTIME_RETURN_KIND}:
        return True
    if data.get("request_id") and data.get("status"):
        return True
    return isinstance(data.get("runtime_trace_results"), list) or isinstance(data.get("results"), list)


def is_named_failure_result(path: Path, data: Any) -> bool:
    """Recognize fail-closed single-request returns that omit request_id."""
    result_names = {
        "RETURN_RUNTIME_TRACE.json",
        "RETURN_RUNTIME_TRACE_RESULT.json",
        "AE_RUNTIME_TRACE_RESULT.json",
    }
    basename = path.name.replace("\\", "/").rsplit("/", 1)[-1]
    return (
        basename in result_names
        and isinstance(data, dict)
        and bool(data.get("status"))
        and isinstance(data.get("failure"), dict)
    )


def find_result_jsons(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    candidates: list[Path] = []
    for path in sorted(root.rglob("*.json")):
        if "__MACOSX" in path.parts or path.name.startswith("._"):
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        if rel.startswith("request_package/") or "/request_package/" in rel:
            continue
        if path.name == "RETURN_RUNTIME_TRACE_TEMPLATE.json":
            continue
        try:
            data = load_json(path)
        except Exception:
            continue
        if is_trace_result(data) or is_named_failure_result(path, data):
            candidates.append(path)
    return candidates


def find_payload_file(source_root: Path, manifest_path: str) -> Path | None:
    normalized_target = manifest_path.replace("\\", "/")
    for path in source_root.rglob("*"):
        if not path.is_file():
            continue
        if str(path.relative_to(source_root)).replace("\\", "/") == normalized_target:
            return path
    return None


def read_answer_summary(source_root: Path, manifest_path: str | None) -> str:
    if not manifest_path:
        return ""
    payload = find_payload_file(source_root, manifest_path)
    if payload is None:
        return f"answer file not found: {manifest_path}"
    try:
        return payload.read_text(encoding="utf-8-sig").strip()
    except Exception as exc:  # noqa: BLE001
        return f"answer file unreadable: {manifest_path}: {exc}"


def normalize_result_status(status: Any, observations: Any) -> str:
    normalized = str(status or "answered").lower()
    if normalized == "answered" and isinstance(observations, dict):
        classification = observations.get("classification")
        if isinstance(classification, str) and classification.lower() == "answered_partial":
            return "answered_partial"
    return normalized


def normalize_results(
    data: dict[str, Any],
    source_path: Path,
    source_root: Path,
    default_request_id: str | None = None,
) -> list[dict[str, Any]]:
    if (
        default_request_id
        and data.get("status")
        and isinstance(data.get("failure"), dict)
        and not data.get("request_id")
    ):
        return [
            {
                "request_id": default_request_id,
                "status": normalize_result_status(data["status"], data),
                "summary": str(data.get("summary") or data["failure"].get("reason") or ""),
                "observations": data,
                "source_file": archive_relative_path(source_root, source_path),
            }
        ]

    if data.get("request_id") and data.get("status") and "results" not in data and "runtime_trace_results" not in data:
        observations = {
            key: value
            for key, value in data.items()
            if key not in {"request_id", "status", "summary", "answer", "notes"}
        }
        return [
            {
                "request_id": str(data["request_id"]),
                "status": normalize_result_status(data.get("status", "answered"), observations),
                "summary": str(data.get("summary") or data.get("answer") or data.get("notes") or ""),
                "observations": observations,
                "source_file": archive_relative_path(source_root, source_path),
            }
        ]

    if data.get("kind") == RUNTIME_RETURN_KIND and isinstance(data.get("requests_answered"), list):
        normalized: list[dict[str, Any]] = []
        for index, row in enumerate(data["requests_answered"], start=1):
            if not isinstance(row, dict):
                raise ValueError(f"{source_path}: requests_answered #{index} must be an object")
            request_id = row.get("request_id")
            if not request_id:
                raise ValueError(f"{source_path}: requests_answered #{index} missing request_id")
            status = str(row.get("status", "answered")).lower()
            answer_file = row.get("answer_file")
            evidence_files = row.get("evidence_files", [])
            normalized.append(
                {
                    "request_id": str(request_id),
                    "status": status,
                    "summary": read_answer_summary(source_root, str(answer_file) if answer_file else None),
                    "observations": {
                        "answer_file": answer_file or "",
                        "evidence_files": evidence_files if isinstance(evidence_files, list) else [],
                    },
                    "source_file": archive_relative_path(source_root, source_path),
                }
            )
        return normalized

    raw_results = data.get("results", data.get("runtime_trace_results", []))
    if not isinstance(raw_results, list):
        raise ValueError(f"{source_path}: results must be a list")
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(raw_results, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"{source_path}: result #{index} must be an object")
        request_id = row.get("request_id") or data.get("request_id") or default_request_id
        if not request_id:
            raise ValueError(f"{source_path}: result #{index} missing request_id")
        request_id = str(request_id)
        if default_request_id and request_id == f"olm_runtime_trace_{default_request_id}":
            request_id = default_request_id
        observations = row.get("observations", row.get("values", row.get("fact")))
        if observations is None:
            observations = {
                key: value
                for key, value in row.items()
                if key not in {"request_id", "status", "summary", "answer", "notes"}
            }
        status = normalize_result_status(row.get("status", data.get("status", "answered")), observations)
        summary = row.get("summary") or row.get("answer") or row.get("notes") or ""
        normalized.append(
            {
                "request_id": str(request_id),
                "status": status,
                "summary": str(summary),
                "observations": observations,
                "source_file": archive_relative_path(source_root, source_path),
            }
        )
    return normalized


def build_summary(root: Path, source_root: Path, package: Path | None) -> dict[str, Any]:
    required_ids = runtime_action_ids(package)
    default_request_id = required_ids[0] if len(required_ids) == 1 else None
    result_files = find_result_jsons(source_root)
    if not result_files:
        raise ValueError("no runtime trace result JSON found")
    results: list[dict[str, Any]] = []
    for path in result_files:
        data = load_json(path)
        if not isinstance(data, dict):
            continue
        results.extend(normalize_results(data, path, source_root, default_request_id))

    by_id: dict[str, list[dict[str, Any]]] = {}
    for row in results:
        by_id.setdefault(row["request_id"], []).append(row)

    required = []
    for request_id in required_ids:
        rows = by_id.get(request_id, [])
        answered = [
            row
            for row in rows
            if row["status"] in {"answered", "ok", "done", "complete", "completed"}
            or row["status"].startswith("answered")
        ]
        required.append(
            {
                "request_id": request_id,
                "count": len(rows),
                "answered": bool(answered),
                "statuses": sorted({row["status"] for row in rows}),
            }
        )
    extra_ids = sorted(set(by_id) - set(required_ids))
    return {
        "kind": "olm_runtime_trace_return_summary",
        "schema": 1,
        "source_root": "runtime-trace-return",
        "package": display_path(root, package) if package else None,
        "required": required,
        "extra_request_ids": extra_ids,
        "results": results,
    }


def format_observations(value: Any) -> str:
    if isinstance(value, dict):
        lines = []
        for key in sorted(value):
            item = value[key]
            if isinstance(item, (dict, list)):
                rendered = json.dumps(item, ensure_ascii=False, sort_keys=True)
            else:
                rendered = str(item)
            lines.append(f"  - {key}: {rendered}")
        return "\n".join(lines) if lines else "  - none"
    if isinstance(value, list):
        return "\n".join(f"  - {json.dumps(item, ensure_ascii=False, sort_keys=True)}" for item in value) or "  - none"
    return f"  - {value}"


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# OLM Runtime Trace Return Summary",
        "",
        f"- Source: {summary.get('source_root', '-')}",
        f"- Package: {summary.get('package') or '-'}",
        "",
        "## Required Requests",
        "",
        "| Request | Answered | Count | Statuses |",
        "| --- | --- | ---: | --- |",
    ]
    for row in summary.get("required", []):
        answered = "yes" if row.get("answered") else "no"
        statuses = ", ".join(row.get("statuses") or []) or "-"
        lines.append(f"| {row.get('request_id', '-')} | {answered} | {row.get('count', 0)} | {statuses} |")

    extra = summary.get("extra_request_ids") or []
    if extra:
        lines.extend(["", "## Extra Request IDs", ""])
        lines.extend(f"- {request_id}" for request_id in extra)

    lines.extend(["", "## Results", ""])
    for row in summary.get("results", []):
        lines.extend(
            [
                f"### {row.get('request_id', '-')}",
                "",
                f"- Status: {row.get('status', '-')}",
                f"- Source file: {row.get('source_file', '-')}",
                f"- Summary: {row.get('summary') or '-'}",
                "",
                "Observations:",
                "",
                format_observations(row.get("observations", {})),
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    if not args.source.exists():
        return fail(f"source not found: {args.source}", 2)
    package = args.package
    package_explicitly_disabled = package is not None and str(package).lower() in {"none", "-"}
    if package_explicitly_disabled:
        package = None
    if package is None and not package_explicitly_disabled:
        package = latest_package(root)
    elif package is not None and not package.is_absolute():
        package = root / package

    with tempfile.TemporaryDirectory(prefix="olm_runtime_trace_return_") as tmp:
        try:
            source_root = extract_if_zip(args.source, Path(tmp) / "source")
            summary = build_summary(root, source_root, package)
        except Exception as exc:  # noqa: BLE001
            return fail(str(exc), 2)

    missing = [row for row in summary["required"] if not row["answered"]]
    for row in summary["required"]:
        mark = "OK" if row["answered"] else "MISS"
        print(f"[{mark}] {row['request_id']} count={row['count']} statuses={','.join(row['statuses']) or '-'}")
    if summary["extra_request_ids"]:
        print("[INFO] extra request ids: " + ", ".join(summary["extra_request_ids"]))

    if args.summary_json:
        output = args.summary_json if args.summary_json.is_absolute() else root / args.summary_json
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"summary_json={output}")
    if args.summary_md:
        output = args.summary_md if args.summary_md.is_absolute() else root / args.summary_md
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_markdown(summary), encoding="utf-8")
        print(f"summary_md={output}")

    if args.require_all and missing:
        return fail("missing answered runtime trace result(s): " + ", ".join(row["request_id"] for row in missing))
    print("[OK] runtime trace return verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
