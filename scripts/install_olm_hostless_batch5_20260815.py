#!/usr/bin/env python3
"""Five-plugin transactional installer. No arguments is a read-only preflight.

The transaction is deliberately disabled until every candidate below is frozen.
Do not weaken ``ready`` or replace a candidate without regenerating the readiness
authority and its pinned SHA256.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import plistlib
import re
import shutil
import stat
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoffs/olm_hostless_batch5_install_20260815"
READINESS = ROOT / "refs/conformance/olm_hostless_batch5_install_readiness_20260815.json"
# Filled only after the five-candidate readiness report is frozen.
READINESS_SHA256 = "17c0cabc862e5b31e52fc4e413a34e2aeb2572b82d7bec729d5af2dc4dc51a44"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
EXPECTED_PRE_IDENTITY = "94c6a1eff87e11705a65be638953cb134ff64bd0d919e8501338601aab333650"
MEDIA_CORE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
POST_IDENTITY = HANDOFF / "olm_installed_identity_manifest_after.json"
PREPARED = HANDOFF / "prepared_transaction.json"
TRANSACTION = HANDOFF / "install_transaction.json"
ROLLBACK = HANDOFF / "rollback_transaction.json"


PLUGINS = {
    "OLMKiraKira": {
        "candidate": ROOT / "handoffs/olmkirakira_mode3_32x18_candidate_20260815/Product/OLMKiraKira.plugin",
        "identity": ROOT / "handoffs/olmkirakira_mode3_32x18_candidate_20260815/build_identity.json",
        "identity_sha256": "637a396a6a1cb5746ff747e16d30f81b5d32e5948a38eb072c6ccceb18727ff9",
        "source": ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp",
        "source_sha256": "abf826dd450bcf879585ae786222ba5d5212d11dd9b292c6ba23d379014baeab",
        "project": ROOT / "mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj/project.pbxproj",
        "project_sha256": "81b2d4246a5dac6f0d8579cb545a7fd9ab201ee63d42a07ccfe544404aff4e4f",
        "old": "edd6953ff0a86efa550ffd8a5be050cb200342ad68427519c092bcac578596a7",
        "new": "d4c9b587d41797259de8627e2d3d5bcf7a376f12fa3c8b99dcd820e0b6d80ae3",
        "exports": {"_EffectMain", "_PluginDataEntryFunction2"},
        "ready": True,
    },
    "OLMColorKey": {
        "candidate": ROOT / "handoffs/olmcolorkey_second_source_universal_candidate_20260815/product/OLMColorKey.plugin",
        "identity": ROOT / "handoffs/olmcolorkey_second_source_universal_candidate_20260815/build_identity.json",
        "identity_sha256": "aadc2c45c65303077b8251f1d4805824c21263e2aaf5f14f6e7c58e4876c3675",
        "source": ROOT / "mac/OLMColorKey/OLMColorKey.cpp",
        "source_sha256": "4dbd264501a0d5d990a3726d16223c01c1996677b925f8546157b6a91ce677d1",
        "project": ROOT / "mac/OLMColorKey/Mac/OLMColorKey.xcodeproj/project.pbxproj",
        "project_sha256": "b5b77f24dec0a1ec9d426c20d68384f03d3381145f1494fec59c491bcec2d72b",
        "old": "701ae9192e19d3e97dd33450e37ae97d90d9be5803ab663405507ed5e3659ca7",
        "new": "51f551a32bd975b7ae1c2437809ecb81af1d06f9e967a8fccbd9dc2a6190ce4d",
        "exports": {"_EffectMain", "_PluginDataEntryFunction2"},
        "ready": True,
    },
    "OLMToonDilate": {
        "candidate": ROOT / "handoffs/olmtoondilate_universal_candidate_macos11_42b47acb_20260815T000245JST/product/OLMToonDilate.plugin",
        "identity": ROOT / "handoffs/olmtoondilate_universal_candidate_macos11_42b47acb_20260815T000245JST/build_identity.json",
        "identity_sha256": "53b682739c4f8ba0e206b3a8b98024a808618a09103f30a4421c73a9ab0b9add",
        "source": ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp",
        "source_sha256": "42b47acbc3cd37bcaefdedc1b46f0507ed2e478c5eaab921f645f9055a9c8470",
        "project": ROOT / "mac/OLMToonDilate/Mac/OLMToonDilate.xcodeproj/project.pbxproj",
        "project_sha256": "eba3266a1dba3f50b217463c5bb077e9976b22febe70bfb7c5d05c6bdaca8abc",
        "old": "5bbe693106072ceff14a1c1ae5a0d64815cddde58356c57575d29e516479036e",
        "new": "cf029885921b6f7cd9ff5ce26ac6c60aa51392cf0bd31d0a721e2a0f6239d029",
        "exports": {"_EffectMain", "_PluginDataEntryFunction2"},
        "ready": True,
    },
    "OLMDirectionalBlur": {
        "candidate": ROOT / "handoffs/olmdirectionalblur_native_ucrt_admission_candidate_20260815/OLMDirectionalBlur.plugin",
        "identity": ROOT / "refs/conformance/olmdirectionalblur_native_ucrt_admission_universal_candidate_20260815.json",
        "identity_sha256": "3c917afb3c5ab9d66e8a8b718fc4662627fef7f7ea6ea9d8a4779e07e647c4ce",
        "source": ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
        "source_sha256": "b39732e285688f1f8ae2fc5f64efcfba3d7ac52a1451a2685dd7b606bb18fb12",
        "project": ROOT / "mac/OLMDirectionalBlur/Mac/OLMDirectionalBlur.xcodeproj/project.pbxproj",
        "project_sha256": "dda5520209f069d0336c3873726a87ff97a8f8f0114d97e21c96289199d83127",
        "old": "856ab700df0881cfb039e9c9d0675bf46a7e92b56e8cb0e311d820fd719bc0de",
        "new": "c64f8ff701008ae0390eb9da1a9e073dcde97a77e9b32701becf6eaa241a2666",
        "exports": {"_EffectMain", "_PluginDataEntryFunction2"},
        "ready": True,
    },
    "OLMDistanceGradation": {
        "candidate": ROOT / "handoffs/olmdistancegradation_pf32_power_native_ucrt_universal_candidate_macos11_20260815/Product/OLMDistanceGradation.plugin",
        "identity": ROOT / "refs/conformance/olmdistancegradation_pf32_power_native_ucrt_universal_candidate_macos11_20260815.json",
        "identity_sha256": "106c2de7989d7b2a27f0acb579b9565377b2a782891b65f86960ac2afa5f4282",
        "source": ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp",
        "source_sha256": "e2f5020f995b59277ee288f48e74a851fc1c9f6a456678cf0361d00e073dd9a9",
        "project": ROOT / "mac/OLMDistanceGradation/Mac/OLMDistanceGradation.xcodeproj/project.pbxproj",
        "project_sha256": "47a276d3f63a6275178eea858a85d8ca0392b994ee025df9d678f2dbdb8e210b",
        "old": "231421e4a0c1607a70947778d99d748baefe07078b7e1145f4a4700268116605",
        "new": "9a97a076c118fd1015f40d922bf7f21be7a041f1f049a0e465cc0bc9cd1cd349",
        "exports": {"_EffectMain"},
        "ready": True,
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True)


def ae_pids() -> list[int]:
    patterns = (
        r"^/Applications/Adobe After Effects .*\.app/Contents/MacOS/After Effects( |$)",
        r"^/Applications/Adobe After Effects [^/]+/aerender( |$)",
    )
    found: set[int] = set()
    for pattern in patterns:
        result = run("pgrep", "-f", pattern)
        if result.returncode not in (0, 1): raise RuntimeError("cannot observe After Effects/aerender")
        found.update(int(x) for x in result.stdout.split() if x.isdigit())
    return sorted(found)


def executable(bundle: Path, name: str) -> Path:
    return bundle / "Contents/MacOS" / name


def inventory(bundle: Path) -> list[dict[str, object]]:
    if not bundle.is_dir():
        raise RuntimeError(f"bundle missing: {bundle}")
    rows = []
    for p in sorted([bundle, *bundle.rglob("*")], key=lambda x: x.relative_to(bundle).as_posix()):
        s = p.lstat()
        row: dict[str, object] = {"path": "." if p == bundle else p.relative_to(bundle).as_posix(), "mode": stat.S_IMODE(s.st_mode)}
        if p.is_symlink(): row.update(type="symlink", target=os.readlink(p))
        elif p.is_dir(): row["type"] = "directory"
        elif p.is_file(): row.update(type="file", bytes=s.st_size, sha256=sha256(p))
        else: raise RuntimeError(f"unsupported bundle node: {p}")
        rows.append(row)
    return rows


def verify_bundle(name: str, bundle: Path, expected: str, *, macos11: bool) -> dict[str, object]:
    binary = executable(bundle, name)
    if sha256(binary) != expected: raise RuntimeError(f"binary mismatch: {name}")
    lipo = run("lipo", "-archs", str(binary))
    archs = lipo.stdout.split()
    if lipo.returncode or set(archs) != {"arm64", "x86_64"}: raise RuntimeError(f"arch mismatch: {name}")
    sign = run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(bundle))
    if sign.returncode: raise RuntimeError(f"codesign mismatch: {name}")
    display = run("codesign", "-dv", "--verbose=4", str(bundle))
    detail = display.stdout + display.stderr
    if display.returncode or "Signature=adhoc" not in detail or "TeamIdentifier=not set" not in detail:
        raise RuntimeError(f"not exact ad-hoc identity: {name}")
    plist_min = plistlib.loads((bundle / "Contents/Info.plist").read_bytes()).get("LSMinimumSystemVersion")
    mins = {}
    for arch in archs:
        out = run("otool", "-arch", arch, "-l", str(binary))
        values = re.findall(r"^\s+minos\s+(\S+)\s*$", out.stdout, re.M)
        if out.returncode or len(values) != 1: raise RuntimeError(f"minOS unavailable: {name}/{arch}")
        mins[arch] = values[0]
        nm = run("nm", "-gU", "-arch", arch, str(binary))
        entry_exports = {"_EffectMain", "_PluginDataEntryFunction2"}.intersection(nm.stdout.split())
        if nm.returncode or entry_exports != PLUGINS[name]["exports"]:
            raise RuntimeError(f"exports missing: {name}/{arch}")
    if macos11 and (plist_min != "11.0" or set(mins.values()) != {"11.0"}):
        raise RuntimeError(f"candidate is not minOS11: {name}")
    return {"binary_sha256": expected, "architectures": archs, "plist_minimum": plist_min,
            "slice_minos": mins, "strict_deep_adhoc": True, "inventory": inventory(bundle)}


def paths(name: str) -> dict[str, Path]:
    return {"installed": MEDIA_CORE / f"{name}.plugin",
            "backup": HANDOFF / "installed_backup" / f"{name}.plugin",
            "pre_swap": HANDOFF / "pre_swap_original" / f"{name}.plugin",
            "moved_old": HANDOFF / "moved_old" / f"{name}.plugin",
            "failed_new": HANDOFF / "failed_new" / f"{name}.plugin",
            "stage": MEDIA_CORE / f".{name}.batch5-stage-20260815"}


def artifact_state() -> str:
    extras = [p for n in PLUGINS for k, p in paths(n).items() if k != "installed" and p.exists()]
    extras += [p for p in (PRE_IDENTITY, POST_IDENTITY, PREPARED, TRANSACTION, ROLLBACK) if p.exists()]
    if not extras: return "clean"
    prepared = PREPARED.exists() and PRE_IDENTITY.exists() and all(paths(n)[k].exists() for n in PLUGINS for k in ("backup", "pre_swap"))
    if prepared and not TRANSACTION.exists() and not POST_IDENTITY.exists() and all(not paths(n)[k].exists() for n in PLUGINS for k in ("moved_old", "failed_new", "stage")): return "prepared"
    if TRANSACTION.exists() and POST_IDENTITY.exists() and all(paths(n)["moved_old"].exists() for n in PLUGINS): return "installed"
    if ROLLBACK.exists() and TRANSACTION.exists() and all(paths(n)["failed_new"].exists() for n in PLUGINS): return "rolled_back"
    return "partial"


def readiness() -> dict[str, object]:
    blockers = {n: s.get("blocker", "candidate not frozen") for n, s in PLUGINS.items() if not s["ready"]}
    if blockers: raise RuntimeError(f"batch5 fail-closed: {blockers}")
    if sha256(READINESS) != READINESS_SHA256: raise RuntimeError("readiness authority drift")
    data = json.loads(READINESS.read_text())
    if data["status"] != "PASS_HOSTLESS_BATCH5_CANDIDATES_READY_FOR_TRANSACTIONAL_PREP_NOT_INSTALLED":
        raise RuntimeError("readiness authority is not green")
    if set(data["plugins"]) != set(PLUGINS): raise RuntimeError("readiness exact plugin keyset drift")
    return data


def collect_preflight() -> dict[str, object]:
    bound = readiness()
    if sha256(IDENTITY) != EXPECTED_PRE_IDENTITY: raise RuntimeError("accepted pre-identity drift")
    if ae_pids(): raise RuntimeError("After Effects is running")
    rows = {r["plugin"]: r for r in json.loads(IDENTITY.read_text())["plugins"]}
    if set(rows).intersection(PLUGINS) != set(PLUGINS): raise RuntimeError("accepted identity target keyset drift")
    result = {}
    for name, s in PLUGINS.items():
        for key in ("identity", "source", "project"):
            if sha256(s[key]) != s[f"{key}_sha256"]: raise RuntimeError(f"{key} drift: {name}")
        if rows[name]["sha256"] != s["old"]: raise RuntimeError(f"identity old row drift: {name}")
        matches = [p.resolve() for p in MEDIA_CORE.rglob(f"{name}.plugin")]
        if matches != [paths(name)["installed"].resolve()]: raise RuntimeError(f"recursive MediaCore bundle count/path drift: {name}")
        candidate = verify_bundle(name, s["candidate"], s["new"], macos11=True)
        installed = verify_bundle(name, paths(name)["installed"], s["old"], macos11=False)
        expected = bound["plugins"][name]
        if candidate["inventory"] != expected["candidate_inventory"] or installed["inventory"] != expected["installed_inventory"]:
            raise RuntimeError(f"readiness inventory drift: {name}")
        result[name] = {"candidate": candidate, "installed_before": installed}
    return {"schema": "olm.hostless-batch5-20260815-preflight/1", "readiness_sha256": READINESS_SHA256,
            "accepted_identity_sha256": EXPECTED_PRE_IDENTITY, "after_effects_processes": [], "plugins": result}


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    tmp = Path(raw)
    try:
        with os.fdopen(fd, "wb") as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True); raise


def atomic_json(path: Path, value: object) -> None:
    atomic_write(path, (json.dumps(value, indent=2) + "\n").encode())


def copy_bundle(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ditto", str(source), str(destination)], check=True)


def atomic_exchange(left: Path, right: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True); fn = libc.renameatx_np
    fn.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]; fn.restype = ctypes.c_int
    if fn(-2, os.fsencode(left), -2, os.fsencode(right), 0x2):
        error = ctypes.get_errno(); raise OSError(error, os.strerror(error), f"{left} <-> {right}")


def cleanup_prepare() -> None:
    for n in PLUGINS:
        for k in ("backup", "pre_swap", "stage"):
            p = paths(n)[k]
            if p.is_dir(): shutil.rmtree(p)
    for p in (PRE_IDENTITY, PREPARED): p.unlink(missing_ok=True)


def prepare(preflight: dict[str, object]) -> dict[str, object]:
    if artifact_state() != "clean": raise RuntimeError("transaction artifacts not clean")
    live = {n: inventory(paths(n)["installed"]) for n in PLUGINS}
    identity_bytes = IDENTITY.read_bytes()
    try:
        atomic_write(PRE_IDENTITY, identity_bytes)
        for n, s in PLUGINS.items():
            for k in ("backup", "pre_swap"):
                copy_bundle(paths(n)["installed"], paths(n)[k])
                if verify_bundle(n, paths(n)[k], s["old"], macos11=False)["inventory"] != live[n]:
                    raise RuntimeError(f"backup drift: {n}/{k}")
        receipt = {"schema": "olm.hostless-batch5-20260815-prepared/1", "status": "prepared_no_mediacore_or_identity_mutation",
                   "preflight": preflight, "pre_identity_sha256": sha256(PRE_IDENTITY), "candidate_count": 5,
                   "backup_copies_per_plugin": 2}
        atomic_json(PREPARED, receipt)
        if IDENTITY.read_bytes() != identity_bytes or any(inventory(paths(n)["installed"]) != live[n] for n in PLUGINS):
            raise RuntimeError("prepare mutated authoritative state")
        return receipt
    except BaseException:
        cleanup_prepare(); raise


def validate_prepared(preflight: dict[str, object]) -> None:
    if artifact_state() != "prepared" or sha256(PRE_IDENTITY) != EXPECTED_PRE_IDENTITY: raise RuntimeError("prepared state incomplete")
    if json.loads(PREPARED.read_text())["preflight"] != preflight: raise RuntimeError("prepared preflight drift")
    for n, s in PLUGINS.items():
        live = verify_bundle(n, paths(n)["installed"], s["old"], macos11=False)["inventory"]
        for k in ("backup", "pre_swap"):
            if verify_bundle(n, paths(n)[k], s["old"], macos11=False)["inventory"] != live: raise RuntimeError(f"old-copy drift: {n}/{k}")


def accepted_after() -> dict[str, object]:
    before = json.loads(PRE_IDENTITY.read_text()); after = json.loads(json.dumps(before))
    rows = {r["plugin"]: r for r in after["plugins"]}
    for n, s in PLUGINS.items():
        if rows[n]["sha256"] != s["old"]: raise RuntimeError(f"old identity row drift: {n}")
        rows[n]["sha256"] = s["new"]
        rows[n]["source_bundle"] = str(s["candidate"].relative_to(ROOT))
        # Identity-manifest semantics: source_bundle is the accepted candidate and
        # source_sha256 is that bundle's executable, while production-source SHA
        # remains separately pinned by the readiness authority.
        rows[n]["source_sha256"] = s["new"]
    now = datetime.now(timezone.utc).isoformat(); after["accepted_at"] = now; after["installed_after"] = now
    # Semantic mutation allowlist: exactly three fields in the five rows plus two top timestamps.
    allowed = {("accepted_at",), ("installed_after",)} | {(n, k) for n in PLUGINS for k in ("sha256", "source_bundle", "source_sha256")}
    changed = set()
    old_rows = {r["plugin"]: r for r in before["plugins"]}
    for key in before:
        if key == "plugins": continue
        if before[key] != after[key]: changed.add((key,))
    for n in old_rows:
        for key in old_rows[n]:
            if old_rows[n][key] != rows[n][key]: changed.add((n, key))
    if changed != allowed: raise RuntimeError(f"identity mutation outside exact allowlist: {changed ^ allowed}")
    return after


def restore(identity_bytes: bytes, swapped: list[str], moved: list[str]) -> None:
    for n in reversed(list(PLUGINS)):
        p = paths(n)
        if n in moved and p["moved_old"].exists():
            p["failed_new"].parent.mkdir(parents=True, exist_ok=True)
            if p["failed_new"].exists(): shutil.rmtree(p["failed_new"])
            atomic_exchange(p["installed"], p["moved_old"])
            os.replace(p["moved_old"], p["failed_new"])
        elif n in swapped and p["stage"].exists() and p["installed"].exists(): atomic_exchange(p["installed"], p["stage"])
        if p["stage"].exists(): shutil.rmtree(p["stage"])
    atomic_write(IDENTITY, identity_bytes); POST_IDENTITY.unlink(missing_ok=True)


def install(preflight: dict[str, object]) -> dict[str, object]:
    validate_prepared(preflight); identity_bytes = PRE_IDENTITY.read_bytes(); swapped = []; moved = []
    try:
        for n, s in PLUGINS.items():
            p = paths(n)
            if p["stage"].exists(): raise RuntimeError(f"stage exists: {n}")
            copy_bundle(s["candidate"], p["stage"])
            if os.stat(p["stage"].parent).st_dev != os.stat(p["installed"].parent).st_dev: raise RuntimeError(f"cross-volume stage: {n}")
            if verify_bundle(n, p["stage"], s["new"], macos11=True)["inventory"] != preflight["plugins"][n]["candidate"]["inventory"]: raise RuntimeError(f"stage drift: {n}")
        if ae_pids(): raise RuntimeError("After Effects appeared before swap")
        for n, s in PLUGINS.items():
            p = paths(n); atomic_exchange(p["installed"], p["stage"]); swapped.append(n)
            new = verify_bundle(n, p["installed"], s["new"], macos11=True)["inventory"]
            old = verify_bundle(n, p["stage"], s["old"], macos11=False)["inventory"]
            if new != preflight["plugins"][n]["candidate"]["inventory"] or old != preflight["plugins"][n]["installed_before"]["inventory"]: raise RuntimeError(f"post-swap drift: {n}")
            p["moved_old"].parent.mkdir(parents=True, exist_ok=True); os.replace(p["stage"], p["moved_old"]); moved.append(n)
        atomic_json(IDENTITY, accepted_after()); shutil.copy2(IDENTITY, POST_IDENTITY)
        if ae_pids(): raise RuntimeError("After Effects appeared before commit")
        receipt = {"schema": "olm.hostless-batch5-20260815-install/1", "status": "installed_pending_batched_ae_smoke",
                   "plugins": {n: {"old": s["old"], "new": s["new"]} for n, s in PLUGINS.items()},
                   "pre_identity_sha256": EXPECTED_PRE_IDENTITY, "post_identity_sha256": sha256(IDENTITY),
                   "same_volume_renameatx_np_swap": True, "after_effects_processes": []}
        atomic_json(TRANSACTION, receipt); return receipt
    except BaseException:
        restore(identity_bytes, swapped, moved); raise


def rollback_installed() -> dict[str, object]:
    if artifact_state() != "installed": raise RuntimeError("rollback requires exact installed state")
    if ae_pids(): raise RuntimeError("After Effects or aerender is running")
    receipt = json.loads(TRANSACTION.read_text())
    if sha256(IDENTITY) != receipt["post_identity_sha256"]: raise RuntimeError("post identity drift")
    for n, s in PLUGINS.items():
        verify_bundle(n, paths(n)["installed"], s["new"], macos11=True)
        verify_bundle(n, paths(n)["moved_old"], s["old"], macos11=False)
    processed: list[str] = []; post_identity = IDENTITY.read_bytes()
    try:
        for n in reversed(list(PLUGINS)):
            p = paths(n); p["failed_new"].parent.mkdir(parents=True, exist_ok=True)
            if p["failed_new"].exists(): raise RuntimeError(f"failed-new quarantine exists: {n}")
            # Both names continuously exist: old becomes installed, new becomes moved_old.
            atomic_exchange(p["installed"], p["moved_old"])
            processed.append(n)
            verify_bundle(n, p["installed"], PLUGINS[n]["old"], macos11=False)
            verify_bundle(n, p["moved_old"], PLUGINS[n]["new"], macos11=True)
            os.replace(p["moved_old"], p["failed_new"])
        atomic_write(IDENTITY, PRE_IDENTITY.read_bytes())
        if sha256(IDENTITY) != EXPECTED_PRE_IDENTITY: raise RuntimeError("rollback identity restore failed")
        POST_IDENTITY.unlink(missing_ok=True)
        result = {"schema": "olm.hostless-batch5-20260815-rollback/1", "status": "rolled_back_exact_five",
                  "restored_identity_sha256": EXPECTED_PRE_IDENTITY, "after_effects_processes": [],
                  "same_volume_renameatx_np_swap": True}
        atomic_json(ROLLBACK, result); return result
    except BaseException:
        # Reverse-compensate every completed rollback swap back to installed-new/moved-old.
        for n in reversed(processed):
            p = paths(n)
            if p["failed_new"].exists(): os.replace(p["failed_new"], p["moved_old"])
            atomic_exchange(p["installed"], p["moved_old"])
        atomic_write(IDENTITY, post_identity)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(); group = parser.add_mutually_exclusive_group()
    group.add_argument("--prepare", action="store_true"); group.add_argument("--install", action="store_true"); group.add_argument("--rollback", action="store_true")
    args = parser.parse_args(); state = artifact_state()
    if args.rollback:
        print(json.dumps(rollback_installed())); return 0
    if state == "rolled_back":
        if args.prepare or args.install: raise RuntimeError("rolled-back transaction is sealed")
        if sha256(IDENTITY) != EXPECTED_PRE_IDENTITY or ae_pids(): raise RuntimeError("rolled-back state drift")
        for n, s in PLUGINS.items(): verify_bundle(n, paths(n)["installed"], s["old"], macos11=False); verify_bundle(n, paths(n)["failed_new"], s["new"], macos11=True)
        print(json.dumps({"status": "rolled_back_exact_five_no_mutation", "candidate_count": 5})); return 0
    if state == "installed":
        if args.prepare or args.install: raise RuntimeError("transaction already installed")
        receipt = json.loads(TRANSACTION.read_text())
        if sha256(IDENTITY) != receipt["post_identity_sha256"] or ae_pids(): raise RuntimeError("installed-state drift")
        for n, s in PLUGINS.items(): verify_bundle(n, paths(n)["installed"], s["new"], macos11=True); verify_bundle(n, paths(n)["moved_old"], s["old"], macos11=False)
        print(json.dumps({"status": "installed_pending_batched_ae_smoke_no_mutation", "candidate_count": 5})); return 0
    preflight = collect_preflight()
    if args.prepare:
        if state != "clean": raise RuntimeError(f"cannot prepare from {state}")
        print(json.dumps(prepare(preflight))); return 0
    if args.install:
        if state != "prepared": raise RuntimeError(f"cannot install from {state}")
        print(json.dumps(install(preflight))); return 0
    if state not in {"clean", "prepared"}: raise RuntimeError(f"unsafe artifact state: {state}")
    if state == "prepared": validate_prepared(preflight)
    print(json.dumps({"status": "dry_run_ready_no_mutation", "transaction_artifact_state": state, "candidate_count": 5})); return 0


if __name__ == "__main__": raise SystemExit(main())
