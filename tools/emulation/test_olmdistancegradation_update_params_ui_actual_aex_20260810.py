#!/usr/bin/env python3
"""Exact DistanceGradation UPDATE_PARAMS_UI matrix: actual AEX vs Mac source."""

from __future__ import annotations

import hashlib
import itertools
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_RSP

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "plugins_2025/DistanceGradation.aex"
AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
ENTRY = 0x181174BD0
HARNESS = ROOT / "tools/emulation/olmdistancegradation_update_params_ui_production_harness_20260810.cpp"
REPORT = ROOT / "refs/conformance/olmdistancegradation_update_params_ui_actual_aex_20260810.json"
MARKDOWN = REPORT.with_suffix(".md")
CASES = list(itertools.product(range(1, 5), range(1, 4), range(1, 3), range(2), range(1, 4)))


def qword(loader: AexLoader, address: int, value: int) -> None:
    loader.write_bytes(address, struct.pack("<Q", value))


def run_actual(case: tuple[int, int, int, int, int]) -> list[list[int]]:
    interp, in_out, render, use_bg, blur = case
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    effect_ref, effect, layer = (loader.host_alloc(8) for _ in range(3))

    def install(name, callback):
        return loader.install_callback(name, callback)

    pf_suite = loader.host_alloc(0x10)
    qword(loader, pf_suite, install("PF/from ref", lambda current, args: qword(current, args[1], effect_ref) or 0))
    qword(loader, pf_suite + 8, install("PF/to effect", lambda current, args: qword(current, args[2], effect) or 0))
    layer_suite = loader.host_alloc(0x78)
    qword(loader, layer_suite + 0x70, install("Layer/get", lambda current, args: qword(current, args[2], layer) or 0))
    effect_suite = loader.host_alloc(0x48)
    qword(loader, effect_suite + 0x40, install("Effect/dispose", lambda _current, _args: 0))

    updates: list[list[int]] = []

    def update(current, args):
        updates.append([int(args[1]), struct.unpack("<I", current.read_bytes(args[2] + 4, 4))[0]])
        return 0

    param_suite = loader.host_alloc(8)
    qword(loader, param_suite, install("ParamUtils/update", update))
    suites = {
        "AEGP PF Interface Suite": pf_suite,
        "AEGP Layer Suite": layer_suite,
        "AEGP Effect Suite": effect_suite,
        "PF Param Utils Suite": param_suite,
    }

    def acquire(current, args):
        name = current.read_bytes(args[0], 80).split(b"\0", 1)[0].decode("ascii")
        assert name in suites, name
        qword(current, args[2], suites[name])
        return 0

    basic = loader.host_alloc(16)
    qword(loader, basic, install("AcquireSuite", acquire))
    qword(loader, basic + 8, install("ReleaseSuite", lambda _current, _args: 0))

    values = {9: interp, 2: in_out, 5: render, 6: use_bg, 11: blur}

    def checkout(current, args):
        blob = bytearray(0xB0)
        struct.pack_into("<I", blob, 4, 0xA5)
        struct.pack_into("<i", blob, 0x38, values.get(int(args[1]), 0))
        rsp = current.uc.reg_read(UC_X86_REG_RSP)
        output = struct.unpack("<Q", current.read_bytes(rsp + 0x30, 8))[0]
        current.write_bytes(output, bytes(blob))
        return 0

    in_data, out_data = loader.host_alloc(0x200), loader.host_alloc(0x300)
    loader.write_bytes(in_data, bytes(0x200))
    loader.write_bytes(out_data, bytes(0x300))
    qword(loader, in_data, install("checkout_param", checkout))
    qword(loader, in_data + 8, install("checkin_param", lambda _current, _args: 0))
    qword(loader, in_data + 0xB8, effect_ref)
    qword(loader, in_data + 0x180, basic)
    result = loader.call_function(ENTRY, [14, in_data, out_data, 0, 0, 0], max_instructions=500_000)
    assert result["rax"] == 0
    return updates


def build_production(directory: Path) -> Path:
    executable = directory / "probe"
    command = [
        "xcrun", "clang++", "-std=c++17", "-O2", "-D__MACH__", "-Wno-pragma-pack",
        "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", str(HARNESS),
        "mac/OLMDistanceGradation/OLMDistanceGradation_Strings.cpp",
        "core/olmdistancegradation_fieldgen.cpp", "Util/AEGP_SuiteHandler.cpp",
        "Util/MissingSuiteError.cpp", "-framework", "Cocoa", "-o", str(executable),
    ]
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert build.returncode == 0, build.stderr
    return executable


def run_production(executable: Path, case: tuple[int, int, int, int, int]) -> list[list[int]]:
    run = subprocess.run([str(executable), *map(str, case)], cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    return [[int(field) for field in item.split(":")] for item in run.stdout.strip().split(",")]


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    rows = []
    payload = bytearray()
    with tempfile.TemporaryDirectory(prefix="olmdg_update_ui_") as raw:
        executable = build_production(Path(raw))
        for case in CASES:
            actual = run_actual(case)
            production = run_production(executable, case)
            assert actual == production
            assert [index for index, _ in actual] == [10, 4, 3, 7, 8, 12]
            assert all(flag in (0, 0x20) for _, flag in actual)
            payload.extend(flag for _, flag in actual)
            rows.append({"values": list(case), "updates": actual})
    digest = hashlib.sha256(payload).hexdigest()
    report = {
        "schema": "olmdistancegradation-update-params-ui-actual-aex/1",
        "status": "exact",
        "aex_sha256": AEX_SHA256,
        "entry_point": hex(ENTRY),
        "command": 14,
        "case_axes": ["interp_mode", "in_out", "render_mode", "use_bg", "blur_mode"],
        "case_count": len(rows),
        "update_order": [10, 4, 3, 7, 8, 12],
        "disabled_bit": 0x20,
        "rules": {
            "power_10": "disabled iff interp_mode != 4",
            "outside_threshold_4": "disabled iff in_out == 1",
            "inside_threshold_3": "disabled iff in_out == 2",
            "gradient_color_7": "disabled iff render_mode != 1",
            "background_color_8": "disabled iff use_bg == 0",
            "blur_size_12": "disabled iff blur_mode == 1",
        },
        "payload_sha256": digest,
        "cases": rows,
        "scope": "All 144 public-range combinations of the five controlling parameters through the exported Windows command-14 entry and Mac EffectMain(PF_Cmd_UPDATE_PARAMS_UI). Exact update order, indices, and ui_flags 0/0x20.",
        "not_proven": ["native AE visual redraw timing", "host callback error propagation", "out-of-range popup values"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MARKDOWN.write_text(
        "# OLMDistanceGradation UPDATE_PARAMS_UI actual-AEX parity\n\n"
        f"- Status: exact\n- Cases: {len(rows)} (complete public-range Cartesian product)\n"
        f"- Actual AEX SHA-256: `{AEX_SHA256}`\n- Observable payload SHA-256: `{digest}`\n\n"
        "The exported Windows command-14 entry and Mac production `EffectMain` emit the same six "
        "`PF_UpdateParamUI` calls, in order `[10, 4, 3, 7, 8, 12]`, with each copied parameter's "
        "`ui_flags` replaced by exactly `0` or `PF_PUI_DISABLED (0x20)`. The JSON report records all cases.\n\n"
        "Boundaries: native AE redraw timing, callback-error injection, and values outside popup ranges are not claimed.\n",
        encoding="utf-8",
    )
    print(f"PASS_OLMDISTANCEGRADATION_UPDATE_PARAMS_UI_ACTUAL_AEX_20260810 cases={len(rows)} exact=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
