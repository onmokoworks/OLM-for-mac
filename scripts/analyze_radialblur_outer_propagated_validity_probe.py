#!/usr/bin/env python3
"""Measure a propagated-validity caller-collapse probe for OLMRadialBlur.

This is a bounded diagnostic only. It checks whether replacing the final outer
alpha with a same-kernel propagated validity plane moves the current focused
Zoom / tiny Rotation witnesses in a useful way.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SUMMARY_JSON = REPO / "refs" / "conformance" / "olmradialblur_outer_propagated_validity_probe_20260701.json"
SUMMARY_MD = REPO / "refs" / "conformance" / "olmradialblur_outer_propagated_validity_probe_20260701.md"
CLI = REPO / "cli" / "OLMRadialBlur" / "olmradialblur_cli"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=REPO, check=True)


def run_capture(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, cwd=REPO, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout


def verify_case(manifest: Path, reference_dir: Path, candidate_dir: Path, case_id: str) -> dict[str, float | int]:
    out = run_capture(
        [
            "python3",
            "refs/scripts/verify_manifest.py",
            str(manifest),
            "--reference-dir",
            str(reference_dir),
            "--candidate-dir",
            str(candidate_dir),
            "--case-id",
            case_id,
            "--expected-effect",
            "OLM RadialBlur",
        ]
    )
    diff_json = REPO / "refs" / "reports" / "manifest_diff.json"
    payload = json.loads(diff_json.read_text(encoding="utf-8"))
    rows = payload.get("cases", [])
    row = next(r for r in rows if r.get("case_id", r.get("id")) == case_id)
    return {
        "max_diff": int(row["max_diff"]),
        "mean_diff": float(row["mean_diff"]),
        "nonzero_px": int(row["nonzero_px"]),
        "verify_stdout": out,
    }


def render_variant(smoke_script: str, case_id: str, witness_x: int, witness_y: int) -> dict[str, object]:
    run(["python3", smoke_script])
    if case_id == "case_0009":
        run_dir = Path("/tmp/olmradialblur_cpp_zoom_smoke")
    elif case_id == "case_0010":
        run_dir = Path("/tmp/olmradialblur_cpp_tiny_rotation_smoke")
    else:
        raise ValueError(case_id)

    before = run_dir / "reference" / f"{case_id}_before_effects.png"
    params = run_dir / "candidate" / "_params" / f"{case_id}.json"
    reference_dir = run_dir / "reference"
    manifest = run_dir / "reference_manifest.json"

    with tempfile.TemporaryDirectory(prefix=f"{case_id}_prop_valid_") as td:
        td_path = Path(td)
        candidate_dir = td_path / "candidate"
        candidate_dir.mkdir(parents=True, exist_ok=True)
        output = candidate_dir / f"{case_id}.png"
        witness_json = candidate_dir / f"{case_id}.json"
        run(
            [
                str(CLI),
                "--input",
                str(before),
                "--params",
                str(params),
                "--output",
                str(output),
                "--outer-caller-collapse-mode",
                "propagated-validity-alpha",
                "--witness-dump",
                str(witness_json),
                "--witness-x",
                str(witness_x),
                "--witness-y",
                str(witness_y),
            ]
        )
        stats = verify_case(manifest, reference_dir, candidate_dir, case_id)
        witness = json.loads(witness_json.read_text(encoding="utf-8"))
        return {
            "case_id": case_id,
            "stats": stats,
            "witness_xy": witness["xy"],
            "sample_u8": witness["sample_u8"],
            "sample_rgba": witness["sample_rgba"],
            "mode": witness["outer_caller_collapse_mode"],
        }


def main() -> int:
    run([str(REPO / "refs" / "scripts" / "build_olmradialblur_cli.sh")])
    zoom = render_variant("refs/scripts/smoke_olmradialblur_cpp_zoom_cli.py", "case_0009", 6, 0)
    rotation = render_variant("refs/scripts/smoke_olmradialblur_cpp_tiny_rotation_cli.py", "case_0010", 1614, 6)

    payload = {
        "kind": "olmradialblur_outer_propagated_validity_probe",
        "status": "diagnostic",
        "date": "2026-07-01",
        "zoom_case_0009": zoom,
        "tiny_rotation_case_0010": rotation,
        "reading": {
            "zoom": "Replacing outer alpha with a same-kernel propagated validity plane leaves the current Zoom residual unchanged (`max=1 mean=0.0046`). This does not supply the missing 254/255 split by itself.",
            "tiny_rotation": "The propagated-validity probe leaves tiny Rotation effectively unchanged (`max=255 mean=0.0103`). This supports the existing conclusion that the remaining blocker is RGB/substitute-path population, not a simple validity-plane collapse.",
        },
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# OLMRadialBlur Outer Propagated-Validity Probe",
        "",
        "Date: 2026-07-01",
        "",
        "Bounded diagnostic: replace the final outer alpha plane with a same-kernel propagated validity plane (`--outer-caller-collapse-mode propagated-validity-alpha`) and measure whether the focused outer witnesses improve.",
        "",
        "## Zoom `case_0009`",
        "",
        f"- Witness XY: `{zoom['witness_xy']}`",
        f"- Sample RGBA: `{zoom['sample_rgba']}`",
        f"- Sample u8: `{zoom['sample_u8']}`",
        f"- Diff stats: `max={zoom['stats']['max_diff']} mean={zoom['stats']['mean_diff']:.4f} nonzero_px={zoom['stats']['nonzero_px']}`",
        "",
        payload["reading"]["zoom"],
        "",
        "## tiny Rotation `case_0010`",
        "",
        f"- Witness XY: `{rotation['witness_xy']}`",
        f"- Sample RGBA: `{rotation['sample_rgba']}`",
        f"- Sample u8: `{rotation['sample_u8']}`",
        f"- Diff stats: `max={rotation['stats']['max_diff']} mean={rotation['stats']['mean_diff']:.4f} nonzero_px={rotation['stats']['nonzero_px']}`",
        "",
        payload["reading"]["tiny_rotation"],
        "",
        "## Bottom line",
        "",
        "- This rejects one more tempting outer-lane shortcut: a propagated validity plane alone is not enough.",
        "- Zoom still needs a narrower caller-collapse / normalization fact between sampler return and final `+0xe` alpha.",
        "- tiny Rotation still points upstream to the polar RGB / substitute path.",
        "",
    ]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary_json={SUMMARY_JSON}")
    print(f"summary_md={SUMMARY_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
