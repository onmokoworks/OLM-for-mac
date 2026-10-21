#!/usr/bin/env python3
"""Windows exported Smart owner for two retained PF16 worker sources."""

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


REPORT = ROOT / "refs/conformance/olmblur_pf16_worker_sources_exported_public_owner_20260813.json"
DOC = ROOT / "refs/conformance/olmblur_pf16_worker_sources_exported_public_owner_20260813.md"
AEX = ROOT / "plugins_2025/OLMBlur.aex"
WORKER_RUNNER = ROOT / "tools/emulation/test_olmblur_worker16_nonlegacy.py"
PUBLIC_RUNNER = ROOT / "tools/emulation/test_olmblur_exported_effectmain_chain_actual_aex_20260811.py"
AEX_SHA = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
CASES = (
    {
        "id": "pf16_12x12_amount3_repeat1_bias1_nonlegacy",
        "width": 12,
        "height": 12,
        "amount": 3.0,
        "source_sha256": "df143537b2c987564fd2c0d0b4f9ad3b2332c4db8d5ccbaf8ac3ebc71b05bb8d",
        "output_sha256": "f4a8b917c50936578f0573b943e5d9baad29af87b8f17f2efec4765c74771922",
        "worker_instructions": 59337,
    },
    {
        "id": "pf16_18x18_amount11_repeat1_bias1_nonlegacy",
        "width": 18,
        "height": 18,
        "amount": 11.0,
        "source_sha256": "bc3bfbf7c3d5a908690b71819c9dd83e4bddb9b6f09a417ff06ec6cc3d3943ae",
        "output_sha256": "fbf43a4c4832c1c2a8e30187361ddaec6bf95c36a793f71573d8b1db4652a46e",
        "worker_instructions": 175713,
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def live() -> dict[str, object]:
    if sha256(AEX) != AEX_SHA:
        raise RuntimeError("AEX drift")
    rows = []
    for spec in CASES:
        case = {
            "id": spec["id"],
            "width": spec["width"],
            "height": spec["height"],
            "blur_amount": spec["amount"],
            "smoothness": 100.0,
            "repeat": 1,
            "bias_direction": 1,
        }
        source = worker.source_bytes(case["width"], case["height"])
        expected, worker_meta = worker.run_case(case)
        if hashlib.sha256(source).hexdigest() != spec["source_sha256"]:
            raise RuntimeError("source drift")
        if hashlib.sha256(expected).hexdigest() != spec["output_sha256"]:
            raise RuntimeError("worker output drift")
        if worker_meta["instructions"] != spec["worker_instructions"]:
            raise RuntimeError("worker execution drift")
        with tempfile.TemporaryDirectory(prefix="olmblur-pf16-worker-public-") as temp:
            fixture = Path(temp)
            (fixture / "source.bin").write_bytes(source)
            (fixture / "expected.bin").write_bytes(expected)
            old = (public.WIDTH, public.HEIGHT, public.PADDING[16], public.FIXTURE)
            try:
                public.WIDTH = case["width"]
                public.HEIGHT = case["height"]
                public.PADDING[16] = 13
                public.FIXTURE = fixture
                row = public.run_row({
                    "id": spec["id"],
                    "depth": 16,
                    "legacy": 0,
                    "amount": spec["amount"],
                    "source": "source.bin",
                    "expected": "expected.bin",
                    "expected_sha256": spec["output_sha256"],
                })
            finally:
                public.WIDTH, public.HEIGHT, public.PADDING[16], public.FIXTURE = old
        rows.append({
            "id": spec["id"],
            "geometry": [spec["width"], spec["height"]],
            "rowbytes": spec["width"] * 8 + 13,
            "padding_per_row": 13,
            "parameters": {"amount_f64": spec["amount"], "smoothness_fixed": 6553600, "repeat": 1, "bias": 1, "legacy": 0},
            "active_source_sha256": spec["source_sha256"],
            "active_output_sha256": spec["output_sha256"],
            "worker_instructions": spec["worker_instructions"],
            "public_result": row,
        })
    return {
        "schema": "olmblur.pf16-worker-sources-exported-public-owner/1",
        "status": "PASS_ACTUAL_EXPORTED_SMART_OWNER_PF16_WORKER_SOURCES_2_RAW_EXACT",
        "identities": {
            "aex": {"path": AEX.relative_to(ROOT).as_posix(), "sha256": AEX_SHA},
            "worker_runner": {"path": WORKER_RUNNER.relative_to(ROOT).as_posix(), "sha256": sha256(WORKER_RUNNER)},
            "public_runner": {"path": PUBLIC_RUNNER.relative_to(ROOT).as_posix(), "sha256": sha256(PUBLIC_RUNNER)},
        },
        "rows": rows,
        "summary": {"cells": 2, "raw_exact": 2, "padding_untouched": 2, "commands": [23, 24], "parameter_checkout_order": [1, 2, 3, 4, 5]},
        "claim_boundary": "Actual Windows 2025 AEX exported SmartPreRender/SmartRender under the repository AexLoader/Unicorn. Each row uses the exact retained PF16 worker source and a fresh same-source internal-worker oracle. This is hostless public-owner evidence, not native AE or arbitrary-source evidence.",
        "claims_not_made": ["native Windows AE", "native Mac AE", "Mac production admission", "installed Mac binary", "other source/tuple/geometry/depth"],
    }


def validate(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {"schema", "status", "identities", "rows", "summary", "claim_boundary", "claims_not_made"}:
        raise ValueError("top schema")
    if value["schema"] != "olmblur.pf16-worker-sources-exported-public-owner/1" or value["status"] != "PASS_ACTUAL_EXPORTED_SMART_OWNER_PF16_WORKER_SOURCES_2_RAW_EXACT":
        raise ValueError("authority")
    if value["summary"] != {"cells": 2, "raw_exact": 2, "padding_untouched": 2, "commands": [23, 24], "parameter_checkout_order": [1, 2, 3, 4, 5]}:
        raise ValueError("summary")
    if len(value["rows"]) != 2 or {row["id"] for row in value["rows"]} != {case["id"] for case in CASES}:
        raise ValueError("rows")
    for row, spec in zip(value["rows"], CASES):
        if set(row) != {"id", "geometry", "rowbytes", "padding_per_row", "parameters", "active_source_sha256", "active_output_sha256", "worker_instructions", "public_result"}:
            raise ValueError("row schema")
        result = row["public_result"]
        if row["id"] != spec["id"] or row["geometry"] != [spec["width"], spec["height"]] or row["rowbytes"] != spec["width"] * 8 + 13:
            raise ValueError("row contract")
        if row["active_source_sha256"] != spec["source_sha256"] or row["active_output_sha256"] != spec["output_sha256"]:
            raise ValueError("row hashes")
        if result["active_sha256"] != spec["output_sha256"] or result["oracle_sha256"] != spec["output_sha256"] or result["mismatched_bytes"] or result["padding_mismatches"]:
            raise ValueError("public result")
        if result["return_codes"] != [0, 0] or result["parameter_checkout_order"] != [1, 2, 3, 4, 5]:
            raise ValueError("public lifecycle")
    if value != live():
        raise ValueError("live recanonicalization drift")


def markdown(value: dict[str, object]) -> str:
    return f"""# OLMBlur PF16 retained worker sources: exported public owner

Status: **{value['status']}**

The exact 12x12/Amount3 and 18x18/Amount11 PF16 sources, both Repeat 1,
Bias 1 and NonLegacy, traverse the Windows exported SmartPreRender and
SmartRender entry points.  Both active outputs equal their fresh actual-worker
oracles and all 13 padding bytes per row remain untouched.

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
        print(fresh["status"])
        return 0
    saved = json.loads(REPORT.read_text())
    validate(saved)
    if saved != fresh or DOC.read_text() != markdown(saved):
        raise RuntimeError("saved evidence drift")
    print(saved["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
