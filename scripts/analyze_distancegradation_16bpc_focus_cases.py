#!/usr/bin/env python3
"""Summarize key 16bpc DistanceGradation residual families.

This focuses on the current Mac AE rerun failures that look like:

1. Constant/background binary mask inversion in extended cases 0020..0023.
2. Render-mode/source-layer fractional-vs-clamped X drift in cases 0027/0028.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt


REPO = Path(__file__).resolve().parents[1]
REQUEST_ZIP = REPO / "handoffs" / "ae_host_validation" / "20260625_221356_16bpc_mac_ae_validation" / "bitdepth16_olmdistancegradation_extended_exact.zip"
CANDIDATE_DIR = REPO / "refs" / "reports" / "ae_pixel_validation_16bpc_mac_20260626_204952_rerun" / "bitdepth16_olmdistancegradation_extended_exact" / "candidate"
SUMMARY_JSON = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_focus_cases_20260626.json"
SUMMARY_MD = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_focus_cases_20260626.md"


FOCUS = {
    "olmdistancegradation_extended__case_0020": {"x": 951, "y": 417, "family": "constant-bg-binary"},
    "olmdistancegradation_extended__case_0021": {"x": 951, "y": 417, "family": "constant-bg-binary"},
    "olmdistancegradation_extended__case_0022": {"x": 4, "y": 0, "family": "constant-bg-binary"},
    "olmdistancegradation_extended__case_0023": {"x": 1699, "y": 7, "family": "constant-bg-binary"},
    "olmdistancegradation_extended__case_0027": {"x": 3, "y": 0, "family": "layer-bg-fractional"},
    "olmdistancegradation_extended__case_0028": {"x": 3, "y": 0, "family": "layer-bg-fractional"},
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = load_module(REPO / "refs" / "scripts" / "verify_manifest.py", "verify_manifest")


def float_rgba_u16(v) -> list[float]:
    return [round(float(x) / 65535.0, 6) for x in v]


def rgb_dist(a: list[int], b: list[int]) -> int:
    return sum(abs(int(x) - int(y)) for x, y in zip(a[:3], b[:3]))


def estimate_x_from_bg_grad(red: int, grad_red: int, bg_red: int) -> float | None:
    denom = float(grad_red - bg_red)
    if abs(denom) < 1e-9:
        return None
    return (float(red) - float(bg_red)) / denom


def norm_actual(arr: np.ndarray, threshold: float) -> np.ndarray:
    t = max(float(threshold), 1.0)
    trunc = np.minimum(arr, t)
    raw_max = float(trunc.max())
    denom = max(raw_max, 1.0)
    return trunc / denom


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        with zipfile.ZipFile(REQUEST_ZIP) as zf:
            zf.extractall(td_path)
        root = next(p for p in td_path.iterdir() if p.is_dir())
        manifest = json.loads((root / "reference_manifest.json").read_text(encoding="utf-8"))

        cases_out: list[dict] = []
        for case in manifest["cases"]:
            cid = case["id"]
            if cid not in FOCUS:
                continue
            xy = FOCUS[cid]
            x = xy["x"]
            y = xy["y"]
            input_img = VERIFY.load_rgba(root / "input" / case["before_effects_frame"])
            ref_img = VERIFY.load_rgba(root / "expected" / case["frame"])
            cand_img = VERIFY.load_rgba(CANDIDATE_DIR / case["frame"])
            params = {str(param["name"]).strip(): param["value"] for param in case["effects"][0]["params"] if param.get("name")}
            bg = params["BG Color"]
            grad = params["Gradation Color"]
            bg_u16 = [round(float(c) * 65535.0) for c in bg[:3]]
            grad_u16 = [round(float(c) * 65535.0) for c in grad[:3]]
            alpha = (input_img[..., 3] > 0).astype(np.uint8)
            inside = distance_transform_edt(alpha)
            outside = distance_transform_edt(1 - alpha)
            inside_x = norm_actual(inside, params["Inside Threshold"])
            outside_x = norm_actual(outside, params["Outside Threshold"])
            ref_px = ref_img[y, x].tolist()
            cand_px = cand_img[y, x].tolist()
            inp_px = input_img[y, x].tolist()

            row = {
                "case_id": cid,
                "family": xy["family"],
                "witness": {"x": x, "y": y},
                "params": {
                    key: params[key]
                    for key in (
                        "Invert",
                        "In/Out",
                        "Render Mode",
                        "Use Background Color",
                        "Gradation Color",
                        "BG Color",
                        "Interpolation Mode",
                        "Power",
                    )
                    if key in params
                },
                "input_rgba_u16": inp_px,
                "input_alpha_nonzero": bool(alpha[y, x]),
                "candidate_rgba_u16": cand_px,
                "reference_rgba_u16": ref_px,
                "bg_rgb_u16": bg_u16,
                "grad_rgb_u16": grad_u16,
                "inside_x_actual": float(inside_x[y, x]),
                "outside_x_actual": float(outside_x[y, x]),
                "both_max_const_after_invert": int((1.0 - max(float(inside_x[y, x]), float(outside_x[y, x]))) > 0.0),
                "both_min_const_after_invert": int((1.0 - min(float(inside_x[y, x]), float(outside_x[y, x]))) > 0.0),
                "candidate_matches_bg_rgb": cand_px[:3] == bg_u16,
                "candidate_matches_grad_rgb": cand_px[:3] == grad_u16,
                "reference_matches_bg_rgb": ref_px[:3] == bg_u16,
                "reference_matches_grad_rgb": ref_px[:3] == grad_u16,
                "candidate_dist_to_bg_rgb_l1": rgb_dist(cand_px, bg_u16),
                "candidate_dist_to_grad_rgb_l1": rgb_dist(cand_px, grad_u16),
                "reference_dist_to_bg_rgb_l1": rgb_dist(ref_px, bg_u16),
                "reference_dist_to_grad_rgb_l1": rgb_dist(ref_px, grad_u16),
                "candidate_x_estimate_from_red": estimate_x_from_bg_grad(cand_px[0], grad_u16[0], bg_u16[0]),
                "reference_x_estimate_from_red": estimate_x_from_bg_grad(ref_px[0], grad_u16[0], bg_u16[0]),
                "candidate_rgba_f": float_rgba_u16(cand_px),
                "reference_rgba_f": float_rgba_u16(ref_px),
            }
            cases_out.append(row)

    payload = {
        "kind": "olmdistancegradation_16bpc_focus_cases",
        "status": "diagnostic",
        "candidate_dir": str(CANDIDATE_DIR),
        "request_zip": str(REQUEST_ZIP),
        "cases": cases_out,
        "conclusion": [
            "cases 0020..0023 are not generic color errors; the witness pixels land exactly on BG or Gradation color, which points to a binary X / field-prep inversion family.",
            "cases 0027/0028 do not collapse to BG color. Instead the Mac candidate pins RGB to the zero-valued source layer while the Windows reference keeps a fractional red contribution from background compositing, which points to X saturation or layer/background compose drift rather than a channel-order bug.",
        ],
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# DistanceGradation 16bpc Focus Cases - 2026-06-26",
        "",
        "Witness-based summary of the current extended-case residual families.",
        "",
        "## Cases",
        "",
        "| Case | Family | Witness | Candidate RGB | Reference RGB | Reading |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in cases_out:
        reading = []
        cand_bg = row["candidate_dist_to_bg_rgb_l1"]
        cand_grad = row["candidate_dist_to_grad_rgb_l1"]
        ref_bg = row["reference_dist_to_bg_rgb_l1"]
        ref_grad = row["reference_dist_to_grad_rgb_l1"]
        if cand_bg < cand_grad and ref_grad < ref_bg:
            reading.append("candidate BG-like, reference Grad-like")
        elif cand_grad < cand_bg and ref_bg < ref_grad:
            reading.append("candidate Grad-like, reference BG-like")
        elif row["params"].get("Render Mode") == 2:
            reading.append("candidate pins source-zero RGB")
        else:
            reading.append("mixed/fractional")
        if row["family"] == "constant-bg-binary":
            reading.append(
                f"inside={row['inside_x_actual']:.6f} outside={row['outside_x_actual']:.6f} "
                f"max->{row['both_max_const_after_invert']} min->{row['both_min_const_after_invert']}"
            )
        lines.append(
            f"| `{row['case_id'].split('__')[-1]}` | `{row['family']}` | `({row['witness']['x']},{row['witness']['y']})` | "
            f"`{row['candidate_rgba_u16'][:3]}` | `{row['reference_rgba_u16'][:3]}` | {'; '.join(reading)} |"
        )
    lines.extend(
        [
            "",
            "## Conclusions",
            "",
            "- `case_0020..0023` are BG-like vs Grad-like binary decisions at the sampled pixels.",
            "- For `case_0021/0022`, the current Mac `Both=max(inside,outside)` witness behavior lands on the Mac candidate side, while `min(inside,outside)` would land on the Windows witness side.",
            "- `case_0023` still disagrees even under the simple `min` witness, and the distinguishing parameter is `Outside Threshold=0`; this suggests a threshold-zero special case or another upstream field-prep branch is still missing.",
            "- These are field-prep / constant-mode questions, not simple channel-order or color-space issues.",
            "- `case_0027/0028` keep alpha exact while RGB collapses to the zero-valued source layer on Mac. The Windows reference still mixes in background red, so the active mismatch is X saturation / compose choice rather than raw writeback byte order.",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary_json={SUMMARY_JSON}")
    print(f"summary_md={SUMMARY_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
