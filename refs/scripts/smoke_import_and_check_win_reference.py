#!/usr/bin/env python3
"""Smoke-test import_and_check_win_reference.py with synthetic returned refs."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def write_synthetic_result(root: Path, request: dict) -> Path:
    result_dir = root / "returned" / "SyntheticEffect"
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
                "selected_layer_effects": [{"name": "Synthetic Effect", "match_name": "Synthetic Effect"}],
            }
        )

    manifest = {
        "kind": "ae_effect_reference_manifest",
        "effect": {"name": "Synthetic Effect", "match_name": "Synthetic Effect"},
        "project_gpu_accel_type": {"current_name": "SOFTWARE", "raw": 1816},
        "cases": cases,
    }
    (result_dir / "reference_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    zip_path = root / "returned.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in result_dir.rglob("*"):
            archive.write(path, path.relative_to(root / "returned"))
    return zip_path


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    runner = repo / "refs" / "scripts" / "import_and_check_win_reference.py"

    with tempfile.TemporaryDirectory(prefix="olm_import_and_check_smoke_") as tmp:
        tmp_path = Path(tmp)
        requests_dir = tmp_path / "requests"
        request = requests_dir / "synthetic_import_and_check_20260606.json"
        data = {
            "request_id": "synthetic_import_and_check_20260606",
            "effect": {"name": "Synthetic Effect", "match_name": "Synthetic Effect"},
            "render_sets": [
                {
                    "id": "SOFTWARE",
                    "required": True,
                    "project_gpu_accel_type.current_name": "SOFTWARE",
                }
            ],
            "manifest_requirements": [],
            "cases": [{"id": "case_a"}, {"id": "case_b"}],
        }
        request.parent.mkdir(parents=True)
        request.write_text(json.dumps(data, indent=2), encoding="utf-8")
        zip_path = write_synthetic_result(tmp_path, data)
        dest_root = tmp_path / "win_references"
        next_actions_json = tmp_path / "next_actions_after_import.json"
        cmd = [
            sys.executable,
            str(runner),
            str(zip_path),
            "--dest-root",
            str(dest_root),
            "--set-id",
            "synthetic_return",
            "--requests-dir",
            str(requests_dir),
            "--request",
            str(request),
            "--next-actions-json",
            str(next_actions_json),
        ]
        proc = subprocess.run(cmd, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode
        next_actions = json.loads(next_actions_json.read_text(encoding="utf-8"))
        action = next_actions["next_action"]
        if action["request_id"] != "synthetic_import_and_check_20260606":
            print("[FAIL] next actions JSON did not record the imported request", file=sys.stderr)
            return 1

    print("[OK] import and check smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
