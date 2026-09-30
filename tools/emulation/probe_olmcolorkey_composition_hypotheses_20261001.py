#!/usr/bin/env python3
"""Counterfactual Thin kernels compared to pinned legal-popup AEX measurements.

Changes only temporary source copies. Does not admit new production tuples.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import probe_olmcolorkey_legal_composition_20261001 as base

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
BASELINE = ROOT / "reports/colorkey_legal_composition_20261001.json"
REPORT = ROOT / "reports/colorkey_composition_hypotheses_20261001.json"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def kernel_variants(original: str) -> dict[str, str]:
    positive_scale = base.replace_once(original,
        "const float distance_scale = (info.color_keep || OLMCKPixelTraits<PixelT>::is_32bpc()) ? 1.0f : 255.0f;",
        "const float distance_scale = OLMCKPixelTraits<PixelT>::is_32bpc() ? 1.0f : 255.0f;")
    positive_limit = base.replace_once(positive_scale,
        "const float limit = (float)info.edge_thin_amount +\n\t\t    ((info.color_keep &&\n\t\t      (info.edge_thin_distance_type == 0 || info.edge_thin_distance_type == 2))\n\t\t         ? 2.0f : 0.0f);",
        "const float limit = (float)info.edge_thin_amount;")
    negative_metric = base.replace_once(positive_limit,
        "const A_long thin_distance_type = info.color_keep\n\t\t    ? info.edge_thin_distance_type : 1;",
        "const A_long thin_distance_type = 1;")
    negative_start = positive_limit.index("\tif (info.edge_thin_amount < 0.0) {")
    negative_end = positive_limit.index("\t} else if (info.edge_thin_amount > 0.0) {", negative_start)
    boundary_negative = positive_limit[:negative_start] + '''\tif (info.edge_thin_amount < 0.0) {
        std::vector<u_char> boundary = Boundary8(matched, w, h);
        std::vector<float> dist = MatteDistanceTo(boundary, w, h, info.edge_thin_distance_type);
        const float scale = OLMCKPixelTraits<PixelT>::is_32bpc() ? 1.0f : 255.0f;
        const float amount = (float)std::fabs(info.edge_thin_amount);
        for (A_long i = 0; i < w * h; ++i) {
            matched[i] = (matched[i] && dist[i] * scale >= amount) ? 1 : 0;
        }
''' + positive_limit[negative_end:]
    alpha_gate = '''\tif (info.color_keep && (info.edge_thin_amount != 0.0 || info.edge_blur_amount != 0.0)) {
        for (A_long y = 0; y < h; ++y) for (A_long x = 0; x < w; ++x) {
            if (OLMCKPixelTraits<PixelT>::a(*PixelAtConst<PixelT>(
                    input, x + input_offset_x, y + input_offset_y)) == 0.0f)
                matched[(size_t)y * (size_t)w + (size_t)x] = 0;
        }
    }
'''
    alpha_boundary = base.replace_once(boundary_negative,
        "\tif (info.edge_thin_amount < 0.0) {", alpha_gate + "\tif (info.edge_thin_amount < 0.0) {")
    alpha_boundary = base.replace_once(alpha_boundary,
        "\tstd::vector<u_char> keep_mask((size_t)w * (size_t)h, 0);",
        alpha_gate + "\tstd::vector<u_char> keep_mask((size_t)w * (size_t)h, 0);")
    alpha_all_modes = alpha_boundary.replace(
        "if (info.color_keep && (info.edge_thin_amount != 0.0 || info.edge_blur_amount != 0.0))",
        "if (info.edge_thin_amount != 0.0 || info.edge_blur_amount != 0.0)")
    final_complement = base.replace_once(alpha_boundary,
        "\tconst size_t pixel_count = (size_t)w * (size_t)h;", r'''	// Native final callbacks subtract the finished matched matte from source.
    if (!info.color_keep && (info.edge_thin_amount != 0.0 || info.edge_blur_amount != 0.0)) {
        OLMColorKeyInfo matte_info = info;
        matte_info.color_keep = true;
        matte_info.enable_replace = false;
        PF_Err err = RenderTyped<PixelT>(input, output, matte_info);
        if (err) return err;
        for (A_long y = 0; y < h; ++y) for (A_long x = 0; x < w; ++x) {
            const PixelT *inP = PixelAtConst<PixelT>(input, x + input_offset_x, y + input_offset_y);
            PixelT *outP = PixelAt<PixelT>(output, x, y);
            outP->alpha = inP->alpha - outP->alpha;
        }
        return PF_Err_NONE;
    }
	const size_t pixel_count = (size_t)w * (size_t)h;''')
    return {"current": original, "positive_typed_scale": positive_scale,
                "positive_scale_no_type2_offset": positive_limit,
                "negative_chessboard_control": negative_metric,
                "negative_native_boundary_strict": boundary_negative,
                "native_boundary_alpha_matte": alpha_boundary,
                "native_boundary_alpha_all_modes": alpha_all_modes,
                "native_final_complement": final_complement}


def main() -> int:
    measured = json.loads(BASELINE.read_text())
    original = SOURCE.read_text()
    if sha(SOURCE.read_bytes()) != measured["production_source_sha256"]:
        raise RuntimeError("baseline production identity drift")
    if sha(Path(base.__file__).read_bytes()) != measured["probe_sha256"]:
        raise RuntimeError("baseline probe identity drift")
    if sha(base.retained.actual_probe.AEX.read_bytes()) != measured["actual_aex_sha256"]:
        raise RuntimeError("baseline AEX identity drift")
    for rel, digest in measured["dependency_sha256"].items():
        if sha((ROOT / rel).read_bytes()) != digest:
            raise RuntimeError(f"baseline dependency drift: {rel}")
    if measured["case_count"] != 108 or len(measured["cases"]) != 108:
        raise RuntimeError("requires all-depth baseline")
    variants = kernel_variants(original)
    result = []
    for name, body in variants.items():
        with tempfile.TemporaryDirectory(prefix="olmck_counterfactual_") as raw:
            modified = Path(raw) / "OLMColorKey.cpp"
            body = base.replace_once(body, '#include "OLMColorKey.h"',
                                     '#include "' + str(SOURCE.with_suffix(".h")) + '"')
            modified.write_text(body)
            saved = base.retained.mac_adapter.SOURCE
            try:
                base.retained.mac_adapter.SOURCE = modified
                output = base.production(("PF8", "PF16", "PF32"))
            finally:
                base.retained.mac_adapter.SOURCE = saved
        offset, rows = 0, []
        for case in measured["cases"]:
            size = (13 * base.retained.FORMATS[case["depth"]] + 8) * 11
            candidate = output[offset:offset + size]
            offset += size
            if len(candidate) != size:
                raise RuntimeError("counterfactual output truncated")
            digest = sha(candidate)
            if name == "current" and digest != case["production_sha256"]:
                raise RuntimeError("baseline replay drift")
            rows.append({"replace": case["replace"], "type": case["thin_distance_type"],
                         "mode": case["mode"]["name"], "depth": case["depth"],
                         "exact": digest == case["actual_sha256"], "baseline_exact": case["exact"],
                         "candidate_sha256": digest})
        if offset != len(output):
            raise RuntimeError("counterfactual output tail")
        item = {"name": name, "exact_count": sum(r["exact"] for r in rows),
                "regressions": sum(r["baseline_exact"] and not r["exact"] for r in rows),
                "candidate_source_sha256": sha(body.encode()), "cases": rows}
        result.append(item)
        print(json.dumps({k: item[k] for k in ("name", "exact_count", "regressions")}), flush=True)
    report = {"schema": "olmcolorkey.composition-counterfactual/1", "date": "2026-10-01",
              "baseline_sha256": sha(BASELINE.read_bytes()), "source_sha256": sha(SOURCE.read_bytes()),
              "probe_sha256": sha(Path(__file__).read_bytes()), "variants": result,
              "scope": "Temporary core-source variants versus retained 108 AEX worker measurements; baseline current replay required; no production edits, no public admission, no new AEX/native capture",
              "interpretation": "Counterfactual agreement is a causal hypothesis, not general algorithm recovery or complete conformance"}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
