#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
VERIFY_MANIFEST = ROOT / "refs" / "scripts" / "verify_manifest.py"


def load_verify_manifest():
    spec = importlib.util.spec_from_file_location("verify_manifest", VERIFY_MANIFEST)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {VERIFY_MANIFEST}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


load_rgba = load_verify_manifest().load_rgba

SRC = ROOT / "handoff" / "ae_pixel_validation_20260618" / "requests" / "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625" / "input" / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0027_before_effects.png"
PROBE_ROOT = ROOT / "handoff" / "ae_pixel_validation_20260618" / "probes" / "distancegradation_case0027_variants"
OUT_JSON = ROOT / "refs" / "conformance" / "olmdistancegradation_16bpc_case0027_probe_x_20260626.json"
OUT_MD = ROOT / "refs" / "conformance" / "olmdistancegradation_16bpc_case0027_probe_x_20260626.md"


def model_fields(alpha: np.ndarray) -> dict[str, np.ndarray]:
    mask = (alpha > 0).astype(np.uint8)
    inside = distance_transform_edt(mask)
    outside = distance_transform_edt(1 - mask)
    inside = np.minimum(inside, 158.0)
    outside = np.minimum(outside, 13.0)
    inside /= max(float(inside.max()), 1.0)
    outside /= max(float(outside.max()), 1.0)
    both = np.maximum(inside, outside)
    both_add = inside + outside
    power = 2.59740734100342
    return {
        "current_max_nopow": both,
        "current_max_pow": np.power(both, power),
        "binary_grounded_add_nopow": both_add,
        "binary_grounded_add_pow": np.power(both_add, power),
        "outside_nopow": outside,
        "outside_pow": np.power(outside, power),
        "inside_nopow": inside,
        "inside_pow": np.power(inside, power),
    }


def compare(obs: np.ndarray, model: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(np.mean(np.abs(obs - model))),
        "rmse": float(np.sqrt(np.mean((obs - model) ** 2))),
        "corr": float(np.corrcoef(obs.reshape(-1), model.reshape(-1))[0, 1]),
    }


def main() -> int:
    src = load_rgba(SRC).astype(np.float32)
    alpha = src[..., 3] / 65535.0
    layer_no_bg = load_rgba(PROBE_ROOT / "layer_no_bg.png").astype(np.float32)
    layer_bg = load_rgba(PROBE_ROOT / "layer_bg.png").astype(np.float32)
    ref = load_rgba(
        ROOT
        / "refs"
        / "win_references"
        / "olm_bitdepth_16bpc_normalized_exact_20260625"
        / "OLMbit-depthconformancebatch"
        / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0027.png"
    ).astype(np.float32)

    observed_x = layer_no_bg[..., 3] / 65535.0
    models = model_fields(alpha)
    scores = {name: compare(observed_x, field) for name, field in models.items()}

    witnesses = []
    points = [(3, 0), (14, 0), (397, 281), (438, 1), (15, 0), (16, 0), (17, 0)]
    for x, y in points:
        witnesses.append(
            {
                "x": x,
                "y": y,
                "observed_x": float(observed_x[y, x]),
                "source_rgba_u16": [int(v) for v in src[y, x]],
                "layer_bg_u16": [int(v) for v in layer_bg[y, x]],
                "layer_no_bg_u16": [int(v) for v in layer_no_bg[y, x]],
                "reference_u16": [int(v) for v in ref[y, x]],
                "models": {name: float(field[y, x]) for name, field in models.items()},
            }
        )

    payload = {
        "kind": "olmdistancegradation_case0027_probe_x_analysis",
        "source": str(SRC.relative_to(ROOT)),
        "probe_root": str(PROBE_ROOT.relative_to(ROOT)),
        "scores": scores,
        "witnesses": witnesses,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# DistanceGradation case_0027 observed X probe - 2026-06-26",
        "",
        "Observed `X` is reconstructed from `layer_no_bg` alpha, because for",
        "`In/Out=Both` and `Use Background Color=0`, the current Mac implementation",
        "writes `out_a = X`.",
        "",
        "## Model scores",
        "",
        "| Model | MAE | RMSE | Corr |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name, score in sorted(scores.items()):
        lines.append(f"| `{name}` | {score['mae']:.6f} | {score['rmse']:.6f} | {score['corr']:.6f} |")
    lines.extend(
        [
            "",
            "## Witnesses",
            "",
            "| Point | Observed X | current_max_pow | binary_add_pow | outside_pow | Reading |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in witnesses:
        m = row["models"]
        if row["observed_x"] > m["binary_grounded_add_pow"] + 0.1:
            reading = "observed field stays much closer to 1 than both max and add models"
        elif row["observed_x"] > m["current_max_pow"] + 0.1:
            reading = "observed field is above the old max model but closer to add"
        else:
            reading = "closer to current/binary-grounded model"
        lines.append(
            f"| `({row['x']},{row['y']})` | {row['observed_x']:.6f} | "
            f"{m['current_max_pow']:.6f} | {m['binary_grounded_add_pow']:.6f} | "
            f"{m['outside_pow']:.6f} | {reading} |"
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            "- The Mac AE probe does not support the earlier `compose/background-branch is dead` hypothesis.",
            "- `layer_bg` and `layer_no_bg` differ materially when read as true 16-bit PNGs, and `grad_bg` / `grad_no_bg` also differ in alpha and RGB once decoded natively.",
            "- The active mismatch for `case_0027` is upstream: the observed field `X` extracted from `layer_no_bg` alpha stays much closer to `1.0` than either the old `max(inside, outside)` shorthand or the binary-grounded `inside + outside` Both model predicts at key witness pixels.",
            "- So the next correction target is still field prep / normalization / threshold ownership, not the final RGB compose branch.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
