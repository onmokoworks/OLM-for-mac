#!/usr/bin/env python3
"""Audit whether DistanceGradation BOTH `add` vs `max` can diverge locally.

The Windows CPU binary path for BOTH is grounded as cv::add/saturating-add in
the current notes, while older local shorthand used max(inside, outside). This
script checks the existing 16bpc reference cases under the current full-res
mask model and reports whether that distinction is exposed before any future
resize/downsample lane is considered.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json"
REFERENCE_DIR = MANIFEST.parent
VERIFY_MANIFEST = ROOT / "refs/scripts/verify_manifest.py"
DG_CLI = ROOT / "refs/scripts/olmdistancegradation_cli.py"
OUT_JSON = ROOT / "refs/conformance/olmdistancegradation_both_add_overlap_audit_20260707.json"
OUT_MD = ROOT / "refs/conformance/olmdistancegradation_both_add_overlap_audit_20260707.md"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = load_module(VERIFY_MANIFEST, "verify_manifest_for_dg_both_overlap")
DG = load_module(DG_CLI, "olmdistancegradation_cli_for_both_overlap")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--reference-dir", type=Path, default=REFERENCE_DIR)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def params_for_case(case: dict[str, Any]) -> dict[str, object]:
    out: dict[str, object] = {}
    for effect in case.get("effects", []):
        if effect.get("match_name") != "OLM Distance Gradation" and effect.get("name") != "Distance Gradation":
            continue
        for param in effect.get("params", []):
            name = param.get("name")
            if name:
                out[DG.key_for_name(str(name))] = param.get("value")
    return out


def analyze_case(case: dict[str, Any], reference_dir: Path) -> dict[str, Any] | None:
    params = params_for_case(case)
    if int(params.get("in_out", 0)) != DG.IN_OUT_BOTH:
        return None
    image = VERIFY.load_rgba(reference_dir / case["before_effects_frame"])
    rgba = image.astype(np.float32)
    max_value = 65535.0 if rgba.dtype == np.float32 and image.dtype == np.uint16 else 255.0
    alpha = rgba[..., 3] / max_value
    mask = (alpha > 0.0).astype(np.uint8)
    ds = 1.0
    inside = DG.dt_to_normalized(mask, int(params.get("inside_threshold", 128)), ds)
    outside = DG.dt_to_normalized(1 - mask, int(params.get("outside_threshold", 128)), ds)
    both_max = np.maximum(inside, outside).astype(np.float32)
    both_add = np.minimum(inside + outside, 1.0).astype(np.float32)
    diff = np.abs(both_add - both_max)
    nonzero = np.argwhere(diff > 1e-7)
    sample = None
    if nonzero.size:
        y, x = (int(v) for v in nonzero[0])
        sample = {
            "xy": [x, y],
            "inside": float(inside[y, x]),
            "outside": float(outside[y, x]),
            "max": float(both_max[y, x]),
            "add": float(both_add[y, x]),
            "delta": float(diff[y, x]),
        }
    return {
        "case_id": case["id"],
        "bits_per_channel": case.get("bits_per_channel"),
        "interpolation_mode": int(params.get("interpolation_mode", 0)),
        "blur_mode": int(params.get("blur_mode", 0)),
        "inside_threshold": int(params.get("inside_threshold", 0)),
        "outside_threshold": int(params.get("outside_threshold", 0)),
        "nonzero_px": int(nonzero.shape[0]),
        "max_delta": float(diff.max()) if diff.size else 0.0,
        "sample": sample,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDistanceGradation BOTH add-vs-max overlap audit - 2026-07-07",
        "",
        "This is a narrow local-model audit. It does not claim AE exact. It only",
        "checks whether the existing 16bpc full-resolution masks expose a difference",
        "between `max(inside, outside)` and `min(inside + outside, 1)` before any",
        "future resize/downsample path is involved.",
        "",
        f"- Manifest: `{report['manifest']}`",
        f"- BOTH cases checked: `{report['both_case_count']}`",
        f"- Cases with add-vs-max divergence: `{report['divergent_case_count']}`",
        f"- Total divergent pixels: `{report['total_divergent_px']}`",
        f"- Decision: `{report['decision']}`",
        "",
        "| Case | Interp | Blur | Inside | Outside | Divergent px | Max delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["cases"]:
        lines.append(
            f"| `{row['case_id']}` | {row['interpolation_mode']} | {row['blur_mode']} | "
            f"{row['inside_threshold']} | {row['outside_threshold']} | "
            f"{row['nonzero_px']} | {row['max_delta']:.9g} |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- In the current full-resolution binary-mask model, inside/outside supports are complementary.",
            "- Therefore `cv::add` and `max` do not diverge on these 16bpc BOTH cases.",
            "- Keep the `cv::add` fact in the IR, but do not use it as an implementation lever for the current residuals unless a resize/downsample witness proves overlapping support.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    rows = []
    for case in manifest.get("cases", []):
        if "olmdistancegradation" not in case.get("id", ""):
            continue
        row = analyze_case(case, args.reference_dir)
        if row is not None:
            rows.append(row)
    divergent = [row for row in rows if row["nonzero_px"] > 0]
    report = {
        "kind": "olmdistancegradation_both_add_overlap_audit",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manifest": str(args.manifest.relative_to(ROOT)),
        "reference_dir": str(args.reference_dir.relative_to(ROOT)),
        "both_case_count": len(rows),
        "divergent_case_count": len(divergent),
        "total_divergent_px": int(sum(row["nonzero_px"] for row in divergent)),
        "decision": "no-current-fullres-add-vs-max-lever" if not divergent else "add-vs-max-diverges-in-current-cases",
        "cases": rows,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    print(f"decision={report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
