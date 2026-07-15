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


def load_subject(repo: Path):
    scripts_dir = repo / "scripts"
    sys.path.insert(0, str(scripts_dir))
    try:
        import list_olm_return_candidates as subject  # type: ignore
    finally:
        sys.path.pop(0)
    return subject


def main() -> int:
    repo = repo_root()
    subject = load_subject(repo)
    script = repo / "scripts" / "list_olm_return_candidates.py"
    with tempfile.TemporaryDirectory(prefix="olm_return_candidates_share_layout_") as tmp:
        tmp_path = Path(tmp)
        legacy_share = tmp_path / "legacy" / "olm_pr"
        legacy_new = legacy_share / "new"
        legacy_new.mkdir(parents=True)
        legacy_return = legacy_new / "legacy_return.zip"
        write_zip(
            legacy_return,
            {
                "RETURN_RUNTIME_TRACE_RESULT.json": json.dumps(
                    {"kind": "olm_runtime_trace_result", "results": [{"request_id": "legacy", "status": "answered"}]}
                )
            },
        )
        assert subject.candidate_paths([legacy_share]) == [legacy_return]

        split_share = tmp_path / "split" / "olm_pr"
        mac_requests = split_share / "new" / "mac_requests"
        windows_processing = split_share / "new" / "windows_processing"
        mac_returns = split_share / "new" / "mac_returns"
        mac_requests.mkdir(parents=True)
        windows_processing.mkdir(parents=True)
        mac_returns.mkdir(parents=True)
        request_zip = mac_requests / "request.zip"
        split_return = mac_returns / "split_return.zip"
        processing_return = windows_processing / "processing_return.zip"
        write_zip(
            request_zip,
            {
                "runtime_trace_package_manifest.json": json.dumps(
                    {"kind": "olm_runtime_trace_request_package", "runtime_actions": [{"request_id": "split_request"}]}
                )
            },
        )
        write_zip(
            split_return,
            {
                "RETURN_RUNTIME_TRACE_RESULT.json": json.dumps(
                    {"kind": "olm_runtime_trace_result", "results": [{"request_id": "split_return", "status": "answered"}]}
                )
            },
        )
        write_zip(
            processing_return,
            {
                "RETURN_RUNTIME_TRACE_RESULT.json": json.dumps(
                    {"kind": "olm_runtime_trace_result", "results": [{"request_id": "processing", "status": "answered"}]}
                )
            },
        )
        assert subject.candidate_paths([split_share]) == [split_return]
        processing_row = subject.build_row(processing_return)
        assert processing_row["kind"] == "unknown"

    with tempfile.TemporaryDirectory(prefix="olm_return_candidates_smoke_") as tmp:
        tmp_path = Path(tmp)
        win_ref = tmp_path / "returned_refs.zip"
        ae_host = tmp_path / "ae_host.zip"
        handoff = tmp_path / "handoff.zip"
        request_pkg = tmp_path / "requests.zip"
        runtime_request_pkg = tmp_path / "runtime_requests.zip"
        wrapped_runtime_request_pkg = tmp_path / "wrapped_runtime_requests.zip"
        windows_action_bundle = tmp_path / "windows_action_bundle.zip"
        windows_action_bundle_return = tmp_path / "windows_action_bundle_return.zip"
        windows_action_bundle_return_multi = tmp_path / "windows_action_bundle_return_multi.zip"
        runtime_return = tmp_path / "runtime_return.zip"
        runtime_return_with_source_request = tmp_path / "runtime_return_with_source_request.zip"
        bare_runtime_return = tmp_path / "bare_runtime_return.zip"
        portable_runtime_return = tmp_path / "portable_runtime_return.zip"
        ae_runtime_return = tmp_path / "ae_runtime_return.zip"
        ae_pixel_request = tmp_path / "ae_pixel_request.zip"
        ae_pixel_bundle = tmp_path / "ae_pixel_bundle.zip"
        olmblur_standalone_witness = tmp_path / "olmblur_standalone_witness.zip"
        unknown = tmp_path / "other.zip"

        write_zip(
            win_ref,
            {
                "OLMColorKey/reference_manifest.json": json.dumps(
                    {"kind": "ae_effect_reference_manifest", "cases": []}
                ),
                "OLMColorKey/case_0001.png": "png",
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
                "RETURN_RUNTIME_TRACE_TEMPLATE.json": json.dumps(
                    {
                        "kind": "olm_runtime_trace_result",
                        "schema": 1,
                        "results": [
                            {
                                "request_id": "radialblur_inner_runtime_trace_20260618",
                                "status": "answered",
                                "summary": "Template placeholder only; not a real return.",
                            }
                        ],
                    }
                ),
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
            windows_action_bundle_return,
            {
                "olm_windows_action_bundle_return/windows_action_bundle_manifest.json": json.dumps(
                    {"kind": "olm_windows_action_bundle"}
                ),
                "olm_windows_action_bundle_return/runtime_trace_returns/synthetic_return.zip": "nested runtime return placeholder\n",
                "olm_windows_action_bundle_return/request_package/synthetic_request.zip": "nested runtime request placeholder\n",
            },
        )
        write_zip(
            windows_action_bundle_return_multi,
            {
                "olm_runtime_trace_requests_20260630_4pack_windows_return/QUEUE_README.txt": "queued bundle return\n",
                "olm_runtime_trace_requests_20260630_4pack_windows_return/olmblur_final_word_witness_20260630/RETURN_RUNTIME_TRACE_RESULT.json": json.dumps(
                    {
                        "kind": "olm_runtime_trace_result",
                        "results": [
                            {"request_id": "olmblur_final_word_witness_20260630", "status": "answered"}
                        ],
                    }
                ),
                "olm_runtime_trace_requests_20260630_4pack_windows_return/olmblur_final_word_witness_20260630/request_package/runtime_trace_package_manifest.json": json.dumps(
                    {
                        "kind": "olm_runtime_trace_request_package",
                        "runtime_actions": [
                            {"request_id": "olmblur_final_word_witness_20260630"}
                        ],
                    }
                ),
                "olm_runtime_trace_requests_20260630_4pack_windows_return/olmradialblur_caller_collapse_witness_20260630/RETURN_RUNTIME_TRACE_RESULT.json": json.dumps(
                    {
                        "kind": "olm_runtime_trace_result",
                        "results": [
                            {"request_id": "olmradialblur_caller_collapse_witness_20260630", "status": "answered_partial"}
                        ],
                    }
                ),
                "olm_runtime_trace_requests_20260630_4pack_windows_return/olmradialblur_caller_collapse_witness_20260630/request_package/runtime_trace_package_manifest.json": json.dumps(
                    {
                        "kind": "olm_runtime_trace_request_package",
                        "runtime_actions": [
                            {"request_id": "olmradialblur_caller_collapse_witness_20260630"}
                        ],
                    }
                ),
                "olm_runtime_trace_requests_20260630_4pack_windows_return/olmblur_final_word_witness_20260630/evidence/olmblur_case0007_16bpc_345_672_b_databreak_probe/WITNESS_RESULT.json": json.dumps(
                    {
                        "plugin": "OLMBlur",
                        "case": "olmblur__case_0007",
                        "bit_depth": "16bpc",
                        "target": {"x": 345, "y": 672, "channel": "B"},
                    }
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
        with zipfile.ZipFile(portable_runtime_return, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "RETURN_RUNTIME_TRACE.json",
                b"\xef\xbb\xbf"
                + json.dumps(
                    {
                        "request_id": "olmdirectionalblur_front_alpha_host_boundary_2025_20260711",
                        "status": "answered",
                        "run_id": "portable-return-smoke",
                    }
                ).encode("utf-8"),
            )
        with zipfile.ZipFile(ae_runtime_return, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "AE_RUNTIME_TRACE_RESULT.json",
                json.dumps({"request_id": "ae-runtime-compat", "status": "answered"}).encode("utf-8"),
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
        write_zip(
            ae_pixel_bundle,
            {
                "README.md": "bundle\n",
                "bundle_manifest.json": json.dumps(
                    {
                        "kind": "olm_ae_pixel_validation_bundle",
                        "request_count": 2,
                        "requests": [],
                    }
                ),
                "requests/bitdepth16_olmblur_exact.zip": "not a real nested zip for this smoke\n",
            },
        )
        write_zip(
            olmblur_standalone_witness,
            {
                "databreak_probe/WITNESS_RESULT.json": json.dumps(
                    {
                        "plugin": "OLMBlur",
                        "case": "olmblur__case_0007",
                        "bit_depth": "16bpc",
                        "target": {"x": 345, "y": 672, "channel": "B"},
                    }
                ),
                "databreak_probe/README_WITNESS.md": "single witness\n",
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
        assert kinds["windows_action_bundle_return.zip"] == "windows-action-bundle-return"
        assert kinds["windows_action_bundle_return_multi.zip"] == "windows-action-bundle-return"
        assert kinds["runtime_return.zip"] == "runtime-trace-return"
        assert kinds["runtime_return_with_source_request.zip"] == "runtime-trace-return"
        assert kinds["bare_runtime_return.zip"] == "runtime-trace-return"
        assert kinds["portable_runtime_return.zip"] == "runtime-trace-return"
        assert kinds["ae_runtime_return.zip"] == "runtime-trace-return"
        assert kinds["ae_pixel_request.zip"] == "ae-pixel-validation-request"
        assert kinds["ae_pixel_bundle.zip"] == "ae-pixel-validation-bundle"
        assert kinds["olmblur_standalone_witness.zip"] == "olmblur-standalone-witness"
        assert "other.zip" not in kinds
        commands = {Path(row["path"]).name: row["suggested_command"] for row in data["candidates"]}
        hints = {Path(row["path"]).name: row["hints"] for row in data["candidates"]}
        assert "--dispatch-dir /tmp/olm_reference_dispatch" in commands["returned_refs.zip"]
        assert any("asset_formats" in hint for hint in hints["returned_refs.zip"])
        assert any("float_preserving_present=False" in hint for hint in hints["returned_refs.zip"])
        assert "--require-all-pass" in commands["ae_host.zip"]
        assert "Windows debugger/helper" in commands["runtime_requests.zip"]
        assert "Windows debugger/helper" in commands["wrapped_runtime_requests.zip"]
        assert "Windows helper" in commands["windows_action_bundle.zip"]
        assert "intake_latest_windows_return_from_share.py" in commands["windows_action_bundle_return.zip"]
        assert "intake_latest_windows_return_from_share.py" in commands["windows_action_bundle_return_multi.zip"]
        assert "--runtime-summary-json" in commands["runtime_return.zip"]
        assert "--runtime-summary-md" in commands["runtime_return.zip"]
        assert "--runtime-comparison-dir" in commands["runtime_return.zip"]
        assert "--runtime-summary-json" in commands["runtime_return_with_source_request.zip"]
        assert "--runtime-summary-json" in commands["bare_runtime_return.zip"]
        assert "--runtime-summary-md" in commands["bare_runtime_return.zip"]
        assert "--runtime-comparison-dir" in commands["bare_runtime_return.zip"]
        assert "--runtime-summary-json" in commands["portable_runtime_return.zip"]
        assert "AE host" in commands["ae_pixel_request.zip"]
        assert "AE host" in commands["ae_pixel_bundle.zip"]
        assert "intake_olmblur_standalone_witness_zip.py" in commands["olmblur_standalone_witness.zip"]

        human = run([sys.executable, str(script), str(tmp_path)], repo)
        assert "win-reference-return" in human.stdout
        assert "runtime-trace-request-package" in human.stdout
        assert "windows-action-bundle-return" in human.stdout
        assert "runtime-trace-return" in human.stdout
        assert "olmblur-standalone-witness" in human.stdout
        assert "ae-pixel-validation-bundle" in human.stdout
        assert "send this package to the Windows AE renderer" in human.stdout

    print("[OK] OLM return candidate lister smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
