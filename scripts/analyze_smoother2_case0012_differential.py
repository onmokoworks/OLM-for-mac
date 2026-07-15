#!/usr/bin/env python3
"""Classify a Smoother2 case_0012 return against local typed evidence.

The input may be a CDB trace fixture or a returned JSON/ZIP.  This is a local
evidence tool: it does not alter production code and never treats fixture
values as Windows truth.  A local reference is optional; without one the
report answers only whether the requested typed stages are complete.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TARGET_CASE = "legacy_case_0012_gamma5_red_blue_current_aex"
TARGET_XY = [91, 841]
TARGET_DESCRIPTOR = [91, 841, 1, 91, 843, 5]
PREFIXES = ("S2_BIND", "S2_E170", "S2_F270", "S2_E3A0", "S2_CCE0", "S2_C280", "S2_WRITER")
STAGES = ("producer", "config", "writer")


def parse_scalar(value: str) -> Any:
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?", value):
        return float(value)
    if "," in value:
        return [parse_scalar(part) for part in value.split(",")]
    return value


def parse_trace(text: str) -> list[dict[str, Any]]:
    events = []
    for line_number, line in enumerate(text.splitlines(), 1):
        fields = line.strip().split()
        if not fields or fields[0] not in PREFIXES:
            continue
        event: dict[str, Any] = {"prefix": fields[0], "line": line_number}
        for token in fields[1:]:
            if "=" in token:
                key, value = token.split("=", 1)
                event[key] = value if key == "config_raw_bytes" else parse_scalar(value)
        events.append(event)
    return events


def read_json_or_zip(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if name.endswith(("RETURN.json", "RETURN_RUNTIME_TRACE_RESULT.json"))]
            if not names:
                raise ValueError(f"no return JSON in {path}")
            return json.loads(archive.read(names[0]).decode("utf-8-sig"))
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def event_from_observation(stage: str, value: Any) -> dict[str, Any]:
    return {"stage": stage, **value} if isinstance(value, dict) else {"stage": stage}


def normalize(path: Path) -> tuple[dict[str, Any], str]:
    if path.suffix.lower() in (".json", ".zip"):
        result = read_json_or_zip(path)
        events = result.get("events")
        run = result.get("run", {})
        if isinstance(events, list):
            return {"events": [{**run, **event} for event in events], "run": run, "status": result.get("status")}, "return"
        obs = result.get("observations", {})
        events = []
        mapping = {"bind": "S2_BIND", "e170": "S2_E170", "f270": "S2_F270", "e3a0": "S2_E3A0", "cce0": "S2_CCE0", "c280": "S2_C280"}
        for stage, prefix in mapping.items():
            value = obs.get(stage)
            if isinstance(value, dict):
                events.append({**run, "prefix": prefix, **value})
        class_bytes = obs.get("class_bytes")
        e170 = next((event for event in events if event["prefix"] == "S2_E170"), None)
        if isinstance(class_bytes, dict) and e170 is not None:
            e170.update({key: class_bytes.get(key) for key in ("center_b0", "prev_b0", "left_b1", "center_class_bytes", "prev_class_bytes", "left_class_bytes") if class_bytes.get(key) is not None})
        writer = obs.get("final_writer")
        if isinstance(writer, dict):
            events.append({**run, "prefix": "S2_WRITER", **writer})
        return {"events": events, "run": run, "status": result.get("status")}, "return"
    return {"events": parse_trace(path.read_text(encoding="utf-8-sig")), "run": {}, "status": "fixture"}, "fixture"


def first(events: list[dict[str, Any]], prefix: str) -> dict[str, Any] | None:
    return next((event for event in events if event.get("prefix") == prefix), None)


def value(event: dict[str, Any] | None, *names: str) -> Any:
    if not event:
        return None
    for name in names:
        if name in event:
            return event[name]
    return None


def stage_snapshot(events: list[dict[str, Any]]) -> dict[str, Any]:
    e170, f270, e3a0 = first(events, "S2_E170"), first(events, "S2_F270"), first(events, "S2_E3A0")
    c280, cce0, writer = first(events, "S2_C280"), first(events, "S2_CCE0"), first(events, "S2_WRITER")
    return {
        "producer": {
            "e170_c": value(e170, "e170_c", "c"),
            "class_bytes": [value(e170, "center_class_bytes"), value(e170, "prev_class_bytes"), value(e170, "left_class_bytes")],
            "f270": {"append": value(f270, "append"), "source_xy": value(f270, "source_xy"), "weight": value(f270, "weight")},
            "e3a0": {"append": value(e3a0, "append"), "source_xy": value(e3a0, "source_xy"), "weight": value(e3a0, "weight")},
        },
        "config": {
            "c280": {"pointer_identity": value(c280, "pointer_identity"), "config_pointer_arithmetic": value(c280, "config_pointer_arithmetic"), "config_raw_bytes": value(c280, "config_raw_bytes"), "scale_fixed": value(c280, "scale_fixed")},
            "cce0": {"pointer_identity": value(cce0, "pointer_identity"), "config_pointer_source": value(cce0, "config_pointer_source"), "config_raw_bytes": value(cce0, "config_raw_bytes"), "mode_byte": value(cce0, "mode_byte")},
        },
        "writer": {"rgba_u8": value(writer, "rgba_u8", "output_rgba_hex"), "rgba_float": value(writer, "rgba_float", "output_rgba_float")},
    }


def compare(local: Any, observed: Any, path: str, diffs: list[dict[str, Any]]) -> None:
    if isinstance(local, dict) and isinstance(observed, dict):
        for key in sorted(set(local) | set(observed)):
            compare(local.get(key), observed.get(key), f"{path}.{key}", diffs)
    elif local != observed:
        diffs.append({"path": path, "local": local, "returned": observed})


def analyze(observed_data: dict[str, Any], source_kind: str, local_data: dict[str, Any] | None = None) -> dict[str, Any]:
    events = observed_data["events"]
    identity_keys = ("run_id", "ae_pid", "module_base", "aex_sha256", "project_bpc", "renderer", "case_id", "witness_id")
    identities = [{key: event.get(key) for key in identity_keys} for event in events]
    identity_ok = bool(events) and all(item == identities[0] for item in identities)
    required = {"S2_BIND", "S2_E170", "S2_F270", "S2_E3A0", "S2_CCE0", "S2_C280", "S2_WRITER"}
    present = {event.get("prefix") for event in events}
    duplicate_prefixes = sorted(prefix for prefix in present if sum(event.get("prefix") == prefix for event in events) != 1)
    snapshot = stage_snapshot(events)
    completeness = {
        "events": required <= present and not duplicate_prefixes,
        "producer": snapshot["producer"]["e170_c"] is not None and all(item is not None for item in snapshot["producer"]["class_bytes"]) and all(snapshot["producer"][unit][field] is not None for unit in ("f270", "e3a0") for field in ("append", "source_xy", "weight")),
        "config": all(snapshot["config"]["c280"][field] is not None for field in ("pointer_identity", "config_pointer_arithmetic", "config_raw_bytes", "scale_fixed")) and all(snapshot["config"]["cce0"][field] is not None for field in ("pointer_identity", "config_pointer_source", "config_raw_bytes", "mode_byte")),
        "writer": snapshot["writer"]["rgba_u8"] is not None and snapshot["writer"]["rgba_float"] is not None,
    }
    blockers = []
    if not identity_ok:
        blockers.append("identity_not_bound_to_one_run")
    if not required <= present:
        blockers.append("missing_typed_event:" + ",".join(sorted(required - present)))
    if duplicate_prefixes:
        blockers.append("duplicate_events:" + ",".join(duplicate_prefixes))
    for stage in STAGES:
        if not completeness[stage]:
            blockers.append(f"incomplete_{stage}_fields")
    diffs: list[dict[str, Any]] = []
    if local_data is not None:
        compare(local_data, snapshot, "", diffs)
    diff_stages = sorted({"producer" if item["path"].startswith(".producer") else "config" if item["path"].startswith(".config") else "writer" for item in diffs})
    first_divergence = next((stage for stage in STAGES if stage in diff_stages), None)
    if blockers:
        verdict = "BLOCKED_INCOMPLETE_RETURN"
    elif local_data is None:
        verdict = "READY_TYPED_FIELDS_ONLY"
    elif not diffs:
        verdict = "MATCHES_LOCAL_REFERENCE"
    else:
        verdict = "DIFF_AT_" + first_divergence.upper()
    return {"schema": "olmsmoother2_case0012_differential_v1", "scope": "local Smoother2 case_0012 fixture/return analysis", "source_kind": source_kind, "verdict": verdict, "FACT": {"identity_bound": identity_ok, "event_prefixes": sorted(present), "completeness": completeness, "typed_snapshot": snapshot, "diffs": diffs}, "INFERENCE": {"first_divergence": first_divergence, "attribution": "producer/config/writer boundary only; no causal Windows claim"}, "blockers": blockers}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="CDB trace, return JSON, or return ZIP")
    parser.add_argument("--local-reference", type=Path, help="JSON snapshot produced by this tool or a matching typed_snapshot")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    observed, kind = normalize(args.input.resolve())
    local = None
    if args.local_reference:
        data = read_json_or_zip(args.local_reference.resolve())
        local = data.get("FACT", {}).get("typed_snapshot", data.get("typed_snapshot", data))
    report = analyze(observed, kind, local)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output_json:
        args.output_json.write_text(rendered, encoding="utf-8")
    if args.output_md:
        lines = ["# OLMSmoother2 case_0012 Differential", "", f"- Verdict: `{report['verdict']}`", f"- Source: `{report['source_kind']}`", "", "## FACT", "", f"- Identity bound: `{report['FACT']['identity_bound']}`", f"- Completeness: `{report['FACT']['completeness']}`", f"- Event prefixes: `{report['FACT']['event_prefixes']}`", "", "## INFERENCE", "", f"- First divergence: `{report['INFERENCE']['first_divergence']}`", f"- Attribution: {report['INFERENCE']['attribution']}"]
        if report["blockers"]:
            lines += ["", "## Blockers", "", *[f"- `{item}`" for item in report["blockers"]]]
        args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(rendered, end="")
    return 0 if report["verdict"] != "BLOCKED_INCOMPLETE_RETURN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
