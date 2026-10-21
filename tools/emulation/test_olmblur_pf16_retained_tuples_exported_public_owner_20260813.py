#!/usr/bin/env python3
"""Bounded exported-owner verdict for the original retained PF16 tuples."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
import test_olmblur_exported_effectmain_chain_actual_aex_20260811 as public  # noqa: E402
import test_olmblur_worker16_nonlegacy as worker  # noqa: E402


REPORT = ROOT / "refs/conformance/olmblur_pf16_retained_tuples_exported_public_owner_20260813.json"
DOC = ROOT / "refs/conformance/olmblur_pf16_retained_tuples_exported_public_owner_20260813.md"
AEX = ROOT / "plugins_2025/OLMBlur.aex"
AEX_SHA = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
PUBLIC_RUNNER = ROOT / "tools/emulation/test_olmblur_exported_effectmain_chain_actual_aex_20260811.py"
WORKER_RUNNER = ROOT / "tools/emulation/test_olmblur_worker16_nonlegacy.py"

CASES = (
    {
        "id": "pf16_12x12_amount3_repeat2_bias1_nonlegacy",
        "width": 12, "height": 12, "amount": 3.0, "repeat": 2, "bias": 1,
        "source_sha256": "df143537b2c987564fd2c0d0b4f9ad3b2332c4db8d5ccbaf8ac3ebc71b05bb8d",
        "oracle_sha256": "28d648118306c3ed9bedbcd7e99c7af8f8bc26813b701b366c56b966f3a3e846",
        "public_sha256": "28d648118306c3ed9bedbcd7e99c7af8f8bc26813b701b366c56b966f3a3e846",
        "mismatched_bytes": 0,
        "worker_instructions": 102918,
        "disposition": "promotable_exact",
    },
    {
        "id": "pf16_18x18_amount11_repeat3_bias2_nonlegacy",
        "width": 18, "height": 18, "amount": 11.0, "repeat": 3, "bias": 2,
        "source_sha256": "bc3bfbf7c3d5a908690b71819c9dd83e4bddb9b6f09a417ff06ec6cc3d3943ae",
        "oracle_sha256": "64355b2ce493e3d318de8fa09f45234b98236029347b62e9d09e4ef8cb98a4bc",
        "public_sha256": "64355b2ce493e3d318de8fa09f45234b98236029347b62e9d09e4ef8cb98a4bc",
        "mismatched_bytes": 0,
        "worker_instructions": 383372,
        "disposition": "promotable_exact",
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(spec: dict[str, object]) -> dict[str, object]:
    case = {
        "id": spec["id"], "width": spec["width"], "height": spec["height"],
        "blur_amount": spec["amount"], "smoothness": 100.0,
        "repeat": spec["repeat"], "bias_direction": spec["bias"],
    }
    source = worker.source_bytes(case["width"], case["height"])
    expected, meta = worker.run_case(case)
    if hashlib.sha256(source).hexdigest() != spec["source_sha256"]:
        raise RuntimeError("source drift")
    if hashlib.sha256(expected).hexdigest() != spec["oracle_sha256"]:
        raise RuntimeError("worker oracle drift")
    if meta["instructions"] != spec["worker_instructions"]:
        raise RuntimeError("worker execution drift")
    with tempfile.TemporaryDirectory(prefix="olmblur-pf16-retained-public-") as temp:
        fixture = Path(temp)
        (fixture / "source.bin").write_bytes(source)
        (fixture / "expected.bin").write_bytes(expected)
        old = (public.WIDTH, public.HEIGHT, public.PADDING[16], public.FIXTURE)
        try:
            public.WIDTH = case["width"]
            public.HEIGHT = case["height"]
            public.PADDING[16] = 13
            public.FIXTURE = fixture
            result = public.run_row({
                "id": spec["id"], "depth": 16, "legacy": 0,
                "amount": spec["amount"], "smoothness": 100,
                "repeat": spec["repeat"], "bias_direction": spec["bias"],
                "expect_exact": spec["mismatched_bytes"] == 0,
                "source": "source.bin", "expected": "expected.bin",
                "expected_sha256": spec["oracle_sha256"],
            })
        finally:
            public.WIDTH, public.HEIGHT, public.PADDING[16], public.FIXTURE = old
    if result["active_sha256"] != spec["public_sha256"]:
        raise RuntimeError("public output drift")
    if result["mismatched_bytes"] != spec["mismatched_bytes"] or result["padding_mismatches"]:
        raise RuntimeError("public verdict drift")
    return {
        "id": spec["id"], "geometry": [spec["width"], spec["height"]],
        "rowbytes": spec["width"] * 8 + 13, "padding_per_row": 13,
        "parameters": {"amount_f64": spec["amount"], "smoothness_fixed": 6553600,
                       "repeat": spec["repeat"], "bias": spec["bias"], "legacy": 0},
        "active_source_sha256": spec["source_sha256"],
        "worker_oracle_sha256": spec["oracle_sha256"],
        "public_output_sha256": spec["public_sha256"],
        "mismatched_bytes": spec["mismatched_bytes"],
        "worker_instructions": spec["worker_instructions"],
        "disposition": spec["disposition"],
        "public_lifecycle": {
            "commands": result["commands"], "return_codes": result["return_codes"],
            "parameter_checkout_order": result["parameter_checkout_order"],
            "padding_mismatches": result["padding_mismatches"],
        },
    }


def live() -> dict[str, object]:
    if sha256(AEX) != AEX_SHA:
        raise RuntimeError("AEX drift")
    rows = [run_case(spec) for spec in CASES]
    return {
        "schema": "olmblur.pf16-retained-tuples-exported-public-owner/1",
        "status": "PASS_TWO_RETAINED_TUPLES_RAW_EXACT",
        "identities": {
            "aex": {"path": AEX.relative_to(ROOT).as_posix(), "sha256": AEX_SHA},
            "public_runner": {"path": PUBLIC_RUNNER.relative_to(ROOT).as_posix(), "sha256": sha256(PUBLIC_RUNNER)},
            "worker_runner": {"path": WORKER_RUNNER.relative_to(ROOT).as_posix(), "sha256": sha256(WORKER_RUNNER)},
        },
        "rows": rows,
        "summary": {"cells": 2, "raw_exact": 2, "public_mismatch": 0,
                    "mismatch_bytes": 0, "padding_untouched": 2},
        "claim_boundary": "Repository AexLoader/Unicorn execution of the current Windows exported SmartPreRender/SmartRender owner. Both exact retained PF16 tuples are raw exact with untouched row padding; no broader source, tuple, geometry, or depth is inferred.",
        "claims_not_made": ["native Windows AE", "native Mac AE", "installed Mac binary",
                            "other source/tuple/geometry/depth"],
    }


def validate(value: object) -> None:
    fresh = live()
    if value != fresh:
        raise ValueError("live exact closure mismatch")


def markdown(value: dict[str, object]) -> str:
    return f"""# OLMBlur PF16 retained tuples: exported public owner

Status: **{value['status']}**

The exact 12x12/Amount3/Repeat2/Bias1/NonLegacy and
18x18/Amount11/Repeat3/Bias2/NonLegacy rows are raw exact. Padding is untouched
in both rows.

{value['claim_boundary']}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    fresh = live()
    if args.write:
        REPORT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n")
        DOC.write_text(markdown(fresh))
    else:
        saved = json.loads(REPORT.read_text())
        validate(saved)
        if DOC.read_text() != markdown(saved):
            raise RuntimeError("documentation drift")
    print(fresh["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
