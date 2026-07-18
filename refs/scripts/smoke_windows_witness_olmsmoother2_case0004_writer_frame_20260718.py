#!/usr/bin/env python3
"""Fail-closed compile/validator smoke for the Smoother2 case_0004 writer-frame package."""

from __future__ import annotations

import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.windows_witness.compiler import compile_witness
from tools.windows_witness.runtime import read_json, validate_trace

SPEC = ROOT / "refs/windows_witness_specs/olmsmoother2_case0004_writer_frame_20260718/witness-spec.json"
CASE = "legacy_case_0004_current_aex"
WITNESS = "olmsmoother2-case0004-writer-frame-v1"


def event(prefix: str, stage: str, extra: str = "") -> str:
    return (
        f"{prefix} run_id=smoke-run ae_pid=42 module_base=0x1000 "
        f"aex_sha256=7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7 "
        f"project_bpc=8 renderer=Software case_id={CASE} witness_id={WITNESS} "
        f"stage={stage} {extra}"
    ).strip()


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        package, archive = compile_witness(SPEC, root / "package", root / "package.zip")
        contract = read_json(package / "witness-contract.json")
        assert archive.is_file()
        assert (package / "request" / "input" / "case_0004_before_effects.png").is_file()
        probe = (package / "cdb" / f"000_{CASE}.cdb.in").read_text(encoding="ascii")
        assert "dwo(@rsp+0x34)==1903" in probe
        assert "dwo(@rsp+0x38)==519" in probe
        assert "hook_rva=3510" in probe
        assert "hook_rva=3610" in probe
        assert "writer_frame_rgba_f32_bits=0x%08x,0x%08x,0x%08x,0x%08x" in probe
        assert "packed_pf8_raw=0x%08x" in probe
        assert "pf8_raw_bytes_le=%u,%u,%u,%u" in probe
        assert "&&" not in probe

        common = dict(run_id="smoke-run", ae_pid=42, module_base="0x1000")
        trace = "\n".join(
            [
                event(
                    "S2_WRITER_FLOAT4",
                    "writer_float4",
                    "hook_rva=3510 x=1903 y=519 "
                    "writer_frame_rgba_f32_bits=0x3f4ee969,0x3f4ee969,0x3f4ee969,0x3ee2154a "
                    "typed_f32=1 same_run_key=writer-frame-1903-519",
                ),
                event(
                    "S2_PF8_STORE",
                    "pf8_store",
                    "hook_rva=3610 x=1903 y=519 store_addr=0x2000 "
                    "packed_pf8_raw=0xe8e8e871 pf8_raw_bytes_le=113,232,232,232 "
                    "typed_argb8=1 same_run_key=writer-frame-1903-519",
                ),
            ]
        ) + "\n"
        answered = validate_trace(contract, trace, common)
        assert answered["status"] == "answered", answered

        failed = validate_trace(contract, trace.replace("hook_rva=3610", "hook_rva=360f"), common)
        assert failed["status"] == "exact_bind_failure"
        wrong_xy = validate_trace(contract, trace.replace("x=1903", "x=1902", 1), common)
        assert wrong_xy["status"] == "exact_bind_failure"
        split_run = validate_trace(contract, trace.replace("run_id=smoke-run", "run_id=other-run", 1), common)
        assert split_run["status"] == "exact_bind_failure"

    print("[OK] OLMSmoother2 case_0004 writer-frame witness smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
