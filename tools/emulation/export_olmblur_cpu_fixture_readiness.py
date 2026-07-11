#!/usr/bin/env python3
"""Record the current OLMBlur helper-fixture and full-entry readiness state."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from aex_loader import AexLoader  # noqa: E402
from test_olmblur_case0006 import (  # noqa: E402
    AEX_PATH,
    FUN_OLMBLUR_NONLEGACY_HORIZONTAL,
    FUN_OLMBLUR_NONLEGACY_VERTICAL,
    run_nonlegacy_helpers,
)

DEFAULT_OUTPUT = ROOT / "core" / "olmblur_cpu_fixture_readiness.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def helper_bytes(rows: list[list[float]]) -> bytes:
    return b"".join(struct.pack("<3f", *row) for row in rows)


def export(output: Path) -> None:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    observed = run_nonlegacy_helpers(loader)
    horizontal = helper_bytes(observed["horizontal_output_rgb_triplets"])
    vertical = helper_bytes(observed["vertical_output_rgb_triplets"])
    readiness = {
        "schema": "olm.aex.cpu-fixture-readiness/1",
        "status": "portable-core-ready",
        "fixture_kind": "function-scope-typed-helper",
        "plugin": "OLMBlur",
        "binary": {
            "path": "plugins_2025/OLMBlur.aex",
            "sha256": sha256_bytes(AEX_PATH.read_bytes()),
        },
        "functions": {
            "horizontal": {
                "address": hex(FUN_OLMBLUR_NONLEGACY_HORIZONTAL),
                "abi": "RCX,RDX,R8,R9 then [RSP+0x28..] = flags,src,dst,weights,width,height64,arg7,arg8,arg9",
                "observed_output_sha256": sha256_bytes(horizontal),
                "observed_output_bytes": len(horizontal),
            },
            "vertical": {
                "address": hex(FUN_OLMBLUR_NONLEGACY_VERTICAL),
                "abi": "RCX,RDX,R8,R9 then [RSP+0x28..] = flags,src,dst,weights,width,height,arg7,arg8,arg9",
                "observed_output_sha256": sha256_bytes(vertical),
                "observed_output_bytes": len(vertical),
            },
        },
        "execution": {
            "oracle": "unicorn-aex",
            "import_free": not loader.import_log,
            "instructions": int(observed["instructions"]),
            "input": {
                "kind": "harness-constructed",
                "16bpc_words": observed["input_16bpc_words"],
                "float_lift": observed["input_float_lift"],
            },
        },
        "blockers": [
            {
                "id": "full-entry-host-layout-missing",
                "scope": "case-bound",
                "detail": "FUN_180005f20 still lacks independently grounded OLMBlur allocation ownership and later host-buffer layout, so full-entry output cannot be treated as an exact case fixture.",
                "unblock_with": "A retained full-entry helper/fullentry capture identifying all PF Handle allocations and host buffer ranges.",
            },
        ],
        "source_of_truth": {
            "helper_probe": "tools/emulation/test_olmblur_case0006.py",
            "fullentry_probe": "tools/emulation/test_olmblur_case0006_fullentry.py",
            "fullentry_report": "refs/conformance/olmblur_case0006_fullentry_probe_20260710.md",
        },
        "portable_core": {
            "header": "core/olmblur_helper.h",
            "implementation": "core/olmblur_helper.cpp",
            "fixture_manifest": "tools/emulation/fixtures/olmblur_helper/manifest.json",
            "smoke": "tools/emulation/smoke_olmblur_helper.py",
            "contract": {
                "input": "float32 interleaved RGB triplets plus one active flag byte per pixel",
                "center": "active flag zero copies the center RGB triplet",
                "weights": "left/top include center weights[0] then weights[d] toward the edge; right/bottom use weights[d]",
                "boundaries": "each direction clamps at the edge/radius and breaks at its first inactive flag",
                "zero_denominator": "sum zero writes positive zero before channel stores",
                "arithmetic": "ordered scalar SSE-style accumulation; FMA contraction disabled",
            },
        },
        "claim": "Portable core matches retained actual AEX helper fixtures byte-for-byte; this is not a full-entry or AE-exact claim.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(readiness, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    export(args.output.resolve())
    print(f"[OK] exported OLMBlur portable-helper readiness: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
