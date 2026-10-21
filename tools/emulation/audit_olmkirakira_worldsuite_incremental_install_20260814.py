#!/usr/bin/env python3
"""Audit the installed bounded Kira WorldSuite candidate without launching AE."""

from __future__ import annotations

import argparse, hashlib, json, stat, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoffs/olmkirakira_worldsuite_lifecycle_install_20260814"
CANDIDATE = ROOT / "handoffs/olmkirakira_worldsuite_lifecycle_candidate_20260814/Product/OLMKiraKira.plugin"
LIVE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMKiraKira.plugin"
OLD = [HANDOFF / name / "OLMKiraKira.plugin" for name in ("installed_backup", "pre_swap_original", "moved_old")]
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
TRANSACTION = HANDOFF / "install_transaction.json"
INSTALLER = ROOT / "scripts/install_olmkirakira_worldsuite_lifecycle_20260814.py"
REPORT = ROOT / "refs/conformance/olmkirakira_worldsuite_incremental_install_identity_20260814.json"
MARKDOWN = REPORT.with_suffix(".md")

NEW = "edd6953ff0a86efa550ffd8a5be050cb200342ad68427519c092bcac578596a7"
OLD_SHA = "260c2d5e635b38213adf88e01298510bf7f180b38bdb5e1d2b85a2906fbfbf18"
SOURCE = "f251b19150a0b490d58cf6bece4c40fe9403f9bd36849cfe8c89ffbd14fc96c2"
PINS = {"identity_before": "b186a6448dc68f3d117617962237f0ff56087c99530f7823b1cb97abfdd872a3",
        "identity_after": "a77f3a5d91787984ca4f1bb4bcffddbea5cb35f71ca12ac31953ed8f30b972e1",
        "transaction": "305d503982086fe02a85af2c506904eef1d769ee6b7ee1252d20f011c1c94a29",
        "installer": "99415bc2147fc5233ba9d0f5bec5a3e6f9cc3ecbe39d74906dcf6470b4598a7c"}
STATUS = "PASS_OLMKIRAKIRA_WORLDSUITE_INCREMENTAL_INSTALL_NO_AE"

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def exe(bundle: Path) -> Path: return bundle / "Contents/MacOS/OLMKiraKira"
def inventory(bundle: Path):
    return [{"path": str(p.relative_to(bundle)), "size": p.stat().st_size,
             "mode": stat.S_IMODE(p.stat().st_mode), "sha256": sha(p)}
            for p in sorted(bundle.rglob("*")) if p.is_file()]
def verify(bundle: Path, expected: str):
    if sha(exe(bundle)) != expected: raise RuntimeError("bundle executable drift")
    if set(subprocess.check_output(["lipo", "-archs", str(exe(bundle))], text=True).split()) != {"arm64", "x86_64"}: raise RuntimeError("architecture drift")
    if subprocess.run(["codesign", "--verify", "--deep", "--strict", str(bundle)], capture_output=True).returncode: raise RuntimeError("codesign drift")
    return inventory(bundle)
def ae():
    return [name for name in ("After Effects", "AfterFX", "aerender")
            if subprocess.run(["pgrep", "-x", name], capture_output=True).returncode == 0]

def generate():
    live = {"identity_before": sha(PRE_IDENTITY), "identity_after": sha(IDENTITY),
            "transaction": sha(TRANSACTION), "installer": sha(INSTALLER)}
    if live != PINS: raise RuntimeError(f"authority drift: {live}")
    if ae(): raise RuntimeError("AE must remain stopped")
    new_inv = verify(CANDIDATE, NEW)
    if verify(LIVE, NEW) != new_inv: raise RuntimeError("installed candidate inventory drift")
    old_inv = verify(OLD[0], OLD_SHA)
    if any(verify(path, OLD_SHA) != old_inv for path in OLD[1:]): raise RuntimeError("rollback inventory drift")
    before, after = json.loads(PRE_IDENTITY.read_text()), json.loads(IDENTITY.read_text())
    before_rows = {row["plugin"]: row for row in before["plugins"]}; after_rows = {row["plugin"]: row for row in after["plugins"]}
    if {k:v for k,v in before_rows.items() if k != "OLMKiraKira"} != {k:v for k,v in after_rows.items() if k != "OLMKiraKira"}: raise RuntimeError("non-Kira identity row changed")
    row = after_rows["OLMKiraKira"]
    if row["sha256"] != NEW or row["source_sha256"] != NEW or row["installed_bundle_count"] != 1: raise RuntimeError("Kira identity row drift")
    tx = json.loads(TRANSACTION.read_text())
    if tx["status"] != "installed" or tx["source_sha256"] != SOURCE or tx["old_binary_sha256"] != OLD_SHA or tx["new_binary_sha256"] != NEW: raise RuntimeError("transaction drift")
    return {"schema":"olmkirakira.worldsuite-install-audit/1", "status":STATUS, "authorities":live,
            "source_sha256":SOURCE, "old_binary_sha256":OLD_SHA, "new_binary_sha256":NEW,
            "candidate_installed_inventory_exact":True, "rollback_copy_count":3,
            "non_kira_identity_rows_exact":True, "after_effects_processes":[],
            "scope":{"native_after_effects":False,"transaction_history":True,"adhoc_codesign_only":True}}

def validate(r):
    if set(r) != {"schema","status","authorities","source_sha256","old_binary_sha256","new_binary_sha256","candidate_installed_inventory_exact","rollback_copy_count","non_kira_identity_rows_exact","after_effects_processes","scope"}: raise RuntimeError("schema drift")
    if r != generate(): raise RuntimeError("report differs from live audit")
def markdown(r): return f"# OLMKiraKira WorldSuite incremental install (2026-08-14)\n\nStatus: `{r['status']}`\n\nInstalled `{NEW}` with three exact `{OLD_SHA}` rollback copies. AE was not launched; signing is strict-valid ad-hoc only.\n"
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--write",action="store_true"); args=ap.parse_args(); r=generate()
    if args.write: REPORT.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n"); MARKDOWN.write_text(markdown(r))
    else:
        validate(json.loads(REPORT.read_text()))
        if MARKDOWN.read_text()!=markdown(r): raise RuntimeError("markdown drift")
    print(STATUS)
if __name__ == "__main__":
    try: main()
    except Exception as exc: print(f"FAIL_OLMKIRAKIRA_WORLDSUITE_INSTALL_AUDIT: {exc}",file=sys.stderr); raise
