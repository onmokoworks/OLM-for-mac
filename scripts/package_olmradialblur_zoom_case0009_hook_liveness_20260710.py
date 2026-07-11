#!/usr/bin/env python3
"""Build the package-local raw hook-liveness request for RadialBlur Zoom."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


REQUEST = "olmradialblur_zoom_case0009_hook_liveness_20260710"
SUPPORT = Path("refs/runtime_trace_support/olmradialblur_zoom_case0009_hook_liveness_20260710")
PAYLOAD = [
    Path("refs/conformance/olmradialblur_zoom_case0009_hook_liveness_contract_20260710.md"),
    Path("scripts/ae_render_single_case.jsx"),
    Path("scripts/run_olmradialblur_zoom_case0009_final_plane_typed_20260710.ps1"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/request_manifest.json"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/reference_manifest.json"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/input/case_0009_before_effects.png"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("refs/runtime_trace_packages/olm_runtime_trace_radialblur_zoom_case0009_hook_liveness_20260710.zip"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output if args.output.is_absolute() else root / args.output
    support = root / SUPPORT
    required = [support / name for name in ("README_RUNTIME_TRACE.md", "hook_liveness.cdb", "RETURN_RUNTIME_TRACE_TEMPLATE.json")]
    for path in [*required, *(root / item for item in PAYLOAD)]:
        if not path.is_file():
            raise SystemExit(f"missing package input: {path}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("README_RUNTIME_TRACE.md", "RETURN_RUNTIME_TRACE_TEMPLATE.json"):
            archive.write(support / name, name)
        archive.write(support / "hook_liveness.cdb", "artifacts/hook_liveness.cdb")
        for path in PAYLOAD:
            target = "artifacts/" + path.name if path.name.startswith("run_olmradialblur") else path.as_posix()
            archive.write(root / path, target)
    print(f"[OK] runtime trace package: {output}")
    print(f"- {REQUEST}: raw hook liveness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
