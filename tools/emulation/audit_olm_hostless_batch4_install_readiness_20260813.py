#!/usr/bin/env python3
"""Bind four reviewed candidates to the live pre-install state without installing."""

from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import re
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olm_hostless_batch4_install_readiness_20260813.json"
DOC = REPORT.with_suffix(".md")
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
MEDIA_CORE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"
IDENTITY_SHA256 = "ef7bf31f4f8907af8d047276296b16c4d918433a94173938ca98b2874c61c368"

SPECS = {
    "OLMBlur": {
        "bundle": ROOT / "handoffs/olmblur_smart_public_admission_macos11_project_20260813/product/Debug/OLMBlur.plugin",
        "source": ROOT / "mac/OLMBlur/OLMBlur.cpp",
        "source_sha256": "ec0e502eb88c45770e8582f179035a4c1da72bb7e26d3ca3a00a30b835320489",
        "project": ROOT / "mac/OLMBlur/Mac/OLMBlur.xcodeproj/project.pbxproj",
        "project_sha256": "23780615103b6b9ccaa3dfd732810bbcf6223b2b8ab56889afce59a04b57eff3",
        "closure": ROOT / "refs/conformance/olmblur_smart_public_admission_20260813.json",
        "closure_sha256": "9e1c3f2f0175198910622d6481a219acb71094d6b2616b42a77e31c614825f34",
        "authority": ROOT / "handoffs/olmblur_smart_public_admission_macos11_project_20260813/build_identity.json",
        "authority_sha256": "1d4ab147557ca06889bb1a02ec76b536bea29b40d1fba8e84e19710d9c027510",
        "binary_sha256": "5893faeaf19d55bb4db6f42eb4c21915c94ad8fe2b945e2002c890d79131c48b",
        "exports": ["_EffectMain", "_PluginDataEntryFunction2"],
    },
    "OLMSmoother": {
        "bundle": ROOT / "handoffs/olmsmoother_source_bound_atomic_universal_candidate_v3_20260813/candidates/OLMSmoother.plugin",
        "source": ROOT / "mac/OLMSmoother/Mac/OLMSmoother_port.cpp",
        "source_sha256": "c8c7b7728553ee4ccaadc7ef802be40e607d7e7a7b829958d4b8dfab80f633dc",
        "project": ROOT / "mac/OLMSmoother/Mac/OLMSmoother.xcodeproj/project.pbxproj",
        "project_sha256": "b4ea2f5f000d68cc5b34fc4d27f61ddf234f23c3a85f27033a613659bc6df8c9",
        "closure": ROOT / "refs/conformance/olmsmoother_public_admission_guard_closure_20260812.json",
        "closure_sha256": "de573b5206c26bd8469e90d5bc34d4797168cbc3521b55897a6db36e42002432",
        "authority": ROOT / "handoffs/olmsmoother_source_bound_atomic_universal_candidate_v3_20260813/build_identity.json",
        "authority_sha256": "5bc7432144a90801319452b1a23e39e131a75a266c270839640eff68a4bd40bd",
        "binary_sha256": "f416579eeb61b73da683437d382f786781e6ecdf27d9c4fc52f3ad1d55577162",
        "exports": ["_EffectMain"],
    },
    "OLMSmoother2": {
        "bundle": ROOT / "handoffs/olmsmoother_source_bound_atomic_universal_candidate_v3_20260813/candidates/OLMSmoother2.plugin",
        "source": ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp",
        "source_sha256": "2f08c720b738d9bb847e9a010afe959a59805249e4c92466c98ff85900782e16",
        "project": ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2.xcodeproj/project.pbxproj",
        "project_sha256": "8a5525814eb7917b4ee124c507caf6a085200decf6072b32d52779e38279b89a",
        "closure": ROOT / "refs/conformance/olmsmoother_public_admission_guard_closure_20260812.json",
        "closure_sha256": "de573b5206c26bd8469e90d5bc34d4797168cbc3521b55897a6db36e42002432",
        "authority": ROOT / "handoffs/olmsmoother_source_bound_atomic_universal_candidate_v3_20260813/build_identity.json",
        "authority_sha256": "5bc7432144a90801319452b1a23e39e131a75a266c270839640eff68a4bd40bd",
        "binary_sha256": "55d138e2a25704ffa59d8bd08d20e2160525f8f8011b8e11c733ae23fddd795e",
        "exports": ["_EffectMain"],
    },
    "OLMColorKey": {
        "bundle": ROOT / "handoffs/olmcolorkey_public_source_bound_universal_candidate_20260813T234500JST/product/Debug/OLMColorKey.plugin",
        "source": ROOT / "mac/OLMColorKey/OLMColorKey.cpp",
        "source_sha256": "8d3083cc2042af230c35f657b1db1c06e4c375ddd2e806198ece42a1c91466cb",
        "project": ROOT / "mac/OLMColorKey/Mac/OLMColorKey.xcodeproj/project.pbxproj",
        "project_sha256": "b5b77f24dec0a1ec9d426c20d68384f03d3381145f1494fec59c491bcec2d72b",
        "closure": ROOT / "refs/conformance/olmcolorkey_public_source_bound_closure_20260813.json",
        "closure_sha256": "dbecbb78a6f0ed7096cbc13e7ebc2a4775aa2edf22640ef57cbd00f6d4326196",
        "authority": ROOT / "handoffs/olmcolorkey_public_source_bound_universal_candidate_20260813T234500JST/build_identity.json",
        "authority_sha256": "2f5e4272ef8eff8795f26cebe7c2f5d510397f4e76a9920492ff8ab3926d0350",
        "binary_sha256": "030e87c5b88c7312e35ecf5998446fb605a522b8a062f1ab798348b3dbf722c4",
        "exports": ["_EffectMain", "_PluginDataEntryFunction2"],
    },
}

EXPECTED_INSTALLED = {
    "OLMBlur": "21b629849011847784aba3b5311f42706504aded3b2c70e0dd3a241427e9ecf6",
    "OLMSmoother": "1d24d89fe1511d3cc69ca46498dc9e76ed7a088a163cd5f79d3e87f70a34de5e",
    "OLMSmoother2": "b8e399a215ffb43d6332593391995daf12bd2e2770ab8757c3ca822993ced69c",
    "OLMColorKey": "2e7a090b73cb08af50003768ca2a72784368104f3aad215ad2531e14bd491258",
}

SMOOTHER_ALLOWED_DRIFT = {
    "refs/conformance/olmsmoother_public_admission_guard_closure_20260812.json": (
        "42f5a4559edd89e98ae69de01a8a50a9084a1d2eaff111e0a8ea9e06d9ca2adb",
        "de573b5206c26bd8469e90d5bc34d4797168cbc3521b55897a6db36e42002432",
    ),
    "scripts/run_olm_mac_fixed_fixture_regression_20260805.py": (
        "ec16a027723d3d56fcce3b146bacba33bdcd2f2a5ed60fc1cd5fa2e1b267b7d3",
        "a926f4afd82a612072b76887503abe9fbb3c49ccdef28ca6898bf253fd39393b",
    ),
}

DOC_TEXT = """# Four-plugin hostless install checkpoint

Verdict: `PASS_HOSTLESS_BATCH4_CANDIDATES_READY_FOR_TRANSACTIONAL_PREP_NOT_INSTALLED`.

OLMBlur, OLMSmoother, OLMSmoother2, and OLMColorKey have live source/closure-bound Universal macOS 11 ad-hoc candidates. Their complete bundle inventories, slice build versions, exports, signatures, and still-distinct installed binaries are checked read-only. The accepted installed identity remains unchanged and After Effects is not running.

The Smoother v3 build manifest remains exact for its source, project, logs, and bundles. Two post-build inputs changed intentionally: the Smoother closure was regenerated after a retained evidence row changed, and the all-plugin runner was updated for the new Blur and ColorKey authorities. These two exact drifts are recorded rather than misrepresented as build-time stability.

This checkpoint does not install, prepare backups, update the accepted identity, launch After Effects, claim Developer ID/notarization, or replace the required post-install smoke and formal release gate. The next allowed action is transactional preparation after its installer simulation is green.
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def run(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)


def inventory(bundle: Path) -> list[dict[str, object]]:
    rows = []
    for path in sorted((p for p in bundle.rglob("*") if p.is_file()), key=lambda p: p.relative_to(bundle).as_posix()):
        info = path.stat()
        rows.append({"path": path.relative_to(bundle).as_posix(), "bytes": info.st_size,
                     "mode": format(stat.S_IMODE(info.st_mode), "04o"), "sha256": sha256(path)})
    return rows


def build_version(binary: Path, arch: str) -> dict[str, str]:
    result = run("otool", "-arch", arch, "-l", str(binary))
    if result.returncode:
        raise RuntimeError(result.stderr)
    match = re.search(r"cmd LC_BUILD_VERSION\s+cmdsize \d+\s+platform 1\s+minos ([0-9.]+)\s+sdk ([0-9.]+)", result.stdout)
    if not match:
        raise RuntimeError(f"missing build version: {binary}/{arch}")
    return {"minos": match.group(1), "sdk": match.group(2)}


def exported(binary: Path, arch: str) -> list[str]:
    result = run("nm", "-gjU", "-arch", arch, str(binary))
    if result.returncode:
        raise RuntimeError(result.stderr)
    return sorted(line for line in result.stdout.splitlines() if line in {"_EffectMain", "_PluginDataEntryFunction2"})


def verify_bundle(name: str, bundle: Path, expected_sha: str, exports: list[str], *, require_macos11: bool) -> dict[str, object]:
    binary = bundle / "Contents/MacOS" / name
    if sha256(binary) != expected_sha:
        raise RuntimeError(f"binary drift: {name}")
    archs_result = run("lipo", "-archs", str(binary))
    archs = archs_result.stdout.split()
    if archs_result.returncode or set(archs) != {"arm64", "x86_64"}:
        raise RuntimeError(f"architecture drift: {name}")
    signature = run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(bundle))
    if signature.returncode:
        raise RuntimeError(f"signature drift: {name}: {signature.stderr}")
    info_min = plistlib.loads((bundle / "Contents/Info.plist").read_bytes()).get("LSMinimumSystemVersion")
    slices = {arch: {**build_version(binary, arch), "exports": exported(binary, arch)} for arch in sorted(archs)}
    if any(row["exports"] != exports for row in slices.values()):
        raise RuntimeError(f"slice contract drift: {name}")
    if require_macos11 and (info_min != "11.0" or any(row["minos"] != "11.0" for row in slices.values())):
        raise RuntimeError(f"candidate deployment target drift: {name}")
    rows = inventory(bundle)
    return {
        "bundle": display_path(bundle), "binary_sha256": expected_sha,
        "architectures": archs, "info_minimum_system_version": info_min,
        "slices": slices, "strict_deep_adhoc_codesign": True,
        "inventory": rows,
        "inventory_sha256": hashlib.sha256(canonical(rows)).hexdigest(),
    }


def ae_pids() -> list[int]:
    result = run("pgrep", "-f", r"^/Applications/Adobe After Effects .*\.app/Contents/MacOS/After Effects( |$)")
    if result.returncode not in (0, 1):
        raise RuntimeError("cannot observe After Effects")
    return sorted(int(value) for value in result.stdout.split() if value.isdigit())


def smoother_drift() -> dict[str, dict[str, str]]:
    manifest = json.loads((SPECS["OLMSmoother"]["authority"]).read_text())
    found = {}
    for relative, row in manifest["bound_inputs_after"].items():
        current = sha256(ROOT / relative)
        if current != row["sha256"]:
            found[relative] = {"build_time_sha256": row["sha256"], "current_sha256": current}
    expected = {key: {"build_time_sha256": old, "current_sha256": new} for key, (old, new) in SMOOTHER_ALLOWED_DRIFT.items()}
    if found != expected:
        raise RuntimeError(f"unexpected Smoother post-build drift: {found}")
    return found


def generate() -> dict[str, object]:
    if sha256(IDENTITY) != IDENTITY_SHA256:
        raise RuntimeError("accepted identity drift")
    identity = json.loads(IDENTITY.read_text())
    accepted = {row["plugin"]: row for row in identity["plugins"]}
    candidates = {}
    installed = {}
    for name, spec in SPECS.items():
        for key in ("source", "project", "closure", "authority"):
            expected = spec[f"{key}_sha256"]
            if sha256(spec[key]) != expected:
                raise RuntimeError(f"{name} {key} drift")
        candidate = verify_bundle(name, spec["bundle"], spec["binary_sha256"], spec["exports"], require_macos11=True)
        installed_bundle = MEDIA_CORE / f"{name}.plugin"
        installed_row = accepted[name]
        if installed_row["sha256"] != EXPECTED_INSTALLED[name]:
            raise RuntimeError(f"accepted row drift: {name}")
        live_installed = verify_bundle(name, installed_bundle, EXPECTED_INSTALLED[name], spec["exports"], require_macos11=False)
        live_installed["installed_bundle_count"] = len(list(MEDIA_CORE.glob(f"{name}.plugin")))
        if live_installed["installed_bundle_count"] != 1 or candidate["binary_sha256"] == live_installed["binary_sha256"]:
            raise RuntimeError(f"pre-install distinction drift: {name}")
        candidates[name] = {
            "source": {"path": str(spec["source"].relative_to(ROOT)), "sha256": spec["source_sha256"]},
            "project": {"path": str(spec["project"].relative_to(ROOT)), "sha256": spec["project_sha256"]},
            "closure": {"path": str(spec["closure"].relative_to(ROOT)), "sha256": spec["closure_sha256"]},
            "authority": {"path": str(spec["authority"].relative_to(ROOT)), "sha256": spec["authority_sha256"]},
            "bundle": candidate,
        }
        installed[name] = live_installed
    pids = ae_pids()
    if pids:
        raise RuntimeError(f"After Effects is running: {pids}")
    return {
        "schema": "olm.hostless-batch4-install-readiness/1",
        "status": "PASS_HOSTLESS_BATCH4_CANDIDATES_READY_FOR_TRANSACTIONAL_PREP_NOT_INSTALLED",
        "accepted_identity": {"path": str(IDENTITY.relative_to(ROOT)), "sha256": IDENTITY_SHA256},
        "candidates": candidates,
        "installed_before": installed,
        "smoother_v3_post_build_allowed_drift": smoother_drift(),
        "after_effects_processes": pids,
        "scope": {
            "candidate_count": 4, "installed": False, "prepared_backups": False,
            "accepted_identity_updated": False, "after_effects_launched": False,
            "developer_id_or_notarization": False, "post_install_smoke_complete": False,
            "formal_release_gate_complete": False,
            "next_allowed_action": "transactional_prepare_after_installer_simulation_passes",
        },
    }


def validate(data: object) -> None:
    if not isinstance(data, dict) or set(data) != {"schema", "status", "accepted_identity", "candidates", "installed_before", "smoother_v3_post_build_allowed_drift", "after_effects_processes", "scope"}:
        raise ValueError("top-level schema")
    if data != generate():
        raise ValueError("saved readiness differs from live state")
    if set(data["candidates"]) != set(SPECS) or set(data["installed_before"]) != set(SPECS):
        raise ValueError("plugin set")
    if data["scope"] != {
        "candidate_count": 4, "installed": False, "prepared_backups": False,
        "accepted_identity_updated": False, "after_effects_launched": False,
        "developer_id_or_notarization": False, "post_install_smoke_complete": False,
        "formal_release_gate_complete": False,
        "next_allowed_action": "transactional_prepare_after_installer_simulation_passes",
    }:
        raise ValueError("scope")
    if DOC.read_text() != DOC_TEXT:
        raise ValueError("documentation drift")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    generated = generate()
    if args.write:
        REPORT.write_bytes(canonical(generated))
        DOC.write_text(DOC_TEXT)
    if not REPORT.is_file() or not DOC.is_file():
        raise SystemExit("readiness artifacts missing; use --write explicitly")
    before = REPORT.read_bytes()
    validate(json.loads(before))
    if before != canonical(generated) or REPORT.read_bytes() != before:
        raise SystemExit("readiness is not canonical/read-only exact")
    print(generated["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
