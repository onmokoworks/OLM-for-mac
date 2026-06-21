#!/usr/bin/env python3
"""Smoke-test scripts/list_olm_return_candidates.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_zip(path: Path, files: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, text in files.items():
            archive.writestr(name, text)


def run(cmd: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def main() -> int:
    repo = repo_root()
    script = repo / "scripts" / "list_olm_return_candidates.py"
    with tempfile.TemporaryDirectory(prefix="olm_return_candidates_smoke_") as tmp:
        tmp_path = Path(tmp)
        win_ref = tmp_path / "returned_refs.zip"
        ae_host = tmp_path / "ae_host.zip"
        handoff = tmp_path / "handoff.zip"
        request_pkg = tmp_path / "requests.zip"
        runtime_request_pkg = tmp_path / "runtime_requests.zip"
        wrapped_runtime_request_pkg = tmp_path / "wrapped_runtime_requests.zip"
        windows_action_bundle = tmp_path / "windows_action_bundle.zip"
        runtime_return = tmp_path / "runtime_return.zip"
        runtime_return_with_source_request = tmp_path / "runtime_return_with_source_request.zip"
        bare_runtime_return = tmp_path / "bare_runtime_return.zip"
        ae_pixel_request = tmp_path / "ae_pixel_request.zip"
        unknown = tmp_path / "other.zip"

        write_zip(
            win_ref,
            {
                "OLMColorKey/reference_manifest.json": json.dumps(
                    {"kind": "ae_effect_reference_manifest", "cases": []}
                )
            },
        )
        write_zip(
            ae_host,
            {
                "AE_VALIDATION_RESULT.template.json": json.dumps(
                    {"kind": "olm_ae_host_validation_result", "plugins": []}
                )
            },
        )
        write_zip(
            handoff,
            {
                "OLM_Port_Handoff/manifest.json": json.dumps(
                    {"kind": "olm_port_handoff_package"}
                )
            },
        )
        write_zip(request_pkg, {"refs/reference_requests/WIN_CODEX_HANDOFF.md": "render these\n"})
        write_zip(
            runtime_request_pkg,
            {
                "README_RUNTIME_TRACE.md": "trace these\n",
                "runtime_trace_package_manifest.json": json.dumps(
                    {
                        "kind": "olm_runtime_trace_request_package",
                        "runtime_actions": [
                            {"request_id": "radialblur_inner_runtime_trace_20260618"}
                        ],
                    }
                ),
            },
        )
        write_zip(
            wrapped_runtime_request_pkg,
            {
                "runtime_trace_request/runtime_trace_package_manifest.json": json.dumps(
                    {
                        "kind": "olm_runtime_trace_request_package",
                        "runtime_actions": [
                            {"request_id": "radialblur_inner_runtime_trace_20260618"}
                        ],
                    }
                )
            },
        )
        write_zip(
            windows_action_bundle,
            {
                "README_WINDOWS_ACTION_BUNDLE.md": "send this to Windows\n",
                "windows_action_bundle_manifest.json": json.dumps(
                    {"kind": "olm_windows_action_bundle"}
                ),
            },
        )
        write_zip(
            runtime_return,
            {
                "results/runtime_trace_result.json": json.dumps(
                    {
                        "kind": "olm_runtime_trace_result",
                        "results": [
                            {
                                "request_id": "radialblur_inner_runtime_trace_20260618",
                                "status": "answered",
                            }
                        ],
                    }
                )
            },
        )
        write_zip(
            runtime_return_with_source_request,
            {
                "source_request/runtime_trace_package_manifest.json": json.dumps(
                    {
                        "kind": "olm_runtime_trace_request_package",
                        "runtime_actions": [
                            {"request_id": "radialblur_inner_runtime_trace_20260618"}
                        ],
                    }
                ),
                "RETURN_RUNTIME_TRACE_RESULT.json": json.dumps(
                    {
                        "kind": "olm_runtime_trace_result",
                        "results": [
                            {
                                "request_id": "radialblur_inner_runtime_trace_20260618",
                                "status": "answered",
                            }
                        ],
                    }
                ),
            },
        )
        write_zip(
            bare_runtime_return,
            {
                "nested/result.json": json.dumps(
                    {
                        "results": [
                            {
                                "request_id": "radialblur_inner_runtime_trace_20260618",
                                "status": "answered",
                            }
                        ]
                    }
                )
            },
        )
        write_zip(
            ae_pixel_request,
            {
                "ae_pixel_olmblur/AE_PIXEL_VALIDATION_REQUEST.md": "render these\n",
                "ae_pixel_olmblur/reference_manifest.json": json.dumps(
                    {"kind": "ae_effect_reference_manifest", "cases": []}
                ),
                "ae_pixel_olmblur/request_manifest.json": json.dumps(
                    {"kind": "olm_ae_pixel_validation_request"}
                ),
            },
        )
        write_zip(unknown, {"hello.txt": "not olm\n"})

        proc = run([sys.executable, str(script), "--json", str(tmp_path)], repo)
        data = json.loads(proc.stdout)
        kinds = {Path(row["path"]).name: row["kind"] for row in data["candidates"]}
        assert kinds["returned_refs.zip"] == "win-reference-return"
        assert kinds["ae_host.zip"] == "ae-host-return"
        assert kinds["handoff.zip"] == "olm-handoff-package"
        assert kinds["requests.zip"] == "reference-request-package"
        assert kinds["runtime_requests.zip"] == "runtime-trace-request-package"
        assert kinds["wrapped_runtime_requests.zip"] == "runtime-trace-request-package"
        assert kinds["windows_action_bundle.zip"] == "windows-action-bundle"
        assert kinds["runtime_return.zip"] == "runtime-trace-return"
        assert kinds["runtime_return_with_source_request.zip"] == "runtime-trace-return"
        assert kinds["bare_runtime_return.zip"] == "runtime-trace-return"
        assert kinds["ae_pixel_request.zip"] == "ae-pixel-validation-request"
        assert "other.zip" not in kinds
        commands = {Path(row["path"]).name: row["suggested_command"] for row in data["candidates"]}
        assert "--dispatch-dir /tmp/olm_reference_dispatch" in commands["returned_refs.zip"]
        assert "--require-all-pass" in commands["ae_host.zip"]
        assert "Windows debugger/helper" in commands["runtime_requests.zip"]
        assert "Windows debugger/helper" in commands["wrapped_runtime_requests.zip"]
        assert "Windows helper" in commands["windows_action_bundle.zip"]
        assert "--runtime-summary-json" in commands["runtime_return.zip"]
        assert "--runtime-summary-md" in commands["runtime_return.zip"]
        assert "--runtime-comparison-dir" in commands["runtime_return.zip"]
        assert "--runtime-summary-json" in commands["runtime_return_with_source_request.zip"]
        assert "--runtime-summary-json" in commands["bare_runtime_return.zip"]
        assert "--runtime-summary-md" in commands["bare_runtime_return.zip"]
        assert "--runtime-comparison-dir" in commands["bare_runtime_return.zip"]
        assert "AE host" in commands["ae_pixel_request.zip"]

        human = run([sys.executable, str(script), str(tmp_path)], repo)
        assert "win-reference-return" in human.stdout
        assert "runtime-trace-request-package" in human.stdout
        assert "runtime-trace-return" in human.stdout
        assert "send this package to the Windows AE renderer" in human.stdout

    print("[OK] OLM return candidate lister smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
