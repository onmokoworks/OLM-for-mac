#!/usr/bin/env python3
"""Freeze the current Mac-side OLMDistanceGradation 16bpc witness baseline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from refs.scripts.verify_manifest import load_rgba


REQUEST_DIR = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
MANIFEST_PATH = REQUEST_DIR / "reference_manifest.json"
OUTPUT_JSON = ROOT / "refs/conformance/olmdistancegradation_16bpc_layer_source_current_baseline_20260629.json"
OUTPUT_MD = ROOT / "refs/conformance/olmdistancegradation_16bpc_layer_source_current_baseline_20260629.md"

CASES = {
    "olmdistancegradation_extended__case_0012": {
        "family": "layer-no-bg-source-or-alpha-ownership",
        "candidate_path": ROOT
        / "refs/reports/ae_single_case_olmdistancegradation_case0012_layer_no_bg_source_fix_installed_20260629/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0012.png",
        "notes": [
            "Primary Layer/no-bg ownership witness after the narrow straight-source-times-output-alpha patch.",
            "Windows runtime trace for source ownership should be judged against this current Mac post-fix baseline, not against the reverted or rejected unpremultiply variants.",
        ],
        "points": [(462, 7), (72, 8), (106, 19), (0, 0)],
    },
    "olmdistancegradation_extended__case_0016": {
        "family": "layer-no-bg-source-or-alpha-ownership",
        "candidate_path": ROOT
        / "refs/reports/ae_single_case_olmdistancegradation_probe_set_20260629/olmdistancegradation_extended__case_0016_rerun/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0016.png",
        "notes": [
            "Secondary Layer/no-bg family under Invert=1.",
            "Useful to confirm whether the same ownership rule explains both the primary and inverted residual family.",
        ],
        "points": [(15, 0), (106, 19), (447, 0), (0, 0)],
    },
    "olmdistancegradation_extended__case_0020": {
        "family": "constant-bg-binary-boundary",
        "candidate_path": ROOT
        / "refs/reports/ae_single_case_olmdistancegradation_probe_set_20260629/olmdistancegradation_extended__case_0020/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0020.png",
        "notes": [
            "Control family after the Constant-specific THRESH_BINARY fix.",
            "This is intentionally not the active runtime-trace target, but it is the best control that the Layer/no-bg patch did not regress the Constant boundary family.",
        ],
        "points": [(951, 417), (950, 417), (951, 416), (0, 0)],
    },
    "olmdistancegradation_extended__case_0022": {
        "family": "constant-bg-binary-boundary",
        "candidate_path": ROOT
        / "refs/reports/ae_single_case_olmdistancegradation_probe_set_20260629/olmdistancegradation_extended__case_0022/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0022.png",
        "notes": [
            "Boundary-localized Constant family after the Constant-specific THRESH_BINARY fix.",
            "Useful to keep the Constant lane separated from the Layer/no-bg ownership lane while Windows runtime evidence is pending.",
        ],
        "points": [(4, 0), (28, 0), (27, 0), (0, 0)],
    },
}


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def case_by_id(manifest: dict, case_id: str) -> dict:
    for case in manifest["cases"]:
        if case["id"] == case_id:
            return case
    raise KeyError(case_id)


def params_by_name(case: dict) -> dict[str, object]:
    params: dict[str, object] = {}
    for effect in case.get("effects", []):
        if effect.get("match_name") != "OLM Distance Gradation":
            continue
        for param in effect.get("params", []):
            params[param["name"]] = param.get("value")
    return params


def max_witness(diff: np.ndarray, ref: np.ndarray, cand: np.ndarray) -> dict[str, object] | None:
    abs_diff = np.abs(diff)
    if not np.any(abs_diff):
        return None
    flat_index = int(abs_diff.reshape(-1).argmax())
    y, x, c = np.unravel_index(flat_index, abs_diff.shape)
    return {
        "x": int(x),
        "y": int(y),
        "channel": int(c),
        "reference": [int(v) for v in ref[y, x]],
        "candidate": [int(v) for v in cand[y, x]],
        "delta": [int(v) for v in diff[y, x]],
    }


def summarize_case(case_id: str, meta: dict, manifest_case: dict) -> dict:
    frame = manifest_case["frame"]
    before = manifest_case["before_effects_frame"]
    reference = load_rgba(REQUEST_DIR / "expected" / frame).astype(np.int64)
    candidate = load_rgba(meta["candidate_path"]).astype(np.int64)
    source = load_rgba(REQUEST_DIR / "input" / before).astype(np.int64)
    diff = candidate - reference
    abs_diff = np.abs(diff)
    changed = np.any(diff != 0, axis=2)
    ys, xs = np.where(changed)
    bbox = None
    if xs.size:
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    samples = []
    for x, y in meta["points"]:
        samples.append(
            {
                "x": x,
                "y": y,
                "input": [int(v) for v in source[y, x]],
                "reference": [int(v) for v in reference[y, x]],
                "candidate": [int(v) for v in candidate[y, x]],
                "delta": [int(v) for v in diff[y, x]],
            }
        )
    return {
        "case_id": case_id,
        "frame": frame,
        "candidate_path": str(meta["candidate_path"].relative_to(ROOT)),
        "family": meta["family"],
        "notes": meta["notes"],
        "params": params_by_name(manifest_case),
        "max_diff": int(abs_diff.max()),
        "mean_abs_diff": float(abs_diff.mean()),
        "changed_pixel_count": int(changed.sum()),
        "changed_bbox": bbox,
        "max_witness": max_witness(diff, reference, candidate),
        "samples": samples,
    }


def write_markdown(payload: dict) -> None:
    lines = [
        "# OLMDistanceGradation 16bpc Layer/no-bg Current Baseline",
        "",
        "- Date: `2026-06-29`",
        f"- Request dir: `{payload['request_dir']}`",
        "- Purpose: freeze the current Mac-side post-fix witness values before the next Windows runtime-trace return is interpreted.",
        "",
        "## Reading",
        "",
        "- `case_0012` / `case_0016` are the active Layer/no-bg source-ownership family.",
        "- `case_0020` / `case_0022` are control families showing the Constant boundary lane after the Constant-specific binary fix.",
        "- Treat this file as the Mac-side baseline to compare against the pending Windows source-ownership runtime trace, not as completion evidence.",
        "",
        "## Cases",
        "",
    ]
    for row in payload["cases"]:
        lines.extend(
            [
                f"### {row['case_id']}",
                "",
                f"- Family: `{row['family']}`",
                f"- Candidate: `{row['candidate_path']}`",
                f"- max: `{row['max_diff']}`",
                f"- mean: `{row['mean_abs_diff']}`",
                f"- nonzero_px: `{row['changed_pixel_count']}`",
                f"- bbox: `{row['changed_bbox']}`",
                f"- max witness: `{row['max_witness']}`",
                f"- params: `{row['params']}`",
            ]
        )
        for note in row["notes"]:
            lines.append(f"- {note}")
        lines.extend(
            [
                "",
                "| Point | input | reference | candidate | delta |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for sample in row["samples"]:
            lines.append(
                f"| `({sample['x']},{sample['y']})` | `{sample['input']}` | "
                f"`{sample['reference']}` | `{sample['candidate']}` | `{sample['delta']}` |"
            )
        lines.append("")
    lines.extend(
        [
            "## Next Evidence Boundary",
            "",
            "- The pending Windows runtime trace should explain whether Layer/no-bg RGB ownership uses straight source RGB times output alpha, another source ownership rule, or an additional quantization step.",
            "- If the returned Windows compose-path source values align with the `case_0012/0016` current Mac samples up to the remaining `-1/-2` RGB family, the next Mac work is likely quantization/rounding cleanup rather than another broad ownership rewrite.",
            "- If they contradict these current samples, update the IR and keep the Constant control families separate from the Layer/no-bg lane.",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    manifest = load_manifest()
    rows = [
        summarize_case(case_id, meta, case_by_id(manifest, case_id))
        for case_id, meta in CASES.items()
    ]
    payload = {
        "kind": "olmdistancegradation_16bpc_layer_source_current_baseline",
        "date": "2026-06-29",
        "request_dir": str(REQUEST_DIR.relative_to(ROOT)),
        "cases": rows,
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(OUTPUT_JSON)
    print(OUTPUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
