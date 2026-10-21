#!/usr/bin/env python3
"""Audit the DirectionalBlur test-seam compatibility incremental install."""
from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
CANDIDATE_ROOT = ROOT / "handoffs/olmdirectionalblur_testseam_compat_candidate_20260814"
CANDIDATE = CANDIDATE_ROOT / "Product/OLMDirectionalBlur.plugin"
CANDIDATE_AUTHORITY = CANDIDATE_ROOT / "build_identity.json"
HANDOFF = ROOT / "handoffs/olmdirectionalblur_testseam_compat_install_20260814"
PREPARED = HANDOFF / "prepared_transaction.json"
TRANSACTION = HANDOFF / "install_transaction.json"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
POST_IDENTITY = HANDOFF / "olm_installed_identity_manifest_after.json"
ACCEPTED_IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDirectionalBlur.plugin"
BACKUPS = {
    "installed_backup": HANDOFF / "installed_backup/OLMDirectionalBlur.plugin",
    "pre_swap_original": HANDOFF / "pre_swap_original/OLMDirectionalBlur.plugin",
    "moved_old": HANDOFF / "moved_old/OLMDirectionalBlur.plugin",
}
REPORT = ROOT / "refs/conformance/olmdirectionalblur_testseam_install_closure_20260814.json"
NOTE = REPORT.with_suffix(".md")

SOURCE_SHA = "494116880d037a0d44a48b0e0ebe0fc5358b4cd8892b90ca8c61ea8a7bb2e845"
NEW_SHA = "856ab700df0881cfb039e9c9d0675bf46a7e92b56e8cb0e311d820fd719bc0de"
OLD_SHA = "6af1f1d6d67cd8087778b3040f913e34836092b283ad9f8f36dce2fe32767434"
PRE_IDENTITY_SHA = "1ae637d09701656113d938273486631d596c2c619f02f57a67a85ad34e8073a7"
POST_IDENTITY_SHA = "94c6a1eff87e11705a65be638953cb134ff64bd0d919e8501338601aab333650"
INSTALL_TIME_AUTHORITY_SHA = "15185edc77645fe47a829a1373abd2c2a9907cc87257bc91e5e01fb00deb8e2a"
CURRENT_AUTHORITY_SHA = "ddc9256d6ca78eec2f521335573589f7c626ae5827927a3399ea64d3a1934eff"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def inventory(bundle: Path) -> dict[str, str]:
    return {
        str(path.relative_to(bundle)): sha256(path)
        for path in sorted(bundle.rglob("*")) if path.is_file()
    }


def executable(bundle: Path) -> Path:
    return bundle / "Contents/MacOS/OLMDirectionalBlur"


def ae_processes() -> list[str]:
    found: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], text=True, capture_output=True)
        found.extend(f"{name}:{pid}" for pid in run.stdout.split() if pid.isdigit())
    return found


def command(*args: str) -> str:
    run = subprocess.run(args, text=True, capture_output=True)
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)
    return run.stdout + run.stderr


def identity_relation(before: dict, after: dict) -> bool:
    if set(before) != set(after) or len(before.get("plugins", [])) != 10:
        return False
    if any(
        before[key] != after[key]
        for key in before
        if key not in {"plugins", "accepted_at", "installed_after"}
    ):
        return False
    b_rows = {row["plugin"]: row for row in before["plugins"]}
    a_rows = {row["plugin"]: row for row in after["plugins"]}
    if set(b_rows) != set(a_rows):
        return False
    for name in b_rows:
        if name != "OLMDirectionalBlur" and b_rows[name] != a_rows[name]:
            return False
    b = b_rows["OLMDirectionalBlur"]
    a = a_rows["OLMDirectionalBlur"]
    changed = {key for key in set(b) | set(a) if b.get(key) != a.get(key)}
    return changed == {"sha256", "source_bundle", "source_sha256"} and all(
        after.get(key) != before.get(key) for key in ("accepted_at", "installed_after")
    )


def generate() -> dict:
    before = json.loads(PRE_IDENTITY.read_text())
    after = json.loads(POST_IDENTITY.read_text())
    accepted = json.loads(ACCEPTED_IDENTITY.read_text())
    prepared = json.loads(PREPARED.read_text())
    transaction = json.loads(TRANSACTION.read_text())
    candidate_authority = json.loads(CANDIDATE_AUTHORITY.read_text())
    candidate_inventory = inventory(CANDIDATE)
    installed_inventory = inventory(INSTALLED)
    backup_inventory = {name: inventory(path) for name, path in BACKUPS.items()}
    return {
        "schema": "olmdirectionalblur.testseam-install-closure/1",
        "status": "PASS_INSTALLED_AE_DEFERRED",
        "identities": {
            "source_sha256": sha256(SOURCE),
            "candidate_authority_sha256": sha256(CANDIDATE_AUTHORITY),
            "install_time_authority_sha256": prepared["preflight"]["plugin"]["authority_sha256"],
            "prepared_sha256": sha256(PREPARED),
            "transaction_sha256": sha256(TRANSACTION),
            "pre_identity_sha256": sha256(PRE_IDENTITY),
            "post_identity_sha256": sha256(POST_IDENTITY),
            "accepted_identity_sha256": sha256(ACCEPTED_IDENTITY),
        },
        "binary": {
            "new_sha256": sha256(executable(INSTALLED)),
            "old_sha256": OLD_SHA,
            "candidate_installed_inventory_exact": candidate_inventory == installed_inventory,
            "candidate_inventory_sha256": canonical(candidate_inventory),
            "installed_inventory_sha256": canonical(installed_inventory),
            "backup_inventory_sha256": {name: canonical(value) for name, value in backup_inventory.items()},
            "backup_binary_sha256": {name: sha256(executable(path)) for name, path in BACKUPS.items()},
            "architectures": command("lipo", "-archs", str(executable(INSTALLED))).split(),
            "minimum_system_version": plistlib.loads((INSTALLED / "Contents/Info.plist").read_bytes())["LSMinimumSystemVersion"],
            "strict_codesign": True,
        },
        "transaction": {
            "same_volume_atomic_exchange": transaction["same_volume_atomic_exchange"],
            "old": transaction["old"],
            "new": transaction["new"],
            "identity_relation_directional_only": identity_relation(before, after),
            "accepted_equals_post_copy": accepted == after,
            "current_authority_rebind_after_evidence_cascade": INSTALL_TIME_AUTHORITY_SHA != CURRENT_AUTHORITY_SHA,
            "current_authority_binary_unchanged": candidate_authority["binary_sha256"] == transaction["new"],
        },
        "scope": {
            "after_effects_processes": ae_processes(),
            "after_effects_launched": False,
            "native_ae_numerical_claim": False,
            "distribution_signature_or_notarization": False,
            "evidence_rebind_is_not_a_second_install": True,
        },
    }


def validate(value: dict, *, live: bool = True) -> bool:
    if set(value) != {"schema", "status", "identities", "binary", "transaction", "scope"}:
        return False
    if value["schema"] != "olmdirectionalblur.testseam-install-closure/1" or value["status"] != "PASS_INSTALLED_AE_DEFERRED":
        return False
    if set(value["identities"]) != {"source_sha256", "candidate_authority_sha256", "install_time_authority_sha256", "prepared_sha256", "transaction_sha256", "pre_identity_sha256", "post_identity_sha256", "accepted_identity_sha256"}:
        return False
    ids = value["identities"]
    if (ids["source_sha256"], ids["candidate_authority_sha256"], ids["install_time_authority_sha256"], ids["pre_identity_sha256"], ids["post_identity_sha256"], ids["accepted_identity_sha256"]) != (SOURCE_SHA, CURRENT_AUTHORITY_SHA, INSTALL_TIME_AUTHORITY_SHA, PRE_IDENTITY_SHA, POST_IDENTITY_SHA, POST_IDENTITY_SHA):
        return False
    binary = value["binary"]
    if set(binary) != {"new_sha256", "old_sha256", "candidate_installed_inventory_exact", "candidate_inventory_sha256", "installed_inventory_sha256", "backup_inventory_sha256", "backup_binary_sha256", "architectures", "minimum_system_version", "strict_codesign"}:
        return False
    if binary["new_sha256"] != NEW_SHA or binary["old_sha256"] != OLD_SHA or binary["candidate_installed_inventory_exact"] is not True:
        return False
    if binary["candidate_inventory_sha256"] != binary["installed_inventory_sha256"] or set(binary["backup_binary_sha256"].values()) != {OLD_SHA}:
        return False
    if len(set(binary["backup_inventory_sha256"].values())) != 1 or set(binary["architectures"]) != {"arm64", "x86_64"} or binary["minimum_system_version"] != "11.0" or binary["strict_codesign"] is not True:
        return False
    transaction = value["transaction"]
    if transaction != {"same_volume_atomic_exchange": True, "old": OLD_SHA, "new": NEW_SHA, "identity_relation_directional_only": True, "accepted_equals_post_copy": True, "current_authority_rebind_after_evidence_cascade": True, "current_authority_binary_unchanged": True}:
        return False
    if value["scope"] != {"after_effects_processes": [], "after_effects_launched": False, "native_ae_numerical_claim": False, "distribution_signature_or_notarization": False, "evidence_rebind_is_not_a_second_install": True}:
        return False
    if live:
        try:
            command("codesign", "--verify", "--deep", "--strict", str(INSTALLED))
        except RuntimeError:
            return False
        return value == generate()
    return True


def markdown(value: dict) -> str:
    return (
        "# OLMDirectionalBlur test-seam compatibility install closure\n\n"
        f"Status: `{value['status']}`. Installed executable: `{NEW_SHA}`; retained predecessor: `{OLD_SHA}`.\n\n"
        "The candidate and installed full bundle inventories are exact, all three rollback bundles are full-inventory identical, and the accepted all-ten identity changes only DirectionalBlur's three identity fields plus top-level timestamps. The install-time authority hash is retained separately from the later evidence-only candidate-manifest rebind; the candidate executable did not change. AE remains stopped and numerical AE output is not claimed.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    value = generate() if args.write else json.loads(REPORT.read_text())
    if not validate(value):
        raise RuntimeError("Directional test-seam install closure failed")
    if args.write:
        REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        NOTE.write_text(markdown(value))
    elif NOTE.read_text() != markdown(value):
        raise RuntimeError("Directional test-seam install note drift")
    print("PASS_OLMDIRECTIONALBLUR_TESTSEAM_INSTALL_AE_DEFERRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
