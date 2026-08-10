#!/usr/bin/env python3
"""Pin why exported PF_Cmd_RENDER cannot own the full DG numerical pipeline."""
import hashlib, json, os, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/DistanceGradation.aex"
AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
PROBE = ROOT / "tools/emulation/probe_olmdistancegradation_pf16_smart_sequence_20260805.py"
PYTHON = ROOT / "tools/emulation/.venv/bin/python"
ASM = ROOT / "disasm/DistanceGradation.aex.asm.txt"
REPORT = ROOT / "refs/conformance/olmdistancegradation_exported_render_owner_boundary_20260811.json"
DOC = ROOT / "refs/conformance/olmdistancegradation_exported_render_owner_boundary_20260811.md"


def run_dispatch(depth):
    env = os.environ.copy()
    env.update({"OLM_DG_SMART_DISPATCH": "1", "OLM_DG_SMART_DEPTH": str(depth)})
    run = subprocess.run([str(PYTHON), str(PROBE)], cwd=ROOT, env=env,
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    payload = json.loads(run.stdout[run.stdout.index("{"):])
    assert payload["failure"] is None and payload["typed_wrapper_reached"]
    capture = payload["smart_capture"]
    assert capture["input_padding_unchanged"] and capture["output_padding_unchanged"]
    wrapper = "0x181170280" if depth == 16 else "0x181170380"
    assert payload["typed_wrapper"] == wrapper
    typed_events = [event for event in payload["events"]
                    if event.get("callback") in ("PF_Iterate8", "PF_Iterate16")]
    assert len(typed_events) == 1 and typed_events[0]["pixels"] == 187
    assert not any(event.get("gate") == "FUN_181174760" for event in payload["events"])
    return {
        "depth": depth,
        "typed_wrapper": wrapper,
        "iterate_callback": typed_events[0]["callback"],
        "compose_callback": typed_events[0]["guest_callback"],
        "pixels": typed_events[0]["pixels"],
        "input_rowbytes": capture["input_rowbytes"],
        "output_rowbytes": capture["output_rowbytes"],
        "active_sha256": capture["active_sha256"],
        "input_padding_unchanged": capture["input_padding_unchanged"],
        "output_padding_unchanged": capture["output_padding_unchanged"],
        "preseeded_field_bytes": len(bytes.fromhex(capture["field_seed_active_hex"])),
        "fieldgen_reached_from_exported_render": False,
    }


def main():
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    asm = ASM.read_text()
    required = [
        "181174da9  MOV R8,qword ptr [R10]",
        "181174db6  TEST byte ptr [R9 + 0x10],0x1",
        "181174df1  CALL 0x181170280",
        "181174e31  CALL 0x181170380",
    ]
    assert all(line in asm for line in required)
    pf8 = run_dispatch(8)
    pf16 = run_dispatch(16)
    report = {
        "schema": "olmdistancegradation.exported-render-owner-boundary/1",
        "status": "blocked_by_actual_aex_architecture",
        "aex_sha256": AEX_SHA256,
        "exported_entry": "0x181174bd0",
        "command": "PF_Cmd_RENDER (0x0b)",
        "dynamic_dispatches": [pf8, pf16],
        "static_dispatch": {
            "selector": "output world byte +0x10 bit 0",
            "bit_set": "FUN_181170280 / PF16 typed compose",
            "bit_clear": "FUN_181170380 / PF8 typed compose",
            "pf32_target": None,
            "fieldgen_target": None,
            "verified_instructions": required,
        },
        "required_precondition": "the output world active pixels already contain the typed field consumed from the green lane; the exported command does not generate or resize that field",
        "requested_representatives": {
            "PF8 Mode4 median": "cannot be distinguished at exported command 0x0b; Blur Mode is upstream of this typed compose owner",
            "PF16 Linear+BG+Gaussian": "cannot be generated at exported command 0x0b; a preseeded PF16 field is required",
            "PF32 Linear+Gaussian": "not dispatched by exported command 0x0b",
        },
        "minimum_missing_host_relation": [
            "the AE-owned or sequence-owned call that runs FUN_181170ff0/sibling field staging before command 0x0b",
            "the exact transfer of that staged world into command 0x0b's output-world argument",
            "for PF32, the host route that calls whole owner FUN_181172a10 because command 0x0b has no PF32 branch",
        ],
        "production_comparison": "not performed: Mac EffectMain PF_Cmd_RENDER owns field generation, while the actual exported command owns only typed composition; comparing them as the same route would manufacture a false equivalence",
        "forbidden_workarounds": [
            "call the numerical helpers separately and label that exported-owner coverage",
            "reuse the PF16 branch for PF32",
            "treat a probe-supplied field seed as AEX host staging evidence",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(
        "# OLMDistanceGradation exported Render owner boundary\n\n"
        "Status: **blocked by the actual AEX architecture**, not by a pixel mismatch.\n\n"
        "The hash-pinned exported entry `0x181174bd0` was executed at `PF_Cmd_RENDER` "
        "for PF8 and PF16. It selects `FUN_181170380` or `FUN_181170280` solely from "
        "output-world byte `+0x10` bit 0, then invokes 187 typed compose callbacks. Both "
        "runs preserve padded input/output rows. Neither run reaches field generation "
        "`FUN_181174760`; the output world must already contain the typed field in its "
        "green lane. Static dispatch contains no PF32 target.\n\n"
        "Therefore PF8 Mode 4 median and PF16 Linear + Background + Gaussian cannot be "
        "distinguished or generated by exported command `0x0b`; those parameters belong "
        "to the upstream field-staging owner. PF32 Linear + Gaussian cannot enter this "
        "command at all and instead requires the host route to whole owner `FUN_181172a10`.\n\n"
        "A true end-to-end comparison needs the missing host/sequence relation that stages "
        "the field and transfers that world into command `0x0b`, plus the separate PF32 "
        "host route. Supplying a field seed inside the probe proves typed composition only "
        "and is not promoted to host-staging evidence. No AEXCompat change was made.\n"
    )
    print("PASS_OLMDISTANCEGRADATION_EXPORTED_RENDER_OWNER_BOUNDARY_PINNED")


if __name__ == "__main__":
    raise SystemExit(main())
