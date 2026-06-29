#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
VERIFY_MANIFEST = ROOT / "refs" / "scripts" / "verify_manifest.py"
RETURN_ROOT = ROOT / "refs" / "win_references" / "olmdistancegradation_16bpc_bg_compose_variants_20260626" / "DistanceGradation"
MAC_PROBE_ROOT = ROOT / "handoff" / "ae_pixel_validation_20260618" / "probes" / "distancegradation_field_cases"
OUT_JSON = ROOT / "refs" / "conformance" / "olmdistancegradation_16bpc_bg_compose_variants_return_20260627.json"
OUT_MD = ROOT / "refs" / "conformance" / "olmdistancegradation_16bpc_bg_compose_variants_return_20260627.md"

FOCUS = {
    "olmdistancegradation_case_0020": {"x": 951, "y": 417, "mac_case": "0020"},
    "olmdistancegradation_case_0021": {"x": 951, "y": 417, "mac_case": "0021"},
    "olmdistancegradation_case_0022": {"x": 4, "y": 0, "mac_case": "0022"},
    "olmdistancegradation_case_0023": {"x": 1699, "y": 7, "mac_case": "0023"},
}


def load_verify_manifest():
    spec = importlib.util.spec_from_file_location("verify_manifest", VERIFY_MANIFEST)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {VERIFY_MANIFEST}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = load_verify_manifest()


def diff_stats(a: np.ndarray, b: np.ndarray) -> dict[str, float | int]:
    delta = np.abs(a.astype(np.int64) - b.astype(np.int64))
    nz = np.any(delta != 0, axis=-1)
    return {
        "max_diff": int(delta.max()),
        "mean_diff": float(delta.mean()),
        "nonzero_px": int(nz.sum()),
    }


def main() -> int:
    manifest = json.loads((RETURN_ROOT / "reference_manifest.json").read_text(encoding="utf-8"))
    cases_out = []

    for stem, focus in FOCUS.items():
        x = focus["x"]
        y = focus["y"]
        on_case = next(c for c in manifest["cases"] if c["id"] == f"{stem}_bg_on_control")
        off_case = next(c for c in manifest["cases"] if c["id"] == f"{stem}_bg_off_variant")
        on_img = VERIFY.load_rgba(RETURN_ROOT / "renders" / on_case["frame"])
        off_img = VERIFY.load_rgba(RETURN_ROOT / "renders" / off_case["frame"])
        mac_probe = VERIFY.load_rgba(MAC_PROBE_ROOT / f"olmdistancegradation_extended__case_{focus['mac_case']}__no_bg.png")

        params = {p.get("name"): p.get("value") for p in on_case["effects"][0]["params"] if p.get("name")}
        row = {
            "case_id": stem.split("_case_")[-1],
            "witness": [x, y],
            "params": {
                "Invert": params.get("Invert"),
                "In/Out": params.get("In/Out"),
                "Inside Threshold": params.get("Inside Threshold"),
                "Outside Threshold": params.get("Outside Threshold"),
                "Render Mode": params.get("Render Mode"),
                "Interpolation Mode": params.get("Interpolation Mode"),
                "Use Background Color (on)": 1,
                "Use Background Color (off)": 0,
                "Gradation Color": params.get("Gradation Color"),
                "BG Color": params.get("BG Color "),
            },
            "windows_bg_on_witness_rgba_u16": [int(v) for v in on_img[y, x]],
            "windows_bg_off_witness_rgba_u16": [int(v) for v in off_img[y, x]],
            "mac_no_bg_probe_witness_rgba_u16": [int(v) for v in mac_probe[y, x]],
            "windows_bg_on_vs_off": diff_stats(on_img, off_img),
            "windows_bg_off_vs_mac_probe": diff_stats(off_img, mac_probe),
        }
        cases_out.append(row)

    payload = {
        "kind": "olmdistancegradation_16bpc_bg_compose_variants_return",
        "cases": cases_out,
        "conclusion": [
            "The Windows bg_off variants do not validate the earlier Mac no_bg field-probe assumption.",
            "For case_0020..0022, the Windows bg_off witness is still the gradation-color opaque output at the sampled pixel, not the transparent Mac no_bg probe value.",
            "Only case_0023 flips to transparent at the sampled witness when Use Background Color is disabled.",
            "So the remaining 16bpc case_0020..0023 gap is not confined to the bg-on compose branch; the Windows bg_off path itself now disagrees with the current Mac no_bg probe on all four focused cases.",
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# DistanceGradation 16bpc bg-compose return audit - 2026-06-27",
        "",
        "Windows returned explicit `Use Background Color=1` and `=0` variants for",
        "`case_0020..0023`. This audit compares those variants at the focused witness",
        "pixels and against the earlier Mac `no_bg` probe.",
        "",
        "| Case | Witness | Windows bg_on | Windows bg_off | Mac no_bg probe | Reading |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in cases_out:
        case_id = row["case_id"]
        on_px = row["windows_bg_on_witness_rgba_u16"]
        off_px = row["windows_bg_off_witness_rgba_u16"]
        mac_px = row["mac_no_bg_probe_witness_rgba_u16"]
        if case_id in {"0020", "0021", "0022"}:
            reading = "Windows bg_off witness stays grad-color opaque; does not match prior Mac no_bg probe"
        else:
            reading = "Windows bg_off witness flips transparent, but still differs from prior Mac no_bg probe"
        lines.append(
            f"| `case_{case_id}` | `({row['witness'][0]},{row['witness'][1]})` | "
            f"`{on_px}` | `{off_px}` | `{mac_px}` | {reading} |"
        )
    lines += [
        "",
        "## Whole-frame diffs",
        "",
        "| Case | Windows bg_on vs bg_off nonzero px | Windows bg_off vs Mac no_bg probe nonzero px |",
        "| --- | ---: | ---: |",
    ]
    for row in cases_out:
        lines.append(
            f"| `case_{row['case_id']}` | {row['windows_bg_on_vs_off']['nonzero_px']} | {row['windows_bg_off_vs_mac_probe']['nonzero_px']} |"
        )
    lines += [
        "",
        "## Conclusion",
        "",
        "- The Windows `bg_off` variants invalidate the earlier simplification that `case_0020..0023` only disagree once `Use Background Color=1` participates.",
        "- `case_0020..0022` keep the gradation-color opaque witness even with `Use Background Color=0` on Windows.",
        "- `case_0023` does change meaningfully between bg_on and bg_off, but the returned bg_off still does not match the prior Mac no_bg probe over the whole frame.",
        "- So the active 16bpc DistanceGradation question is again upstream of just the bg-on compose branch.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary_json={OUT_JSON}")
    print(f"summary_md={OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
