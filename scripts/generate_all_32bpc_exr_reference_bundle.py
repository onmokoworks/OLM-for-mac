#!/usr/bin/env python3
"""Create the all-plugin 32bpc EXR-first Windows reference request bundle."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST_DIR = ROOT / "refs/reference_requests"
OUTPUT = ROOT / "handoffs/windows_batch/olm_windows_reference_request_32bpc_all_plugins_exr_20260710.zip"

EXTRA = {
    "OLMRadialBlur": "olm_final_random10_olm_radialblur_20260629.json",
    "OLMDirectionalBlur": "olm_final_random10_olm_directionalblur_20260629.json",
    "OLMKiraKira": "olm_final_random10_olm_kira_kira_20260629.json",
    "OLMSmoother2": "olm_final_random10_olm_smoother_v2_20260629.json",
    "OLMSmoother v1": "olm_final_random10_olm_smoother_20260629.json",
}
BASE_FLOAT = "olm_bitdepth_32bpc_colorkey_float_20260710.json"


def load(name: str) -> dict:
    return json.loads((REQUEST_DIR / name).read_text(encoding="utf-8"))


def make_32bpc(source: dict, plugin: str) -> dict:
    result = copy.deepcopy(source)
    result["request_id"] = f"olm_bitdepth_32bpc_{plugin.lower().replace(' ', '_')}_exr_20260710"
    result["scope"] = {
        "bit_depth": "32bpc",
        "plugin_filters": [plugin],
        "feature_filters": [],
        "plugin_count": 1,
        "case_count": len(result.get("cases", [])),
    }
    result["render_sets"] = [{
        "id": "software_32bpc",
        "project_gpu_accel_type.current_name": "SOFTWARE",
        "bit_depth": "32bpc",
        "bits_per_channel": 32,
        "required": True,
    }]
    result["common_setup"] = {
        **result.get("common_setup", {}),
        "bit_depth": 32,
        "comp_width": 1920,
        "comp_height": 1080,
        "frame_rate": 24,
        "project_renderer": "SOFTWARE",
    }
    result["why"] = [
        f"Existing Windows range-metadata random10 cases for {plugin}; preserve case IDs and parameters.",
        "Render in a 32bpc Windows AE SOFTWARE project; CUDA/GPU is outside this request.",
        "Return EXR first, with typed float-preserving fallback only when EXR is unavailable.",
        "PNG-only output is probe-only and cannot support an AE exact claim.",
    ]
    base = load(BASE_FLOAT)
    result["compare_policy"] = copy.deepcopy(base["compare_policy"])
    result["output_requirements"] = copy.deepcopy(base["output_requirements"])
    result["manifest_requirements"] = copy.deepcopy(base["manifest_requirements"])
    return result


def main() -> int:
    generated: list[Path] = []
    for plugin, source_name in EXTRA.items():
        target = REQUEST_DIR / f"olm_bitdepth_32bpc_{plugin.lower().replace(' ', '_')}_exr_20260710.json"
        target.write_text(json.dumps(make_32bpc(load(source_name), plugin), indent=2) + "\n", encoding="utf-8")
        generated.append(target)

    selected = [
        "olm_bitdepth_32bpc_full_probe_exr_rerun_20260703.json",
        *[path.name for path in generated],
    ]
    command = [
        sys.executable,
        "refs/scripts/package_reference_requests.py",
        "--output",
        str(OUTPUT),
    ]
    for name in selected:
        command.extend(["--only", name])
    subprocess.run(command, cwd=ROOT, check=True)
    print(f"[OK] generated {len(generated)} additional request specs")
    print(f"[OK] bundle: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
