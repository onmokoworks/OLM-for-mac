#!/usr/bin/env python3
"""Bounded OLMKiraKira parameter-surface validation contract.

This contract is intentionally about Windows-manifest-to-Mac-surface identity
only. It does not claim production behavior parity or change the Mac plug-in.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
WINDOWS_MANIFEST = ROOT / "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMKiraKira/reference_manifest.json"
MAC_SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
MAC_HEADER = ROOT / "mac/OLMKiraKira/OLMKiraKira.h"
MAC_STRINGS = ROOT / "mac/OLMKiraKira/OLMKiraKira_Strings.cpp"
OUT_JSON = ROOT / "refs/conformance/olmkirakira_parameter_surface_contract_20260717.json"
OUT_MD = ROOT / "refs/conformance/olmkirakira_parameter_surface_contract_20260717.md"
PLUGIN_NAME = "OLM Kira Kira"
PLUGIN_MATCH_NAME = "OLM OLM Kira Kira"
ARTIFACT_DATE = "2026-07-17"
GENERATED_ON = "2026-07-17"


@dataclass(frozen=True)
class MacRow:
    mac_surface_order: int
    label: str
    macro: str
    disk_id_symbol: str
    disk_id: int
    mac_match_name: str
    source_file: str


@dataclass(frozen=True)
class WindowsRow:
    windows_surface_order: int
    property_index: int | None
    name: str
    match_name: str
    property_value_type: str | None
    value: Any

    def request_row(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "match_name": self.match_name,
            "property_index": self.property_index,
            "property_value_type": self.property_value_type,
            "value": self.value,
        }


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def split_top_level(arg_string: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    depth = 0
    in_string = False
    prev = ""
    for ch in arg_string:
        if ch == '"' and prev != "\\":
            in_string = not in_string
        if not in_string:
            if ch in "({[":
                depth += 1
            elif ch in ")}]":
                depth -= 1
            elif ch == "," and depth == 0:
                items.append("".join(current).strip())
                current = []
                prev = ch
                continue
        current.append(ch)
        prev = ch
    tail = "".join(current).strip()
    if tail:
        items.append(tail)
    return items


def load_strings(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    pairs = re.findall(r'\{\s*(StrID_[A-Za-z0-9_]+)\s*,\s*"([^"]*)"\s*\}', text)
    return {key: value for key, value in pairs}


def resolve_label(expr: str, strings: dict[str, str]) -> str:
    match = re.search(r"GetStringPtr\((StrID_[A-Za-z0-9_]+)\)", expr)
    if match:
        return strings.get(match.group(1), match.group(1))
    if expr.startswith('"') and expr.endswith('"'):
        return expr[1:-1]
    return expr


def params_setup_body(source: str) -> str:
    start = source.index("static PF_Err ParamsSetup(")
    end = source.index("out_data->num_params = OLMKIRAKIRA_NUM_PARAMS;", start)
    return source[start:end]


def parse_disk_ids(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8")
    pairs = re.findall(r"([A-Z0-9_]+_DISK_ID)\s*=\s*(\d+)", text)
    if not pairs:
        raise ValueError(f"no disk ids found in {path}")
    return {symbol: int(raw) for symbol, raw in pairs}


def load_mac_surface() -> list[MacRow]:
    strings = load_strings(MAC_STRINGS)
    disk_ids = parse_disk_ids(MAC_HEADER)
    body = params_setup_body(MAC_SOURCE.read_text(encoding="utf-8"))
    pattern = re.compile(r"PF_ADD_([A-Z0-9_]+)\s*\((.*?)\);", re.DOTALL)
    rows: list[MacRow] = []
    for order, match in enumerate(pattern.finditer(body), start=1):
        macro = match.group(1)
        args = split_top_level(match.group(2))
        if not args:
            continue
        disk_id_symbol = args[-1]
        if disk_id_symbol not in disk_ids:
            raise ValueError(f"unknown disk id symbol in ParamsSetup: {disk_id_symbol}")
        label = resolve_label(args[0], strings)
        disk_id = disk_ids[disk_id_symbol]
        rows.append(
            MacRow(
                mac_surface_order=order,
                label=label,
                macro=macro,
                disk_id_symbol=disk_id_symbol,
                disk_id=disk_id,
                mac_match_name=f"{PLUGIN_MATCH_NAME}-{disk_id:04d}",
                source_file=str(MAC_SOURCE.relative_to(ROOT)),
            )
        )
    return rows


def find_kirakira_effect(case: dict[str, Any]) -> dict[str, Any]:
    effects = case.get("effects", [])
    for effect in effects:
        if not isinstance(effect, dict):
            continue
        if effect.get("match_name") == PLUGIN_MATCH_NAME or effect.get("name") == PLUGIN_NAME:
            return effect
    raise ValueError(f"case {case.get('id')} has no {PLUGIN_NAME} effect")


def load_windows_surface(path: Path = WINDOWS_MANIFEST) -> tuple[list[WindowsRow], dict[str, Any]]:
    manifest = load_json(path)
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{path} has no cases")
    identity_by_case: dict[str, list[tuple[Any, ...]]] = {}
    first_rows: list[WindowsRow] | None = None
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError(f"{path} contains a non-object case entry")
        effect = find_kirakira_effect(case)
        params = effect.get("params")
        if not isinstance(params, list) or not params:
            raise ValueError(f"case {case.get('id')} has no parameter rows")
        rows: list[WindowsRow] = []
        identity: list[tuple[Any, ...]] = []
        for order, param in enumerate(params, start=1):
            if not isinstance(param, dict):
                raise ValueError(f"case {case.get('id')} has a non-object param row")
            row = WindowsRow(
                windows_surface_order=order,
                property_index=param.get("property_index"),
                name=str(param.get("name") or ""),
                match_name=str(param.get("match_name") or ""),
                property_value_type=str(param.get("property_value_type")) if param.get("property_value_type") is not None else None,
                value=param.get("value"),
            )
            rows.append(row)
            identity.append((row.property_index, row.name, row.match_name, row.property_value_type))
        case_id = str(case.get("id") or "")
        identity_by_case[case_id] = identity
        if first_rows is None:
            first_rows = rows
    assert first_rows is not None
    canonical_identity = next(iter(identity_by_case.values()))
    drift = {
        case_id: identity
        for case_id, identity in identity_by_case.items()
        if identity != canonical_identity
    }
    if drift:
        raise ValueError(f"Windows KiraKira surface drifted across cases: {sorted(drift)}")
    metadata = {
        "manifest": str(path.relative_to(ROOT)),
        "case_count": len(identity_by_case),
        "case_ids": sorted(identity_by_case),
    }
    return first_rows, metadata


def classify_windows_row(row: WindowsRow, mac_by_match_name: dict[str, MacRow]) -> dict[str, Any]:
    mac_row = mac_by_match_name.get(row.match_name)
    if mac_row is not None:
        return {
            "status": "mapped_plugin_surface",
            "mac_match_name": mac_row.mac_match_name,
            "mac_label": mac_row.label,
            "mac_surface_order": mac_row.mac_surface_order,
            "mac_disk_id": mac_row.disk_id,
            "application_allowed": True,
            "settable": True,
            "reason": "Mac source-backed surface exposes the same disk-id-derived match name.",
        }
    if row.match_name.startswith("ADBE "):
        return {
            "status": "shared_builtin_passthrough",
            "mac_match_name": row.match_name,
            "mac_label": row.name,
            "mac_surface_order": None,
            "mac_disk_id": None,
            "application_allowed": True,
            "settable": False,
            "reason": "Built-in AE row is shared metadata, not a Mac plug-in surface row.",
        }
    if row.name.endswith("Color Ramp") and row.property_value_type == "6412":
        return {
            "status": "unmappable_missing_ramp_row",
            "mac_match_name": None,
            "mac_label": None,
            "mac_surface_order": None,
            "mac_disk_id": None,
            "application_allowed": False,
            "settable": False,
            "reason": "Windows custom ramp row is absent from the Mac ParamsSetup schema.",
        }
    if row.name == "Ramp":
        return {
            "status": "unmappable_custom_ramp_payload_row",
            "mac_match_name": None,
            "mac_label": None,
            "mac_surface_order": None,
            "mac_disk_id": None,
            "application_allowed": False,
            "settable": False,
            "reason": "Windows custom ramp payload row has no corresponding Mac surface row.",
        }
    if row.name == "":
        return {
            "status": "unmappable_windows_group_separator",
            "mac_match_name": None,
            "mac_label": None,
            "mac_surface_order": None,
            "mac_disk_id": None,
            "application_allowed": False,
            "settable": False,
            "reason": "Windows blank/group separator row has no Mac surface identity.",
        }
    return {
        "status": "unmappable_unknown_windows_only_row",
        "mac_match_name": None,
        "mac_label": None,
        "mac_surface_order": None,
        "mac_disk_id": None,
        "application_allowed": False,
        "settable": False,
        "reason": "Row is not source-backed on the Mac surface and is not a shared built-in row.",
    }


def build_mapping_table(windows_rows: Iterable[WindowsRow], mac_rows: Iterable[MacRow]) -> list[dict[str, Any]]:
    mac_by_match_name = {row.mac_match_name: row for row in mac_rows}
    table: list[dict[str, Any]] = []
    for row in windows_rows:
        classification = classify_windows_row(row, mac_by_match_name)
        table.append(
            {
                "windows_surface_order": row.windows_surface_order,
                "windows_property_index": row.property_index,
                "windows_name": row.name,
                "windows_match_name": row.match_name,
                "windows_property_value_type": row.property_value_type,
                **classification,
            }
        )
    return table


def mapping_table_by_match_name(mapping_table: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["windows_match_name"]): dict(row) for row in mapping_table}


def validate_requested_rows(
    requested_rows: Iterable[dict[str, Any]],
    mapping_by_match_name: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    saw_missing_ramp = False
    saw_unmappable = False
    saw_index_only = False

    for ordinal, row in enumerate(requested_rows, start=1):
        match_name = row.get("match_name")
        property_index = row.get("property_index")
        if not isinstance(match_name, str) or not match_name:
            code = "index_only_identity_rejected" if property_index is not None else "missing_match_name_rejected"
            rejected.append(
                {
                    "request_row": ordinal,
                    "code": code,
                    "reason": "KiraKira request rows must be keyed by match_name; property_index is non-authoritative.",
                    "match_name": match_name,
                    "property_index": property_index,
                }
            )
            saw_index_only = True
            continue

        mapping = mapping_by_match_name.get(match_name)
        if mapping is None:
            rejected.append(
                {
                    "request_row": ordinal,
                    "code": "unknown_match_name_rejected",
                    "reason": "Row is not present in the bounded Windows-to-Mac surface table.",
                    "match_name": match_name,
                    "property_index": property_index,
                }
            )
            saw_unmappable = True
            continue

        status = str(mapping["status"])
        if status == "mapped_plugin_surface":
            accepted.append(
                {
                    "request_row": ordinal,
                    "match_name": match_name,
                    "property_index": property_index,
                    "decision": "accepted_settable",
                    "mac_match_name": mapping["mac_match_name"],
                }
            )
            continue
        if status == "shared_builtin_passthrough":
            accepted.append(
                {
                    "request_row": ordinal,
                    "match_name": match_name,
                    "property_index": property_index,
                    "decision": "accepted_passthrough",
                    "mac_match_name": mapping["mac_match_name"],
                }
            )
            continue

        rejected.append(
            {
                "request_row": ordinal,
                "code": status,
                "reason": mapping["reason"],
                "match_name": match_name,
                "property_index": property_index,
            }
        )
        saw_unmappable = True
        if status == "unmappable_missing_ramp_row":
            saw_missing_ramp = True

    if saw_missing_ramp:
        status = "unmappable"
        code = "missing_ramp_row_present"
    elif saw_unmappable:
        status = "unmappable"
        code = "unmappable_row_present"
    elif saw_index_only:
        status = "rejected"
        code = "index_only_request_rejected"
    else:
        status = "accepted"
        code = "all_rows_match_name_mapped"

    return {
        "status": status,
        "code": code,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "accepted_rows": accepted,
        "rejected_rows": rejected,
    }


def canonical_validation_examples(
    windows_rows: list[WindowsRow],
    mapping_by_match_name: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    full_case_rows = [row.request_row() for row in windows_rows]
    mapped_only_rows = [
        row.request_row()
        for row in windows_rows
        if mapping_by_match_name[row.match_name]["application_allowed"]
    ]
    index_only_rows = [
        {
            "name": row.name,
            "property_index": row.property_index,
            "value": row.value,
        }
        for row in windows_rows[:4]
    ]
    return {
        "full_windows_case": validate_requested_rows(full_case_rows, mapping_by_match_name),
        "mapped_rows_by_match_name": validate_requested_rows(mapped_only_rows, mapping_by_match_name),
        "index_only_rows": validate_requested_rows(index_only_rows, mapping_by_match_name),
    }


def build_report() -> dict[str, Any]:
    windows_rows, windows_meta = load_windows_surface()
    mac_rows = load_mac_surface()
    mapping_table = build_mapping_table(windows_rows, mac_rows)
    mapping_by_match = mapping_table_by_match_name(mapping_table)
    counts = Counter(str(row["status"]) for row in mapping_table)
    validation_examples = canonical_validation_examples(windows_rows, mapping_by_match)
    windows_first_four = [
        {
            "property_index": row.property_index,
            "match_name": row.match_name,
            "name": row.name,
        }
        for row in windows_rows[:4]
    ]
    mac_first_four = [
        {
            "mac_surface_order": row.mac_surface_order,
            "disk_id": row.disk_id,
            "match_name": row.mac_match_name,
            "label": row.label,
        }
        for row in mac_rows[:4]
    ]
    return {
        "kind": "olmkirakira_parameter_surface_contract",
        "schema_version": 1,
        "artifact_date": ARTIFACT_DATE,
        "generated_on": GENERATED_ON,
        "scope": "bounded Windows-manifest-to-Mac-surface validation only",
        "ae_exact_claim": False,
        "inputs": {
            "windows_manifest": str(WINDOWS_MANIFEST.relative_to(ROOT)),
            "mac_source": str(MAC_SOURCE.relative_to(ROOT)),
            "mac_header": str(MAC_HEADER.relative_to(ROOT)),
            "mac_strings": str(MAC_STRINGS.relative_to(ROOT)),
        },
        "proven_facts": [
            "Windows rows OLM OLM Kira Kira-0029/-0031/-0033/-0037/-0039 are absent from the Mac ParamsSetup schema.",
            "Windows property_index 1..4 are Channel/Blur Mode/Merge mode/Approximated Input, while the Mac surface order begins at Glow Rotation/Brightness Gain/Vertical Length/Horizontal Length.",
            "Mac surface rows can still be accepted when the request is keyed by match_name, because the shared effect prefix and source-backed disk ids preserve the same match-name suffixes.",
        ],
        "mac_match_name_inference": {
            "basis": "Mac disk ids in OLMKiraKira.h plus the shared effect match-name prefix already used by checked-in Mac validation scripts.",
            "format": f"{PLUGIN_MATCH_NAME}-NNNN",
            "example": f"{PLUGIN_MATCH_NAME}-0008",
        },
        "windows_surface": {
            **windows_meta,
            "row_count": len(windows_rows),
            "ordered_first_four": windows_first_four,
        },
        "mac_surface": {
            "row_count": len(mac_rows),
            "ordered_first_four": mac_first_four,
        },
        "mapping_summary": dict(sorted(counts.items())),
        "windows_to_mac_match_name_status_table": mapping_table,
        "windows_to_mac_match_name_index": mapping_by_match,
        "validation_policy": {
            "application_identity": "match_name only",
            "index_only_requests": "rejected",
            "missing_ramp_rows": "fail closed as unmappable",
            "mapped_rows": "accepted by match_name",
        },
        "validation_examples": validation_examples,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMKiraKira Parameter Surface Contract",
        "",
        f"- Requested artifact date: `{report['artifact_date']}`",
        f"- Generated on: `{report['generated_on']}`",
        "- Scope: bounded Windows-manifest-to-Mac-surface validation only.",
        "- AE exact claim: `false`",
        "",
        "## Contract",
        "",
        "- Identity is `match_name` only for KiraKira request application.",
        "- Index-only request rows are rejected.",
        "- Any request row that includes a missing Windows ramp row fails closed as `unmappable`.",
        "- Existing mapped rows are accepted by match-name even though Windows and Mac visible ordering differs.",
        "",
        "## Ordered Surface Drift",
        "",
        "| Surface | Slot | Identity | Label |",
        "| --- | ---: | --- | --- |",
    ]
    for row in report["windows_surface"]["ordered_first_four"]:
        lines.append(
            f"| Windows | {row['property_index']} | `{row['match_name']}` | `{row['name']}` |"
        )
    for row in report["mac_surface"]["ordered_first_four"]:
        lines.append(
            f"| Mac | {row['disk_id']} | `{row['match_name']}` | `{row['label']}` |"
        )
    lines.extend(
        [
            "",
            "## Mapping Summary",
            "",
            "| Status | Count |",
            "| --- | ---: |",
        ]
    )
    for status, count in sorted(report["mapping_summary"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "## Validation Examples",
            "",
            f"- Full Windows case: `{report['validation_examples']['full_windows_case']['status']}` / `{report['validation_examples']['full_windows_case']['code']}`",
            f"- Mapped rows by match-name: `{report['validation_examples']['mapped_rows_by_match_name']['status']}` / `{report['validation_examples']['mapped_rows_by_match_name']['code']}`",
            f"- Index-only rows: `{report['validation_examples']['index_only_rows']['status']}` / `{report['validation_examples']['index_only_rows']['code']}`",
            "",
            "## Table",
            "",
            "| Win idx | Windows match-name | Windows label | Status | Mac match-name |",
            "| ---: | --- | --- | --- | --- |",
        ]
    )
    for row in report["windows_to_mac_match_name_status_table"]:
        lines.append(
            "| {idx} | `{win}` | `{name}` | `{status}` | {mac} |".format(
                idx=row["windows_property_index"],
                win=row["windows_match_name"],
                name=row["windows_name"] or "(blank)",
                status=row["status"],
                mac=f"`{row['mac_match_name']}`" if row["mac_match_name"] else "",
            )
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def write_report(report: dict[str, Any], out_json: Path = OUT_JSON, out_md: Path = OUT_MD) -> None:
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")


def main() -> int:
    report = build_report()
    write_report(report)
    summary = {
        "status": report["validation_examples"]["mapped_rows_by_match_name"]["status"],
        "mapping_summary": report["mapping_summary"],
        "json": str(OUT_JSON.relative_to(ROOT)),
        "md": str(OUT_MD.relative_to(ROOT)),
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
