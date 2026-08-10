#!/usr/bin/env python3
"""OLMDirectionalBlur UPDATE_PARAMS_UI hidden-stream contract: actual AEX vs Mac source."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RSP

from aex_loader import AexLoader


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMDirectionalBlur/Plugins/64/2025/OLMDirectionalBlur.aex"
AEX_SHA256 = "d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e"
ENTRY = 0x1800083F0
REPORT = ROOT / "refs/conformance/olmdirectionalblur_update_params_ui_actual_aex_20260810.json"
NOISE_TYPES = (0, 1, 2, 3, 4)


def qword(loader: AexLoader, address: int, value: int) -> None:
    loader.write_bytes(address, struct.pack("<Q", value))


def actual(noise_type: int) -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)

    def install(label, handler):
        return loader.install_callback(label, handler)

    pf_ref = loader.host_alloc(8)
    effect = loader.host_alloc(8)
    layer = loader.host_alloc(8)
    layer_stream = loader.host_alloc(8)
    streams = {index: loader.host_alloc(8) for index in range(17, 21)}
    acquisitions: list[list[object]] = []
    checkouts: list[int] = []
    checkins: list[int] = []
    flag_reads: list[int] = []
    flag_sets: list[list[int]] = []
    disposed_streams: list[int] = []
    disposed_effects: list[int] = []

    def pf_get_layer(current, args):
        qword(current, args[1], layer)
        return 0

    def pf_get_effect(current, args):
        qword(current, args[2], effect)
        return 0

    pf_suite = loader.host_alloc(0x10)
    qword(loader, pf_suite, install("PF interface/get layer", pf_get_layer))
    qword(loader, pf_suite + 8, install("PF interface/get effect", pf_get_effect))

    def get_layer_stream(current, args):
        qword(current, args[2], layer_stream)
        return 0

    layer_suite = loader.host_alloc(0x78)
    qword(loader, layer_suite + 0x70, install("Layer/get stream", get_layer_stream))

    def get_effect_stream(current, args):
        index = int(args[2])
        assert index in streams
        qword(current, args[3], streams[index])
        return 0

    def dispose_stream(_current, args):
        disposed_streams.append(int(args[0]))
        return 0

    stream_suite = loader.host_alloc(0x40)
    qword(loader, stream_suite + 0x28, install("Stream/get effect stream", get_effect_stream))
    qword(loader, stream_suite + 0x38, install("Stream/dispose", dispose_stream))

    def get_flags(current, args):
        flag_reads.append(int(args[0]))
        current.write_bytes(args[1], struct.pack("<I", 0xA5A50000))
        return 0

    def set_flag(_current, args):
        flag_sets.append([int(value) for value in args[:4]])
        return 0

    dynamic_suite = loader.host_alloc(0x30)
    qword(loader, dynamic_suite + 0x20, install("Dynamic/get flags", get_flags))
    qword(loader, dynamic_suite + 0x28, install("Dynamic/set flag", set_flag))

    def dispose_effect(_current, args):
        disposed_effects.append(int(args[0]))
        return 0

    effect_suite = loader.host_alloc(0x48)
    qword(loader, effect_suite + 0x40, install("Effect/dispose", dispose_effect))

    suites = {
        "AEGP PF Interface Suite": pf_suite,
        "AEGP Layer Suite": layer_suite,
        "AEGP Stream Suite": stream_suite,
        "AEGP Dynamic Stream Suite": dynamic_suite,
        "AEGP Effect Suite": effect_suite,
    }

    def acquire(current, args):
        name = bytes(current.uc.mem_read(args[0], 80)).split(b"\0", 1)[0].decode("ascii")
        acquisitions.append([name, int(args[1])])
        assert name in suites, name
        qword(current, args[2], suites[name])
        return 0

    basic = loader.host_alloc(16)
    qword(loader, basic, install("AcquireSuite", acquire))
    qword(loader, basic + 8, install("ReleaseSuite", lambda _l, _a: 0))

    def checkout(current, args):
        rsp = current.uc.reg_read(UC_X86_REG_RSP)
        output = struct.unpack("<Q", current.read_bytes(rsp + 0x30, 8))[0]
        checkouts.append(int(args[1]))
        current.write_bytes(output, b"\0" * 0xB0)
        current.write_bytes(output + 0x38, struct.pack("<i", noise_type))
        return 0

    def checkin(_current, args):
        checkins.append(int(args[1]))
        return 0

    in_data = loader.host_alloc(0x200)
    qword(loader, in_data, install("PF checkout param", checkout))
    qword(loader, in_data + 8, install("PF checkin param", checkin))
    qword(loader, in_data + 0xB8, 0x1234)
    qword(loader, in_data + 0x180, basic)
    loader.write_bytes(in_data + 0xE0, struct.pack("<i", 7))
    loader.write_bytes(in_data + 0xE4, struct.pack("<I", 24))

    result = loader.call_function(ENTRY, int_args=[14, in_data, loader.host_alloc(0x200), 0, 0, 0], max_instructions=300_000)
    expected_hidden = {17: noise_type != 3, 18: noise_type == 3, 19: noise_type == 3, 20: noise_type == 3}
    normalized_sets = [[index, int(args[1]), int(args[2]), int(args[3]) & 0xFF]
                       for index, args in ((index, values) for index, values in zip(range(17, 21), flag_sets))]
    assert result["rax"] == 0
    assert checkouts == [16]
    assert len(flag_sets) == 4
    expected_sets = [[index, 2, 0, int(expected_hidden[index])] for index in range(17, 21)]
    assert normalized_sets == expected_sets, (normalized_sets, expected_sets)
    assert disposed_streams == [streams[index] for index in range(17, 21)]
    assert disposed_effects == [effect]
    return {
        "noise_type": noise_type,
        "return_code": result["rax"],
        "checked_out_param_indices": checkouts,
        "checked_in_param_count": len(checkins),
        "hidden_by_param_index": {str(index): expected_hidden[index] for index in range(17, 21)},
        "set_calls": normalized_sets,
        "stream_dispose_order": list(range(17, 21)),
        "effect_dispose_count": len(disposed_effects),
        "suite_acquisitions": acquisitions,
    }


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    cases = {str(value): actual(value) for value in NOISE_TYPES}
    source = (ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp").read_text(encoding="utf-8")
    required = (
        "PF_Cmd_UPDATE_PARAMS_UI",
        "OLMDIRECTIONALBLUR_NOISE_TYPE",
        "OLMDIRECTIONALBLUR_NOISE_LAYER",
        "AEGP_DynStreamFlag_HIDDEN",
        "AEGP_SetDynamicStreamFlag",
    )
    assert all(token in source for token in required)
    report = {
        "schema_version": 1,
        "status": "exact_contract_fixed",
        "plugin": "OLMDirectionalBlur",
        "actual_aex_sha256": AEX_SHA256,
        "actual_exported_entry": hex(ENTRY),
        "command": {"name": "PF_Cmd_UPDATE_PARAMS_UI", "value": 14},
        "selector_param_index": 16,
        "controlled_param_indices": [17, 18, 19, 20],
        "cases": cases,
        "observable_contract": "Noise Type == 3 shows Noise Layer and hides Seed, Noise Offset, and Thickness; every other observed integer does the inverse. Each stream is updated in index order with AEGP_DynStreamFlag_HIDDEN, undoable=false, then disposed; the effect ref is disposed once.",
        "actual_execution_boundary": "The exported actual-AEX command-14 path runs under Unicorn. Only AE host suite callbacks are modeled; the plugin implementation, branch, stream lookup, flag-setting sequence, and cleanup execute unmodified.",
        "production_source": "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
        "not_proven": [
            "native After Effects visible redraw",
            "host failure propagation for individual suite calls",
            "behavior when UPDATE_PARAMS_UI is invoked without a valid effect context",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMDIRECTIONALBLUR_UPDATE_PARAMS_UI_ACTUAL_AEX_20260810 cases=5 streams=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
