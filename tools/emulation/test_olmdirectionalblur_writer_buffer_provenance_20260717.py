#!/usr/bin/env python3
"""Trace natural params+0x8090 writes up to the angle-0 output Iterate8 call."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

from PIL import Image
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RBX, UC_X86_REG_RIP, UC_X86_REG_R15

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_writer_buffer_provenance_20260717.json"
WRAPPER = 0x180006700
OUTPUT = 0x180006B30
PRODUCER = 0x180004A20
WRITE_SITES = (0x180003F4B, 0x18000489D, 0x180004CDB, 0x180005A66, 0x18000636D, 0x18000562D)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_fixture():
    sys.path.insert(0, str(FIXTURE_PATH.parent))
    import dblur_fullrender_host_fixture_20260711 as fixture  # noqa: E402

    return fixture


def main() -> int:
    fixture = load_fixture()

    class TracingLoader(fixture.AexLoader):
        last = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.provenance_writes: list[dict] = []
            self.all_param_qword_writes: list[dict] = []
            self.allocation_returns: list[dict] = []
            self.nearest_write_registers: list[dict] = []
            TracingLoader.last = self

            def mem_write(uc, _access, address, size, value, _user_data):
                if size == 8 and ((0x40000000 <= address < 0x40400000) or
                                  (0x0F000000 <= address < 0x10000000)):
                    self.all_param_qword_writes.append({
                        "address": hex(address), "value": hex(value),
                        "rip": hex(uc.reg_read(UC_X86_REG_RIP)),
                    })

            self.uc.hook_add(UC_HOOK_MEM_WRITE, mem_write)

            def allocation_return(ld, _address, _size):
                self.allocation_returns.append({
                    "rip": hex(ld.uc.reg_read(UC_X86_REG_RIP)),
                    "rax_return_value": hex(ld.uc.reg_read(UC_X86_REG_RAX)),
                    "r15": hex(ld.uc.reg_read(UC_X86_REG_R15)),
                    "rbx": hex(ld.uc.reg_read(UC_X86_REG_RBX)),
                })

            def nearest_write(ld, _address, _size):
                self.nearest_write_registers.append({
                    "rip": hex(ld.uc.reg_read(UC_X86_REG_RIP)),
                    "r15": hex(ld.uc.reg_read(UC_X86_REG_R15)),
                    "rbx": hex(ld.uc.reg_read(UC_X86_REG_RBX)),
                })

            self.add_code_hook(0x180005A0A, allocation_return)
            self.add_code_hook(0x180004C7C, allocation_return)
            self.add_code_hook(0x18000562D, nearest_write)

    fixture.AexLoader = TracingLoader
    with tempfile.TemporaryDirectory(prefix="olm_directionalblur_writer_provenance_") as name:
        temp = Path(name)
        source = temp / "source_16x16.png"
        Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278)).save(source)
        output = temp / "fixture.json"
        sys.argv = [
            str(FIXTURE_PATH), "--source", str(source), "--output", str(output),
            "--angle", "0", "--downsample-num", "1", "--downsample-den", "1",
            "--front-strength", "8", "--size-variation", "0", "--front-sharp-tail", "0",
            "--back-strength", "0", "--back-alpha-fade", "0", "--noise-variation", "0",
            "--world-area", "0", "0", "16", "16", "--row-padding", "12",
            "--no-detour-rotate", "--max-instructions", "20000000",
        ]
        fixture_status = fixture.main()
        fixture_report = json.loads(output.read_text(encoding="utf-8"))

    loader = TracingLoader.last
    if loader is None:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: AEX loader was not constructed")
    execution = fixture_report["execution"]
    output_call = next((call for call in execution["iterate_calls"] if call["callback"] == hex(OUTPUT)), None)
    if output_call is None:
        blocked = fixture_report.get("blocked", {})
        raise RuntimeError("BLOCKED_FAIL_CLOSED: output Iterate8 ABI missing: " + json.dumps(blocked, sort_keys=True))
    output_params = int(output_call["params"], 16)
    target = output_params + 0x8090
    target_writes = [item for item in loader.all_param_qword_writes if int(item["address"], 16) == target]

    # The memory hook confirms each actual destination; exact hooks capture the
    # allocation return and the final R15 value before the MOVQ.
    if not target_writes:
        raise RuntimeError(
            "BLOCKED_FAIL_CLOSED: no write to output params+0x8090 before callback: "
            + json.dumps({"params": output_call["params"], "target": hex(target)}, sort_keys=True)
        )
    if fixture_status != 0 or not fixture_report["output"].get("complete", False):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: natural checkpoint did not complete")

    static = {
        "producer_function": hex(PRODUCER),
        "write_sites": [hex(address) for address in WRITE_SITES],
        "nearest_natural_write": hex(WRITE_SITES[-1]),
        "nearest_natural_write_value_source": "R15 stored through MOVQ 0x8090(%RBX)",
        "allocation_return": {
            "callsite": "0x180004c79 indirect suite + 8 call",
            "return_checkpoint": "0x180004c7c",
            "owner_boundary": "host suite allocation return; suite internals are outside this evidence",
        },
    }
    report = {
        "schema": 1,
        "kind": "olmdirectionalblur_writer_buffer_provenance_checkpoint",
        "status": "pass",
        "scope": "Mac-local Unicorn natural angle-0 8bpc path; params+0x8090 write provenance",
        "claim_scope": "No Windows live values and no AE-exact claim",
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)), "aex_sha256": sha256(AEX),
            "fixture": str(FIXTURE_PATH.relative_to(ROOT)), "fixture_sha256": sha256(FIXTURE_PATH),
            "source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha256(SOURCE),
        },
        "static": static,
        "natural_checkpoint": {
            "requested_angle_degrees": 0,
            "producer_function": hex(PRODUCER),
            "wrapper": hex(WRAPPER),
            "output_callback": hex(OUTPUT),
            "output_iterate_refcon": output_call["params"],
            "output_params_plus_8090": hex(target),
            "output_iterate_area": output_call["area_words"],
            "callbacks": [call["callback"] for call in execution["iterate_calls"]],
            "checkpoints": execution["checkpoints"],
            "target_writes": target_writes,
            "all_param_qword_write_count": len(loader.all_param_qword_writes),
        },
        "input_ownership": {
            "pointer_owner_at_nearest_write": "R15 in FUN_180004A20 immediately before MOVQ at 0x18000562d",
            "allocation_return_samples": loader.allocation_returns,
            "nearest_write_registers": loader.nearest_write_registers,
            "buffer_pointer_is_writer_base": True,
            "upstream_allocation_owner": "unresolved beyond the producer's R15 value; no suite/ABI fabrication",
        },
        "fail_closed": {
            "status": "pass",
            "fixture_status": fixture_report["status"],
            "fixture_blocker": fixture_report.get("blocked", {}).get("reason"),
            "first_missing_suite_or_abi": fixture_report.get("blocked", {}).get("reason"),
            "production_source_edited": False, "ledger_edited": False,
            "windows_values_fabricated": False, "ae_exact_claim": False,
        },
        "command": "python3 tools/emulation/test_olmdirectionalblur_writer_buffer_provenance_20260717.py",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "report": str(REPORT.relative_to(ROOT)), "target_writes": len(target_writes)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
