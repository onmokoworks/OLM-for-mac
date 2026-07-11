#!/usr/bin/env python3
"""Build the self-contained RadialBlur Zoom final-plane witness package."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


REQUEST = "olmradialblur_zoom_case0009_final_plane_typed_20260710"
SUPPORT = Path("refs/runtime_trace_support/olmradialblur_zoom_case0009_final_plane_typed_20260710")
PAYLOAD = (
    Path("refs/conformance/olmradialblur_zoom_case0009_final_plane_typed_contract_20260710.md"),
    Path("refs/conformance/olmradialblur_zoom_remaining_polar_sampler_audit_20260710.md"),
    Path("refs/conformance/olmradialblur_zoom_case0009_final_plane_cells_contract_20260709.md"),
    Path("scripts/ae_render_single_case.jsx"),
    Path("scripts/run_olmradialblur_zoom_case0009_final_plane_typed_20260710.ps1"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/request_manifest.json"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/reference_manifest.json"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/input/case_0009_before_effects.png"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("refs/runtime_trace_packages/olm_runtime_trace_radialblur_zoom_case0009_final_plane_typed_20260710.zip"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output if args.output.is_absolute() else root / args.output
    support = root / SUPPORT
    required = (
        support / "README_RUNTIME_TRACE.md",
        support / "runtime_trace_package_manifest.json",
        support / "RETURN_RUNTIME_TRACE_TEMPLATE.json",
        support / "final_plane_hook_fragment.cdb.template",
        *(root / path for path in PAYLOAD),
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("missing package input:\n" + "\n".join(missing))

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("README_RUNTIME_TRACE.md", "runtime_trace_package_manifest.json", "RETURN_RUNTIME_TRACE_TEMPLATE.json"):
            archive.write(support / name, name)
        archive.write(support / "final_plane_hook_fragment.cdb.template", "artifacts/final_plane_hook_fragment.cdb")
        for path in PAYLOAD:
            target = "artifacts/" + path.name if path.name.startswith("run_olmradialblur") else path.as_posix()
            archive.write(root / path, target)

    print(f"[OK] runtime trace package: {output}")
    print(f"- {REQUEST}: package-local runner and final-plane typed witness contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
