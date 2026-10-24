#!/usr/bin/env python3
"""Bounded exported-owner verdict for the retained PF16 Legacy fixtures."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset, asset_relative

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
import test_olmblur_exported_effectmain_chain_actual_aex_20260811 as public  # noqa: E402
import test_olmblur_worker16_legacy as worker  # noqa: E402


REPORT = ROOT / "refs/conformance/olmblur_pf16_legacy_retained_exported_public_owner_20260813.json"
DOC = ROOT / "refs/conformance/olmblur_pf16_legacy_retained_exported_public_owner_20260813.md"
AEX = resolve_asset(ROOT / "plugins_2025/OLMBlur.aex")
AEX_SHA = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
PUBLIC_RUNNER = ROOT / "tools/emulation/test_olmblur_exported_effectmain_chain_actual_aex_20260811.py"
WORKER_RUNNER = ROOT / "tools/emulation/test_olmblur_worker16_legacy.py"

CASES = (
    {
        "id": "pf16_legacy_12x12_amount3_repeat2_bias1",
        "width": 12, "height": 12, "amount": 3.0, "smoothness": 100.0,
        "repeat": 2, "bias": 1, "mixed_alpha": False, "pattern": "",
        "source_sha256": "c97013f8c7c515a75701bb0979f435a0f81bbe9309157cc56a6135e7dbef0eb4",
        "oracle_sha256": "6119d2c5760e5f5234b9c53c990dad3a529777124bdbab794dc46bd562c1e9c0",
        "public_sha256": "6119d2c5760e5f5234b9c53c990dad3a529777124bdbab794dc46bd562c1e9c0",
        "mismatched_bytes": 0, "worker_instructions": 184049,
        "disposition": "promotable_exact",
    },
    {
        "id": "pf16_legacy_18x18_amount11_repeat3_bias2",
        "width": 18, "height": 18, "amount": 11.0, "smoothness": 100.0,
        "repeat": 3, "bias": 2, "mixed_alpha": False, "pattern": "",
        "source_sha256": "6f911aa2fb9d2aa0f5c9db56936ff1bb0b2a5710cd49adc8e05467722ddef565",
        "oracle_sha256": "b47c25529ac36c0c7af7fb43659d67a5e7d3a4d77172706813dad47e1a700d26",
        "public_sha256": "b47c25529ac36c0c7af7fb43659d67a5e7d3a4d77172706813dad47e1a700d26",
        "mismatched_bytes": 0, "worker_instructions": 1363250,
        "disposition": "promotable_exact",
    },
    {
        "id": "pf16_legacy_18x12_mixed_alpha_repeat2_bias2",
        "width": 18, "height": 12, "amount": 3.0, "smoothness": 100.0,
        "repeat": 2, "bias": 2, "mixed_alpha": True, "pattern": "",
        "source_sha256": "c402d7ee39d3ef39015414094c13ca7f7308bad7414872a5edf6aa6005bdc6f9",
        "oracle_sha256": "28b16efe8ef4535661f1f514ff69195e944d1c071d78df1e8f5a8034cbcdc346",
        "public_sha256": "28b16efe8ef4535661f1f514ff69195e944d1c071d78df1e8f5a8034cbcdc346",
        "mismatched_bytes": 0, "worker_instructions": 196858,
        "disposition": "promotable_exact",
    },
    {
        "id": "pf16_legacy_20x16_smooth62_5_repeat4_bias1",
        "width": 20, "height": 16, "amount": 7.0, "smoothness": 62.5,
        "repeat": 4, "bias": 1, "mixed_alpha": False, "pattern": "word_boundaries",
        "source_sha256": "d73bbdd3cf1872f20883fa596615702552eadf308e40552763d1eaa698007366",
        "oracle_sha256": "7ac117f2430da7a8d132c1f5318b89218cefa0601100173a99294b1ea175b305",
        "public_sha256": "2e97a898b15328c6fb11876f88951c9b1a593a66eb23bcbe89b94784c477ca1b",
        "mismatched_bytes": 369, "worker_instructions": 425837,
        "disposition": "fail_closed_public_mismatch",
    },
)
EXPECTED_CANONICAL_SHA256 = "315ef514605c9baf378bc27bd012db29cc1409bee9588d923726a96ef03fdb16"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(spec: dict[str, object]) -> dict[str, object]:
    case = {
        "id": spec["id"], "width": spec["width"], "height": spec["height"],
        "blur_amount": spec["amount"], "smoothness": spec["smoothness"],
        "repeat": spec["repeat"], "bias_direction": spec["bias"],
        "mixed_alpha": spec["mixed_alpha"], "pattern": spec["pattern"],
    }
    source = worker.source_bytes(case["width"], case["height"], case["mixed_alpha"], case["pattern"])
    expected, meta = worker.run_case(case)
    if hashlib.sha256(source).hexdigest() != spec["source_sha256"]:
        raise RuntimeError("source drift")
    if hashlib.sha256(expected).hexdigest() != spec["oracle_sha256"]:
        raise RuntimeError("worker oracle drift")
    if meta["instructions"] != spec["worker_instructions"]:
        raise RuntimeError("worker execution drift")
    with tempfile.TemporaryDirectory(prefix="olmblur-pf16-legacy-public-") as temp:
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
                "id": spec["id"], "depth": 16, "legacy": 1,
                "amount": spec["amount"], "smoothness": spec["smoothness"],
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
        "parameters": {
            "amount_f64": spec["amount"], "smoothness_f64": spec["smoothness"],
            "smoothness_fixed": int(spec["smoothness"] * 65536),
            "repeat": spec["repeat"], "bias": spec["bias"], "legacy": 1,
        },
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
        "schema": "olmblur.pf16-legacy-retained-exported-public-owner/1",
        "status": "PASS_THREE_LEGACY_RETAINED_EXACT_ONE_PUBLIC_MISMATCH_FAIL_CLOSED",
        "identities": {
            "aex": {"path": asset_relative(AEX, ROOT).as_posix(), "sha256": AEX_SHA},
            "public_runner": {"path": PUBLIC_RUNNER.relative_to(ROOT).as_posix(), "sha256": sha256(PUBLIC_RUNNER)},
            "worker_runner": {"path": WORKER_RUNNER.relative_to(ROOT).as_posix(), "sha256": sha256(WORKER_RUNNER)},
        },
        "rows": rows,
        "summary": {"cells": 4, "raw_exact": 3, "public_mismatch": 1,
                    "mismatch_bytes": 369, "padding_untouched": 4},
        "claim_boundary": "Repository AexLoader/Unicorn execution of the current Windows exported SmartPreRender/SmartRender owner. The exact 12x12 and 18x18 constant-alpha Legacy rows plus the exact 18x12 mixed-alpha Legacy row are promotable. The exact Smoothness62.5 word-boundary row differs from its retained worker oracle and must remain public fail-closed.",
        "claims_not_made": ["native Windows AE", "native Mac AE", "installed Mac binary",
                            "other source/tuple/geometry/depth", "correction of either mismatched row"],
    }


def validate(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {"schema", "status", "identities", "rows", "summary", "claim_boundary", "claims_not_made"}:
        raise ValueError("top schema")
    digest = hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    if digest != EXPECTED_CANONICAL_SHA256:
        raise ValueError("canonical exact closure mismatch")


def markdown(value: dict[str, object]) -> str:
    return f"""# OLMBlur PF16 retained Legacy tuples: exported public owner

Status: **{value['status']}**

The exact 12x12/Amount3/Repeat2/Bias1 and 18x18/Amount11/Repeat3/Bias2
constant-alpha Legacy rows, plus 18x12/Amount3/Repeat2/Bias2 mixed-alpha, are
raw exact.  The exact 20x16 Smoothness62.5 word-boundary row differs by 369
active bytes and remains fail-closed.  Padding is untouched in all four rows.

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
        if saved != fresh or DOC.read_text() != markdown(saved):
            raise RuntimeError("documentation drift")
    print(fresh["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
