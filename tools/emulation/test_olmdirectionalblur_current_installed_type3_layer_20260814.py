#!/usr/bin/env python3
"""Replay the installed DirectionalBlur Type-3 Layer admission on both slices."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
PROBE = ROOT / "tools/emulation/probe_olmdirectionalblur_current_installed_type3_layer_20260813.cpp"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
TRANSACTION = ROOT / "handoffs/olmdirectionalblur_testseam_compat_install_20260814/install_transaction.json"
BUILD = ROOT / "handoffs/olmdirectionalblur_testseam_compat_candidate_20260814/build_identity.json"
CLOSURE = ROOT / "refs/conformance/olmdirectionalblur_type3_layer_source_guard_closure_20260813.json"
IMAGE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_current_installed_type3_layer_20260814.json"
NOTE = REPORT.with_suffix(".md")
EXPECTED_SOURCE = "494116880d037a0d44a48b0e0ebe0fc5358b4cd8892b90ca8c61ea8a7bb2e845"
EXPECTED_BINARY = "856ab700df0881cfb039e9c9d0675bf46a7e92b56e8cb0e311d820fd719bc0de"
EXPECTED_TRANSCRIPT = "395c9f84e0aa17e1ca43303b740d7f8734115856b07244c51ac17762d5683058"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ae_processes() -> list[str]:
    rows: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], capture_output=True, text=True)
        rows += [f"{name}:{pid}" for pid in run.stdout.split() if pid.isdigit()]
    return rows


def compile_probe(output: Path, arch: str) -> None:
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    command = [
        "clang++", "-std=c++17", "-arch", arch, "-O2", "-fno-fast-math",
        "-ffp-contract=off", "-isysroot", sdk, "-Wno-pragma-pack",
        "-Wno-deprecated-declarations",
    ]
    for include in ("Headers", "Headers/SP", "Util", "Resources", "core", "mac/OLMDirectionalBlur"):
        command += ["-I", str(ROOT / include)]
    command += [
        str(PROBE), str(ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.cpp"),
        str(ROOT / "Util/AEGP_SuiteHandler.cpp"), str(ROOT / "Util/MissingSuiteError.cpp"),
        str(ROOT / "core/dblur_frontonly.cpp"), str(ROOT / "core/dblur_rotate.cpp"),
        str(ROOT / "core/dblur_rowdriver.cpp"), str(ROOT / "core/dblur_field.cpp"),
        "-framework", "Cocoa", "-o", str(output),
    ]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)


def replay() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="directional-type3-installed.") as raw:
        temp = Path(raw)
        rgba = temp / "input.rgba"
        rgba.write_bytes(Image.open(IMAGE).convert("RGBA").crop((472, 262, 488, 278)).tobytes())
        slices = {}
        for arch in ("arm64", "x86_64"):
            executable = temp / f"probe-{arch}"
            compile_probe(executable, arch)
            command = [str(executable), str(INSTALLED), str(rgba)]
            if arch == "x86_64":
                command = ["arch", "-x86_64", *command]
            run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            digest = hashlib.sha256(run.stdout.encode()).hexdigest()
            if run.returncode or run.stderr or digest != EXPECTED_TRANSCRIPT or not run.stdout.endswith("SUMMARY pass=57 total=57\n"):
                raise RuntimeError(f"installed Type3 replay drift: {arch}: {run.stderr}")
            slices[arch] = {
                "positive": 3, "negative": 54, "total": 57,
                "transcript_sha256": digest,
            }
        return slices


def identities() -> dict[str, str]:
    return {
        "source_sha256": sha256(SOURCE), "probe_sha256": sha256(PROBE),
        "installed_binary_sha256": sha256(INSTALLED),
        "accepted_identity_sha256": sha256(IDENTITY),
        "transaction_sha256": sha256(TRANSACTION), "build_identity_sha256": sha256(BUILD),
        "type3_closure_sha256": sha256(CLOSURE), "fixture_png_sha256": sha256(IMAGE),
    }


def generate() -> dict[str, object]:
    ids = identities()
    if ids["source_sha256"] != EXPECTED_SOURCE or ids["installed_binary_sha256"] != EXPECTED_BINARY:
        raise RuntimeError("installed/source identity drift")
    manifest = json.loads(IDENTITY.read_text())
    row = next(item for item in manifest["plugins"] if item["plugin"] == "OLMDirectionalBlur")
    if row["sha256"] != EXPECTED_BINARY or row["source_sha256"] != EXPECTED_BINARY or not row["source_installed_exact"]:
        raise RuntimeError("accepted DirectionalBlur row drift")
    processes = ae_processes()
    if processes:
        raise RuntimeError("AE-family process running")
    return {
        "schema": "olmdirectionalblur.current-installed-type3-layer/1",
        "status": "PASS_CURRENT_INSTALLED_TYPE3_LAYER_BOTH_SLICES_57_OF_57_AE_FREE",
        "identities": ids, "slices": replay(), "after_effects_processes": [],
        "claim": {
            "windows_exported_smart_same_source": True,
            "installed_public_raw_exact_depths": [8, 16, 32],
            "one_away_fail_closed_per_slice": 54,
            "input_layer_output_padding_headers_immutable": True,
            "native_after_effects": False, "native_windows": False,
            "arbitrary_source_tuple_geometry": False,
        },
    }


def validate(value: dict[str, object]) -> bool:
    if set(value) != {"schema", "status", "identities", "slices", "after_effects_processes", "claim"}:
        return False
    if value["schema"] != "olmdirectionalblur.current-installed-type3-layer/1" or value["status"] != "PASS_CURRENT_INSTALLED_TYPE3_LAYER_BOTH_SLICES_57_OF_57_AE_FREE":
        return False
    if value["identities"] != identities() or value["after_effects_processes"] != []:
        return False
    expected_slice = {"positive": 3, "negative": 54, "total": 57, "transcript_sha256": EXPECTED_TRANSCRIPT}
    if value["slices"] != {"arm64": expected_slice, "x86_64": expected_slice}:
        return False
    return value["claim"] == {
        "windows_exported_smart_same_source": True,
        "installed_public_raw_exact_depths": [8, 16, 32],
        "one_away_fail_closed_per_slice": 54,
        "input_layer_output_padding_headers_immutable": True,
        "native_after_effects": False, "native_windows": False,
        "arbitrary_source_tuple_geometry": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    current = generate()
    if args.write:
        REPORT.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        NOTE.write_text(
            "# OLMDirectionalBlur current installed Type-3 Layer\n\n"
            "The installed arm64 and Rosetta x86_64 slices each replay the fixed 16x16 "
            "Type-3 Layer public route at PF8/PF16/PF32: 3 raw-exact positives and 54 "
            "source/layout one-away fail-closed controls. This is hostless evidence; no native "
            "After Effects or native Windows execution is claimed.\n"
        )
    if not REPORT.exists():
        raise RuntimeError("report missing")
    stored = json.loads(REPORT.read_text())
    if stored != current or not validate(stored):
        raise RuntimeError("installed Type3 report drift")
    print(current["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
