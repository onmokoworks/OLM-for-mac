#!/usr/bin/env python3
"""Classify Mac AE 16bpc validation residuals.

This is a diagnostic script, not a conformance gate. It reads the true-16bit
AE pixel validation reports plus their request zips and labels each failing
case with coarse evidence: whether the candidate looks like the input, whether
it is quantized to 8-bit steps, and whether the delta is small enough to be a
rounding issue.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("refs/reports/ae_pixel_validation_16bpc_mac_20260626_1247_distancegradation_clean_stable"),
        help="Batch run directory produced by verify_ae_pixel_validation_batch.py.",
    )
    parser.add_argument(
        "--request-dir",
        type=Path,
        default=Path("handoffs/ae_host_validation/20260625_221356_16bpc_mac_ae_validation"),
        help="Directory containing the original AE pixel validation request zips.",
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=Path("refs/conformance/bitdepth_16bpc_mac_ae_residual_classes_20260626_distancegradation_inside_no_source.json"),
    )
    parser.add_argument(
        "--summary-md",
        type=Path,
        default=Path("refs/conformance/bitdepth_16bpc_mac_ae_residual_classes_20260626_distancegradation_inside_no_source.md"),
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_verify_manifest_module(repo: Path):
    import importlib.util

    path = repo / "refs" / "scripts" / "verify_manifest.py"
    spec = importlib.util.spec_from_file_location("verify_manifest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def safe_extract_zip(path: Path, dest: Path) -> Path:
    with zipfile.ZipFile(path) as archive:
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
    roots = [child for child in dest.iterdir() if child.is_dir() and child.name != "__MACOSX"]
    return roots[0] if len(roots) == 1 else dest


def read_report_rows(run_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for report in sorted(run_dir.glob("*/reports/*.json")):
        data = json.loads(report.read_text(encoding="utf-8"))
        request_name = report.parts[-3]
        for case in data.get("cases", []):
            if case.get("pass"):
                continue
            rows.append(
                {
                    "request_name": request_name,
                    "case_id": case.get("id"),
                    "frame": case.get("frame"),
                    "report": str(report),
                    "max_diff": case.get("max_diff"),
                    "mean_diff": case.get("mean_diff"),
                    "nonzero_px_percent": case.get("nonzero_px_percent"),
                }
            )
    return rows


def request_zip_for(request_dir: Path, request_name: str) -> Path:
    path = request_dir / f"{request_name}.zip"
    if path.exists():
        return path
    matches = sorted(request_dir.glob(f"*{request_name}*.zip"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"request zip not found for {request_name} in {request_dir}")


def case_map(reference_manifest: dict) -> dict[str, dict]:
    return {case.get("id"): case for case in reference_manifest.get("cases", []) if isinstance(case, dict)}


def effect_name(case: dict) -> str:
    requested = case.get("requested_effect")
    if isinstance(requested, dict):
        return str(requested.get("match_name") or requested.get("name") or "")
    effects = case.get("effects")
    if isinstance(effects, list) and effects:
        effect = effects[0]
        if isinstance(effect, dict):
            return str(effect.get("match_name") or effect.get("name") or "")
    return ""


def param_values(case: dict) -> dict[str, object]:
    effects = case.get("effects")
    if not isinstance(effects, list) or not effects:
        return {}
    first = effects[0]
    if not isinstance(first, dict):
        return {}
    values: dict[str, object] = {}
    for param in first.get("params", []):
        if not isinstance(param, dict):
            continue
        name = param.get("name")
        if not isinstance(name, str) or not name:
            continue
        values[name.strip()] = param.get("value")
    return values


SELECTED_PARAMS = {
    "OLM Blur": [
        "Blur Amount",
        "Blur Smoothness",
        "Number of Repeat",
        "Bias Direction",
        "Legacy",
    ],
    "OLM Color Key": [
        "Color Keep",
        "Threshold",
        "Premultiplied Color",
        "Color Space",
        "Force Lower Precision",
        "Per Color",
        "Key Color",
        "Edge Thin",
        "Edge Blur",
    ],
    "OLM Distance Gradation": [
        "Invert",
        "In/Out",
        "Inside Threshold",
        "Outside Threshold",
        "Render Mode",
        "Use Background Color",
        "Gradation Color",
        "BG Color",
        "Interpolation Mode",
        "Power",
        "Blur",
    ],
}


def selected_param_summary(effect: str, values: dict[str, object]) -> dict[str, object]:
    keys = SELECTED_PARAMS.get(effect, [])
    return {key: values[key] for key in keys if key in values}


def plugin_from_case_id(case_id: str) -> str:
    return case_id.split("__", 1)[0] if "__" in case_id else case_id


def feature_flags(case_id: str, effect: str, values: dict[str, object]) -> list[str]:
    flags: list[str] = [plugin_from_case_id(case_id)]
    if effect == "OLM Blur":
        for key in ("Horizontal Radius", "Vertical Radius", "Sampling", "Repeat Edge Pixels"):
            if key in values:
                flags.append(f"{key}={values[key]}")
    elif effect == "OLM Color Key":
        for key in ("Color Keep", "Threshold", "Color Space", "Force Lower Precision", "Edge Thin", "Edge Blur"):
            if key in values:
                flags.append(f"{key}={values[key]}")
    elif effect == "OLM Distance Gradation":
        for key in ("In/Out", "Render Mode", "Use Background Color", "Interpolation Mode", "Power", "Blur"):
            if key in values:
                flags.append(f"{key}={values[key]}")
    return flags


def abs_delta_stats(a: np.ndarray, b: np.ndarray) -> dict:
    if a.shape != b.shape:
        return {"shape_mismatch": [list(a.shape), list(b.shape)]}
    delta = np.abs(a.astype(np.int64) - b.astype(np.int64))
    return {
        "max": int(delta.max()),
        "mean": float(delta.mean()),
        "nonzero_px_percent": float(delta.any(axis=-1).sum() * 100.0 / (a.shape[0] * a.shape[1])),
    }


def quantized_8bit_score(image: np.ndarray) -> float:
    if image.dtype.itemsize < 2:
        return 1.0
    rgb = image[..., :3].astype(np.int64)
    nearest = np.rint(rgb / 257.0) * 257.0
    close = np.abs(rgb - nearest) <= 1.0
    return float(close.sum() / close.size)


def dominant_delta_channels(reference: np.ndarray, candidate: np.ndarray) -> list[int]:
    delta = np.abs(reference.astype(np.int64) - candidate.astype(np.int64))
    channel_means = delta.reshape((-1, delta.shape[-1])).mean(axis=0)
    return [int(v) for v in channel_means.round().tolist()]


def classify(row: dict, reference: np.ndarray, candidate: np.ndarray, before: np.ndarray | None) -> dict:
    ref_vs_candidate = abs_delta_stats(reference, candidate)
    candidate_quant = quantized_8bit_score(candidate)
    reference_quant = quantized_8bit_score(reference)
    input_similarity = None
    if before is not None and before.shape == candidate.shape:
        input_similarity = abs_delta_stats(before, candidate)

    max_diff = int(ref_vs_candidate.get("max", row.get("max_diff") or 0))
    mean_diff = float(ref_vs_candidate.get("mean", row.get("mean_diff") or 0.0))
    if max_diff <= 257 and mean_diff <= 16:
        label = "rounding-or-low-amplitude"
    elif input_similarity and input_similarity.get("max", 999999) <= 257 and input_similarity.get("mean", 999999.0) <= 16:
        label = "candidate-close-to-input"
    elif candidate_quant >= 0.995 and reference_quant < 0.995:
        label = "candidate-looks-8bit-quantized"
    elif max_diff >= 65000:
        label = "full-scale-mismatch"
    else:
        label = "large-structured-mismatch"

    return {
        **row,
        "label": label,
        "candidate_8bit_quantized_score": candidate_quant,
        "reference_8bit_quantized_score": reference_quant,
        "candidate_vs_input": input_similarity,
        "channel_mean_abs_delta_rgba": dominant_delta_channels(reference, candidate),
    }


def write_outputs(summary_json: Path, summary_md: Path, results: list[dict]) -> None:
    counts: dict[str, int] = {}
    plugin_counts: dict[str, dict[str, int]] = {}
    flag_counts: dict[str, int] = {}
    for row in results:
        counts[row["label"]] = counts.get(row["label"], 0) + 1
        plugin = plugin_from_case_id(str(row.get("case_id") or ""))
        plugin_counts.setdefault(plugin, {})
        plugin_counts[plugin][row["label"]] = plugin_counts[plugin].get(row["label"], 0) + 1
        for flag in row.get("feature_flags", []):
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
    payload = {
        "kind": "olm_16bpc_mac_ae_residual_classes",
        "status": "classified-not-exact",
        "case_count": len(results),
        "label_counts": counts,
        "plugin_label_counts": plugin_counts,
        "feature_flag_counts": flag_counts,
        "results": results,
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# 16bpc Mac AE Residual Classes - 2026-06-26 DistanceGradation Inside No-Source",
        "",
        "Status: classified, not AE exact.",
        "",
        "This classification uses the Mac AE batch after the ColorKey Force Lower Precision fix and the DistanceGradation Inside/all-opaque no-source distance-field fix.",
        "",
        "| Label | Count |",
        "| --- | ---: |",
    ]
    for label, count in sorted(counts.items()):
        lines.append(f"| {label} | {count} |")
    lines += [
        "",
        "| Plugin slice | Residual labels |",
        "| --- | --- |",
    ]
    for plugin, labels in sorted(plugin_counts.items()):
        label_text = ", ".join(f"{label}={count}" for label, count in sorted(labels.items()))
        lines.append(f"| {plugin} | {label_text} |")
    lines += [
        "",
        "| Feature flag | Failing cases |",
        "| --- | ---: |",
    ]
    for flag, count in sorted(flag_counts.items(), key=lambda item: (-item[1], item[0])):
        if count < 2:
            continue
        lines.append(f"| `{flag}` | {count} |")
    lines += [
        "",
        "| Request | Case | Label | Max | Mean | Candidate 8bit score | Channel mean delta RGBA | Key params |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in results:
        lines.append(
            "| {request_name} | {case_id} | {label} | {max_diff} | {mean:.4f} | {q:.4f} | `{channels}` | `{params}` |".format(
                request_name=row["request_name"],
                case_id=row["case_id"],
                label=row["label"],
                max_diff=row.get("max_diff"),
                mean=float(row.get("mean_diff") or 0.0),
                q=float(row.get("candidate_8bit_quantized_score") or 0.0),
                channels=row.get("channel_mean_abs_delta_rgba"),
                params=json.dumps(row.get("selected_params", {}), ensure_ascii=False, sort_keys=True),
            )
        )
    lines += [
        "",
        "Interpretation:",
        "- `full-scale-mismatch` is too large to treat as rounding; inspect parameter replay/color management/effect path before tuning kernels.",
        "- `candidate-close-to-input` suggests the effect path may not have applied or a controlling parameter was replayed incorrectly.",
        "- `candidate-looks-8bit-quantized` suggests a bit-depth/writeback path issue.",
        "",
    ]
    summary_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo = repo_root()
    loader = load_verify_manifest_module(repo)
    rows = read_report_rows(args.run_dir)
    if not rows:
        print(f"[FAIL] no failing report rows found in {args.run_dir}", file=sys.stderr)
        return 1

    results: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="olm_16bpc_residuals_") as tmp:
        tmp_root = Path(tmp)
        request_roots: dict[str, Path] = {}
        manifests: dict[str, dict] = {}
        for row in rows:
            request_name = row["request_name"]
            if request_name not in request_roots:
                request_roots[request_name] = safe_extract_zip(
                    request_zip_for(args.request_dir, request_name),
                    tmp_root / request_name,
                )
                manifests[request_name] = json.loads(
                    (request_roots[request_name] / "reference_manifest.json").read_text(encoding="utf-8")
                )
            root = request_roots[request_name]
            cases = case_map(manifests[request_name])
            case = cases.get(row["case_id"], {})
            reference = loader.load_rgba(root / "expected" / row["frame"])
            candidate = loader.load_rgba(args.run_dir / request_name / "candidate" / row["frame"])
            before = None
            before_name = case.get("before_effects_frame")
            if isinstance(before_name, str) and before_name:
                before_path = root / "input" / before_name
                if before_path.exists():
                    before = loader.load_rgba(before_path)
            effect = effect_name(case)
            values = param_values(case)
            result = classify(row, reference, candidate, before)
            result["effect"] = effect
            result["selected_params"] = selected_param_summary(effect, values)
            result["feature_flags"] = feature_flags(str(row["case_id"]), effect, values)
            results.append(result)

    write_outputs(args.summary_json, args.summary_md, results)
    print(f"summary_json={args.summary_json}")
    print(f"summary_md={args.summary_md}")
    for label, count in sorted(json.loads(args.summary_json.read_text(encoding='utf-8'))["label_counts"].items()):
        print(f"{label}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
