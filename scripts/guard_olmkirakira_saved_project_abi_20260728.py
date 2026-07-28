#!/usr/bin/env python3
"""Fail-closed OLMKiraKira saved-project parameter compatibility gate.

This is an offline transfer guard.  It does not change either plug-in.  The
Windows ABI below is deliberately literal: ordering and disk IDs are saved
project data, not UI decoration.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


MATCH_PREFIX = "OLM OLM Kira Kira-"
RAMP_PAYLOAD_SUPPORTED = False


@dataclass(frozen=True)
class AbiRow:
    order: int
    disk_id: int
    name: str
    kind: str

    @property
    def match_name(self) -> str:
        return f"{MATCH_PREFIX}{self.disk_id:04d}"


# Exact Windows plug-in row order.  AE's Effect Opacity and GPU Rendering
# built-ins are intentionally outside this 40-row plug-in ABI.
WINDOWS_ABI: tuple[AbiRow, ...] = (
    AbiRow(1, 8, "Channel", "mapped"), AbiRow(2, 9, "Blur Mode", "mapped"),
    AbiRow(3, 17, "Merge mode", "mapped"), AbiRow(4, 10, "Approximated Input", "mapped"),
    AbiRow(5, 2, "Brightness Gain", "mapped"), AbiRow(6, 11, "Strength multiplier", "mapped"),
    AbiRow(7, 27, "Fade Out", "mapped"), AbiRow(8, 7, "Glow Opacity", "mapped"),
    AbiRow(9, 12, "Source Opacity", "mapped"), AbiRow(10, 3, "Vertical Length", "mapped"),
    AbiRow(11, 13, "Vertical Color", "mapped"),
    AbiRow(12, 29, "Vertical Color Ramp", "ramp_label"),
    AbiRow(13, 18, "Use Ramp", "mapped"), AbiRow(14, 19, "Ramp", "ramp_payload"),
    AbiRow(15, 30, "", "separator"),
    AbiRow(16, 4, "Horizontal Length", "mapped"), AbiRow(17, 14, "Horizontal Color", "mapped"),
    AbiRow(18, 31, "Horizontal Color Ramp", "ramp_label"),
    AbiRow(19, 20, "Use Ramp", "mapped"), AbiRow(20, 21, "Ramp", "ramp_payload"),
    AbiRow(21, 32, "", "separator"),
    AbiRow(22, 5, "Diagonal Length", "mapped"), AbiRow(23, 15, "Diagonal Color", "mapped"),
    AbiRow(24, 33, "Diagonal Color Ramp", "ramp_label"),
    AbiRow(25, 22, "Use Ramp", "mapped"), AbiRow(26, 23, "Ramp", "ramp_payload"),
    AbiRow(27, 34, "", "separator"),
    AbiRow(28, 26, "Diagonal 2 length", "mapped"), AbiRow(29, 28, "Diagonal Color2", "mapped"),
    AbiRow(30, 37, "Diagonal 2 Color Ramp", "ramp_label"),
    AbiRow(31, 35, "Use Ramp", "mapped"), AbiRow(32, 36, "Ramp", "ramp_payload"),
    AbiRow(33, 38, "", "separator"),
    AbiRow(34, 6, "Highlight Radius", "mapped"), AbiRow(35, 16, "Highlight Color", "mapped"),
    AbiRow(36, 39, "Highlight Color Ramp", "ramp_label"),
    AbiRow(37, 24, "Use Ramp", "mapped"), AbiRow(38, 25, "Ramp", "ramp_payload"),
    AbiRow(39, 40, "", "separator"), AbiRow(40, 1, "Glow Rotation", "mapped"),
)

ABI_BY_MATCH_NAME = {row.match_name: row for row in WINDOWS_ABI}
USE_RAMP_MATCH_NAMES = frozenset(
    row.match_name for row in WINDOWS_ABI if row.name == "Use Ramp"
)
MAPPED_MATCH_NAMES = frozenset(
    row.match_name for row in WINDOWS_ABI if row.kind == "mapped"
)


def _enabled(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return bool(value)


def verify_embedded_abi() -> None:
    if len(WINDOWS_ABI) != 40:
        raise AssertionError("Windows ABI must contain exactly 40 rows")
    if [row.order for row in WINDOWS_ABI] != list(range(1, 41)):
        raise AssertionError("Windows ABI order must be contiguous 1..40")
    if len({row.disk_id for row in WINDOWS_ABI}) != 40:
        raise AssertionError("Windows ABI disk IDs must be unique")
    counts = {kind: sum(row.kind == kind for row in WINDOWS_ABI) for kind in
              ("mapped", "ramp_label", "ramp_payload", "separator")}
    if counts != {"mapped": 25, "ramp_label": 5, "ramp_payload": 5, "separator": 5}:
        raise AssertionError(f"unexpected ABI classification counts: {counts}")


def gate_saved_project(
    rows: Iterable[dict[str, Any]],
    identity: str,
    *,
    allow_partial: bool = False,
) -> dict[str, Any]:
    """Return an explicit accept/reject result and, on success, 25 Mac rows."""
    verify_embedded_abi()
    source = list(rows)
    if identity not in {"match_name", "index"}:
        return _reject("unsupported_identity", "identity must be match_name or index")
    if not source:
        return _reject("empty_transfer", "a saved-project transfer must contain at least one row")

    if identity == "index":
        if len(source) > 11:
            return _reject(
                "index_only_after_row_11",
                "index-only KiraKira transfer is forbidden after Windows row 11",
            )
        for position, item in enumerate(source, start=1):
            source_order = item.get("property_index")
            if not isinstance(source_order, int) or source_order < 1 or source_order > 40:
                return _reject("invalid_property_index", f"invalid Windows row index {source_order!r}")
            if source_order > 11:
                return _reject(
                    "index_only_after_row_11",
                    "index-only KiraKira transfer is forbidden after Windows row 11",
                )
            if source_order != position:
                return _reject(
                    "noncanonical_index_prefix",
                    f"index-only rows must be the unique contiguous prefix 1..N; "
                    f"row {position} carries property_index {source_order}",
                )
        candidates = [(WINDOWS_ABI[pos - 1], item)
                      for pos, item in enumerate(source, start=1)]
    else:
        candidates = []
        seen: set[str] = set()
        for item in source:
            match_name = item.get("match_name")
            if not isinstance(match_name, str) or not match_name:
                return _reject("missing_match_name", "every row must carry a non-empty match_name")
            if match_name in seen:
                return _reject("duplicate_match_name", f"duplicate row {match_name}")
            seen.add(match_name)
            abi = ABI_BY_MATCH_NAME.get(match_name)
            if abi is None:
                return _reject("unknown_match_name", f"unknown KiraKira row {match_name}")
            supplied_index = item.get("property_index")
            if supplied_index is not None and supplied_index != abi.order:
                return _reject(
                    "windows_abi_order_mismatch",
                    f"{match_name} must be Windows row {abi.order}, got {supplied_index}",
                )
            candidates.append((abi, item))

    enabled_ramps = [
        abi.match_name for abi, item in candidates
        if abi.match_name in USE_RAMP_MATCH_NAMES and _enabled(item.get("value"))
    ]
    if enabled_ramps and not RAMP_PAYLOAD_SUPPORTED:
        return _reject(
            "ramp_payload_unsupported",
            "ramp-enabled saved projects are blocked until opaque 0x144-byte payload support exists",
            enabled_ramps=enabled_ramps,
        )

    present_mapped = {abi.match_name for abi, _item in candidates if abi.kind == "mapped"}
    if not present_mapped:
        return _reject("no_mapped_rows", "transfer contains no safely mappable parameter rows")
    missing_mapped = sorted(MAPPED_MATCH_NAMES - present_mapped)
    if identity == "match_name" and missing_mapped and not allow_partial:
        return _reject(
            "incomplete_mapped_surface",
            "full saved-project transfer requires all 25 mapped match-name rows; "
            "use explicit partial-transfer opt-in only for a deliberately bounded update",
            missing_match_names=missing_mapped,
        )

    mapped = [
        {
            "match_name": abi.match_name,
            "disk_id": abi.disk_id,
            "name": abi.name,
            "value": item.get("value"),
        }
        for abi, item in candidates if abi.kind == "mapped"
    ]
    return {
        "status": "accepted",
        "code": "safe_match_name_mapping" if identity == "match_name" else "bounded_index_prefix",
        "mapped_rows": mapped,
        "mapped_count": len(mapped),
        "ramp_payload_supported": RAMP_PAYLOAD_SUPPORTED,
    }


def _reject(code: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "status": "rejected",
        "code": code,
        "reason": reason,
        "mapped_rows": [],
        "mapped_count": 0,
        "ramp_payload_supported": RAMP_PAYLOAD_SUPPORTED,
        **extra,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_json", type=Path, help="JSON object containing a rows array")
    parser.add_argument("--identity", choices=("match_name", "index"), default="match_name")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="permit an explicitly bounded match-name subset instead of all 25 mapped rows",
    )
    args = parser.parse_args()
    document = json.loads(args.project_json.read_text(encoding="utf-8"))
    result = gate_saved_project(
        document.get("rows", []),
        args.identity,
        allow_partial=args.allow_partial,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "accepted" else 2


if __name__ == "__main__":
    raise SystemExit(main())
