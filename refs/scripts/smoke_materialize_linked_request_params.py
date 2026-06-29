#!/usr/bin/env python3
"""Smoke test for materializing params_full into linked reference requests."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def params_full_value(case: dict, name: str):
    for row in case.get("params_full", []):
        if row.get("name") == name:
            return row.get("value")
    raise AssertionError(f"missing params_full entry for {name}")


def main() -> int:
    request_paths = [
        ROOT / "refs/reference_requests/radialblur_inner_20260605.json",
        ROOT / "refs/reference_requests/smoother2_legacy_current_aex_recapture_20260621.json",
    ]
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        copied = []
        for src in request_paths:
            dst = tmp_root / src.name
            shutil.copy2(src, dst)
            copied.append(dst)
        cmd = ["python3", "scripts/materialize_linked_request_params.py", "--write", *map(str, copied)]
        subprocess.run(cmd, cwd=ROOT, check=True)

        radial = load_json(copied[0])
        rb_case = radial["cases"][0]
        assert len(rb_case["params_full"]) == 22
        assert params_full_value(rb_case, "Strength") == 62
        assert params_full_value(rb_case, "Quality") == 5

        smoother = load_json(copied[1])
        exact_case = smoother["cases"][0]
        control_case = smoother["cases"][1]
        assert len(exact_case["params_full"]) == 15
        assert len(control_case["params_full"]) == 15
        assert params_full_value(control_case, "Smoothness") == 0
        assert params_full_value(exact_case, "Smoothness") != 0

    print("[OK] linked request params_full materialization smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
