#!/usr/bin/env python3
"""Bounded local actual-AEX replay of the legacy case_0012 tuple.

This deliberately proves only execution of the checked-in AEX against the
checked-in host-trace tuple.  It does not assert Windows or After Effects
truth, and it does not compare against the production Mac implementation.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from aex_loader import AexLoader  # noqa: E402
from test_smoother2_fullchain_diff import (  # noqa: E402
    FC280,
    FCCE0,
    call_cce0_entry,
    call_c280_entry,
)
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402

LOG_PATH = ROOT / "refs/conformance/olmsmoother2_case0012_class_neighborhood_20260712.log"
TARGET_RE = re.compile(
    r"stage=input_setup pixel_bytes=(?P<pixel_bytes>\d+) xy=(?P<x>\d+),(?P<y>\d+) "
    r"raw=(?P<raw>[0-9,]+) setup=(?P<setup>[0-9.,-]+) class=(?P<class>[0-9,]+) "
    r"range=(?P<range>\d+) version=(?P<version>\d+) gamma=(?P<gamma>\d+)"
)
NEIGHBOR_RE = re.compile(
    r"class_neighbor xy=(?P<x>\d+),(?P<y>\d+) offset=(?P<dx>-?\d+),(?P<dy>-?\d+) "
    r"class=(?P<class>[0-9,]+) setup=(?P<setup>[0-9.eE+,-]+)"
)
PARAM_RE = re.compile(
    r"params smoothness=(?P<smoothness>[0-9.eE+-]+) extra=(?P<extra>[0-9.eE+-]+) "
    r"gamma_value=(?P<gamma_value>[0-9.eE+-]+) gamma_count=(?P<gamma_count>\d+) "
    r"gamma0=(?P<gamma0>[0-9.,-]+)"
)


def floats(text: str) -> list[float]:
    return [float(value) for value in text.split(",")]


def ints(text: str) -> list[int]:
    return [int(value) for value in text.split(",")]


def parse_log(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    target = next((TARGET_RE.fullmatch(line) for line in lines if line.startswith("stage=input_setup ")), None)
    params = next((PARAM_RE.fullmatch(line) for line in lines if line.startswith("params ")), None)
    neighbors = [NEIGHBOR_RE.fullmatch(line) for line in lines if line.startswith("class_neighbor ")]
    if target is None or params is None or len(neighbors) != 25 or any(item is None for item in neighbors):
        raise ValueError("required target, params, and exactly 25 neighborhood records are not all present")
    target_data = target.groupdict()
    if target_data["pixel_bytes"] != "4" or target_data["range"] != "88" or target_data["version"] != "2":
        raise ValueError("input_setup metadata does not match the grounded 8bpc/version-2 tuple")
    parsed_neighbors = []
    offsets = set()
    for item in neighbors:
        data = item.groupdict()
        offset = (int(data["dx"]), int(data["dy"]))
        offsets.add(offset)
        classes = ints(data["class"])
        setup = floats(data["setup"])
        if len(classes) != 4 or len(setup) != 4:
            raise ValueError(f"malformed neighborhood tuple at offset {offset}")
        parsed_neighbors.append({"offset": offset, "class": classes, "setup": setup})
    if offsets != {(dx, dy) for dy in range(-2, 3) for dx in range(-2, 3)}:
        raise ValueError("neighborhood offsets are not the exact 5x5 range -2..2")
    p = params.groupdict()
    gamma0 = floats(p["gamma0"])
    if len(gamma0) != 4 or int(p["gamma_count"]) != 5:
        raise ValueError("gamma metadata is not the grounded case_0012 shape")
    return {
        "source": str(path.relative_to(ROOT)),
        "target_xy": [int(target_data["x"]), int(target_data["y"])],
        "target_raw": ints(target_data["raw"]),
        "target_setup": floats(target_data["setup"]),
        "target_class": ints(target_data["class"]),
        "pixel_bytes": int(target_data["pixel_bytes"]),
        "range": int(target_data["range"]),
        "version": int(target_data["version"]),
        "gamma_mode_logged": int(target_data["gamma"]),
        "neighbors": sorted(parsed_neighbors, key=lambda row: (row["offset"][1], row["offset"][0])),
        "params": {
            "smoothness": float(p["smoothness"]),
            "extra": float(p["extra"]),
            "gamma_value": float(p["gamma_value"]),
            "gamma_count": int(p["gamma_count"]),
            "gamma0": gamma0,
        },
    }


def replay(tuple_data: dict) -> dict:
    # The local origin is intentionally unrelated to the host image address.
    origin = (8, 8)
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls()
    ss = SmootherStruct(loader, 16, 16)
    ss.set_cur(*origin)
    ss.set_smoothness(tuple_data["params"]["smoothness"])
    ss.set_base_weight(tuple_data["params"]["extra"])
    ss.set_src_pixel(*origin, tuple(tuple_data["target_setup"]))
    for row in tuple_data["neighbors"]:
        dx, dy = row["offset"]
        ss.set_src_pixel(origin[0] + dx, origin[1] + dy, tuple(row["setup"]))
        ss.set_class_pixel(origin[0] + dx, origin[1] + dy, *row["class"])

    # c280/cce0 descriptor ABI copied from test_smoother2_fullchain_diff.py.
    c280 = call_c280_entry(loader, ss, *origin)
    cce0 = call_cce0_entry(loader, ss, *origin, gamma_colors=False)
    return {
        "local_origin": list(origin),
        "aex_path": str(AEX_PATH.relative_to(ROOT)),
        "entries_executed": [hex(FC280), hex(FCCE0)],
        "c280": c280,
        "cce0_no_gamma_entry": cce0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, default=LOG_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        tuple_data = parse_log(args.log)
        replay_data = replay(tuple_data)
        result = {
            "verdict": "PASS_LOCAL_ACTUAL_AEX_TUPLE_REPLAY",
            "scope": "bounded local AEX binary-semantic evidence only; never Windows/AE truth",
            "grounding": {
                "fixture": "exact 5x5 class/setup neighborhood parsed from the supplied log",
                "host_coordinates": tuple_data["target_xy"],
                "local_coordinates": replay_data["local_origin"],
                "coordinate_mapping": "offset-preserving translation only; no host-image address or frame claim",
                "aex": replay_data["aex_path"],
                "abi": "AexLoader/SmootherStruct plus c280/cce0 descriptor/config scaffolding reused from test_smoother2_fullchain_diff.py",
                "c280_scale_fixed": [65536, 65536],
                "cce0_mode": "no-gamma entry mode 0; logged gamma metadata is reported but not promoted into an ungrounded ABI claim",
            },
            "input_tuple": tuple_data,
            "replay": replay_data,
            "claims_not_made": [
                "No Windows AEX host binding is established.",
                "No After Effects render, pixel packing, or production-plugin truth is established.",
                "No claim is made that the local translated fixture is the live case_0012 memory tuple.",
            ],
        }
    except (OSError, ValueError, RuntimeError, struct.error) as exc:
        result = {
            "verdict": "BLOCKED_UNGROUNDED_REQUIRED_FIELD",
            "scope": "local replay did not execute because required tuple grounding failed",
            "error": str(exc),
            "claims_not_made": ["No Windows/AE truth is claimed."],
        }
        text = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(text, encoding="utf-8")
        print(text, end="")
        return 2
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
