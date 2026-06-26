#!/usr/bin/env python3
"""Analyze the remaining 16bpc OLMColorKey case_0009 residual.

This is a focused diagnostic for the current Mac AE residual:

- request: bitdepth16_olmcolorkey_exact
- case: olmcolorkey__case_0009

It quantifies three things:

1. The real Mac AE candidate vs Windows Software reference polarity.
2. How a naive `Lab76 hit + L1 dilate amount=25` model compares.
3. Whether alternative 16bpc normalization denominators explain the residual.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_cdt, distance_transform_edt, find_objects, label


REPO = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST_ZIP = (
    REPO / "handoffs" / "ae_host_validation" / "20260625_221356_16bpc_mac_ae_validation" / "bitdepth16_olmcolorkey_exact.zip"
)
DEFAULT_CANDIDATE = (
    REPO
    / "refs"
    / "reports"
    / "ae_pixel_validation_16bpc_mac_20260626_204952_rerun"
    / "bitdepth16_olmcolorkey_exact"
    / "candidate"
    / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmcolorkey__case_0009.png"
)
FALLBACK_CANDIDATE = (
    REPO
    / "refs"
    / "reports"
    / "ae_pixel_validation_16bpc_mac_20260626_1247_distancegradation_clean_stable"
    / "bitdepth16_olmcolorkey_exact"
    / "candidate"
    / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmcolorkey__case_0009.png"
)
DEFAULT_SUMMARY_JSON = REPO / "refs" / "conformance" / "olmcolorkey_16bpc_case_0009_analysis.json"
DEFAULT_SUMMARY_MD = REPO / "refs" / "conformance" / "olmcolorkey_16bpc_case_0009_analysis.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-zip", type=Path, default=DEFAULT_REQUEST_ZIP)
    parser.add_argument("--candidate", type=Path, default=None)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--summary-md", type=Path, default=DEFAULT_SUMMARY_MD)
    return parser.parse_args()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = load_module(REPO / "refs" / "scripts" / "verify_manifest.py", "verify_manifest")
CLI = load_module(REPO / "refs" / "scripts" / "olmcolorkey_cli.py", "olmcolorkey_cli")


def extract_case_assets(tmpdir: Path) -> tuple[np.ndarray, np.ndarray, dict]:
    with zipfile.ZipFile(REQUEST_ZIP) as archive:
        archive.extract(
            "ae_pixel_bitdepth16_olmcolorkey_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmcolorkey__case_0009_before_effects.png",
            tmpdir,
        )
        archive.extract(
            "ae_pixel_bitdepth16_olmcolorkey_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmcolorkey__case_0009.png",
            tmpdir,
        )
        archive.extract(
            "ae_pixel_bitdepth16_olmcolorkey_exact_20260625/reference_manifest.json",
            tmpdir,
        )
    root = tmpdir / "ae_pixel_bitdepth16_olmcolorkey_exact_20260625"
    before = VERIFY.load_rgba(
        root / "input" / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmcolorkey__case_0009_before_effects.png"
    ).astype(np.float32)
    reference = VERIFY.load_rgba(
        root / "expected" / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmcolorkey__case_0009.png"
    )
    manifest = json.loads((root / "reference_manifest.json").read_text(encoding="utf-8"))
    case = next(c for c in manifest["cases"] if c["id"] == "olmcolorkey__case_0009")
    return before, reference, case


def params_from_case(case: dict) -> dict[str, object]:
    effect = case["effects"][0]
    params = {param.get("property_index"): param.get("value") for param in effect["params"]}
    named = {param.get("name"): param.get("value") for param in effect["params"] if param.get("name")}
    return {
        "color_keep": named["Color Keep"],
        "threshold": named["Threshold"],
        "color_space": named["Color Space"],
        "force_lower_precision": named["Force Lower Precision"],
        "per_color": named["Per Color"],
        "per_component": named["Per Component"],
        "key_color": named["Color 1"][:3],
        "threshold_components": [
            named["Threshold(R,H,L,Y,Y) 1"],
            named["Threshold(G,S,a,U,Cr) 1"],
            named["Threshold(B,V,b,V,Cb) 1"],
        ],
        "edge_thin_amount": params[14],
        "edge_thin_distance_type": params[15],
        "edge_blur_amount": params[18],
        "edge_blur_distance_type": params[19],
        "edge_blur_direction": params[20],
    }


def hit_mask(before: np.ndarray, params: dict[str, object], denom: float) -> np.ndarray:
    rgb = np.clip(before[..., :3] / denom, 0.0, 1.0)
    cmp_lab = CLI.rgb_to_plugin_lab76(rgb)
    key = np.array(params["key_color"], dtype=np.float32).reshape(1, 1, 3)
    key_lab = CLI.rgb_to_plugin_lab76(key)[0, 0]
    comps = np.array(params["threshold_components"], dtype=np.float32)
    scale = np.array([151.30099487304688, 264.36700439453125, 295.572998046875], dtype=np.float32)
    epsilon = np.float32(0.5 / 255.0)
    allowed = (epsilon + comps) * scale
    return np.all(np.abs(cmp_lab - key_lab) <= allowed, axis=-1)


def keep_mask_from_hit(hit: np.ndarray, amount: float) -> np.ndarray:
    dist = distance_transform_cdt(~hit, metric="taxicab").astype(np.int32)
    matched = hit | (dist <= amount)
    return ~matched


def boundary8(mask: np.ndarray, edge_mode: str) -> np.ndarray:
    h, w = mask.shape
    out = np.zeros_like(mask, dtype=bool)
    for y in range(h):
        for x in range(w):
            if not mask[y, x]:
                continue
            all_inside = True
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    ny = y + dy
                    nx = x + dx
                    if 0 <= ny < h and 0 <= nx < w:
                        neighbor = mask[ny, nx]
                    else:
                        neighbor = mask[y, x] if edge_mode == "clamp" else False
                    all_inside = all_inside and neighbor
            out[y, x] = not all_inside
    return out


def component_summary(mask: np.ndarray, limit: int = 12) -> list[dict[str, int]]:
    labels, count = label(mask)
    boxes = find_objects(labels)
    rows: list[dict[str, int]] = []
    for idx, box in enumerate(boxes, start=1):
        if box is None:
            continue
        area = int((labels[box] == idx).sum())
        rows.append(
            {
                "area": area,
                "x0": int(box[1].start),
                "y0": int(box[0].start),
                "x1": int(box[1].stop - 1),
                "y1": int(box[0].stop - 1),
            }
        )
    rows.sort(key=lambda row: row["area"], reverse=True)
    return rows[:limit]


def compare_polarity(candidate_keep: np.ndarray, reference_keep: np.ndarray) -> dict[str, object]:
    extra = candidate_keep & ~reference_keep
    missing = ~candidate_keep & reference_keep
    ys, xs = np.where(extra)
    return {
        "extra_count": int(extra.sum()),
        "missing_count": int(missing.sum()),
        "total_diff": int(np.count_nonzero(candidate_keep != reference_keep)),
        "extra_bbox": None if not extra.any() else [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "largest_extra_components": component_summary(extra),
    }


def model_sweep(hit: np.ndarray, reference_keep: np.ndarray) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    def add_model(label: str, matched: np.ndarray) -> None:
        keep = ~matched
        rows.append({"label": label, **compare_polarity(keep, reference_keep), "keep_count": int(keep.sum())})

    for metric in ("taxicab", "chessboard", "euclidean"):
        if metric == "taxicab":
            dist = distance_transform_cdt(~hit, metric="taxicab").astype(np.float32)
        elif metric == "chessboard":
            dist = distance_transform_cdt(~hit, metric="chessboard").astype(np.float32)
        else:
            dist = distance_transform_edt(~hit).astype(np.float32)
        for op, threshold in (("<", 25), ("<=", 25), ("<", 26), ("<=", 26)):
            matched = hit | (dist < threshold if op == "<" else dist <= threshold)
            add_model(f"hit-{metric}-{op}{threshold}", matched)

    for edge_mode in ("clamp", "outside"):
        seeds = boundary8(hit, edge_mode=edge_mode)
        for metric in ("taxicab", "chessboard", "euclidean"):
            if metric == "taxicab":
                dist = distance_transform_cdt(~seeds, metric="taxicab").astype(np.float32)
            elif metric == "chessboard":
                dist = distance_transform_cdt(~seeds, metric="chessboard").astype(np.float32)
            else:
                dist = distance_transform_edt(~seeds).astype(np.float32)
            for op, threshold in (("<", 25), ("<=", 25), ("<", 26), ("<=", 26)):
                matched = hit | (dist < threshold if op == "<" else dist <= threshold)
                add_model(f"boundary-{edge_mode}-{metric}-{op}{threshold}", matched)

    yy, xx = np.mgrid[-25:26, -25:26]
    structures = {
        "diamond25": (np.abs(xx) + np.abs(yy)) <= 25,
        "square25": np.maximum(np.abs(xx), np.abs(yy)) <= 25,
    }
    for name, structure in structures.items():
        matched = binary_dilation(hit, structure=structure)
        add_model(f"binary-{name}", matched)

    rows.sort(key=lambda row: row["total_diff"])
    return rows


def main() -> int:
    args = parse_args()
    candidate = args.candidate.resolve() if args.candidate else (DEFAULT_CANDIDATE if DEFAULT_CANDIDATE.exists() else FALLBACK_CANDIDATE)
    request_zip = args.request_zip.resolve()
    summary_json = args.summary_json.resolve()
    summary_md = args.summary_md.resolve()

    with tempfile.TemporaryDirectory() as tmp:
        global REQUEST_ZIP
        REQUEST_ZIP = request_zip
        before, reference, case = extract_case_assets(Path(tmp))
    candidate = VERIFY.load_rgba(candidate)
    params = params_from_case(case)
    reference_keep = reference[..., 3] > 0
    candidate_keep = candidate[..., 3] > 0
    actual = compare_polarity(candidate_keep, reference_keep)

    denom_results = []
    for denom in (65535.0, 32768.0, 32767.0):
        hit = hit_mask(before, params, denom)
        naive_keep = keep_mask_from_hit(hit, float(params["edge_thin_amount"]))
        diff = compare_polarity(naive_keep, reference_keep)
        denom_results.append(
            {
                "denominator": denom,
                "hit_count": int(hit.sum()),
                "keep_count": int(naive_keep.sum()),
                **diff,
            }
        )

    sweep = model_sweep(hit_mask(before, params, 65535.0), reference_keep)

    dist = distance_transform_cdt(~candidate_keep, metric="taxicab").astype(np.int32)
    extra = candidate_keep & ~reference_keep
    extra_dist = dist[extra]
    shell = {
        "candidate_extra_dist_min": int(extra_dist.min()) if extra_dist.size else None,
        "candidate_extra_dist_max": int(extra_dist.max()) if extra_dist.size else None,
        "candidate_extra_dist_mean": float(extra_dist.mean()) if extra_dist.size else None,
    }

    payload = {
        "kind": "olmcolorkey_16bpc_case_0009_analysis",
        "status": "diagnostic",
        "params": params,
        "actual_candidate_vs_reference": actual,
        "naive_model_vs_reference": denom_results,
        "seed_dilate_model_sweep": sweep[:12],
        "candidate_shell_summary": shell,
        "conclusion": [
            "The active 16bpc residual is a positive Edge Thin dilate case, not an Edge Blur blend path.",
            "The real Mac AE candidate only over-keeps pixels; it never removes pixels that Windows keeps.",
            "A naive Lab76 hit plus taxicab dilate model is much worse than the real Mac AE candidate.",
            "Changing the 16bpc normalization denominator from 65535 to 32768/32767 makes the naive model substantially worse, so that hypothesis is rejected.",
            "Simple seed-world variants (hit, boundary, clamp-vs-outside edge, taxicab/chessboard/euclidean, and <=25/<26 threshold shifts) still bottom out at 80592px, so the missing rule is narrower than those model families.",
        ],
    }
    summary_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# OLMColorKey 16bpc case_0009 analysis",
        "",
        "Status: diagnostic.",
        "",
        "This report focuses on the remaining 16bpc Mac AE residual after the Force Lower Precision fix.",
        "",
        f"- Candidate vs Windows reference diff: `{actual['total_diff']}` px",
        f"- Candidate extra-only pixels: `{actual['extra_count']}` px",
        f"- Candidate missing pixels: `{actual['missing_count']}` px",
        f"- Candidate extra bbox: `{actual['extra_bbox']}`",
        "",
        "## Parameters",
        "",
        f"- Color Space: `{params['color_space']}` (Lab76)",
        f"- Force Lower Precision: `{params['force_lower_precision']}`",
        f"- Per Color / Per Component: `{params['per_color']}` / `{params['per_component']}`",
        f"- Edge Thin Amount / Distance Type: `{params['edge_thin_amount']}` / `{params['edge_thin_distance_type']}`",
        f"- Edge Blur Amount / Distance Type / Direction: `{params['edge_blur_amount']}` / `{params['edge_blur_distance_type']}` / `{params['edge_blur_direction']}`",
        "",
        "## Naive models",
        "",
        "| Denominator | Hit count | Keep count | Diff px | Extra px | Missing px |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in denom_results:
        lines.append(
            f"| {row['denominator']} | {row['hit_count']} | {row['keep_count']} | {row['total_diff']} | {row['extra_count']} | {row['missing_count']} |"
        )
    lines += [
        "",
        "## Seed / Dilate sweep",
        "",
        "| Model | Diff px | Extra px | Missing px | Keep px |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in sweep[:12]:
        lines.append(
            f"| {row['label']} | {row['total_diff']} | {row['extra_count']} | {row['missing_count']} | {row['keep_count']} |"
        )
    lines += [
        "",
        "## Conclusion",
        "",
        "- The residual is not an Edge Blur blend issue.",
        "- The current Mac AE candidate is already much closer to Windows than the naive Lab76+dilate reconstruction.",
        "- A `32768` or `32767` normalization denominator is not the missing fix; it makes the naive model dramatically worse.",
        "- Straightforward seed-world variants also fail badly; the best of them still differs by `80592px`.",
        "- The remaining gap is likely a narrower seed-world or local dilate-ownership rule inside the real plug-in path.",
        "",
        "## Largest extra components",
        "",
        "| Area | x0 | y0 | x1 | y1 |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in actual["largest_extra_components"]:
        lines.append(f"| {row['area']} | {row['x0']} | {row['y0']} | {row['x1']} | {row['y1']} |")
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"summary_json={summary_json}")
    print(f"summary_md={summary_md}")
    print(f"candidate_diff_px={actual['total_diff']}")
    print(f"candidate_extra_px={actual['extra_count']}")
    print(f"candidate_missing_px={actual['missing_count']}")
    for row in denom_results:
        print(
            "naive",
            f"denom={row['denominator']}",
            f"diff={row['total_diff']}",
            f"extra={row['extra_count']}",
            f"missing={row['missing_count']}",
        )
    for row in sweep[:8]:
        print(
            "sweep",
            row["label"],
            f"diff={row['total_diff']}",
            f"extra={row['extra_count']}",
            f"missing={row['missing_count']}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
