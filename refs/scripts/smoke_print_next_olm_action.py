#!/usr/bin/env python3
"""Smoke-test scripts/print_next_olm_action.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def write_zip(path: Path, files: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, text in files.items():
            archive.writestr(name, text)


def package_pending_requests(repo: Path, output: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "refs" / "scripts" / "package_reference_requests.py"),
            "--pending",
            "--output",
            str(output),
        ],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="")


def main() -> int:
    repo = repo_root()
    script = repo / "scripts" / "print_next_olm_action.py"
    with tempfile.TemporaryDirectory(prefix="olm_next_action_smoke_") as tmp:
        tmp_path = Path(tmp)
        returned = tmp_path / "returned_refs.zip"
        ae_pixel_request = tmp_path / "ae_pixel_request.zip"
        old_pending = tmp_path / "olm_reference_requests_pending_20260606.zip"
        fresh_pending = tmp_path / "olm_reference_requests_pending_20260612.zip"
        smoke_request = tmp_path / "olm_reference_requests_smoke.zip"
        request = json.loads(
            (repo / "refs/reference_requests/radialblur_inner_20260605.json").read_text(
                encoding="utf-8"
            )
        )
        required_set = next(item for item in request["render_sets"] if item.get("required"))
        render_set = required_set.get("id") or required_set["project_gpu_accel_type"]["current_name"]
        cases = []
        files = {}
        for case in request["cases"]:
            if case.get("optional"):
                continue
            case_id = case["id"]
            frame = f"{case_id}.png"
            before = f"{case_id}_before.png"
            cases.append(
                {
                    "id": case_id,
                    "request_case_id": case_id,
                    "frame": frame,
                    "before_effects_frame": before,
                    "render_set": render_set,
                    "selected_effect": request["effect"]["name"],
                }
            )
            files[f"OLMSmoother2/{frame}"] = "png\n"
            files[f"OLMSmoother2/{before}"] = "png\n"
        write_zip(
            returned,
            {
                "OLMSmoother2/reference_manifest.json": json.dumps(
                    {
                        "kind": "ae_effect_reference_manifest",
                        "effect": {"name": request["effect"]["name"]},
                        "cases": cases,
                    }
                ),
                **files,
            },
        )
        write_zip(
            ae_pixel_request,
            {
                "ae_pixel_olmblur/AE_PIXEL_VALIDATION_REQUEST.md": "render these\n",
                "ae_pixel_olmblur/reference_manifest.json": json.dumps(
                    {"kind": "ae_effect_reference_manifest", "cases": []}
                ),
            },
        )
        proc = run([sys.executable, str(script), "--json", str(tmp_path)], repo)
        data = json.loads(proc.stdout)
        assert data["decision"]["action"] == "import-windows-reference-return"
        assert "intake_olm_return.py" in data["decision"]["command"]
        kinds = {Path(row["path"]).name: row["kind"] for row in data["candidates"]}
        assert kinds["ae_pixel_request.zip"] == "ae-pixel-validation-request"

        human = run([sys.executable, str(script), str(tmp_path)], repo)
        assert "OLM next action" in human.stdout
        assert "import-windows-reference-return" in human.stdout
        assert "- target:" in human.stdout

        package_pending_requests(repo, old_pending)
        package_pending_requests(repo, fresh_pending)
        os.utime(fresh_pending, (old_pending.stat().st_mtime + 10, old_pending.stat().st_mtime + 10))
        write_zip(
            smoke_request,
            {
                "refs/reference_requests/WIN_CODEX_HANDOFF.md": "stale\n",
                "refs/reference_requests/stale_request_20260606.json": json.dumps(
                    {
                        "request_id": "stale_request_20260606",
                        "manifest_requirements": [],
                        "cases": [{"id": "case_a"}],
                    }
                ),
            },
        )
        returned.unlink()
        proc = run([sys.executable, str(script), "--json", str(tmp_path)], repo)
        data = json.loads(proc.stdout)
        assert data["decision"]["action"] == "send-windows-reference-package"
        assert Path(data["decision"]["target"]["path"]).name == "olm_reference_requests_pending_20260612.zip"

        old_pending.unlink()
        fresh_pending.unlink()
        proc = run([sys.executable, str(script), "--json", str(tmp_path)], repo)
        data = json.loads(proc.stdout)
        assert data["decision"]["action"] == "package-windows-reference-requests"

    print("[OK] OLM next action printer smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
