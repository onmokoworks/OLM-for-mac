#!/usr/bin/env python3
"""Build the focused Windows runtime package for the RadialBlur typed witness."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


REQUEST = "olmradialblur_zoom_case0009_final_plane_typed_20260710"
SUPPORT = Path("refs/runtime_trace_support/olmradialblur_zoom_case0009_final_plane_typed_20260710")
CONTRACT = Path("refs/conformance/olmradialblur_zoom_case0009_final_plane_typed_contract_20260710.md")
PAYLOAD = [
    CONTRACT,
    Path("refs/conformance/olmradialblur_zoom_remaining_polar_sampler_audit_20260710.md"),
    Path("refs/conformance/olmradialblur_zoom_case0009_final_plane_cells_contract_20260709.md"),
    Path("refs/win_references/20260604_olm/OLMRadialBlur/reference_manifest.json"),
    Path("refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"),
    Path("refs/win_references/20260604_olm/OLMRadialBlur/case_0009.png"),
    Path("scripts/ae_render_single_case.jsx"),
    Path("scripts/run_olmradialblur_zoom_case0009_final_plane_typed_20260710.ps1"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/request_manifest.json"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/reference_manifest.json"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/input/case_0009_before_effects.png"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/expected/case_0009.png"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/OLMRADIALBLUR_PROBE_PLAN.json"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("refs/runtime_trace_packages/olm_runtime_trace_radialblur_zoom_case0009_final_plane_typed_20260710.zip"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output if args.output.is_absolute() else root / args.output
    support = root / SUPPORT
    required = [support / name for name in ("README_RUNTIME_TRACE.md", "runtime_trace_package_manifest.json", "RETURN_RUNTIME_TRACE_TEMPLATE.json", "final_plane_hook_fragment.cdb.template")]
    for path in [*required, *(root / path for path in PAYLOAD)]:
        if not path.is_file():
            raise SystemExit(f"missing package input: {path}")
    manifest = json.loads((support / "runtime_trace_package_manifest.json").read_text())
    if manifest["runtime_actions"][0]["request_id"] != REQUEST:
        raise SystemExit("unexpected request id")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("README_RUNTIME_TRACE.md", "runtime_trace_package_manifest.json", "RETURN_RUNTIME_TRACE_TEMPLATE.json"):
            archive.write(support / name, name)
        archive.write(support / "final_plane_hook_fragment.cdb.template", "artifacts/final_plane_hook_fragment.cdb")
        archive.write(support / "runtime_trace_package_manifest.json", "next_reference_actions_snapshot.json")
        for path in PAYLOAD:
            target = path.as_posix()
            if path.name == "run_olmradialblur_zoom_case0009_final_plane_typed_20260710.ps1":
                target = "artifacts/" + path.name
            archive.write(root / path, target)
    print(f"[OK] runtime trace package: {output}")
    print(f"- {REQUEST}: {manifest['runtime_actions'][0]['plugin_area']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
