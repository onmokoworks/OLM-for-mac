#!/usr/bin/env python3
"""Smoke-test request-result importing with a synthetic Windows reference zip."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def write_synthetic_result(root: Path, request: dict) -> Path:
    result_dir = root / "returned" / "OLM_Kira_Kira"
    result_dir.mkdir(parents=True)
    cases = []
    for case in request["cases"]:
        if case.get("optional"):
            continue
        frame = f"SOFTWARE_{case['id']}.png"
        before = f"SOFTWARE_{case['id']}_before_effects.png"
        (result_dir / frame).write_bytes(b"png")
        (result_dir / before).write_bytes(b"png")
        cases.append(
            {
                "id": f"SOFTWARE_{case['id']}",
                "request_case_id": case["id"],
                "render_set": "SOFTWARE",
                "project_gpu_accel_type": {"current_name": "SOFTWARE", "raw": 1816},
                "frame": frame,
                "before_effects_frame": before,
                "selected_layer_effects": [
                    {"name": "OLM Kira Kira", "match_name": "OLM OLM Kira Kira"}
                ],
            }
        )

    manifest = {
        "kind": "ae_effect_reference_manifest",
        "effect": {"name": "OLM Kira Kira", "match_name": "OLM OLM Kira Kira"},
        "project_gpu_accel_type": {"current_name": "SOFTWARE", "raw": 1816},
        "cases": cases,
    }
    (result_dir / "reference_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    zip_path = root / "returned.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in result_dir.rglob("*"):
            archive.write(path, path.relative_to(root / "returned"))
    return zip_path


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    request = repo / "refs/reference_requests/kirakira_single_ray_20260606.json"
    importer = repo / "refs/scripts/import_win_reference.py"
    data = json.loads(request.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="olm_ref_import_smoke_") as tmp:
        tmp_path = Path(tmp)
        zip_path = write_synthetic_result(tmp_path, data)
        dest_root = tmp_path / "win_references"
        cmd = [
            sys.executable,
            str(importer),
            str(zip_path),
            "--dest-root",
            str(dest_root),
            "--set-id",
            "synthetic_return",
            "--allow-missing-optional-render-sets",
        ]
        proc = run(cmd)
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode
        imported = dest_root / "synthetic_return" / "OLMKiraKira" / "reference_manifest.json"
        if not imported.exists():
            print(f"[FAIL] imported manifest missing: {imported}")
            return 1

    print("[OK] import_win_reference smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
