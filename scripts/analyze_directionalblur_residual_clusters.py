#!/usr/bin/env python3
"""Analyze OLMDirectionalBlur residual clusters for the full-choreo smoke."""

from __future__ import annotations

import argparse
import json
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SMOKE_ROOT = Path("/tmp/olmdirectionalblur_cpp_rotated_aex_full_choreo_smoke")
DEFAULT_CASES = {
    "angle0_case_0001": {
        "case_id": "case_0001",
        "classification_hint": "angle-0/front-only residual; separates rowdriver/valid-alpha/writeback",
        "reference": SMOKE_ROOT / "reference/case_0001.png",
        "candidate": SMOKE_ROOT / "candidate/case_0001.png",
    },
    "diagonal_case_0005": {
        "case_id": "case_0005",
        "classification_hint": "diagonal rotate-path residual; separates rotate sampler/validity/group normalization",
        "reference": SMOKE_ROOT / "reference/case_0005.png",
        "candidate": SMOKE_ROOT / "candidate/case_0005.png",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / f"refs/reports/olmdirectionalblur_residual_clusters_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        if str(resolved).startswith("/private/tmp/") or str(resolved).startswith("/tmp/"):
            return f"temporary smoke output/{path.name}"
        return str(path)


def load_rgba(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"), dtype=np.int16)


def connected_components(mask: np.ndarray) -> list[dict[str, Any]]:
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    components = []
    for y in range(h):
        xs = np.where(mask[y] & ~seen[y])[0]
        for x0 in xs:
            if seen[y, x0]:
                continue
            q: deque[tuple[int, int]] = deque([(int(x0), int(y))])
            seen[y, x0] = True
            xs_list: list[int] = []
            ys_list: list[int] = []
            while q:
                x, yy = q.popleft()
                xs_list.append(x)
                ys_list.append(yy)
                for nx, ny in ((x - 1, yy), (x + 1, yy), (x, yy - 1), (x, yy + 1)):
                    if nx < 0 or ny < 0 or nx >= w or ny >= h or seen[ny, nx] or not mask[ny, nx]:
                        continue
                    seen[ny, nx] = True
                    q.append((nx, ny))
            components.append(
                {
                    "size": len(xs_list),
                    "bbox": [min(xs_list), min(ys_list), max(xs_list), max(ys_list)],
                    "centroid": [float(np.mean(xs_list)), float(np.mean(ys_list))],
                    "touches_border": min(xs_list) == 0
                    or min(ys_list) == 0
                    or max(xs_list) == w - 1
                    or max(ys_list) == h - 1,
                    "near_border_8px": min(xs_list) < 8
                    or min(ys_list) < 8
                    or max(xs_list) >= w - 8
                    or max(ys_list) >= h - 8,
                }
            )
    return sorted(components, key=lambda row: row["size"], reverse=True)


def classify_case(name: str, diff: np.ndarray, signed: np.ndarray, components: list[dict[str, Any]]) -> dict[str, Any]:
    mask = np.any(diff != 0, axis=2)
    rgb_mask = np.any(diff[..., :3] != 0, axis=2)
    alpha_mask = diff[..., 3] != 0
    rgb_count = int(rgb_mask.sum())
    alpha_count = int(alpha_mask.sum())
    rgb_max = int(diff[..., :3].max()) if diff.size else 0
    alpha_max = int(diff[..., 3].max()) if diff.size else 0
    nonzero = int(mask.sum())
    border_components = [row for row in components if row.get("near_border_8px")]
    interior_components = [row for row in components if not row.get("near_border_8px")]
    rgb_signed = signed[..., :3][rgb_mask]
    alpha_signed = signed[..., 3][alpha_mask]

    if name.startswith("angle0") and alpha_max == 0 and rgb_max >= 100:
        residual_kind = "angle0-rgb-only-rowdriver-or-valid-alpha"
    elif name.startswith("diagonal") and rgb_max >= 200 and alpha_max > 0:
        residual_kind = "diagonal-rgb-alpha-rotate-validity"
    elif rgb_max >= 128:
        residual_kind = "high-rgb-sampler-or-normalization"
    elif alpha_max > 0:
        residual_kind = "alpha-mixed-low-rgb"
    else:
        residual_kind = "low-amplitude-rgb-only"

    return {
        "residual_kind": residual_kind,
        "rgb_nonzero_px": rgb_count,
        "alpha_nonzero_px": alpha_count,
        "rgb_nonzero_percent_of_diff": float(rgb_count * 100.0 / nonzero) if nonzero else 0.0,
        "alpha_nonzero_percent_of_diff": float(alpha_count * 100.0 / nonzero) if nonzero else 0.0,
        "rgb_max": rgb_max,
        "alpha_max": alpha_max,
        "border_component_count_8px": len(border_components),
        "interior_component_count_8px": len(interior_components),
        "largest_component_touches_border": bool(components and components[0].get("touches_border")),
        "largest_border_component": border_components[0] if border_components else None,
        "largest_interior_component": interior_components[0] if interior_components else None,
        "rgb_signed_min": int(rgb_signed.min()) if rgb_signed.size else 0,
        "rgb_signed_max": int(rgb_signed.max()) if rgb_signed.size else 0,
        "alpha_signed_min": int(alpha_signed.min()) if alpha_signed.size else 0,
        "alpha_signed_max": int(alpha_signed.max()) if alpha_signed.size else 0,
    }


def top_witnesses(ref: np.ndarray, cand: np.ndarray, diff: np.ndarray, signed: np.ndarray) -> list[dict[str, Any]]:
    pixel_score = diff.max(axis=2)
    ys, xs = np.where(pixel_score > 0)
    ranked = sorted(((int(pixel_score[y, x]), int(x), int(y)) for y, x in zip(ys, xs)), reverse=True)
    witnesses = []
    seen: set[tuple[int, int]] = set()
    for _, x, y in ranked:
        if (x, y) in seen:
            continue
        seen.add((x, y))
        witnesses.append(
            {
                "x": x,
                "y": y,
                "reference_rgba": [int(v) for v in ref[y, x]],
                "candidate_rgba": [int(v) for v in cand[y, x]],
                "abs_delta_rgba": [int(v) for v in diff[y, x]],
                "signed_delta_candidate_minus_reference": [int(v) for v in signed[y, x]],
            }
        )
        if len(witnesses) >= 8:
            break
    return witnesses


def analyze_case(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    reference_path = Path(spec["reference"])
    candidate_path = Path(spec["candidate"])
    ref = load_rgba(reference_path)
    cand = load_rgba(candidate_path)
    if ref.shape != cand.shape:
        return {
            "name": name,
            "case_id": spec["case_id"],
            "status": "shape-mismatch",
            "reference": display_path(reference_path),
            "candidate": display_path(candidate_path),
            "reference_shape": list(ref.shape),
            "candidate_shape": list(cand.shape),
        }
    diff = np.abs(ref - cand)
    signed = cand - ref
    mask = np.any(diff != 0, axis=2)
    flat = diff.reshape(-1, 4)
    total_px = diff.shape[0] * diff.shape[1]
    max_index = int(np.argmax(diff))
    max_y, max_x, max_c = (int(v) for v in np.unravel_index(max_index, diff.shape))
    channel_signed = []
    for channel in range(4):
        values = signed[..., channel][mask]
        if values.size:
            channel_signed.append(
                {
                    "positive": int((values > 0).sum()),
                    "negative": int((values < 0).sum()),
                    "zero": int((values == 0).sum()),
                    "min": int(values.min()),
                    "max": int(values.max()),
                }
            )
        else:
            channel_signed.append({"positive": 0, "negative": 0, "zero": 0, "min": 0, "max": 0})
    components = connected_components(mask)
    classification = classify_case(name, diff, signed, components)
    return {
        "name": name,
        "case_id": spec["case_id"],
        "status": "compared",
        "classification_hint": spec["classification_hint"],
        "reference": display_path(reference_path),
        "candidate": display_path(candidate_path),
        "max_diff": int(diff.max()),
        "mean_diff": float(diff.mean()),
        "nonzero_px": int(mask.sum()),
        "nonzero_px_percent": float(mask.sum() * 100.0 / total_px),
        "channel_max_rgba": [int(v) for v in flat.max(axis=0)],
        "channel_mean_rgba": [float(v) for v in flat.mean(axis=0)],
        "channel_signed_rgba": channel_signed,
        "classification": classification,
        "max_at": {
            "x": max_x,
            "y": max_y,
            "channel": max_c,
            "reference": [int(v) for v in ref[max_y, max_x]],
            "candidate": [int(v) for v in cand[max_y, max_x]],
            "delta": [int(v) for v in diff[max_y, max_x]],
            "signed": [int(v) for v in signed[max_y, max_x]],
        },
        "top_witnesses": top_witnesses(ref, cand, diff, signed),
        "component_count": len(components),
        "largest_components": components[:10],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDirectionalBlur Residual Cluster Audit",
        "",
        "Candidate: `rotated-aex-full-choreo`.",
        "",
        "| Case | Classification | Max | Mean | Nonzero px | Components | Max witness |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for case in report["cases"]:
        witness = case.get("max_at", {})
        classification = case.get("classification", {})
        witness_text = (
            f"`x={witness.get('x')} y={witness.get('y')} c={witness.get('channel')} "
            f"ref={witness.get('reference')} cand={witness.get('candidate')} signed={witness.get('signed')}`"
            if witness
            else "-"
        )
        lines.append(
            f"| {case['name']} | `{classification.get('residual_kind', '-')}` | "
            f"{case.get('max_diff')} | {case.get('mean_diff', 0.0):.9f} | "
            f"{case.get('nonzero_px')} ({case.get('nonzero_px_percent', 0.0):.4f}%) | "
            f"{case.get('component_count')} | {witness_text} |"
        )
    for case in report["cases"]:
        lines.extend(["", f"## {case['name']}", "", case.get("classification_hint", ""), ""])
        lines.extend(["Top witnesses:", ""])
        for witness in case.get("top_witnesses", []):
            lines.append(
                f"- `x={witness['x']} y={witness['y']}` ref `{witness['reference_rgba']}` "
                f"cand `{witness['candidate_rgba']}` signed `{witness['signed_delta_candidate_minus_reference']}`"
            )
        lines.extend(["", "Largest components:", ""])
        for component in case.get("largest_components", [])[:5]:
            lines.append(
                f"- size `{component['size']}`, bbox `{component['bbox']}`, centroid `{component['centroid']}`"
            )
        lines.extend(["", "Signed channel counts:", ""])
        for label, row in zip("RGBA", case.get("channel_signed_rgba", [])):
            lines.append(
                f"- {label}: positive `{row['positive']}`, negative `{row['negative']}`, "
                f"min `{row['min']}`, max `{row['max']}`"
            )
        classification = case.get("classification", {})
        lines.extend(["", "Classification:", ""])
        lines.append(f"- residual kind: `{classification.get('residual_kind', '-')}`")
        lines.append(
            "- nonzero split: "
            f"RGB `{classification.get('rgb_nonzero_px', 0)}` "
            f"({classification.get('rgb_nonzero_percent_of_diff', 0.0):.2f}% of diff px), "
            f"alpha `{classification.get('alpha_nonzero_px', 0)}` "
            f"({classification.get('alpha_nonzero_percent_of_diff', 0.0):.2f}% of diff px)"
        )
        lines.append(
            "- component split within 8px border: "
            f"border `{classification.get('border_component_count_8px', 0)}`, "
            f"interior `{classification.get('interior_component_count_8px', 0)}`, "
            f"largest touches border `{classification.get('largest_component_touches_border', False)}`"
        )
        if classification.get("largest_border_component"):
            lines.append(f"- largest border component: `{classification['largest_border_component']}`")
        if classification.get("largest_interior_component"):
            lines.append(f"- largest interior component: `{classification['largest_interior_component']}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cases = []
    for name, spec in DEFAULT_CASES.items():
        reference = Path(spec["reference"])
        candidate = Path(spec["candidate"])
        if not reference.exists() or not candidate.exists():
            raise FileNotFoundError(
                f"missing smoke output for {name}; run refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_full_choreo_cli.py first"
            )
        cases.append(analyze_case(name, spec))
    report = {"kind": "olmdirectionalblur_residual_clusters", "schema": 1, "cases": cases}
    (args.output_dir / "residual_clusters.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (args.output_dir / "residual_clusters.md").write_text(render_markdown(report), encoding="utf-8")
    print(f"report={args.output_dir / 'residual_clusters.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
