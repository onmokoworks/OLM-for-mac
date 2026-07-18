#!/usr/bin/env python3
"""Read-only audit of RadialBlur worker checkpoints and hook contracts.

This test only parses existing checkpoint headers and source text.  It never
loads, resumes, patches, or creates an AEX checkpoint.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "refs/conformance/olmradialblur_checkpoint_hook_audit_20260718.json"
MAGIC = b"AEXCP64\x00"
PREFIX_SIZE = len(MAGIC) + 4 + 8 + 32
TARGETS = (0x180005C90, 0x18000A9D0)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def header(path: Path) -> dict:
    with path.open("rb") as source:
        prefix = source.read(PREFIX_SIZE)
        if not prefix.startswith(MAGIC):
            raise AssertionError(f"invalid checkpoint magic: {path}")
        size = int.from_bytes(prefix[len(MAGIC) + 4:len(MAGIC) + 12], "little")
        payload = source.read(size)
    if hashlib.sha256(payload).digest() != prefix[-32:]:
        raise AssertionError(f"invalid checkpoint header checksum: {path}")
    return json.loads(payload.decode("ascii"))


def checkpoint_row(index: int) -> dict:
    paths = [
        Path(f"/tmp/olm_radial_case0009_workers_progress{index}_20260718.aexcp"),
        Path(f"/tmp/olm_radial_case0009_workers_progress{index}_20260717.aexcp"),
    ]
    path = next((item for item in paths if item.is_file()), None)
    if path is None:
        return {"index": index, "present": False}
    data = header(path)
    registers = data["registers"]["gp"]
    metadata = data.get("metadata", {})
    config = metadata.get("config", {})
    return {
        "index": index,
        "present": True,
        "path": str(path),
        "size": path.stat().st_size,
        "sha256": sha256(path),
        "rip": hex(int(registers["rip"])),
        "instructions_executed": int(data.get("instructions_executed", 0)),
        "lineage": metadata.get("checkpoint_lineage", []),
        "aex_sha256": data.get("aex", {}).get("sha256"),
        "natural_harness": metadata.get("harness") == "test_zoom_case0009",
        "direct_zoom_core": bool(config.get("direct_zoom_core")),
        "synthetic_prefill": bool(
            config.get("direct_fast_forward_prefill")
            or config.get("direct_python_prefill")
        ),
        "worker_detours": bool(
            config.get("direct_detour_prepass") or config.get("direct_detour_scatter")
        ),
        "target_entry": int(registers["rip"]) in TARGETS,
    }


def main() -> int:
    runner = (ROOT / "tools/emulation/test_zoom_case0009.py").read_text(encoding="utf-8")
    progress_runner = (ROOT / "tools/emulation/run_radialblur_natural_progress_hook_20260718.py").read_text(encoding="utf-8")
    disasm = (ROOT / "disasm/OLMRadialBlur.aex.asm.txt").read_text(encoding="utf-8")
    checkpoints = [checkpoint_row(index) for index in range(1, 7)]
    present = [item for item in checkpoints if item["present"]]
    target_entry = [item for item in present if item["target_entry"]]
    report = {
        "kind": "olmradialblur_checkpoint_hook_audit_20260718",
        "status": "pass_audit_no_existing_entry_checkpoint",
        "claim_boundary": "serialized-header and source-contract audit only; no AEX execution",
        "checkpoints": checkpoints,
        "checks": {
            "all_six_present": len(present) == 6,
            "all_natural": all(item["natural_harness"] for item in present),
            "all_no_direct_core": all(not item["direct_zoom_core"] for item in present),
            "all_no_synthetic_prefill": all(not item["synthetic_prefill"] for item in present),
            "all_no_worker_detours": all(not item["worker_detours"] for item in present),
            "no_existing_target_entry": not target_entry,
            "progress_hook_is_observational": "original_add_code_hook" in progress_runner and "capture_worker_boundary" in progress_runner,
            "save_hook_is_before_rip": "Save primary-render state before RIP executes" in runner,
            "caller_callsite_is_real_a9d0_entry": bool(re.search(r"180005c90  CALL 0x18000a9d0", disasm)),
            "normalization_follows_call": bool(re.search(r"180005c9f  XORPS XMM6,XMM6", disasm)),
        },
        "earliest_reproducible_route": {
            "result": "not_available_from_existing_checkpoints",
            "reason": "progress1..6 are all inside FUN_18000a9d0; a forward resume cannot create an entry checkpoint",
            "required_checkpoint_rip": "0x180005c90",
            "alternative_entry_rip": "0x18000a9d0",
            "runner_command_shape": "python3 tools/emulation/test_zoom_case0009.py --save-checkpoint-at-rip /tmp/olm_radial_case0009_a9d0_entry_20260718.aexcp 0x180005c90 ...",
            "constraint": "must start from a genuine natural pre-call state; do not use direct-core, synthetic-prefill, worker-detour, or register/state editing",
        },
        "rejected_shortcuts": [
            "resume progress6 and edit RIP backward",
            "resume any mid-A9D0 checkpoint and label it an entry checkpoint",
            "direct-core or synthetic-prefill setup",
            "worker detour or no-op substitution",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checks = report["checks"]
    if not all(checks.values()):
        raise SystemExit(f"audit failed: {checks}")
    print("PASS RadialBlur checkpoint/hook audit: six natural checkpoints, no existing A9D0 entry")
    print("earliest_reproducible_route=not_available_from_existing_checkpoints")
    print(f"report={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
