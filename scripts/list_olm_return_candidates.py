#!/usr/bin/env python3
"""List likely OLM return/package artifacts and suggested next commands."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any


RETURN_EXTENSIONS = {".zip"}
MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".hdr", ".bmp"}
FLOAT_PRESERVING_EXTENSIONS = {".exr", ".tif", ".tiff", ".hdr"}
RUNTIME_RESULT_FILENAMES = {
    "RETURN_RUNTIME_TRACE_RESULT.json",
    "RETURN_RUNTIME_TRACE.json",
    "AE_RUNTIME_TRACE_RESULT.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or directories to inspect. Defaults to ~/Downloads and /tmp.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--limit", type=int, default=40, help="Maximum candidates to print.")
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def candidate_paths(paths: list[Path]) -> list[Path]:
    roots = paths or [Path.home() / "Downloads", Path("/tmp")]
    candidates: list[Path] = []
    for root in roots:
        root = root.expanduser()
        if root.is_file():
            candidates.append(root)
        elif root.is_dir():
            candidates.extend(
                path
                for path in root.iterdir()
                if path.is_file() and path.suffix.lower() in RETURN_EXTENSIONS
            )
    return sorted(set(candidates), key=lambda path: path.stat().st_mtime, reverse=True)


def clean_zip_names(path: Path) -> list[str]:
    try:
        with zipfile.ZipFile(path) as archive:
            return [
                name.replace("\\", "/")
                for name in archive.namelist()
                if "__MACOSX" not in Path(name.replace("\\", "/")).parts
                and not any(part.startswith("._") for part in Path(name.replace("\\", "/")).parts)
            ]
    except Exception:
        return []


def is_clean_zip_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    parts = Path(normalized).parts
    return "__MACOSX" not in parts and not any(part.startswith("._") for part in parts)


def read_zip_json(path: Path, name: str) -> dict[str, Any] | None:
    try:
        with zipfile.ZipFile(path) as archive:
            member_name = next(
                (member for member in archive.namelist() if member.replace("\\", "/") == name),
                name,
            )
            data = json.loads(archive.read(member_name).decode("utf-8-sig"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def classify_zip(path: Path) -> tuple[str, list[str]]:
    try:
        archive = zipfile.ZipFile(path)
    except Exception:
        return ("unknown", [])
    with archive:
        raw_names = archive.namelist()
        member_by_clean_name = {name.replace("\\", "/"): name for name in raw_names}
        names = [
            name.replace("\\", "/")
            for name in raw_names
            if is_clean_zip_name(name)
        ]
        json_cache: dict[str, dict[str, Any] | None] = {}

        def read_json(name: str) -> dict[str, Any] | None:
            if name not in json_cache:
                try:
                    member_name = member_by_clean_name.get(name, name)
                    data = json.loads(archive.read(member_name).decode("utf-8-sig"))
                except Exception:
                    data = None
                json_cache[name] = data if isinstance(data, dict) else None
            return json_cache[name]

        return classify_zip_names(names, read_json)


def classify_zip_names(names: list[str], read_json: Any) -> tuple[str, list[str]]:
    if not names:
        return ("unknown", [])

    hints: list[str] = []
    runtime_result_names = [
        name for name in names if Path(name).name in RUNTIME_RESULT_FILENAMES
    ]
    runtime_manifest_names = [
        name
        for name in names
        if Path(name).name == "runtime_trace_package_manifest.json"
    ]
    if len(runtime_result_names) > 1 and runtime_manifest_names:
        hint = (
            f"contains {len(runtime_result_names)} runtime trace result files "
            f"and {len(runtime_manifest_names)} runtime_trace_package_manifest.json files"
        )
        return ("windows-action-bundle-return", [hint])
    for name in names:
        base = Path(name).name
        if base not in {"WITNESS_RESULT.json", "README_WITNESS.md"}:
            continue
        witness_json_name = next((item for item in names if Path(item).name == "WITNESS_RESULT.json"), None)
        if witness_json_name is None:
            continue
        data = read_json(witness_json_name)
        plugin = data.get("plugin") if data else None
        case_id = data.get("case") if data else None
        bit_depth = data.get("bit_depth") if data else None
        if plugin == "OLMBlur":
            hint = f"{witness_json_name}: standalone witness"
            if case_id:
                hint += f" case={case_id}"
            if bit_depth:
                hint += f" bit_depth={bit_depth}"
            return ("olmblur-standalone-witness", [hint])
    for name in names:
        if Path(name).name != "windows_action_bundle_manifest.json":
            continue
        data = read_json(name)
        kind = data.get("kind") if data else None
        has_runtime_returns = any("/runtime_trace_returns/" in f"/{item}" and item.endswith(".zip") for item in names)
        if kind == "olm_windows_action_bundle" and has_runtime_returns:
            return ("windows-action-bundle-return", [f"{name}: {kind}"])
    for name in names:
        if Path(name).name not in RUNTIME_RESULT_FILENAMES:
            continue
        data = read_json(name)
        kind = data.get("kind") if data else None
        if (
            kind == "olm_runtime_trace_result"
            or (data and isinstance(data.get("runtime_trace_results"), list))
            or (data and isinstance(data.get("results"), list))
            or (
                data
                and isinstance(data.get("request_id"), str)
                and isinstance(data.get("status"), str)
            )
        ):
            return ("runtime-trace-return", [f"{name}: {kind or 'runtime_trace_results'}"])
    for name in names:
        if Path(name).name != "runtime_trace_package_manifest.json":
            continue
        data = read_json(name)
        kind = data.get("kind") if data else None
        if kind == "olm_runtime_trace_request_package":
            has_result = any(
                Path(item).name in RUNTIME_RESULT_FILENAMES
                for item in names
            )
            if not has_result:
                return ("runtime-trace-request-package", [f"{name}: {kind}"])
    if any(name.endswith("AE_VALIDATION_EXACT_REPORT.json") for name in names):
        return ("ae-pixel-validation-return", ["contains AE_VALIDATION_EXACT_REPORT.json"])
    if any("/ae_pixel_validation_return/returns/" in f"/{name}" and name.endswith("_return.zip") for name in names):
        return ("ae-pixel-validation-return", ["contains nested AE pixel return zips"])
    if any(name.endswith("AE_PIXEL_VALIDATION_REQUEST.md") for name in names):
        return ("ae-pixel-validation-request", ["contains AE_PIXEL_VALIDATION_REQUEST.md"])
    for name in names:
        if Path(name).name != "bundle_manifest.json":
            continue
        data = read_json(name)
        kind = data.get("kind") if data else None
        if kind == "olm_ae_pixel_validation_bundle":
            request_count = data.get("request_count") if data else None
            hint = f"{name}: {kind}"
            if request_count is not None:
                hint += f" ({request_count} requests)"
            return ("ae-pixel-validation-bundle", [hint])
    for name in names:
        if Path(name).name != "windows_action_bundle_manifest.json":
            continue
        data = read_json(name)
        kind = data.get("kind") if data else None
        if kind == "olm_windows_action_bundle":
            return ("windows-action-bundle", [f"{name}: {kind}"])
    for name in names:
        if not name.endswith(".json"):
            continue
        if Path(name).name == "RETURN_RUNTIME_TRACE_TEMPLATE.json":
            continue
        data = read_json(name)
        kind = data.get("kind") if data else None
        if (
            kind == "olm_runtime_trace_result"
            or (data and isinstance(data.get("runtime_trace_results"), list))
            or (data and isinstance(data.get("results"), list) and Path(name).name in RUNTIME_RESULT_FILENAMES)
            or (
                data
                and Path(name).name in RUNTIME_RESULT_FILENAMES
                and isinstance(data.get("request_id"), str)
                and isinstance(data.get("status"), str)
            )
        ):
            return ("runtime-trace-return", [f"{name}: {kind or 'runtime_trace_results'}"])
    for name in names:
        if Path(name).name != "runtime_trace_package_manifest.json":
            continue
        data = read_json(name)
        kind = data.get("kind") if data else None
        if kind == "olm_runtime_trace_request_package":
            return ("runtime-trace-request-package", [f"{name}: {kind}"])
    if any(name.endswith("manifest.json") for name in names):
        for name in names:
            if not name.endswith("manifest.json"):
                continue
            data = read_json(name)
            kind = data.get("kind") if data else None
            if kind == "olm_port_handoff_package":
                return ("olm-handoff-package", [f"{name}: {kind}"])
            if kind == "olm_mac_plugin_package":
                return ("mac-plugin-package", [f"{name}: {kind}"])
            if kind == "ae_effect_reference_manifest":
                media_exts = {}
                for candidate in names:
                    ext = Path(candidate).suffix.lower()
                    if ext in MEDIA_EXTENSIONS:
                        media_exts[ext] = media_exts.get(ext, 0) + 1
                hints = [f"{name}: {kind}"]
                if media_exts:
                    hints.append(f"asset_formats={dict(sorted(media_exts.items()))}")
                    hints.append(
                        f"float_preserving_present={any(ext in FLOAT_PRESERVING_EXTENSIONS for ext in media_exts)}"
                    )
                return ("win-reference-return", hints)
            if kind == "olm_ae_pixel_validation_request":
                return ("ae-pixel-validation-request", [f"{name}: {kind}"])
    for name in names:
        if not (Path(name).name.startswith("AE_VALIDATION_RESULT") and name.endswith(".json")):
            continue
        data = read_json(name)
        kind = data.get("kind") if data else None
        if kind == "olm_ae_host_validation_result":
            return ("ae-host-return", [f"{name}: {kind}"])
    for name in names:
        if not name.endswith(".json"):
            continue
        if Path(name).name == "RETURN_RUNTIME_TRACE_TEMPLATE.json":
            continue
        data = read_json(name)
        kind = data.get("kind") if data else None
        if (
            kind == "olm_runtime_trace_result"
            or (data and isinstance(data.get("runtime_trace_results"), list))
            or (data and isinstance(data.get("results"), list))
        ):
            return ("runtime-trace-return", [f"{name}: {kind or 'runtime_trace_results'}"])
    if any(name.endswith("AE_PIXEL_VALIDATION/request_manifest.json") for name in names):
        return ("mac-plugin-package", ["contains AE_PIXEL_VALIDATION requests"])
    if any(name.endswith("reference_manifest.json") for name in names):
        media_exts = {}
        for candidate in names:
            ext = Path(candidate).suffix.lower()
            if ext in MEDIA_EXTENSIONS:
                media_exts[ext] = media_exts.get(ext, 0) + 1
        hints = ["contains reference_manifest.json"]
        if media_exts:
            hints.append(f"asset_formats={dict(sorted(media_exts.items()))}")
            hints.append(
                f"float_preserving_present={any(ext in FLOAT_PRESERVING_EXTENSIONS for ext in media_exts)}"
            )
        return ("win-reference-return", hints)
    if any(name.endswith("WIN_CODEX_HANDOFF.md") for name in names):
        return ("reference-request-package", ["contains WIN_CODEX_HANDOFF.md"])
    if any(name.endswith("next_reference_actions.json") for name in names):
        hints.append("contains next_reference_actions.json")
    return ("unknown", hints)


def suggested_command(kind: str, path: Path) -> str:
    path_text = str(path)
    if kind == "olmblur-standalone-witness":
        return f"python3 scripts/intake_olmblur_standalone_witness_zip.py {path_text!r}"
    if kind == "win-reference-return":
        return (
            f"python3 scripts/intake_olm_return.py {path_text!r} "
            "--quick --dispatch-dir /tmp/olm_reference_dispatch"
        )
    if kind == "ae-host-return":
        return f"python3 scripts/intake_olm_return.py {path_text!r} --require-all-pass"
    if kind == "ae-pixel-validation-return":
        return f"python3 scripts/intake_olm_return.py {path_text!r} --kind ae-pixel-validation"
    if kind == "olm-handoff-package":
        return f"python3 scripts/verify_olm_handoff_package.py {path_text!r}"
    if kind == "mac-plugin-package":
        return f"python3 scripts/verify_mac_plugin_package.py {path_text!r}"
    if kind == "ae-pixel-validation-request":
        return f"send {path_text!r} to the AE host for pixel validation"
    if kind == "ae-pixel-validation-bundle":
        return f"send {path_text!r} to the AE host for pixel validation"
    if kind == "windows-action-bundle":
        return f"send {path_text!r} to the Windows helper"
    if kind == "windows-action-bundle-return":
        return "use intake_latest_windows_return_from_share.py to unpack and route the bundled runtime returns"
    if kind == "reference-request-package":
        return "send this package to the Windows AE renderer"
    if kind == "runtime-trace-request-package":
        return "send this package to the Windows debugger/helper"
    if kind == "runtime-trace-return":
        return (
            f"python3 scripts/intake_olm_return.py {path_text!r} "
            "--runtime-summary-json refs/reports/runtime_trace_summary.json "
            "--runtime-summary-md refs/reports/runtime_trace_summary.md "
            "--runtime-comparison-dir refs/reports/runtime_trace_comparisons"
        )
    return ""


def build_row(path: Path) -> dict[str, Any]:
    kind, hints = classify_zip(path)
    return {
        "path": str(path),
        "kind": kind,
        "mtime": path.stat().st_mtime,
        "size": path.stat().st_size,
        "hints": hints,
        "suggested_command": suggested_command(kind, path),
    }


def main() -> int:
    args = parse_args()
    rows = [build_row(path) for path in candidate_paths(args.paths)]
    interesting = [row for row in rows if row["kind"] != "unknown"]
    output = interesting[: args.limit]
    if args.json:
        print(json.dumps({"candidates": output}, indent=2, sort_keys=True))
        return 0

    if not output:
        print("no likely OLM return/package candidates found")
        return 0
    print("OLM return/package candidates")
    for row in output:
        print(f"- {row['kind']}: {row['path']}")
        if row["hints"]:
            print(f"  hints: {', '.join(row['hints'])}")
        if row["suggested_command"]:
            print(f"  run: {row['suggested_command']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
