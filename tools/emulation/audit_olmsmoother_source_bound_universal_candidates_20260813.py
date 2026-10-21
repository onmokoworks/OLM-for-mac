#!/usr/bin/env python3
"""Validate frozen Smoother candidates and their current installed relation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoffs/olmsmoother_source_bound_atomic_universal_candidate_v3_20260813"
MANIFEST = HANDOFF / "build_identity.json"
FROZEN_MANIFEST_SHA256 = "5bc7432144a90801319452b1a23e39e131a75a266c270839640eff68a4bd40bd"
CURRENT_CLOSURE_SHA256 = "55c5a81188a5042d25fb691abb154c4b44dbbec1b93cd3de8536fdced3cc92b8"
ACCEPTED_IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
ACCEPTED_IDENTITY_SHA256 = "426dce713a9595157fe4c9fa3731c464e4ef10afd5db269335a12fa4b38beccc"
BATCH4_INSTALL = ROOT / "refs/conformance/olm_hostless_batch4_incremental_install_20260813.json"
BATCH4_INSTALL_SHA256 = "415e1b26b77097248173da13239b85ae70d0b6a446fa6eb31bc13a0bdc6895af"
VALIDATION_FILES = [
    Path(__file__).resolve(),
    ROOT / "tests/test_olmsmoother_source_bound_universal_candidates_20260813.py",
]

CONFIGS = {
    "OLMSmoother": {
        "project": ROOT / "mac/OLMSmoother/Mac/OLMSmoother.xcodeproj",
        "scheme": "OLMSmoother",
        "source": ROOT / "mac/OLMSmoother/Mac/OLMSmoother_port.cpp",
        "project_file": ROOT / "mac/OLMSmoother/Mac/OLMSmoother.xcodeproj/project.pbxproj",
    },
    "OLMSmoother2": {
        "project": ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2.xcodeproj",
        "scheme": "OLMSmoother2",
        "source": ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp",
        "project_file": ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2.xcodeproj/project.pbxproj",
    },
}

BOUND_INPUTS = [
    ROOT / "core/olm_sha256_rows.h",
    ROOT / "tools/emulation/olmsmoother_v1_public_guard_harness_20260812.cpp",
    ROOT / "tools/emulation/olmsmoother2_public_guard_harness_20260812.cpp",
    ROOT / "tools/emulation/test_olmsmoother_public_admission_guard_closure_20260812.py",
    ROOT / "tools/emulation/test_olmsmoother_public_admission_guard_closure_unit_20260812.py",
    ROOT / "refs/conformance/olmsmoother_public_admission_guard_closure_20260812.json",
    ROOT / "tests/test_olmsmoother_source_contract_20260813.py",
    ROOT / "tools/emulation/probe_olmsmoother_real_sdk_suite_lifecycle_20260813.cpp",
    ROOT / "tests/test_olmsmoother_real_sdk_suite_lifecycle_20260813.py",
    ROOT / "scripts/run_olm_mac_fixed_fixture_regression_20260805.py",
]

README_TEXT = (
    "# Smoother source-bound Universal candidates\n\n"
    "Both bundles are durable Debug Universal candidates built from the fixed-source, atomic-output public admissions. "
    "They are ad-hoc signed and target macOS 11.0. They are not installed, notarized, or AE-smoked. "
    "Numerical authority remains the separately validated public admission closure.\n"
)


def expected_command(name: str, cfg: dict[str, object], derived: Path | None = None) -> list[str]:
    derived_arg = str(derived) if derived is not None else f"<DERIVED_DATA:{name}>"
    return [
        "xcodebuild", "-project", Path(cfg["project"]).relative_to(ROOT).as_posix(),
        "-scheme", str(cfg["scheme"]), "-configuration", "Debug",
        "-derivedDataPath", derived_arg, "ARCHS=arm64 x86_64", "ONLY_ACTIVE_ARCH=NO",
        "CODE_SIGNING_ALLOWED=NO", "MACOSX_DEPLOYMENT_TARGET=11.0", "build",
    ]


def normalized_command(command: list[str]) -> list[str]:
    result = list(command)
    index = result.index("-derivedDataPath") + 1
    result[index] = f"<DERIVED_DATA:{result[result.index('-scheme') + 1]}>"
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"path": path.relative_to(ROOT).as_posix(), "size": path.stat().st_size, "sha256": sha256(path)}


def validation_identities() -> dict[str, dict[str, object]]:
    return {path.relative_to(ROOT).as_posix(): identity(path) for path in VALIDATION_FILES}


def run(*args: str, check: bool = True) -> str:
    result = subprocess.run(args, cwd=ROOT, check=check, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.stdout


def inventory(bundle: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in [bundle, *sorted(bundle.rglob("*"), key=lambda p: p.relative_to(bundle).as_posix())]:
        relative = "." if path == bundle else path.relative_to(bundle).as_posix()
        mode = stat.filemode(path.lstat().st_mode)
        if path.is_symlink():
            rows.append({"path": relative, "kind": "symlink", "mode": mode, "target": str(path.readlink())})
        elif path.is_dir():
            rows.append({"path": relative, "kind": "directory", "mode": mode})
        elif path.is_file():
            rows.append({"path": relative, "kind": "file", "mode": mode,
                         "size": path.stat().st_size, "sha256": sha256(path)})
        else:
            raise RuntimeError(f"unsupported artifact entry: {path}")
    return rows


def build_version(binary: Path, arch: str) -> dict[str, str]:
    text = run("otool", "-arch", arch, "-l", str(binary))
    match = re.search(r"cmd LC_BUILD_VERSION\s+cmdsize \d+\s+platform 1\s+minos ([0-9.]+)\s+sdk ([0-9.]+)", text)
    if not match:
        raise RuntimeError(f"LC_BUILD_VERSION missing: {arch}")
    return {"minos": match.group(1), "sdk": match.group(2)}


def exports(binary: Path, arch: str) -> list[str]:
    text = run("nm", "-arch", arch, "-gU", str(binary))
    found = sorted({line.split()[-1] for line in text.splitlines()
                    if line.split() and line.split()[-1] in {"_EffectMain", "_PluginDataEntryFunction2"}})
    return found


def build() -> None:
    if HANDOFF.exists():
        raise RuntimeError(f"refusing to overwrite durable handoff: {HANDOFF}")
    explicit = [entry for cfg in CONFIGS.values() for entry in (cfg["source"], cfg["project_file"])] + BOUND_INPUTS
    before = {path.relative_to(ROOT).as_posix(): identity(path) for path in explicit}
    stage = Path(tempfile.mkdtemp(prefix="olmsmoother-candidate-stage-", dir=str(ROOT / "handoffs")))
    try:
        (stage / "candidates").mkdir()
        (stage / "logs").mkdir()
        builds: dict[str, object] = {}
        for name, cfg in CONFIGS.items():
            derived = Path(tempfile.mkdtemp(prefix=f"{name.lower()}-derived-"))
            command = expected_command(name, cfg, derived)
            command[2] = str(cfg["project"])
            completed = subprocess.run(command, cwd=ROOT, text=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log = stage / "logs" / f"{name}_xcodebuild.log"
            log.write_text(completed.stdout)
            if completed.returncode or "** BUILD SUCCEEDED **" not in completed.stdout:
                raise RuntimeError(f"{name} build failed; inspect {log}")
            products = list((derived / "Build/Products/Debug").glob(f"{name}.plugin"))
            if len(products) != 1:
                raise RuntimeError(f"{name} product count: {len(products)}")
            candidate = stage / "candidates" / f"{name}.plugin"
            shutil.copytree(products[0], candidate, symlinks=True)
            run("codesign", "--force", "--deep", "--sign", "-", str(candidate))
            run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(candidate))
            binary = candidate / "Contents/MacOS" / name
            archs = run("lipo", "-archs", str(binary)).strip().split()
            if set(archs) != {"arm64", "x86_64"}:
                raise RuntimeError(f"{name} architecture drift: {archs}")
            plist = plistlib.loads((candidate / "Contents/Info.plist").read_bytes())
            builds[name] = {
                "project": Path(cfg["project"]).relative_to(ROOT).as_posix(),
                "scheme": cfg["scheme"],
                "configuration": "Debug",
                "deployment_target": "11.0",
                "command": [part if not part.startswith(str(ROOT)) else Path(part).relative_to(ROOT).as_posix()
                            for part in command],
                "log": {"path": log.relative_to(stage).as_posix(), "size": log.stat().st_size,
                        "sha256": sha256(log)},
                "bundle": candidate.relative_to(stage).as_posix(),
                "binary_sha256": sha256(binary),
                "architectures": sorted(archs),
                "build_versions": {arch: build_version(binary, arch) for arch in sorted(archs)},
                "exports": {arch: exports(binary, arch) for arch in sorted(archs)},
                "info_minimum_system_version": plist.get("LSMinimumSystemVersion"),
                "codesign": "ad-hoc strict/deep valid",
                "inventory": inventory(candidate),
            }
            shutil.rmtree(derived)
        after = {path.relative_to(ROOT).as_posix(): identity(path) for path in explicit}
        if before != after:
            raise RuntimeError("bound source/evidence changed during build")
        manifest = {
            "schema": "olm.smoother-source-bound-atomic-universal-candidate/1",
            "verdict": "PASS_DURABLE_SOURCE_BOUND_ATOMIC_UNIVERSAL_CANDIDATES_NOT_INSTALLED",
            "claim_boundary": {
                "installed": False,
                "after_effects_launched": False,
                "after_effects_smoke": False,
                "distribution_signed": False,
                "notarized": False,
                "numerical_claim_authority": "refs/conformance/olmsmoother_public_admission_guard_closure_20260812.json",
            },
            "bound_inputs_before": before,
            "bound_inputs_after": after,
            "source_stable_during_build": True,
            "validation_files": validation_identities(),
            "builds": builds,
        }
        (stage / "build_identity.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        (stage / "README.md").write_text(README_TEXT)
        os.rename(stage, HANDOFF)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def validate_data(data: dict[str, object], *, live: bool = True) -> None:
    if set(data) != {"schema", "verdict", "claim_boundary", "bound_inputs_before",
                     "bound_inputs_after", "source_stable_during_build", "validation_files", "builds"}:
        raise AssertionError("top-level schema drift")
    if data["schema"] != "olm.smoother-source-bound-atomic-universal-candidate/1":
        raise AssertionError("schema drift")
    if data["verdict"] != "PASS_DURABLE_SOURCE_BOUND_ATOMIC_UNIVERSAL_CANDIDATES_NOT_INSTALLED":
        raise AssertionError("verdict drift")
    boundary = data["claim_boundary"]
    if set(boundary) != {"installed", "after_effects_launched", "after_effects_smoke",
                        "distribution_signed", "notarized", "numerical_claim_authority"}:
        raise AssertionError("claim boundary schema drift")
    for key in ("installed", "after_effects_launched", "after_effects_smoke", "distribution_signed", "notarized"):
        if boundary.get(key) is not False:
            raise AssertionError(f"claim widened: {key}")
    if boundary["numerical_claim_authority"] != "refs/conformance/olmsmoother_public_admission_guard_closure_20260812.json":
        raise AssertionError("numerical authority drift")
    if data["bound_inputs_before"] != data["bound_inputs_after"] or data["source_stable_during_build"] is not True:
        raise AssertionError("source stability drift")
    expected_inputs = {
        path.relative_to(ROOT).as_posix()
        for cfg in CONFIGS.values() for path in (cfg["source"], cfg["project_file"])
    } | {path.relative_to(ROOT).as_posix() for path in BOUND_INPUTS}
    if set(data["bound_inputs_after"]) != expected_inputs:
        raise AssertionError("bound input set drift")
    for relative, row in data["bound_inputs_after"].items():
        if set(row) != {"path", "size", "sha256"} or row["path"] != relative:
            raise AssertionError(f"bound input identity schema drift: {relative}")
    if set(data["validation_files"]) != {path.relative_to(ROOT).as_posix() for path in VALIDATION_FILES}:
        raise AssertionError("validation file set drift")
    for relative, row in data["validation_files"].items():
        if set(row) != {"path", "size", "sha256"} or row["path"] != relative:
            raise AssertionError(f"validation identity schema drift: {relative}")
    if set(data["builds"]) != set(CONFIGS):
        raise AssertionError("build set drift")
    for name, build_row in data["builds"].items():
        cfg = CONFIGS[name]
        if set(build_row) != {"project", "scheme", "configuration", "deployment_target", "command", "log", "bundle",
                             "binary_sha256", "architectures", "build_versions", "exports",
                             "info_minimum_system_version", "codesign", "inventory"}:
            raise AssertionError(f"build schema drift: {name}")
        if build_row["project"] != Path(cfg["project"]).relative_to(ROOT).as_posix() or build_row["scheme"] != cfg["scheme"]:
            raise AssertionError(f"project identity drift: {name}")
        if build_row["configuration"] != "Debug" or build_row["deployment_target"] != "11.0":
            raise AssertionError(f"build configuration drift: {name}")
        if build_row["bundle"] != f"candidates/{name}.plugin" or build_row["log"]["path"] != f"logs/{name}_xcodebuild.log":
            raise AssertionError(f"artifact path drift: {name}")
        if normalized_command(build_row["command"]) != expected_command(name, cfg):
            raise AssertionError(f"build command drift: {name}")
        if build_row["codesign"] != "ad-hoc strict/deep valid":
            raise AssertionError(f"codesign claim drift: {name}")
        if set(build_row["log"]) != {"path", "size", "sha256"}:
            raise AssertionError(f"log schema drift: {name}")
        if build_row["architectures"] != ["arm64", "x86_64"]:
            raise AssertionError(f"architecture contract drift: {name}")
        if set(build_row["build_versions"]) != {"arm64", "x86_64"} or set(build_row["exports"]) != {"arm64", "x86_64"}:
            raise AssertionError(f"slice record drift: {name}")
        for arch in ("arm64", "x86_64"):
            if set(build_row["build_versions"][arch]) != {"minos", "sdk"} or build_row["build_versions"][arch]["minos"] != "11.0":
                raise AssertionError(f"build-version record drift: {name}/{arch}")
            if build_row["exports"][arch] != ["_EffectMain"]:
                raise AssertionError(f"export record drift: {name}/{arch}")
        if build_row["info_minimum_system_version"] != "11.0":
            raise AssertionError(f"Info.plist deployment record drift: {name}")
    if not live:
        return
    if data["validation_files"] != validation_identities():
        raise AssertionError("validator identity drift")
    for relative, expected in data["bound_inputs_after"].items():
        if identity(ROOT / relative) != expected:
            raise AssertionError(f"bound input drift: {relative}")
    if (HANDOFF / "README.md").read_text() != README_TEXT:
        raise AssertionError("README drift")
    for name, build_row in data["builds"].items():
        bundle = HANDOFF / build_row["bundle"]
        binary = bundle / "Contents/MacOS" / name
        log = HANDOFF / build_row["log"]["path"]
        if {"path": build_row["log"]["path"], "size": log.stat().st_size,
            "sha256": sha256(log)} != build_row["log"]:
            raise AssertionError(f"build log drift: {name}")
        if sha256(binary) != build_row["binary_sha256"]:
            raise AssertionError(f"binary drift: {name}")
        if sorted(run("lipo", "-archs", str(binary)).strip().split()) != build_row["architectures"]:
            raise AssertionError(f"architecture drift: {name}")
        if build_row["architectures"] != ["arm64", "x86_64"]:
            raise AssertionError(f"architecture contract drift: {name}")
        for arch in build_row["architectures"]:
            if build_version(binary, arch) != build_row["build_versions"][arch]:
                raise AssertionError(f"build-version drift: {name}/{arch}")
            if build_row["build_versions"][arch]["minos"] != "11.0":
                raise AssertionError(f"deployment target drift: {name}/{arch}")
            if exports(binary, arch) != ["_EffectMain"]:
                raise AssertionError(f"export drift: {name}/{arch}")
        if build_row["info_minimum_system_version"] != "11.0":
            raise AssertionError(f"Info.plist deployment drift: {name}")
        run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(bundle))
        if inventory(bundle) != build_row["inventory"]:
            raise AssertionError(f"bundle inventory drift: {name}")


def validate_current_relation(data: dict[str, object]) -> None:
    """Keep the build-time claim frozen while proving the later install relation."""
    validate_data(data, live=False)
    if sha256(MANIFEST) != FROZEN_MANIFEST_SHA256:
        raise AssertionError("frozen candidate manifest drift")
    if data != json.loads(MANIFEST.read_text(encoding="utf-8")):
        raise AssertionError("frozen candidate data drift")

    # These bytes were compiled into the frozen candidates and must still be exact.
    compiled_inputs = {
        "core/olm_sha256_rows.h",
        "mac/OLMSmoother/Mac/OLMSmoother.xcodeproj/project.pbxproj",
        "mac/OLMSmoother/Mac/OLMSmoother_port.cpp",
        "mac/OLMSmoother2/Mac/OLMSmoother2.xcodeproj/project.pbxproj",
        "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp",
    }
    for relative in compiled_inputs:
        if identity(ROOT / relative) != data["bound_inputs_after"][relative]:
            raise AssertionError(f"compiled input drift: {relative}")

    closure_path = ROOT / data["claim_boundary"]["numerical_claim_authority"]
    if sha256(closure_path) != CURRENT_CLOSURE_SHA256:
        raise AssertionError("current closure drift")
    closure = json.loads(closure_path.read_text(encoding="utf-8"))
    for key, relative in (
        ("production_v1_sha256", "mac/OLMSmoother/Mac/OLMSmoother_port.cpp"),
        ("production_v2_sha256", "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"),
    ):
        if closure["identities"][key] != sha256(ROOT / relative):
            raise AssertionError(f"closure/source relation drift: {key}")

    if sha256(ACCEPTED_IDENTITY) != ACCEPTED_IDENTITY_SHA256:
        raise AssertionError("accepted identity drift")
    accepted = json.loads(ACCEPTED_IDENTITY.read_text(encoding="utf-8"))
    accepted_rows = {row["plugin"]: row for row in accepted["plugins"]}
    if sha256(BATCH4_INSTALL) != BATCH4_INSTALL_SHA256:
        raise AssertionError("batch4 install authority drift")
    batch4 = json.loads(BATCH4_INSTALL.read_text(encoding="utf-8"))
    if batch4["status"] != "PASS_BATCH4_INSTALLED_IDENTITY_AND_ROLLBACK_CLOSED_PENDING_ONE_AE_SMOKE":
        raise AssertionError("batch4 install status drift")
    if batch4["authorities"]["post_identity_sha256"] != ACCEPTED_IDENTITY_SHA256:
        raise AssertionError("batch4/accepted identity relation drift")

    media_core = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"
    for name, build_row in data["builds"].items():
        candidate = HANDOFF / build_row["bundle"]
        binary = candidate / "Contents/MacOS" / name
        if sha256(binary) != build_row["binary_sha256"]:
            raise AssertionError(f"candidate binary drift: {name}")
        if inventory(candidate) != build_row["inventory"]:
            raise AssertionError(f"candidate inventory drift: {name}")
        if sorted(run("lipo", "-archs", str(binary)).strip().split()) != build_row["architectures"]:
            raise AssertionError(f"candidate architecture drift: {name}")
        for arch in build_row["architectures"]:
            if build_version(binary, arch) != build_row["build_versions"][arch]:
                raise AssertionError(f"candidate build-version drift: {name}/{arch}")
            if exports(binary, arch) != build_row["exports"][arch]:
                raise AssertionError(f"candidate export drift: {name}/{arch}")
        run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(candidate))

        accepted_row = accepted_rows.get(name)
        expected_source = candidate.relative_to(ROOT).as_posix()
        if accepted_row is None or set(accepted_row) != {
            "architectures", "codesign_exact", "installed_bundle", "installed_bundle_count",
            "plugin", "sha256", "source_bundle", "source_installed_exact", "source_sha256",
            "universal_exact",
        }:
            raise AssertionError(f"accepted identity row schema drift: {name}")
        if accepted_row["sha256"] != build_row["binary_sha256"] or \
                accepted_row["source_sha256"] != build_row["binary_sha256"] or \
                accepted_row["source_bundle"] != expected_source or \
                set(accepted_row["architectures"]) != set(build_row["architectures"]) or \
                accepted_row["installed_bundle_count"] != 1 or \
                any(accepted_row[key] is not True for key in
                    ("codesign_exact", "source_installed_exact", "universal_exact")):
            raise AssertionError(f"accepted identity row drift: {name}")

        install_row = batch4["plugins"].get(name)
        if install_row is None or install_row["new_sha256"] != build_row["binary_sha256"] or \
                install_row["candidate_installed_full_inventory_exact"] is not True:
            raise AssertionError(f"batch4 install row drift: {name}")

        installed = Path(accepted_row["installed_bundle"])
        installed_binary = installed / "Contents/MacOS" / name
        if not installed.is_dir() or sha256(installed_binary) != build_row["binary_sha256"]:
            raise AssertionError(f"installed binary drift: {name}")
        if inventory(installed) != build_row["inventory"]:
            raise AssertionError(f"installed/candidate full inventory drift: {name}")
        run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(installed))
        if len(list(media_core.glob(f"{name}.plugin"))) != 1:
            raise AssertionError(f"installed bundle count drift: {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--historical-build-only", action="store_true")
    args = parser.parse_args()
    if args.build:
        build()
    if not MANIFEST.exists():
        raise RuntimeError("candidate manifest missing; use --build")
    data = json.loads(MANIFEST.read_text())
    if args.historical_build_only:
        validate_data(data, live=False)
        print(data["verdict"])
    else:
        validate_current_relation(data)
        print("PASS_FROZEN_SMOOTHER_V3_BUILD_AND_CURRENT_BATCH4_INSTALLED_RELATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
