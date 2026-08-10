#!/usr/bin/env python3
"""Fresh actual-AEX GLOBAL/PARAMS_SETUP gate for KiraKira's 40 owned rows."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
MAC = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
STRINGS = ROOT / "mac/OLMKiraKira/OLMKiraKira_Strings.cpp"
REPORT = ROOT / "refs/conformance/olmkirakira_ui_setup_actual_aex_20260806.json"
ENTRY = 0x181155F20
CTOR = 0x1811513A0
VTABLE = 0x18148DB50
SHA = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"


EXPECTED = [
    (8, 7, "Channel"), (9, 7, "Blur Mode"), (17, 7, "Merge mode"),
    (10, 4, "Approximated Input"), (2, 10, "Brightness Gain"),
    (11, 1, "Strength multiplier"), (27, 10, "Fade Out"),
    (7, 1, "Glow Opacity"), (12, 1, "Source Opacity"),
    (3, 1, "Vertical Length"), (13, 5, "Vertical Color"),
    (29, 13, "Vertical Color Ramp"), (18, 4, "Use Ramp"), (19, 11, "Ramp"), (30, 14, ""),
    (4, 1, "Horizontal Length"), (14, 5, "Horizontal Color"),
    (31, 13, "Horizontal Color Ramp"), (20, 4, "Use Ramp"), (21, 11, "Ramp"), (32, 14, ""),
    (5, 1, "Diagonal Length"), (15, 5, "Diagonal Color"),
    (33, 13, "Diagonal Color Ramp"), (22, 4, "Use Ramp"), (23, 11, "Ramp"), (34, 14, ""),
    (26, 1, "Diagonal 2 length"), (28, 5, "Diagonal Color2"),
    (37, 13, "Diagonal 2 Color Ramp"), (35, 4, "Use Ramp"), (36, 11, "Ramp"), (38, 14, ""),
    (6, 1, "Highlight Radius"), (16, 5, "Highlight Color"),
    (39, 13, "Highlight Color Ramp"), (24, 4, "Use Ramp"), (25, 11, "Ramp"), (40, 14, ""),
    (1, 3, "Glow Rotation"),
]


def u32(blob: bytes, offset: int) -> int:
    return struct.unpack_from("<I", blob, offset)[0]


def run_actual() -> tuple[dict[str, int], list[dict[str, object]]]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    callbacks = lambda name, fn: loader.install_callback(name, fn)
    allocations: dict[int, int] = {}

    def new_handle(current: AexLoader, args: list[int]) -> int:
        pointer = current.host_alloc(args[0])
        current.write_bytes(pointer, bytes(args[0]))
        allocations[pointer] = args[0]
        return pointer

    def lock_handle(_current: AexLoader, args: list[int]) -> int:
        return args[0]

    zero = lambda _current, _args: 0
    handles = loader.host_alloc(48)
    loader.write_bytes(handles, struct.pack("<6Q",
        callbacks("new", new_handle), callbacks("lock", lock_handle),
        callbacks("unlock", zero), callbacks("dispose", zero),
        callbacks("size", lambda _current, args: allocations.get(args[0], 0)),
        callbacks("resize", zero)))

    registrations: list[dict[str, object]] = []

    def register_with_aegp(current: AexLoader, args: list[int]) -> int:
        registrations.append({
            "global_refcon": args[0],
            "plugin_name": cstr(args[1]),
        })
        current.write_bytes(args[2], struct.pack("<i", 42))
        return 0

    utility = loader.host_alloc(0x50)
    loader.write_bytes(utility, bytes(0x50))
    loader.write_bytes(utility + 0x48, struct.pack("<Q", callbacks(
        "register_with_aegp", register_with_aegp)))

    def cstr(address: int, limit: int = 256) -> str:
        return loader.read_bytes(address, limit).split(b"\0", 1)[0].decode("ascii")

    def acquire(current: AexLoader, args: list[int]) -> int:
        suite = utility if cstr(args[0]) == "AEGP Utility Suite" else handles
        current.write_bytes(args[2], struct.pack("<Q", suite))
        return 0

    provider = loader.host_alloc(16)
    loader.write_bytes(provider, struct.pack("<2Q", callbacks("acquire", acquire), callbacks("release", zero)))
    in_data, out_data = loader.host_alloc(0x200), loader.host_alloc(0x300)
    loader.write_bytes(in_data, bytes(0x200)); loader.write_bytes(out_data, bytes(0x300))
    loader.write_bytes(in_data + 0x180, struct.pack("<Q", provider))

    global_result = loader.call_function(ENTRY, [1, in_data, out_data, 0, 0, 0], max_instructions=500_000)
    assert global_result["rax"] == 0
    global_setup = {
        "my_version": u32(loader.read_bytes(out_data, 0x300), 0),
        "out_flags": u32(loader.read_bytes(out_data, 0x300), 0x60),
        "out_flags2": u32(loader.read_bytes(out_data, 0x300), 0x190),
        "aegp_registrations": registrations,
    }

    # PARAMS_SETUP uses the already-proven concrete owner object. Its string-copy
    # callback is part of PF_InData's host callbacks, not a manifest.
    def copy_string(current: AexLoader, args: list[int]) -> int:
        value = current.read_bytes(args[1], 256).split(b"\0", 1)[0]
        current.write_bytes(args[0], value + b"\0")
        return args[0]

    utils = loader.host_alloc(0x160)
    loader.write_bytes(utils, bytes(0x160))
    loader.write_bytes(utils + 0x150, struct.pack("<Q", callbacks("copy_string", copy_string)))
    loader.write_bytes(in_data + 0xB0, struct.pack("<Q", utils))
    loader.write_bytes(in_data + 0xB8, struct.pack("<Q", 0x1234))
    custom_ui_registrations: list[dict[str, object]] = []

    def register_custom_ui(current: AexLoader, args: list[int]) -> int:
        words = list(struct.unpack("<10i", current.read_bytes(args[1], 40)))
        custom_ui_registrations.append({
            "effect_ref": args[0],
            "words": words,
        })
        return 0

    loader.write_bytes(in_data + 0x28, struct.pack("<Q", callbacks(
        "register_custom_ui", register_custom_ui)))
    effect = loader.host_alloc(0x260)
    loader.write_bytes(effect, bytes(0x260))
    loader.call_function(CTOR, [effect], max_instructions=300_000)
    loader.write_bytes(effect, struct.pack("<Q", VTABLE))
    loader.write_bytes(out_data + 0x28, struct.pack("<Q", effect))
    raw: list[bytes] = []
    loader.write_bytes(in_data + 0x10, struct.pack("<Q", callbacks(
        "add_param", lambda current, args: raw.append(current.read_bytes(args[2], 0xB0)) or 0)))
    setup_result = loader.call_function(ENTRY, [4, in_data, out_data, 0, 0, 0], max_instructions=5_000_000)
    assert setup_result["rax"] == 0 and len(raw) == 40
    assert u32(loader.read_bytes(out_data, 0x300), 0x30) == 41
    global_setup["custom_ui_registrations"] = custom_ui_registrations

    rows = []
    for blob in raw:
        row: dict[str, object] = {
            "disk_id": u32(blob, 0), "ui_flags": u32(blob, 4),
            "ui_width": struct.unpack_from("<H", blob, 8)[0],
            "ui_height": struct.unpack_from("<H", blob, 10)[0],
            "param_type": u32(blob, 12),
            "name": blob[16:48].split(b"\0", 1)[0].decode("ascii"),
            "flags": u32(blob, 48),
        }
        kind = row["param_type"]
        if kind == 7:
            row["popup"] = {"choices": struct.unpack_from("<H", blob, 60)[0],
                            "default": struct.unpack_from("<H", blob, 62)[0],
                            "names": cstr(struct.unpack_from("<Q", blob, 64)[0])}
        elif kind == 1:
            row["slider"] = list(struct.unpack_from("<6i", blob, 56))[:1] + list(struct.unpack_from("<5i", blob, 124))
        elif kind == 10:
            row["float_slider"] = list(struct.unpack_from("<5d", blob, 104)) + list(struct.unpack_from("<hh", blob, 144))
        elif kind == 4:
            row["checkbox_default"] = blob[60]
        elif kind == 5:
            row["color_default_raw"] = f"0x{u32(blob, 60):08x}"
        elif kind == 11:
            refcon = struct.unpack_from("<Q", blob, 80)[0]
            row["arbitrary"] = {"id": struct.unpack_from("<h", blob, 56)[0],
                                "default_size": allocations[struct.unpack_from("<Q", blob, 64)[0]],
                                "refcon_nonnull": refcon != 0,
                                "refcon_effect_delta": refcon - effect}
        elif kind == 3:
            row["angle"] = list(struct.unpack_from("<4i", blob, 56))
        rows.append(row)
    return global_setup, rows


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == SHA
    global_setup, rows = run_actual()
    assert global_setup == {
        "my_version": 0x00190000,
        "out_flags": 0x02008040,
        "out_flags2": 0x08001400,
        "aegp_registrations": [{"global_refcon": 0, "plugin_name": "OLM Kira Kira"}],
        "custom_ui_registrations": [{
            "effect_ref": 0x1234,
            "words": [0, 4, 0, 0, 0, 0, 0, 0, 0, 0],
        }],
    }
    assert [(r["disk_id"], r["param_type"], r["name"]) for r in rows] == EXPECTED
    assert [r["popup"] for r in rows[:3]] == [
        {"choices": 6, "default": 1, "names": "Alpha|Luminance|RGB|Brightness"},
        {"choices": 3, "default": 2, "names": "Box|Approximated Gaussian|Gaussian|Exponential"},
        {"choices": 2, "default": 1, "names": "premultiply|add"},
    ]
    ramp_rows = [r for r in rows if r["param_type"] == 11]
    assert len(ramp_rows) == 5
    assert all(r["name"] == "Ramp" and r["ui_width"] == 310 and r["ui_height"] == 170 for r in ramp_rows)
    assert all(r["ui_flags"] == 0x82 and r["flags"] == 0x60 for r in ramp_rows)
    assert [r["arbitrary"] for r in ramp_rows] == [
        {"id": disk_id, "default_size": 0x260, "refcon_nonnull": True,
         "refcon_effect_delta": 0x200}
        for disk_id in (19, 21, 23, 36, 25)]

    mac = MAC.read_text(encoding="utf-8")
    strings = STRINGS.read_text(encoding="utf-8")
    assert 'std::strncpy(def.name, "Ramp", sizeof(def.name) - 1);' in mac
    assert "PF_PUI_CONTROL | PF_PUI_DONT_ERASE_CONTROL" in mac
    assert "PF_ParamFlag_SUPERVISE | PF_ParamFlag_START_COLLAPSED" in mac
    assert "def.u.arb_d.refconPV = const_cast<char *>(&ramp_handler_refcon);" in mac
    assert 'AEGP_RegisterWithAEGP(\n\t\tnullptr, "OLM Kira Kira", &plugin_id)' in mac
    assert "PF_REGISTER_UI(in_data, &custom_ui)" in mac
    assert '"Premultiply Add|Add"' not in strings
    assert '"premultiply|add"' in strings
    assert "PF_Cmd_EVENT" in mac and "PF_EO_HANDLED_EVENT" in mac and "PF_InvalidateRect" in mac

    report = {
        "schema": "olmkirakira-ui-setup-actual-aex/1", "status": "exact",
        "aex_sha256": SHA, "entry_point": hex(ENTRY), "global_setup": global_setup,
        "params_setup": {"return_code": 0, "num_params_including_input": 41, "rows": rows},
        "fixed_mac_mismatch": {
            "before": {
                "name": "", "ui_flags": "0x12", "flags": "0x40",
                "aegp_registration": False, "custom_ui_registration": False,
                "ramp_refcon": None,
            },
            "after": {
                "name": "Ramp", "ui_flags": "0x82", "flags": "0x60",
                "aegp_registration": "OLM Kira Kira",
                "custom_ui_registration_words": [0, 4, 0, 0, 0, 0, 0, 0, 0, 0],
                "ramp_refcon": "one stable opaque address shared by five rows",
            },
        },
        "event_contract": (
            "PF_Cmd_EVENT + handled/update-now + invalidate retained; AE 26.3.0.87 arm64 "
            "live Drawbot expansion and click insertion passed on 2026-08-10"
        ),
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_UI_SETUP_ACTUAL_AEX_20260806 rows=40 ramps=5 global=exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
