#!/usr/bin/env python3
"""Cluster OLMSmoother2 current-AEX residual pixels by alpha/diff shape."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


REQUEST_ID = "smoother2_legacy_full_current_aex_recapture_20260621"
EXPECTED_EFFECT = "OLM Smoother v2"
DEFAULT_CASES = [
    "legacy_case_0004_current_aex",
    "legacy_case_0005_current_aex",
    "legacy_case_0006_current_aex",
    "legacy_case_0007_current_aex",
    "legacy_case_0008_current_aex",
    "legacy_case_0009_v1mode_current_aex",
    "legacy_case_0010_gamma3_current_aex",
    "legacy_case_0011_gamma5_blue_current_aex",
    "legacy_case_0012_gamma5_red_blue_current_aex",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", action="append", default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp/olmsmoother2_current_aex_diff_clusters"))
    parser.add_argument("--top-components", type=int, default=8)
    parser.add_argument("--keep-run-dir", action="store_true")
    return parser.parse_args()


def load_status_rows(root: Path) -> list[dict[str, Any]]:
    sys.path.insert(0, str(root / "refs" / "scripts"))
    from check_reference_request_status import load_status_rows as load_rows

    return load_rows(root / "refs" / "reference_requests", root / "refs" / "win_references")


def covered_manifest(root: Path) -> Path:
    for row in load_status_rows(root):
        if row.get("request_id") != REQUEST_ID or row.get("status") != "covered":
            continue
        manifest = (row.get("best") or {}).get("manifest")
        if isinstance(manifest, str) and manifest:
            path = Path(manifest)
            return path if path.is_absolute() else (root / path).resolve()
    raise FileNotFoundError(f"covered manifest not found for {REQUEST_ID}")


def run(command: list[Any], root: Path) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(str(part) for part in command), flush=True)
    return subprocess.run([str(part) for part in command], cwd=root)


def read_rgba(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))


def read_csv(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["id"]: row for row in csv.DictReader(handle)}


def component_rows(mask: np.ndarray) -> list[list[tuple[int, int]]]:
    height, width = mask.shape
    seen = np.zeros(mask.shape, dtype=bool)
    components: list[list[tuple[int, int]]] = []
    for y in range(height):
        xs = np.flatnonzero(mask[y] & ~seen[y])
        for x0 in xs:
            if seen[y, x0] or not mask[y, x0]:
                continue
            q: deque[tuple[int, int]] = deque([(int(x0), int(y))])
            seen[y, x0] = True
            component: list[tuple[int, int]] = []
            while q:
                x, yy = q.popleft()
                component.append((x, yy))
                for ny in (yy - 1, yy, yy + 1):
                    if ny < 0 or ny >= height:
                        continue
                    for nx in (x - 1, x, x + 1):
                        if nx < 0 or nx >= width or seen[ny, nx] or not mask[ny, nx]:
                            continue
                        seen[ny, nx] = True
                        q.append((nx, ny))
            components.append(component)
    return components


def summarize_component(component: list[tuple[int, int]], reference: np.ndarray, candidate: np.ndarray) -> dict[str, Any]:
    xs = np.array([x for x, _ in component], dtype=np.int32)
    ys = np.array([y for _, y in component], dtype=np.int32)
    ref = reference[ys, xs].astype(np.int32)
    cand = candidate[ys, xs].astype(np.int32)
    delta = np.abs(ref - cand)
    max_i = int(np.argmax(delta.max(axis=1)))
    ref_alpha = ref[:, 3]
    cand_alpha = cand[:, 3]
    only_reference = int(((ref_alpha > 0) & (cand_alpha == 0)).sum())
    only_candidate = int(((ref_alpha == 0) & (cand_alpha > 0)).sum())
    both_alpha = int(((ref_alpha > 0) & (cand_alpha > 0)).sum())
    both_zero = int(((ref_alpha == 0) & (cand_alpha == 0)).sum())
    if only_reference >= only_candidate and only_reference >= both_alpha:
        alpha_shape = "windows-only-alpha"
    elif only_candidate >= only_reference and only_candidate >= both_alpha:
        alpha_shape = "mac-only-alpha"
    elif both_alpha > 0:
        alpha_shape = "both-alpha-color-or-alpha-drift"
    else:
        alpha_shape = "transparent-rgb-drift"
    return {
        "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "pixels": len(component),
        "max_diff": int(delta.max()),
        "mean_diff": float(delta.mean()),
        "alpha_shape": alpha_shape,
        "alpha_counts": {
            "windows_only_alpha": only_reference,
            "mac_only_alpha": only_candidate,
            "both_alpha": both_alpha,
            "both_zero": both_zero,
        },
        "max_witness": {
            "x": int(xs[max_i]),
            "y": int(ys[max_i]),
            "reference_rgba": [int(v) for v in ref[max_i]],
            "candidate_rgba": [int(v) for v in cand[max_i]],
            "delta_rgba": [int(v) for v in delta[max_i]],
        },
    }


def summarize_case(case_id: str, reference_path: Path, candidate_path: Path, top_components: int) -> dict[str, Any]:
    reference = read_rgba(reference_path)
    candidate = read_rgba(candidate_path)
    if reference.shape != candidate.shape:
        raise ValueError(f"shape mismatch for {case_id}: {reference.shape} vs {candidate.shape}")
    delta = np.abs(reference.astype(np.int32) - candidate.astype(np.int32))
    mask = delta.any(axis=-1)
    components = component_rows(mask)
    summaries = [
        summarize_component(component, reference, candidate)
        for component in components
    ]
    summaries.sort(key=lambda row: (int(row["max_diff"]), int(row["pixels"])), reverse=True)
    alpha_shapes: dict[str, int] = {}
    for row in summaries:
        alpha_shapes[row["alpha_shape"]] = alpha_shapes.get(row["alpha_shape"], 0) + int(row["pixels"])
    y, x = np.unravel_index(np.argmax(delta.max(axis=-1)), delta.shape[:2])
    return {
        "case_id": case_id,
        "nonzero_px": int(mask.sum()),
        "component_count": len(summaries),
        "max_diff": int(delta.max()),
        "mean_diff": float(delta.mean()),
        "alpha_shape_pixels": alpha_shapes,
        "max_witness": {
            "x": int(x),
            "y": int(y),
            "reference_rgba": [int(v) for v in reference[y, x]],
            "candidate_rgba": [int(v) for v in candidate[y, x]],
            "delta_rgba": [int(v) for v in delta[y, x]],
        },
        "top_components": summaries[:top_components],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMSmoother2 Current-AEX Diff Clusters",
        "",
        f"- Request: `{report['request_id']}`",
        f"- Manifest: `{report['manifest']}`",
        f"- Run dir: `{report['run_dir']}`",
        "",
        "| Case | Max witness | Components | Alpha-shape pixels | Mean |",
        "| --- | --- | ---: | --- | ---: |",
    ]
    for case in report["cases"]:
        w = case["max_witness"]
        lines.append(
            f"| `{case['case_id']}` | `({w['x']},{w['y']}) ref={w['reference_rgba']} cand={w['candidate_rgba']} delta={w['delta_rgba']}` | "
            f"{case['component_count']} | `{case['alpha_shape_pixels']}` | {case['mean_diff']:.6f} |"
        )
    for case in report["cases"]:
        lines.extend(["", f"## {case['case_id']}", "", "| Shape | Pixels | BBox | Max witness |", "| --- | ---: | --- | --- |"])
        for component in case["top_components"]:
            w = component["max_witness"]
            lines.append(
                f"| `{component['alpha_shape']}` | {component['pixels']} | `{component['bbox']}` | "
                f"`({w['x']},{w['y']}) ref={w['reference_rgba']} cand={w['candidate_rgba']} delta={w['delta_rgba']}` |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    manifest_path = covered_manifest(root)
    case_ids = args.case_id or DEFAULT_CASES
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    if output_dir.exists() and not args.keep_run_dir:
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    build = run([root / "refs" / "scripts" / "build_olmsmoother2_cli.sh"], root)
    if build.returncode != 0:
        return build.returncode

    run_dir = output_dir / "run"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = '"cli/OLMSmoother2/olmsmoother2_cli" --input "{input}" --params "{params}" --output "{output}"'
    ref_run = [
        sys.executable,
        root / "refs" / "scripts" / "run_reference_test.py",
        manifest_path.parent,
        "--run-dir",
        run_dir,
        "--expected-effect",
        EXPECTED_EFFECT,
        "--command",
        command,
        "--max-diff",
        "255",
        "--mean-diff",
        "255",
        "--nonzero-px-percent",
        "100",
    ]
    for case_id in case_ids:
        ref_run.extend(["--case-id", case_id])
    proc = run(ref_run, root)
    if proc.returncode != 0:
        return proc.returncode

    diff_rows = read_csv(run_dir / "reports" / "diff.csv")
    cases: list[dict[str, Any]] = []
    for case_id in case_ids:
        row = diff_rows.get(case_id)
        if not row:
            raise KeyError(f"diff row missing for {case_id}")
        frame = row["frame"]
        cases.append(
            {
                **summarize_case(
                    case_id,
                    run_dir / "reference" / frame,
                    run_dir / "candidate" / frame,
                    args.top_components,
                ),
                "diff_metrics": row,
            }
        )

    report = {
        "kind": "olmsmoother2_current_aex_diff_clusters",
        "schema": 1,
        "request_id": REQUEST_ID,
        "manifest": str(manifest_path),
        "run_dir": str(run_dir),
        "cases": cases,
    }
    json_path = output_dir / "diff_clusters.json"
    md_path = output_dir / "diff_clusters.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"report_json={json_path}")
    print(f"report_md={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
