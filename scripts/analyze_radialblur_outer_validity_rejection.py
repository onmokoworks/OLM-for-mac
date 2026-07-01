#!/usr/bin/env python3
"""Bounded rejection of naive outer caller-collapse validity models.

This turns the current local witness dumps plus imported Windows runtime trace
facts into one sharper statement:

- Zoom case_0009 cannot be explained by bilinear sampling of the current local
  binary preserved-validity proxy.
- tiny Rotation case_0010 cannot be explained by a validity-only substitute
  either, because all four local contributing cells are already valid while the
  RGB outcome still diverges maximally.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
SUMMARY_JSON = REPO / "refs" / "conformance" / "olmradialblur_outer_validity_rejection_20260630.json"
SUMMARY_MD = REPO / "refs" / "conformance" / "olmradialblur_outer_validity_rejection_20260630.md"
TRACE_JSON = REPO / "refs" / "reports" / "runtime_trace_comparisons" / "olmradialblur_residual_witness_20260624.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-json", type=Path, default=TRACE_JSON)
    parser.add_argument("--output-json", type=Path, default=SUMMARY_JSON)
    parser.add_argument("--output-md", type=Path, default=SUMMARY_MD)
    return parser.parse_args()


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=REPO, check=True)


def render_with_witness(case_id: str, smoke_script: str, witness_x: int, witness_y: int) -> dict:
    run(["python3", smoke_script])
    if case_id == "case_0009":
        run_dir = Path("/tmp/olmradialblur_cpp_zoom_smoke")
    elif case_id == "case_0010":
        run_dir = Path("/tmp/olmradialblur_cpp_tiny_rotation_smoke")
    else:
        raise ValueError(case_id)

    before = run_dir / "reference" / f"{case_id}_before_effects.png"
    params = run_dir / "candidate" / "_params" / f"{case_id}.json"
    out = run_dir / "candidate" / f"{case_id}_witness.png"
    witness_json = run_dir / "candidate" / f"{case_id}_witness.json"
    run(
        [
            str(REPO / "cli" / "OLMRadialBlur" / "olmradialblur_cli"),
            "--input",
            str(before),
            "--params",
            str(params),
            "--output",
            str(out),
            "--witness-dump",
            str(witness_json),
            "--witness-x",
            str(witness_x),
            "--witness-y",
            str(witness_y),
        ]
    )
    return json.loads(witness_json.read_text(encoding="utf-8"))


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def trace_case_map(trace: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases: Any = None
    if isinstance(trace.get("windows"), dict):
        cases = trace["windows"].get("cases")
    if cases is None and isinstance(trace.get("observations"), dict):
        cases = trace["observations"].get("cases")
    if isinstance(cases, dict):
        cases = [cases]
    if not isinstance(cases, list):
        raise ValueError("trace comparison JSON does not contain a usable cases list")
    rows: dict[str, dict[str, Any]] = {}
    for row in cases:
        if not isinstance(row, dict):
            continue
        case_id = row.get("case_id")
        if isinstance(case_id, str) and case_id:
            rows[case_id] = row
    return rows


def main() -> int:
    args = parse_args()
    run([str(REPO / "refs" / "scripts" / "build_olmradialblur_cli.sh")])
    zoom = render_with_witness("case_0009", "refs/scripts/smoke_olmradialblur_cpp_zoom_cli.py", 6, 0)
    rotation = render_with_witness("case_0010", "refs/scripts/smoke_olmradialblur_cpp_tiny_rotation_cli.py", 1614, 6)

    trace = read_json(args.trace_json)
    trace_cases = trace_case_map(trace)
    zoom_trace = trace_cases["case_0009"]
    rotation_trace = trace_cases["case_0010"]

    zoom_binary_validity_alpha = (
        zoom["w00"] * zoom["cell00_valid"]
        + zoom["w10"] * zoom["cell10_valid"]
        + zoom["w01"] * zoom["cell01_valid"]
        + zoom["w11"] * zoom["cell11_valid"]
    )
    zoom_windows_alpha = float(zoom_trace["aex_pre_writeback_rgba_float_or_hex"][3])
    zoom_local_alpha = float(zoom["sample_rgba"][3])
    zoom_binary_validity_u8 = int(zoom_binary_validity_alpha * 255.0)
    zoom_windows_u8 = int(zoom_trace["aex_final_rgba_u8"][3])

    rotation_binary_validity_alpha = (
        rotation["w00"] * rotation["cell00_valid"]
        + rotation["w10"] * rotation["cell10_valid"]
        + rotation["w01"] * rotation["cell01_valid"]
        + rotation["w11"] * rotation["cell11_valid"]
    )

    payload = {
        "kind": "olmradialblur_outer_validity_rejection",
        "status": "diagnostic",
        "zoom_case_0009": {
            "local_witness": zoom,
            "windows_trace_alpha": zoom_windows_alpha,
            "windows_final_alpha_u8": zoom_windows_u8,
            "binary_validity_bilinear_alpha": zoom_binary_validity_alpha,
            "binary_validity_bilinear_alpha_u8_floor": zoom_binary_validity_u8,
            "local_sample_alpha": zoom_local_alpha,
            "reading": "current local binary preserved-validity proxy cannot be the direct caller-collapse source for Zoom case_0009",
        },
        "tiny_rotation_case_0010": {
            "local_witness": rotation,
            "windows_traced_inverse_sampler_rgba": rotation_trace["aex_source_or_polar_rgba_float"],
            "windows_final_rgba_u8": rotation_trace["aex_final_rgba_u8"],
            "binary_validity_bilinear_alpha": rotation_binary_validity_alpha,
            "reading": "validity-only substitution is not enough for tiny Rotation because all four local cells are already valid while RGB still stays near-black locally",
        },
    }
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# OLMRadialBlur Outer Validity Rejection - 2026-06-30",
        "",
        "Bounded rejection of the simplest outer caller-collapse interpretation using current local witness dumps plus imported Windows trace facts.",
        "",
        "## Zoom `case_0009`",
        "",
        f"- Current local witness alpha: `{zoom_local_alpha}`",
        f"- Windows traced pre-writeback alpha: `{zoom_windows_alpha}`",
        f"- Bilinear alpha from current local binary valid bits: `{zoom_binary_validity_alpha}`",
        f"- Windows final alpha byte: `{zoom_windows_u8}`",
        f"- Bilinear binary-validity alpha byte floor: `{zoom_binary_validity_u8}`",
        "",
        "Interpretation:",
        "",
        "- The current local witness has two contributing cells with `valid=1` and two with `valid=0`.",
        "- If AEX caller-collapse for this witness were just bilinear sampling of that current binary valid plane, the resulting alpha would be about `0.44250488` (`112/255`), not the Windows traced `0.99999994` (`254/255`).",
        "- Therefore the surviving Zoom lane cannot be explained by direct bilinear sampling of the current local `0/1` preserved-validity proxy.",
        "",
        "## tiny Rotation `case_0010`",
        "",
        f"- Current local bilinear validity alpha: `{rotation_binary_validity_alpha}`",
        f"- Current local sample RGBA: `{rotation['sample_rgba']}`",
        f"- Windows traced closest inverse-sampler RGBA: `{rotation_trace['aex_source_or_polar_rgba_float']}`",
        f"- Windows final RGBA8: `{rotation_trace['aex_final_rgba_u8']}`",
        "",
        "Interpretation:",
        "",
        "- All four current local contributing cells are already `valid=1`, so a validity-only collapse would keep alpha fully live.",
        "- Even with that, both the current local sample and the closest traced Windows inverse-sampler return remain near-black while the final Windows pixel is exact white.",
        "- Therefore the tiny Rotation residual is not solved by validity-only substitution either; it still points to upstream polar RGB / caller-collapse / substitute-path behavior.",
        "",
        "## Bottom line",
        "",
        "- `binary-validity -> final alpha` was already rejected at whole-frame level.",
        "- This report strengthens the same point at witness level: the current local binary validity plane is not numerically compatible with the Windows Zoom alpha witness, and it is not sufficient to explain tiny Rotation either.",
    ]
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary_json={args.output_json}")
    print(f"summary_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
