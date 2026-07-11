#!/usr/bin/env python3
"""Smoke-test Windows reference request package handoff contents."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import json
import zipfile
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    output = Path(tempfile.gettempdir()) / "olm_reference_requests_handoff_smoke.zip"
    proc = subprocess.run(
        [
            sys.executable,
            "refs/scripts/package_reference_requests.py",
            "--only",
            "kirakira_single_ray_20260606",
            "--output",
            str(output),
        ],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="")
    if proc.returncode != 0:
        return proc.returncode

    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert "refs/reference_requests/WIN_CODEX_HANDOFF.md" in names
        assert "refs/reference_requests/README.md" in names
        assert any(name.endswith(".json") for name in names)
        handoff = archive.read("refs/reference_requests/WIN_CODEX_HANDOFF.md").decode("utf-8")
        readme = archive.read("refs/reference_requests/README.md").decode("utf-8")

    assert "project_gpu_accel_type.current_name = SOFTWARE" in handoff
    assert "ADBE Force CPU GPU" in handoff
    assert "render PNGs, and write the return manifest." in handoff
    assert "Rendered PNG outputs." in handoff
    assert "python3 scripts/intake_olm_return.py path/to/returned_reference.zip --quick --dispatch-dir" in handoff
    assert "python3 refs/scripts/import_and_check_win_reference.py path/to/returned_reference.zip --quick --dispatch-dir" in handoff
    assert "Import with refs/scripts/import_win_reference.py" not in handoff
    assert "python3 refs/scripts/next_reference_actions.py" in readme
    assert "python3 scripts/intake_olm_return.py path/to/packed_reference.zip --quick" in readme

    linked_output = Path(tempfile.gettempdir()) / "olm_reference_requests_linked_smoke.zip"
    proc = subprocess.run(
        [
            sys.executable,
            "refs/scripts/package_reference_requests.py",
            "--only",
            "directionalblur_context_scale_20260606",
            "--output",
            str(linked_output),
        ],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="")
    if proc.returncode != 0:
        return proc.returncode
    with zipfile.ZipFile(linked_output) as archive:
        data = json.loads(
            archive.read("refs/reference_requests/directionalblur_context_scale_20260606.json").decode("utf-8-sig")
        )
    linked_cases = {case["id"]: case for case in data["cases"]}
    assert isinstance(linked_cases["db_existing_case_0001_software_pair"].get("params_full"), list)
    assert len(linked_cases["db_existing_case_0001_software_pair"]["params_full"]) == 15
    assert linked_cases["db_angle0_no_tail_no_size"].get("params_full") in (None, [])

    verify = subprocess.run(
        [
            sys.executable,
            "refs/scripts/verify_reference_request_package.py",
            str(output),
        ],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(verify.stdout, end="")
    if verify.returncode != 0:
        return verify.returncode

    float_output = Path(tempfile.gettempdir()) / "olm_reference_requests_float_handoff_smoke.zip"
    proc = subprocess.run(
        [
            sys.executable,
            "refs/scripts/package_reference_requests.py",
            "--only",
            "olm_bitdepth_32bpc_colorkey_float_20260710",
            "--only",
            "olm_bitdepth_32bpc_toondilate_float_20260710",
            "--output",
            str(float_output),
        ],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="")
    if proc.returncode != 0:
        return proc.returncode

    with zipfile.ZipFile(float_output) as archive:
        float_handoff = archive.read("refs/reference_requests/WIN_CODEX_HANDOFF.md").decode("utf-8")

    assert "render the requested float-preserving outputs" in float_handoff
    assert "return `EXR` first" in float_handoff
    assert "typed float-preserving fallbacks: `TIFF`, `TIF`, `HDR`, `raw-float-RGBA`" in float_handoff
    assert "Typed fallback requirements from the selected requests:" in float_handoff
    assert "PNG-only output is `probe-only`" in float_handoff
    assert "Record SHA-256 for every required artifact:" in float_handoff
    assert "Record header/sample metadata for each float-preserving artifact:" in float_handoff
    assert "Float-preserving effect outputs in `EXR` first" in float_handoff
    assert "PNG companion/probe outputs only when the request emitted them." in float_handoff
    assert "Rendered PNG outputs." not in float_handoff

    verify_float = subprocess.run(
        [
            sys.executable,
            "refs/scripts/verify_reference_request_package.py",
            str(float_output),
        ],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(verify_float.stdout, end="")
    if verify_float.returncode != 0:
        return verify_float.returncode

    print("[OK] reference request package handoff smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
