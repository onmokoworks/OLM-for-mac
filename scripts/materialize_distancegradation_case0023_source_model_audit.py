#!/usr/bin/env python3
"""Audit DG case_0023 Mac source-model field samples against AEX CPU helper samples."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

import opencv_impls as ocv  # noqa: E402

AEX_CPU_SIMU_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_aex_cpu_simu_fullframe_20260707.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex-cpu-simu-json", type=Path, default=AEX_CPU_SIMU_JSON)
    parser.add_argument(
        "--stamp",
        default=datetime.now().strftime("%Y%m%d"),
        help="Date stamp for output filenames (default: today in local time).",
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args()


def load_verify_manifest():
    path = ROOT / "refs" / "scripts" / "verify_manifest.py"
    spec = importlib.util.spec_from_file_location("verify_manifest_for_dg_source_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def constant_binary_field(mask: np.ndarray, threshold: int) -> np.ndarray:
    raw = ocv.cvdisttransform_l2_precise_native(mask)
    return np.where(raw > float(threshold), 1.0, 0.0).astype(np.float32)


def build_report(aex_data: dict[str, Any]) -> dict[str, Any]:
    verify = load_verify_manifest()
    source_png = ROOT / aex_data["source_png"]
    rgba = verify.load_rgba(source_png)
    mask = np.where(rgba[..., 3].astype(np.float64) > 0.0, 255, 0).astype(np.uint8)
    inside = constant_binary_field(mask, int(aex_data["inside_threshold"]))
    outside_mask = np.where(mask != 0, 0, 255).astype(np.uint8)
    outside = constant_binary_field(outside_mask, int(aex_data["outside_threshold"]))
    both = np.minimum(inside + outside, 1.0).astype(np.float32)

    comparisons = []
    for sample in aex_data["samples"]:
        x, y = sample["xy"]
        local = {
            "inside_field": float(inside[y, x]),
            "outside_field": float(outside[y, x]),
            "both_add_saturate_field": float(both[y, x]),
        }
        expected = {
            "inside_field": float(sample["inside_field"]),
            "outside_field": float(sample["outside_field"]),
            "both_add_saturate_field": float(sample["both_add_saturate_field"]),
        }
        comparisons.append(
            {
                "xy": [x, y],
                "mac_source_model": local,
                "aex_cpu_helper": expected,
                "match": local == expected,
            }
        )
    all_match = all(row["match"] for row in comparisons)
    return {
        "kind": "olmdistancegradation_case0023_source_model_audit",
        "materialized_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "source-model-matches-aex-helper-samples" if all_match else "source-model-mismatch",
        "source": "scripts/materialize_distancegradation_case0023_source_model_audit.py",
        "input_aex_cpu_simu_json": str(Path(aex_data.get("input_path", "") or AEX_CPU_SIMU_JSON).relative_to(ROOT))
        if Path(aex_data.get("input_path", "") or AEX_CPU_SIMU_JSON).is_absolute()
        else str(AEX_CPU_SIMU_JSON.relative_to(ROOT)),
        "source_png": aex_data["source_png"],
        "inside_threshold": int(aex_data["inside_threshold"]),
        "outside_threshold": int(aex_data["outside_threshold"]),
        "mask_channel": aex_data["mask_channel"],
        "samples": comparisons,
        "safe_claim": (
            "For the recorded case_0023 witness points, a Mac-source-shaped Constant/BOTH field model "
            "matches the Windows AEX CPU helper samples. This is not AE exact, but it makes broad "
            "field-helper retuning unsafe and keeps the live lane on reference/export/source ownership."
        ),
        "limitations": [
            "comparison is sampled at the recorded witness points, not a full image diff against an exported Windows field buffer",
            "model uses the already-grounded OpenCV-detour EDT implementation rather than re-entering the Mac plug-in binary",
            "this does not settle stale packaged PNG vs current Windows Software export provenance",
        ],
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        f"# OLMDistanceGradation case_0023 Source Model Audit - {report['materialized_at'][:10]}",
        "",
        f"- Status: `{report['status']}`",
        f"- Source: `{report['source']}`",
        f"- AEX helper input: `{report['input_aex_cpu_simu_json']}`",
        f"- Source PNG: `{report['source_png']}`",
        f"- Inside threshold: `{report['inside_threshold']}`",
        f"- Outside threshold: `{report['outside_threshold']}`",
        f"- Safe claim: {report['safe_claim']}",
        "",
        "| XY | Mac inside | AEX inside | Mac outside | AEX outside | Mac both | AEX both | match |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["samples"]:
        xy = row["xy"]
        mac = row["mac_source_model"]
        aex = row["aex_cpu_helper"]
        lines.append(
            f"| `({xy[0]},{xy[1]})` | `{mac['inside_field']}` | `{aex['inside_field']}` | "
            f"`{mac['outside_field']}` | `{aex['outside_field']}` | "
            f"`{mac['both_add_saturate_field']}` | `{aex['both_add_saturate_field']}` | `{row['match']}` |"
        )
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    aex_path = args.aex_cpu_simu_json.resolve()
    aex_data = json.loads(aex_path.read_text(encoding="utf-8"))
    aex_data["input_path"] = str(aex_path)
    report = build_report(aex_data)
    output_json = args.output_json or ROOT / "refs/conformance" / f"olmdistancegradation_case0023_source_model_audit_{args.stamp}.json"
    output_md = args.output_md or ROOT / "refs/conformance" / f"olmdistancegradation_case0023_source_model_audit_{args.stamp}.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_md.write_text(render_md(report), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    return 0 if report["status"] == "source-model-matches-aex-helper-samples" else 1


if __name__ == "__main__":
    raise SystemExit(main())
