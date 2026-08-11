#!/usr/bin/env python3
"""Fail-closed OLMToonDilate entry-to-installed-bundle completion route."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from olm_installed_identity import verified_binary

ROOT = Path(__file__).resolve().parents[2]
ACTUAL = ROOT / "tools/emulation/probe_olmtoondilate_actual_aex_sequence_smartpre_20260805.py"
ADAPTER = ROOT / "tools/emulation/test_olmtoondilate_mac_smartrender_adapter_20260717.py"
DYNAMIC = ROOT / "tools/emulation/test_olmtoondilate_installed_dynamic_all_depths_20260806.py"
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
SOURCE_REPO_PATH = SOURCE.relative_to(ROOT).as_posix()
REPORT = ROOT / "refs/conformance/olmtoondilate_installed_completion_route_20260805.json"
MARKDOWN = REPORT.with_suffix(".md")
# These commits establish the two production behaviors that changed after the
# original completion-route snapshot.  Source identity is fixed to the checked
# out HEAD below, rather than to a stale content hash: an uncommitted source
# edit must still fail closed, while a reviewed successor commit is accepted
# only when the behavioral adapter and installed dynamic gates also pass.
REQUIRED_SOURCE_COMMITS = {
    "legacy_render_noop": "55e7a4c85aa3e784b5d7e689ce22591d4e0b1e56",
    "high_radius_downsample_ratio": "47ee394d63ca5e06ab41963c4fea5f1f052d581f",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_json(path: Path) -> dict:
    run = subprocess.run([sys.executable, str(path)], cwd=ROOT, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: {path.name} failed\n{run.stdout}\n{run.stderr}")
    return json.loads(run.stdout)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=check
    )


def source_head_identity() -> dict:
    head = git("rev-parse", "HEAD").stdout.strip()
    head_bytes = subprocess.run(
        ["git", "show", f"HEAD:{SOURCE_REPO_PATH}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    required_ancestors = {
        name: git("merge-base", "--is-ancestor", commit, "HEAD", check=False).returncode == 0
        for name, commit in REQUIRED_SOURCE_COMMITS.items()
    }
    return {
        "head_commit": head,
        "head_blob": git("rev-parse", f"HEAD:{SOURCE_REPO_PATH}").stdout.strip(),
        "head_source_sha256": hashlib.sha256(head_bytes).hexdigest(),
        "worktree_source_sha256": sha(SOURCE),
        "worktree_matches_head": SOURCE.read_bytes() == head_bytes,
        "required_ancestor_commits": required_ancestors,
    }


def main() -> int:
    binary, identity = verified_binary("OLMToonDilate")
    installed = binary.parents[2]
    actual = run_json(ACTUAL)
    adapter = run_json(ADAPTER)
    dynamic = run_json(DYNAMIC)
    source_identity = source_head_identity()
    archs = subprocess.run(["lipo", "-archs", str(binary)], capture_output=True, text=True, check=True).stdout.split()
    sign = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(installed)], capture_output=True)
    selected = [
        "smart_pre_entry_returned", "smart_render_entry_returned",
        "mixed_3x2_all_depths_exact", "radius2_4x2_all_depths_exact",
        "radius3_pf8_5x1_exact", "radius3_pf16_5x1_exact", "radius3_pf32_5x1_exact",
        "radius4_pf8_6x1_exact", "radius4_pf16_6x1_exact", "radius4_pf32_6x1_exact",
        "downsample_radius_matrix_all_depths_exact", "legacy_render_public_noop_all_depths_exact",
        "empty_width_pf8_exact", "empty_height_pf16_exact", "empty_both_pf32_exact",
    ]
    gates = {
        "actual_entry_chain_exact": actual.get("status") == "PASS_SEQUENCE_AND_SMARTPRE_ENTRY" and all(actual.get("gates", {}).get(k) for k in selected),
        "production_adapter_exact": adapter.get("status") == "ok",
        "production_source_identity": source_identity["worktree_matches_head"] and all(
            source_identity["required_ancestor_commits"].values()
        ),
        "installed_binary_identity": sha(binary) == identity["sha256"],
        "installed_universal": set(archs) == {"arm64", "x86_64"},
        "installed_codesign_valid": sign.returncode == 0,
        "single_active_bundle": len(list(installed.parent.glob("OLMToonDilate.plugin"))) == 1,
        "installed_dynamic_entry_exact": dynamic.get("status") == "PASS_INSTALLED_DYNAMIC_ALL_DEPTHS" and all(
            dynamic.get("gates", {}).get(key) for key in ("dlopen_effectmain", "PF8_exact", "PF16_exact", "PF32_bitwise_exact")
        ),
    }
    status = "PASS_INSTALLED_COMPLETION_ROUTE" if all(gates.values()) else "BLOCKED_FAIL_CLOSED"
    report = {
        "status": status,
        "route": [
            "actual AEX entry_point command 0x17 SmartPreRender",
            "actual AEX entry_point command 0x18 typed PF8/PF16/PF32 workers and writers",
            "actual and production public legacy PF_Cmd_RENDER constant-zero no-op",
            "source-included production EffectMain SmartPreRender/SmartRender exact adapter",
            "current production source SHA identity",
            "current installed signed Universal bundle SHA identity",
            "installed arm64 EffectMain dynamic PF8/PF16/PF32 SmartPreRender/SmartRender execution",
        ],
        "actual_aex_sha256": actual["aex_sha256"],
        "actual_report_sha256": sha(ROOT / "refs/conformance/olmtoondilate_actual_aex_sequence_smartpre_20260805.json"),
        "production_source_sha256": sha(SOURCE),
        "production_source_identity": source_identity,
        "installed": {"path": str(installed), "binary_sha256": sha(binary), "architectures": archs, "codesign": "valid" if sign.returncode == 0 else "invalid"},
        "gates": gates,
        "restart_required_from_install_record": False,
        "installed_dynamic_entry": dynamic,
        "claim_boundary": "AE-free completion route including dynamic execution of the installed arm64 EffectMain under focused host callbacks. Real AE execution remains unclaimed.",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    MARKDOWN.write_text(
        f"# OLMToonDilate installed completion route — 2026-08-05\n\n"
        f"- Status: **{status}**\n"
        f"- Actual entrypoint SmartPre/SmartRender, all typed workers/writers, production adapter, source identity, installed Universal identity, and installed arm64 EffectMain dynamic execution are fail-closed.\n"
        f"- Installed binary SHA-256: `{report['installed']['binary_sha256']}`.\n"
        f"- AE-free boundary: focused installed dynamic loading is proven; real AE loading and rendering remain unclaimed.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if status.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
