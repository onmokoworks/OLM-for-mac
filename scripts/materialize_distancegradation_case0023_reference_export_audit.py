#!/usr/bin/env python3
"""Audit OLMDistanceGradation case_0023 reference/export provenance."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
VERIFY_MANIFEST = ROOT / "refs/scripts/verify_manifest.py"

PACKAGED_16BPC = (
    ROOT
    / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/"
    "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
    "olmdistancegradation_extended__case_0023.png"
)
CURRENT_WIN_20260703 = (
    ROOT
    / "refs/win_references/olm_reference_return_windows_20260703_combined/DistanceGradation/"
    "olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__"
    "olmdistancegradation_extended__case_0023_current_aex.png"
)
CURRENT_WIN_20260706 = (
    ROOT
    / "refs/win_references/olm_return_20260706/DistanceGradation/"
    "olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__"
    "olmdistancegradation_extended__case_0023_current_aex.png"
)
MAC_LIVE_BG_ON_20260703 = (
    ROOT
    / "refs/reports/ae_single_case_distancegradation_case0023_live_20260703_bg_on/"
    "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
    "olmdistancegradation_extended__case_0023.png"
)
WIN_BG_OFF = (
    ROOT
    / "refs/win_references/olmdistancegradation_16bpc_bg_compose_variants_20260626/DistanceGradation/renders/"
    "olmdistancegradation_16bpc_bg_compose_variants_20260626__software_16bpc__fr24__"
    "olmdistancegradation_case_0023_bg_off_variant.png"
)
MAC_BG_OFF_20260703 = (
    ROOT
    / "refs/reports/ae_single_case_distancegradation_case0023_live_20260703_bg_off/"
    "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
    "olmdistancegradation_extended__case_0023.png"
)
MAC_BG_OFF_REFRESH = (
    ROOT
    / "refs/reports/ae_single_case_distancegradation_case0023_live_refresh_bg_off/"
    "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
    "olmdistancegradation_extended__case_0023.png"
)

SAMPLE_POINTS = [
    (1698, 7),
    (1699, 7),
    (1700, 7),
    (414, 393),
    (415, 393),
    (416, 393),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stamp",
        default=datetime.now().strftime("%Y%m%d"),
        help="Date stamp for output filenames (default: today in local time).",
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args()


def load_verify_manifest() -> Any:
    spec = importlib.util.spec_from_file_location("verify_manifest", VERIFY_MANIFEST)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {VERIFY_MANIFEST}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare_arrays(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    if a.shape != b.shape:
        return {
            "status": "shape_mismatch",
            "shape_a": list(a.shape),
            "shape_b": list(b.shape),
        }
    if np.issubdtype(a.dtype, np.floating) or np.issubdtype(b.dtype, np.floating):
        a_cmp = a.astype(np.float64, copy=False)
        b_cmp = b.astype(np.float64, copy=False)
    else:
        a_cmp = a.astype(np.int64, copy=False)
        b_cmp = b.astype(np.int64, copy=False)
    delta = np.abs(a_cmp - b_cmp)
    pixel_delta = np.max(delta, axis=2)
    return {
        "status": "compared",
        "shape": list(a.shape),
        "dtype_a": str(a.dtype),
        "dtype_b": str(b.dtype),
        "nonzero_px": int(np.count_nonzero(pixel_delta)),
        "max_diff": float(delta.max()) if np.issubdtype(delta.dtype, np.floating) else int(delta.max()),
        "mean_diff": float(delta.mean()),
    }


def sample_pixels(array: np.ndarray) -> dict[str, list[int] | list[float]]:
    samples: dict[str, list[int] | list[float]] = {}
    for x, y in SAMPLE_POINTS:
        value = array[y, x].tolist()
        samples[f"{x},{y}"] = value
    return samples


def image_record(path: Path, array: np.ndarray) -> dict[str, Any]:
    return {
        "path": rel(path),
        "sha256": sha256(path),
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "samples": sample_pixels(array),
    }


def build_report() -> dict[str, Any]:
    verify_manifest = load_verify_manifest()
    images = {
        "packaged_16bpc": PACKAGED_16BPC,
        "current_win_20260703": CURRENT_WIN_20260703,
        "current_win_20260706": CURRENT_WIN_20260706,
        "mac_live_bg_on_20260703": MAC_LIVE_BG_ON_20260703,
        "win_bg_off": WIN_BG_OFF,
        "mac_bg_off_20260703": MAC_BG_OFF_20260703,
        "mac_bg_off_refresh": MAC_BG_OFF_REFRESH,
    }
    missing = {name: rel(path) for name, path in images.items() if not path.exists()}
    arrays = {name: verify_manifest.load_rgba(path) for name, path in images.items() if path.exists()}

    comparisons = {
        "packaged_vs_current_win_20260703": compare_arrays(arrays["packaged_16bpc"], arrays["current_win_20260703"]),
        "packaged_vs_current_win_20260706": compare_arrays(arrays["packaged_16bpc"], arrays["current_win_20260706"]),
        "current_win_20260703_vs_20260706": compare_arrays(
            arrays["current_win_20260703"], arrays["current_win_20260706"]
        ),
    }
    if "mac_live_bg_on_20260703" in arrays:
        comparisons["current_win_20260706_vs_mac_live_bg_on_20260703"] = compare_arrays(
            arrays["current_win_20260706"], arrays["mac_live_bg_on_20260703"]
        )
    if "win_bg_off" in arrays and "mac_bg_off_20260703" in arrays:
        comparisons["win_bg_off_vs_mac_bg_off_20260703"] = compare_arrays(
            arrays["win_bg_off"], arrays["mac_bg_off_20260703"]
        )
    if "win_bg_off" in arrays and "mac_bg_off_refresh" in arrays:
        comparisons["win_bg_off_vs_mac_bg_off_refresh"] = compare_arrays(
            arrays["win_bg_off"], arrays["mac_bg_off_refresh"]
        )

    reference_exact = all(
        comparisons[key]["status"] == "compared"
        and comparisons[key]["nonzero_px"] == 0
        and comparisons[key]["max_diff"] == 0
        for key in [
            "packaged_vs_current_win_20260703",
            "packaged_vs_current_win_20260706",
            "current_win_20260703_vs_20260706",
        ]
    )
    records = {name: image_record(path, arrays[name]) for name, path in images.items() if name in arrays}
    return {
        "kind": "olmdistancegradation_case0023_reference_export_audit",
        "materialized_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "case_id": "olmdistancegradation_extended__case_0023",
        "sample_points": [[x, y] for x, y in SAMPLE_POINTS],
        "missing": missing,
        "images": records,
        "comparisons": comparisons,
        "reference_exact": reference_exact,
        "safe_claim": (
            "The packaged 2026-06-25 16bpc Windows Software reference is byte-identical to the "
            "2026-07-03 and 2026-07-06 current-AEX Windows recaptures for case_0023. The old "
            "packaged-stale explanation is therefore not valid for the current files in this worktree."
        )
        if reference_exact
        else (
            "The packaged/current Windows references are not all identical; keep reference/export "
            "provenance open before implementation tuning."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# OLMDistanceGradation case_0023 Reference Export Audit - {report['materialized_at'][:10]}",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Reference exact: `{report['reference_exact']}`",
        f"- Safe claim: {report['safe_claim']}",
        "",
        "## Reference Comparisons",
        "",
        "| Pair | Status | Nonzero px | Max diff | Mean diff |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for name, comparison in report["comparisons"].items():
        lines.append(
            f"| `{name}` | `{comparison.get('status')}` | `{comparison.get('nonzero_px', '')}` | "
            f"`{comparison.get('max_diff', '')}` | `{comparison.get('mean_diff', '')}` |"
        )
    lines.extend(
        [
            "",
            "## Sample Pixels",
            "",
            "| Image | (1698,7) | (1699,7) | (1700,7) | (414,393) | (415,393) | (416,393) |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    sample_keys = ["1698,7", "1699,7", "1700,7", "414,393", "415,393", "416,393"]
    for name, image in report["images"].items():
        samples = image["samples"]
        values = " | ".join(f"`{samples[key]}`" for key in sample_keys)
        lines.append(f"| `{name}` | {values} |")
    if report["missing"]:
        lines.extend(["", "## Missing", ""])
        for name, path in report["missing"].items():
            lines.append(f"- {name}: `{path}`")
    lines.extend(["", "## Inputs", ""])
    for name, image in report["images"].items():
        lines.append(f"- {name}: `{image['path']}` (`sha256:{image['sha256']}`)")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report()
    output_json = args.output_json or (
        ROOT / "refs/conformance" / f"olmdistancegradation_case0023_reference_export_audit_{args.stamp}.json"
    )
    output_md = args.output_md or (
        ROOT / "refs/conformance" / f"olmdistancegradation_case0023_reference_export_audit_{args.stamp}.md"
    )
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
