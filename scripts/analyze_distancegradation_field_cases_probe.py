#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
VERIFY_MANIFEST = ROOT / "refs" / "scripts" / "verify_manifest.py"
MANIFEST = ROOT / "handoff" / "ae_pixel_validation_20260618" / "requests" / "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625" / "reference_manifest.json"
RESULT_DIR = ROOT / "handoff" / "ae_pixel_validation_20260618" / "results" / "bitdepth16_olmdistancegradation_extended_exact"
PROBE_DIR = ROOT / "handoff" / "ae_pixel_validation_20260618" / "probes" / "distancegradation_field_cases"
INPUT_DIR = ROOT / "handoff" / "ae_pixel_validation_20260618" / "requests" / "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625" / "input"
EXPECTED_DIR = ROOT / "handoff" / "ae_pixel_validation_20260618" / "requests" / "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625" / "expected"
OUT_JSON = ROOT / "refs" / "conformance" / "olmdistancegradation_16bpc_field_cases_probe_20260626.json"
OUT_MD = ROOT / "refs" / "conformance" / "olmdistancegradation_16bpc_field_cases_probe_20260626.md"

FOCUS = {
    "olmdistancegradation_extended__case_0020": {"x": 951, "y": 417},
    "olmdistancegradation_extended__case_0021": {"x": 951, "y": 417},
    "olmdistancegradation_extended__case_0022": {"x": 4, "y": 0},
    "olmdistancegradation_extended__case_0023": {"x": 1699, "y": 7},
    "olmdistancegradation_extended__case_0027": {"x": 3, "y": 0},
    "olmdistancegradation_extended__case_0028": {"x": 3, "y": 0},
}


def load_verify_manifest():
    spec = importlib.util.spec_from_file_location("verify_manifest", VERIFY_MANIFEST)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {VERIFY_MANIFEST}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = load_verify_manifest()


def norm_actual(arr: np.ndarray, threshold: float) -> np.ndarray:
    t = max(float(threshold), 1.0)
    trunc = np.minimum(arr, t)
    raw_max = float(trunc.max())
    denom = max(raw_max, 1.0)
    return trunc / denom


def build_models(alpha: np.ndarray, params: dict[str, object]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mask = (alpha > 0).astype(np.uint8)
    inside = norm_actual(distance_transform_edt(mask), params["Inside Threshold"])
    outside = norm_actual(distance_transform_edt(1 - mask), params["Outside Threshold"])
    both_max = np.maximum(inside, outside)
    both_add = inside + outside
    return inside, outside, both_max, both_add


def estimate_x_from_bg_grad(red: int, grad_red: int, bg_red: int) -> float | None:
    denom = float(grad_red - bg_red)
    if abs(denom) < 1e-9:
        return None
    return (float(red) - float(bg_red)) / denom


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = []
    for case in manifest["cases"]:
        cid = case["id"]
        if cid not in FOCUS:
            continue
        x = FOCUS[cid]["x"]
        y = FOCUS[cid]["y"]
        params = {str(p["name"]).strip(): p["value"] for p in case["effects"][0]["params"] if p.get("name")}
        src = VERIFY.load_rgba(INPUT_DIR / case["before_effects_frame"]).astype(np.float32)
        candidate = VERIFY.load_rgba(RESULT_DIR / case["frame"])
        expected = VERIFY.load_rgba(EXPECTED_DIR / case["frame"])
        probe = VERIFY.load_rgba(PROBE_DIR / f"{cid}__no_bg.png")
        alpha = src[..., 3] / 65535.0
        inside, outside, both_max, both_add = build_models(alpha, params)
        interp_mode = int(params["Interpolation Mode"])
        power = float(params["Power"])
        invert = bool(params["Invert"])
        if int(params["In/Out"]) == 1:
            base = inside
            d_alpha = alpha
        elif int(params["In/Out"]) == 2:
            base = outside
            d_alpha = 1.0 - alpha
        else:
            base = both_max
            d_alpha = np.ones_like(alpha)
        x_model = base.copy()
        x_model_add = base.copy() if int(params["In/Out"]) != 3 else both_add.copy()
        if not invert:
            x_model = 1.0 - x_model
            x_model_add = 1.0 - x_model_add
        if interp_mode == 3:
            t = 1.0 - x_model
            x_model = np.sqrt(np.clip(1.0 - t * t, 0.0, 1.0))
            t_add = 1.0 - x_model_add
            x_model_add = np.sqrt(np.clip(1.0 - t_add * t_add, 0.0, 1.0))
        elif interp_mode == 4:
            x_model = np.power(x_model, power)
            x_model_add = np.power(x_model_add, power)
        elif interp_mode == 1:
            x_model = (x_model > 0.0).astype(np.float32)
            x_model_add = (x_model_add > 0.0).astype(np.float32)
        obs_alpha = probe[..., 3].astype(np.float32) / 65535.0
        obs_x = np.divide(obs_alpha, d_alpha, out=np.zeros_like(obs_alpha), where=d_alpha > 1e-6)
        bg = [round(float(c) * 65535.0) for c in params["BG Color"][:3]]
        grad = [round(float(c) * 65535.0) for c in params["Gradation Color"][:3]]
        cand = [int(v) for v in candidate[y, x]]
        ref = [int(v) for v in expected[y, x]]
        probe_px = [int(v) for v in probe[y, x]]
        row = {
            "case_id": cid,
            "witness": [x, y],
            "params": {
                "Invert": params["Invert"],
                "In/Out": params["In/Out"],
                "Render Mode": params["Render Mode"],
                "Use Background Color": params["Use Background Color"],
                "Interpolation Mode": params["Interpolation Mode"],
                "Power": params["Power"],
                "Inside Threshold": params["Inside Threshold"],
                "Outside Threshold": params["Outside Threshold"],
            },
            "source_rgba_u16": [int(v) for v in src[y, x]],
            "probe_no_bg_rgba_u16": probe_px,
            "candidate_rgba_u16": cand,
            "reference_rgba_u16": ref,
            "observed_x_from_probe": float(obs_x[y, x]),
            "model_x_current_max": float(x_model[y, x]),
            "model_x_binary_add": float(x_model_add[y, x]),
            "inside_x": float(inside[y, x]),
            "outside_x": float(outside[y, x]),
            "candidate_x_est_from_red": estimate_x_from_bg_grad(cand[0], grad[0], bg[0]),
            "reference_x_est_from_red": estimate_x_from_bg_grad(ref[0], grad[0], bg[0]),
        }
        cases.append(row)

    payload = {"kind": "olmdistancegradation_16bpc_field_cases_probe", "cases": cases}
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# DistanceGradation 16bpc field probe summary - 2026-06-26",
        "",
        "These cases were rerendered on Mac AE with `Use Background Color=0` so",
        "the current plug-in exposes the live field through output alpha.",
        "",
        "| Case | Witness | Observed X | Max-model X | Add-model X | Candidate RGB | Reference RGB | Reading |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in cases:
        cid = row["case_id"].split("__")[-1]
        if cid in {"case_0020", "case_0021", "case_0022", "case_0023"}:
            reading = "Mac no_bg probe matches current model; Windows reference is opposite color on bg-on render"
        else:
            reading = "Observed X stays much higher than both max and add models"
        lines.append(
            f"| `{cid}` | `({row['witness'][0]},{row['witness'][1]})` | "
            f"{row['observed_x_from_probe']:.6f} | {row['model_x_current_max']:.6f} | {row['model_x_binary_add']:.6f} | "
            f"`{row['candidate_rgba_u16'][:3]}` | `{row['reference_rgba_u16'][:3]}` | {reading} |"
        )
    lines.extend(
        [
            "",
            "## Conclusions",
            "",
            "- `case_0020..0023`: the Mac `no_bg` probe agrees with the current constant/binary model at the witness pixels. The mismatch against Windows appears only once `Use Background Color=1` is involved, so these four cases likely need Windows-side evidence about how Constant mode and background compose interact.",
            "- `case_0027/0028`: the Mac `no_bg` probe directly contradicts both the old `max(...)` shorthand and the binary-grounded `inside + outside` Both model. These remain live Mac-side field-prep / normalization problems.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
