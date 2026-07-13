#!/usr/bin/env python3
"""Smoke-test intake_latest_windows_return_from_share.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import shutil
import zipfile
from pathlib import Path

from smoke_runtime_trace_return import make_return_zip
from smoke_olm_return_intake import make_windows_ref_return

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


def write_runtime_request_zip(path: Path, request_id: str) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "runtime_trace_package_manifest.json",
            (
                "{\n"
                '  "kind": "olm_runtime_trace_request_package",\n'
                '  "runtime_actions": [\n'
                f'    {{"request_id": "{request_id}"}}\n'
                "  ]\n"
                "}\n"
            ),
        )
        archive.writestr("README_RUNTIME_TRACE.md", "synthetic runtime request\n")


def write_runtime_return_zip(path: Path, request_id: str, *, portable: bool = False) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if portable:
            archive.writestr(
                "RETURN_RUNTIME_TRACE.json",
                b"\xef\xbb\xbf"
                + (
                    "{\n"
                    f'  "request_id": "{request_id}",\n'
                    '  "status": "answered",\n'
                    '  "run_id": "portable-return-smoke"\n'
                    "}\n"
                ).encode("utf-8"),
            )
            return
        archive.writestr(
            "RETURN_RUNTIME_TRACE_RESULT.json",
            (
                "{\n"
                '  "kind": "olm_runtime_trace_result",\n'
                '  "schema": 1,\n'
                '  "results": [\n'
                "    {\n"
                f'      "request_id": "{request_id}",\n'
                '      "status": "answered",\n'
                '      "summary": "Synthetic bundled runtime witness.",\n'
                '      "observations": {"synthetic_value": 31}\n'
                "    }\n"
                "  ]\n"
                "}\n"
            ),
        )


def write_bundle_return_zip(path: Path, request_zip: Path, return_zip: Path) -> None:
    bundle_stem = path.stem
    request_stem = request_zip.stem
    return_stem = return_zip.stem
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            f"{bundle_stem}/windows_action_bundle_manifest.json",
            '{\n  "kind": "olm_windows_action_bundle",\n  "priority": "priority4-runtime"\n}\n',
        )
        archive.writestr(
            f"{bundle_stem}/README_RETURN_BUNDLE.md",
            "synthetic bundle return\n",
        )
        archive.writestr(
            f"{bundle_stem}/request_package/{request_stem}/windows_action_bundle_manifest.json",
            '{\n  "kind": "olm_windows_action_bundle",\n  "priority": "priority4-runtime"\n}\n',
        )
        archive.write(
            request_zip,
            f"{bundle_stem}/request_package/{request_stem}/runtime_trace/{request_zip.name}",
        )
        archive.write(
            return_zip,
            f"{bundle_stem}/runtime_trace_returns/{return_zip.name}",
        )


def write_folder_style_bundle_return_zip(path: Path, request_ids: list[str]) -> None:
    bundle_stem = path.stem
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            f"{bundle_stem}/QUEUE_README.txt",
            "synthetic folder-style runtime bundle\n",
        )
        for request_id in request_ids:
            archive.writestr(
                f"{bundle_stem}/{request_id}/RETURN_RUNTIME_TRACE_RESULT.json",
                (
                    "{\n"
                    '  "kind": "olm_runtime_trace_result",\n'
                    '  "schema": 1,\n'
                    '  "results": [\n'
                    "    {\n"
                    f'      "request_id": "{request_id}",\n'
                    '      "status": "answered",\n'
                    '      "summary": "Synthetic folder-style bundled runtime witness."\n'
                    "    }\n"
                    "  ]\n"
                    "}\n"
                ),
            )
            archive.writestr(
                f"{bundle_stem}/{request_id}/request_package/runtime_trace_package_manifest.json",
                (
                    "{\n"
                    '  "kind": "olm_runtime_trace_request_package",\n'
                    '  "runtime_actions": [\n'
                    f'    {{"request_id": "{request_id}"}}\n'
                    "  ]\n"
                    "}\n"
                ),
            )


def write_olmblur_standalone_witness_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "databreak_probe/WITNESS_RESULT.json",
            (
                "{\n"
                '  "plugin": "OLMBlur",\n'
                '  "case": "olmblur__case_0007",\n'
                '  "bit_depth": "16bpc",\n'
                '  "target": {"x": 345, "y": 672, "channel": "B"},\n'
                '  "runtime_path": "FUN_180005f20",\n'
                '  "registers_at_write": {"rcx": "0x0"},\n'
                '  "source_float_triplet_raw_words": ["0x46440000", "0x00003100", "0x00000000"],\n'
                '  "source_float_triplet_big_endian_decode": {"b": 12544.498046875},\n'
                '  "final_word": {"decimal": 12544, "hex": "0x3100"},\n'
                '  "interpretation": "Synthetic standalone witness."\n'
                "}\n"
            ),
        )
        archive.writestr("databreak_probe/README_WITNESS.md", "synthetic standalone witness\n")


def main() -> int:
    root = repo_root()
    helper = root / "scripts" / "intake_latest_windows_return_from_share.py"
    py = sys.executable

    with tempfile.TemporaryDirectory(prefix="olm_share_intake_smoke_") as tmp:
        tmp_root = Path(tmp)
        share_root = tmp_root / "olm_pr"
        new_dir = share_root / "new"
        old_dir = share_root / "old"
        new_dir.mkdir(parents=True)
        old_dir.mkdir(parents=True)

        package = tmp_root / "runtime_request.zip"
        run([py, "scripts/package_runtime_trace_requests.py", "--output", str(package)], root)
        shutil.copyfile(package, new_dir / f"20260711_230000__{package.name}")

        returned = new_dir / "runtime_trace_return.zip"
        make_return_zip(returned)
        (new_dir / "runtime_trace_return__README.txt").write_text("runtime trace return\n", encoding="utf-8")
        (new_dir / "unrelated_pending_request.zip").write_text("leave me alone\n", encoding="utf-8")

        summary_json = tmp_root / "runtime_summary.json"
        summary_md = tmp_root / "runtime_summary.md"
        comparisons = tmp_root / "runtime_comparisons"

        dry = run(
            [
                py,
                str(helper),
                "--share-root",
                str(share_root),
                "--dry-run",
            ],
            root,
        )
        if "runtime-trace-return" not in dry.stdout:
            print("[FAIL] dry-run did not choose runtime-trace return")
            return 1

        proc = run(
            [
                py,
                str(helper),
                "--share-root",
                str(share_root),
                "--kind",
                "runtime-trace-return",
                f"--intake-arg=--runtime-package",
                f"--intake-arg={package}",
                "--intake-arg=--runtime-summary-json",
                f"--intake-arg={summary_json}",
                "--intake-arg=--runtime-summary-md",
                f"--intake-arg={summary_md}",
                "--intake-arg=--runtime-comparison-dir",
                f"--intake-arg={comparisons}",
            ],
            root,
        )
        if "[INFO] detected return kind: runtime-trace" not in proc.stdout:
            print("[FAIL] helper did not route to runtime-trace intake")
            return 1
        if "proof_lane_json=" not in proc.stdout or "proof_lane_md=" not in proc.stdout:
            print("[FAIL] helper did not emit runtime proof-lane summary")
            return 1
        if not summary_json.exists() or not summary_md.exists():
            print("[FAIL] helper did not produce runtime trace summaries")
            return 1
        if not (tmp_root / "runtime_summary_proof_lanes.json").exists():
            print("[FAIL] helper did not produce runtime proof-lane JSON")
            return 1

        older_request = tmp_root / "older_runtime_request.zip"
        newer_request = tmp_root / "newer_runtime_request.zip"
        write_runtime_request_zip(older_request, "older_request_id")
        write_runtime_request_zip(newer_request, "newer_request_id")
        runtime_package_dir = root / "refs" / "runtime_trace_packages"
        old_repo_pkg = runtime_package_dir / "zzz_smoke_old_request_package.zip"
        new_repo_pkg = runtime_package_dir / "zzz_smoke_new_request_package.zip"
        shutil.copyfile(older_request, old_repo_pkg)
        shutil.copyfile(newer_request, new_repo_pkg)
        try:
            mismatched_return = new_dir / "mismatched_runtime_trace_return.zip"
            write_runtime_return_zip(mismatched_return, "older_request_id", portable=True)
            dry_runtime = run(
                [
                    py,
                    str(helper),
                    "--share-root",
                    str(share_root),
                    "--kind",
                    "runtime-trace-return",
                    "--dry-run",
                ],
                root,
            )
            if str(old_repo_pkg) not in dry_runtime.stdout:
                print("[FAIL] helper did not auto-resolve runtime package from return request_id")
                return 1
            if str(new_repo_pkg) in dry_runtime.stdout:
                print("[FAIL] helper chose the newest runtime package instead of matching request_id")
                return 1
        finally:
            mismatched_return.unlink(missing_ok=True)
            old_repo_pkg.unlink(missing_ok=True)
            new_repo_pkg.unlink(missing_ok=True)
        if not (tmp_root / "runtime_summary_proof_lanes.md").exists():
            print("[FAIL] helper did not produce runtime proof-lane Markdown")
            return 1
        remaining_names = {path.name for path in new_dir.iterdir() if path.is_file()}
        if remaining_names != {"unrelated_pending_request.zip"}:
            print(f"[FAIL] helper archived the wrong files from share/new: {sorted(remaining_names)}")
            return 1
        archived_names = {path.name for path in old_dir.iterdir() if path.is_file()}
        if not any(name.endswith("runtime_trace_return.zip") for name in archived_names):
            print("[FAIL] helper did not archive the processed zip")
            return 1
        if not any(name.endswith("runtime_trace_return__README.txt") for name in archived_names):
            print("[FAIL] helper did not archive the companion README")
            return 1

        bundle_share_root = tmp_root / "olm_pr_bundle"
        bundle_new = bundle_share_root / "new"
        bundle_old = bundle_share_root / "old"
        bundle_new.mkdir(parents=True)
        bundle_old.mkdir(parents=True)

        request_id = "synthetic_bundle_runtime_trace_20260630"
        request_zip = tmp_root / f"{request_id}.zip"
        write_runtime_request_zip(request_zip, request_id)
        nested_return_zip = tmp_root / f"{request_id}_return_windows.zip"
        write_runtime_return_zip(nested_return_zip, request_id)
        bundle_zip = bundle_new / "olm_windows_action_bundle_synthetic_return_windows.zip"
        write_bundle_return_zip(bundle_zip, request_zip, nested_return_zip)

        bundle_dry = run(
            [
                py,
                str(helper),
                "--share-root",
                str(bundle_share_root),
                "--dry-run",
            ],
            root,
        )
        if "windows-action-bundle-return" not in bundle_dry.stdout:
            print("[FAIL] dry-run did not choose windows-action-bundle-return")
            return 1

        bundle_proc = run(
            [
                py,
                str(helper),
                "--share-root",
                str(bundle_share_root),
                "--kind",
                "windows-action-bundle-return",
            ],
            root,
        )
        if "[OK] processed bundled runtime returns into" not in bundle_proc.stdout:
            print("[FAIL] helper did not process bundled runtime returns")
            return 1
        if "proof_lane_json=" not in bundle_proc.stdout:
            print("[FAIL] helper did not emit proof-lane summary for bundled runtime returns")
            return 1
        bundle_report_dir = (
            root
            / "refs"
            / "reports"
            / "runtime_trace_bundle"
            / "olm_windows_action_bundle_synthetic_return_windows"
        )
        if not any(bundle_report_dir.glob("runtime_trace_summary_*.json")):
            print("[FAIL] helper did not write bundled runtime summary JSON")
            return 1
        if not any(bundle_report_dir.glob("runtime_trace_summary_*_proof_lanes.json")):
            print("[FAIL] helper did not write bundled proof-lane JSON")
            return 1
        if any(path.is_file() for path in bundle_new.iterdir()):
            print("[FAIL] helper did not archive bundle-return files out of share/new")
            return 1

        folder_bundle_share_root = tmp_root / "olm_pr_folder_bundle"
        folder_bundle_new = folder_bundle_share_root / "new"
        folder_bundle_old = folder_bundle_share_root / "old"
        folder_bundle_new.mkdir(parents=True)
        folder_bundle_old.mkdir(parents=True)

        folder_request_ids = [
            "olmblur_final_word_witness_20260630",
            "olmradialblur_caller_collapse_witness_20260630",
        ]
        folder_bundle_zip = folder_bundle_new / "olm_runtime_trace_requests_20260630_4pack_windows_return.zip"
        write_folder_style_bundle_return_zip(folder_bundle_zip, folder_request_ids)

        folder_bundle_proc = run(
            [
                py,
                str(helper),
                "--share-root",
                str(folder_bundle_share_root),
                "--kind",
                "windows-action-bundle-return",
            ],
            root,
        )
        if "[OK] processed bundled runtime returns into" not in folder_bundle_proc.stdout:
            print("[FAIL] helper did not process folder-style bundled runtime returns")
            return 1
        if "proof_lane_json=" not in folder_bundle_proc.stdout or folder_request_ids[0] not in folder_bundle_proc.stdout:
            print("[FAIL] helper did not emit expected folder-style runtime summary/proof-lane output")
            return 1
        if any(path.is_file() for path in folder_bundle_new.iterdir()):
            print("[FAIL] helper did not archive folder-style bundle-return files out of share/new")
            return 1

        witness_share_root = tmp_root / "olm_pr_witness"
        witness_new = witness_share_root / "new"
        witness_old = witness_share_root / "old"
        witness_new.mkdir(parents=True)
        witness_old.mkdir(parents=True)

        witness_zip = witness_new / "olmblur_case0007_16bpc_345_672_b_witness_windows_20260630.zip"
        write_olmblur_standalone_witness_zip(witness_zip)
        (witness_new / "still_pending_request.zip").write_text("pending\n", encoding="utf-8")

        witness_dry = run(
            [
                py,
                str(helper),
                "--share-root",
                str(witness_share_root),
                "--dry-run",
            ],
            root,
        )
        if "olmblur-standalone-witness" not in witness_dry.stdout:
            print("[FAIL] dry-run did not choose OLMBlur standalone witness")
            return 1

        witness_proc = run(
            [
                py,
                str(helper),
                "--share-root",
                str(witness_share_root),
                "--kind",
                "olmblur-standalone-witness",
            ],
            root,
        )
        if "output_json=" not in witness_proc.stdout or "output_md=" not in witness_proc.stdout:
            print("[FAIL] helper did not run standalone witness intake")
            return 1
        witness_remaining = {path.name for path in witness_new.iterdir() if path.is_file()}
        if witness_remaining != {"still_pending_request.zip"}:
            print(f"[FAIL] helper archived the wrong standalone witness files: {sorted(witness_remaining)}")
            return 1
        archived_witness_names = {path.name for path in witness_old.iterdir() if path.is_file()}
        if not any(name.endswith("olmblur_case0007_16bpc_345_672_b_witness_windows_20260630.zip") for name in archived_witness_names):
            print("[FAIL] helper did not archive the standalone witness zip")
            return 1

        winref_share_root = tmp_root / "olm_pr_winref"
        winref_new = winref_share_root / "new"
        winref_old = winref_share_root / "old"
        winref_new.mkdir(parents=True)
        winref_old.mkdir(parents=True)
        winref_build = tmp_root / "winref_build"
        winref_build.mkdir(parents=True)
        winref_zip, winref_requests_dir, winref_request_path = make_windows_ref_return(winref_build)
        shared_winref_zip = winref_new / "synthetic_win_reference_return.zip"
        shutil.copyfile(winref_zip, shared_winref_zip)
        (winref_new / "synthetic_win_reference_return__README.txt").write_text("reference return\n", encoding="utf-8")
        winref_dest_root = tmp_root / "winref_imported_refs"
        winref_set_id = "synthetic_win_reference_return_smoke"
        winref_summary_json = tmp_root / "winref_summary.json"
        winref_summary_md = tmp_root / "winref_summary.md"

        winref_dry = run(
            [
                py,
                str(helper),
                "--share-root",
                str(winref_share_root),
                "--kind",
                "win-reference-return",
                "--dry-run",
            ],
            root,
        )
        if "win-reference-return" not in winref_dry.stdout:
            print("[FAIL] dry-run did not choose win-reference-return")
            return 1
        if "--quick --dispatch-dir /tmp/olm_reference_dispatch" not in winref_dry.stdout:
            print("[FAIL] helper did not emit the expected win-reference intake command")
            return 1

        winref_proc = run(
            [
                py,
                "scripts/intake_olm_return.py",
                str(shared_winref_zip),
                "--set-id",
                winref_set_id,
                "--dest-root",
                str(winref_dest_root),
                "--requests-dir",
                str(winref_requests_dir),
                "--request",
                str(winref_request_path),
                "--no-next-actions",
            ],
            root,
        )
        if "[INFO] detected return kind: win-reference" not in winref_proc.stdout:
            print("[FAIL] win-reference intake did not detect the expected return kind")
            return 1
        if "reference_manifest.json" not in winref_proc.stdout:
            print("[FAIL] win-reference intake did not report the imported manifest")
            return 1

        winref_summary_proc = run(
            [
                py,
                "scripts/summarize_win_reference_return.py",
                str(shared_winref_zip),
                "--imported-set-dir",
                str(winref_dest_root / winref_set_id),
                "--output-json",
                str(winref_summary_json),
                "--output-md",
                str(winref_summary_md),
            ],
            root,
        )
        if "win_reference_summary_json=" not in winref_summary_proc.stdout:
            print("[FAIL] win-reference summary did not emit output paths")
            return 1
        if not (winref_dest_root / winref_set_id / "SyntheticEffect" / "reference_manifest.json").exists():
            print("[FAIL] helper did not import win-reference return into the isolated destination")
            return 1
        if not winref_summary_json.exists() or not winref_summary_md.exists():
            print("[FAIL] win-reference summary did not create output files")
            return 1

    print("[OK] intake latest Windows return from share smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
