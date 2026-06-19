#!/usr/bin/env python3
"""Package the current Windows-side action bundle.

The bundle is intentionally a wrapper around already validated request zips.
It gives the Windows helper one date-stamped artifact to pick up, while keeping
the individual runtime trace / AE pixel validation packages intact.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import zipfile
from pathlib import Path
from typing import Any


RUNTIME_PACKAGES = [
    Path(
        "refs/runtime_trace_packages/"
        "olm_runtime_trace_olmsmoother2_no_key_grid_idx7_context_with_mac_baseline_20260619_041000.zip"
    ),
    Path("refs/runtime_trace_packages/olm_runtime_trace_olmblur_repeat_threshold_with_mac_baseline_20260619_030743.zip"),
    Path("refs/runtime_trace_packages/olm_runtime_trace_colorkey_edge_erode_blur_with_mac_baseline_20260619_031350.zip"),
    Path("refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_field_prep_opencv_args_20260619_030427.zip"),
]

BLUR_KIRAKIRA_RUNTIME_PACKAGES = [
    Path("refs/runtime_trace_packages/olm_runtime_trace_olmblur_repeat_threshold_20260620_overnight.zip"),
    Path("refs/runtime_trace_packages/olm_runtime_trace_kirakira_stage_values_20260620_overnight.zip"),
]

AE_PIXEL_PACKAGES = [
    Path("refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmsmoother_v1_20260619_031933.zip"),
    Path("refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmsmoother2_legacy_20260619_031933.zip"),
    Path("refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmsmoother2_no_key_grid_20260619_031933.zip"),
    Path("refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmblur_exact_20260619_033243.zip"),
    Path("refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmtoondilate_exact_20260619_033243.zip"),
    Path("refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmcolorkey_exact_20260619_032431.zip"),
    Path("refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_basic_exact_20260619_032933.zip"),
    Path("refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_extended_exact_20260619_032933.zip"),
    Path("refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_blur_exact_20260619_032933.zip"),
]

SUPPORTING_NOTES = [
    Path("notes/CONFORMANCE_LEDGER.md"),
    Path("notes/WINDOWS_RETURN_INTAKE_PLAYBOOK_20260619.md"),
    Path("notes/IR_OLMSmoother2.md"),
    Path("notes/IR_OLMBlur.md"),
    Path("notes/IR_OLMColorKey_Edge.md"),
    Path("notes/IR_OLMDistanceGradation.md"),
]

BLUR_KIRAKIRA_SUPPORTING_NOTES = [
    Path("notes/CONFORMANCE_LEDGER.md"),
    Path("notes/WINDOWS_RETURN_INTAKE_PLAYBOOK_20260619.md"),
    Path("notes/IR_OLMBlur.md"),
    Path("notes/IR_OLMKiraKira.md"),
    Path("notes/OLMKiraKira_ASM_FACTS.md"),
    Path("notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md"),
    Path("refs/reports/runtime_trace_summary.md"),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output zip. Defaults to handoffs/windows_batch/olm_windows_action_bundle_<stamp>_smoother_priority.zip.",
    )
    parser.add_argument(
        "--runtime-only",
        action="store_true",
        help="Only include runtime trace packages, omitting AE pixel validation packages.",
    )
    parser.add_argument(
        "--focus",
        choices=["smoother-priority", "blur-kirakira"],
        default="smoother-priority",
        help="Select the package set to bundle.",
    )
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def zip_kind(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if name.endswith("runtime_trace_package_manifest.json"):
                    data = json.loads(archive.read(name).decode("utf-8"))
                    if data.get("kind") == "olm_runtime_trace_request_package":
                        return "runtime-trace-request-package"
                if name.endswith("request_manifest.json"):
                    data = json.loads(archive.read(name).decode("utf-8"))
                    if data.get("kind") == "olm_ae_pixel_validation_request":
                        return "ae-pixel-validation-request"
    except Exception:
        return "unknown"
    return "unknown"


def file_rows(root: Path, paths: list[Path], bundle_dir: str) -> list[dict[str, Any]]:
    rows = []
    for index, path in enumerate(paths, start=1):
        full = root / path
        rows.append(
            {
                "priority": index,
                "source": path.as_posix(),
                "bundle_path": f"{bundle_dir}/{path.name}",
                "kind": zip_kind(full),
                "size_bytes": full.stat().st_size,
            }
        )
    return rows


def supporting_notes_for_focus(focus: str) -> list[Path]:
    if focus == "blur-kirakira":
        return BLUR_KIRAKIRA_SUPPORTING_NOTES
    return SUPPORTING_NOTES


def build_manifest(root: Path, runtime_paths: list[Path], ae_paths: list[Path], focus: str) -> dict[str, Any]:
    supporting_notes = supporting_notes_for_focus(focus)
    return {
        "kind": "olm_windows_action_bundle",
        "schema": 1,
        "created_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "priority": focus,
        "runtime_trace_packages": file_rows(root, runtime_paths, "runtime_trace"),
        "ae_pixel_validation_packages": file_rows(root, ae_paths, "ae_pixel_validation"),
        "supporting_notes": [path.as_posix() for path in supporting_notes if (root / path).exists()],
    }


def build_readme(manifest: dict[str, Any]) -> str:
    lines = [
        "# OLM Windows Action Bundle",
        "",
        "This bundle is for the Windows machine / Windows Codex session.",
        "Run the runtime trace package first; AE pixel validation packages are included so they can be rendered in the same trip if convenient.",
        "",
        "Priority:",
        "",
    ]
    for row in manifest["runtime_trace_packages"]:
        lines.append(f"{row['priority']}. Runtime trace: `{row['bundle_path']}`")
    if manifest["ae_pixel_validation_packages"]:
        lines.extend(["", "AE pixel validation packages:", ""])
        for row in manifest["ae_pixel_validation_packages"]:
            lines.append(f"- `{row['bundle_path']}`")
    lines.extend(
        [
            "",
            "Return artifacts:",
            "",
            "- Runtime trace: fill and zip the package's `RETURN_RUNTIME_TRACE_TEMPLATE.json`.",
            "- AE pixel validation: return rendered candidate PNGs plus the filled result template from each request.",
            "",
            "Do not treat any returned near miss as completion. Mac AE exact requires max_diff=0 against the Windows Software reference.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    runtime_paths = BLUR_KIRAKIRA_RUNTIME_PACKAGES if args.focus == "blur-kirakira" else RUNTIME_PACKAGES
    ae_paths = [] if args.runtime_only or args.focus == "blur-kirakira" else AE_PIXEL_PACKAGES
    missing = [path for path in [*runtime_paths, *ae_paths] if not (root / path).exists()]
    if missing:
        return fail("missing bundle input(s): " + ", ".join(path.as_posix() for path in missing))

    output = args.output
    if output is None:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        output = root / "handoffs" / "windows_batch" / f"olm_windows_action_bundle_{stamp}_{args.focus.replace('-', '_')}.zip"
    elif not output.is_absolute():
        output = root / output

    manifest = build_manifest(root, runtime_paths, ae_paths, args.focus)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README_WINDOWS_ACTION_BUNDLE.md", build_readme(manifest))
        archive.writestr("windows_action_bundle_manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
        for row in manifest["runtime_trace_packages"]:
            archive.write(root / row["source"], row["bundle_path"])
        for row in manifest["ae_pixel_validation_packages"]:
            archive.write(root / row["source"], row["bundle_path"])
        for note in manifest["supporting_notes"]:
            archive.write(root / note, note)

    print(f"[OK] Windows action bundle: {output}")
    for row in manifest["runtime_trace_packages"]:
        print(f"- runtime {row['priority']}: {row['source']}")
    if manifest["ae_pixel_validation_packages"]:
        print(f"- AE pixel validation packages: {len(manifest['ae_pixel_validation_packages'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
