#!/usr/bin/env python3
"""Parse the three case0012 returns and prove the class plane is incomplete."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

from aex_loader import AexLoader  # noqa: E402
from audit_olmsmoother2_corrected_witness_20260717 import (  # noqa: E402
    execute_function,
    load_function_code,
)
from test_smoother2_fullchain_diff import call_c280_entry  # noqa: E402
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402

CASE_ID = "legacy_case_0012_gamma5_red_blue_current_aex"
DESCRIPTOR = [92, 841, 1, 92, 842, 2]
X, Y = 92, 841
RETURN_MEMBER = "RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.json"
TRACE_MEMBER = "logs/collector_legacy_case_0012_gamma5_red_blue_current_aex_collector_trace.txt"
OLD_LOG = ROOT / "refs/conformance/olmsmoother2_case0012_class_neighborhood_20260712.log"
ARCHIVES = {
    "initial": (
        "refs/windows_returns/20260716/20260716_142500__RETURN__OLMSMOOTHER2_LEGACY_KEY_PRODUCER_INPROCESS/RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.zip",
        "3ccc3817091e48e537af746c6b984f5275f91d35a8cab09f7d3fce4519c46b9f",
    ),
    "corrected": (
        "refs/windows_returns/20260716/20260716_150500__RETURN__OLMSMOOTHER2_RDX_DESCRIPTOR_CORRECTED/RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.zip",
        "8c031837ac6a2e95fec657cd444ca303ba3c8fb66bf2235f3c038b37e207efcf",
    ),
    "reentrant": (
        "refs/windows_returns/20260716/20260716_155333__RETURN__OLMSMOOTHER2_UPSTREAM_CLASSPLANE_REENTRANT/RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.zip",
        "2743bc7e6e391cb3b0965a90bc069adb2eaa74df7e913a4bc8c92a0322c48e33",
    ),
}
KNOWN = {
    "center": [255, 255, 0, 255],
    "previous": [255, 0, 0, 0],
    "left": [0, 255, 0, 255],
}
SOURCE = {
    "previous": [0.18447503, 0.18447503, 0.18447503, 0.68235296],
    "center": [1.0, 1.0, 1.0, 1.0],
    "second": [0.125, 0.25, 0.75, 0.625],
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def parse_csv(value: str, count: int, label: str) -> list[int]:
    parts = value.split(",")
    require(len(parts) == count and all(re.fullmatch(r"\d+", p) for p in parts), f"invalid {label}")
    values = [int(p) for p in parts]
    require(all(0 <= item <= 255 for item in values) if count == 4 else True, f"out-of-range {label}")
    return values


def parse_trace(raw: bytes) -> list[dict[str, Any]]:
    text = raw.decode("utf-8", errors="strict")
    events = []
    for line_number, line in enumerate(text.splitlines(), 1):
        require(line and not line[0].isspace(), f"malformed trace line {line_number}")
        tokens = line.split()
        require(tokens[0].startswith("S2_"), f"unknown trace prefix at line {line_number}")
        fields: dict[str, str] = {}
        for token in tokens[1:]:
            require(token.count("=") == 1, f"malformed token at line {line_number}")
            key, value = token.split("=", 1)
            require(bool(re.fullmatch(r"[a-z0-9_]+", key)) and key not in fields and value != "", f"invalid field at line {line_number}")
            fields[key] = value
        events.append({"prefix": tokens[0], "fields": fields})
    return events


def read_archive(label: str, relative: str, expected_hash: str) -> dict[str, Any]:
    path = ROOT / relative
    require(path.is_file(), f"missing {label} archive")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected_hash, f"{label} archive hash drift")
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        require(len(names) == len(set(names)), f"duplicate member in {label} archive")
        require(RETURN_MEMBER in names and TRACE_MEMBER in names, f"required member missing from {label} archive")
        for info in infos:
            member = PurePosixPath(info.filename)
            require(not member.is_absolute() and ".." not in member.parts and "\\" not in info.filename, f"unsafe member in {label} archive")
            mode = info.external_attr >> 16
            require(not stat.S_ISLNK(mode), f"symlink member in {label} archive")
        payload = json.loads(archive.read(RETURN_MEMBER).decode("utf-8", errors="strict"))
        trace = parse_trace(archive.read(TRACE_MEMBER))
    require(isinstance(payload, dict) and payload.get("schema_version") == 1, f"unsupported {label} return schema")
    return {"path": relative, "sha256": expected_hash, "status": payload.get("status"), "payload": payload, "trace": trace, "members": names}


def unique_event(archive: dict[str, Any], prefix: str) -> dict[str, str]:
    matches = [item["fields"] for item in archive["trace"] if item["prefix"] == prefix]
    require(len(matches) == 1, f"expected exactly one {prefix} event")
    return matches[0]


def validate_returns(parsed: dict[str, dict[str, Any]]) -> dict[str, Any]:
    require(parsed["initial"]["status"] == "answered", "initial return status changed")
    require(parsed["corrected"]["status"] == "answered", "corrected return status changed")
    require(parsed["reentrant"]["status"] == "exact_bind_failure", "reentrant return must remain a failed render")

    corrected = unique_event(parsed["corrected"], "S2_PRODUCER_E170_ENTRY")
    reentrant = unique_event(parsed["reentrant"], "S2_PRODUCER_E170_ENTRY")
    initial = unique_event(parsed["initial"], "S2_PRODUCER_E170_ENTRY")
    require(parse_csv(corrected["descriptor"], 6, "corrected descriptor") == DESCRIPTOR, "corrected descriptor mismatch")
    require(parse_csv(reentrant["descriptor"], 6, "reentrant descriptor") == DESCRIPTOR, "reentrant descriptor mismatch")
    require(initial["center_class_bytes"] != corrected["center_class_bytes"], "initial return unexpectedly became authoritative")

    extracted = {
        "center": parse_csv(corrected["center_class_bytes"], 4, "center bytes"),
        "previous": parse_csv(corrected["prev_class_bytes"], 4, "previous bytes"),
        "left": parse_csv(corrected["left_class_bytes"], 4, "left bytes"),
    }
    require(extracted == KNOWN, "corrected retained class bytes changed")
    for key, field in (("center", "center_class_bytes"), ("previous", "prev_class_bytes"), ("left", "left_class_bytes")):
        require(parse_csv(reentrant[field], 4, f"reentrant {key} bytes") == KNOWN[key], f"returns disagree on {key}")
    require(unique_event(parsed["corrected"], "S2_PRODUCER_E170_RETURN")["e170_c"] == "7", "corrected e170 result changed")
    require(unique_event(parsed["reentrant"], "S2_PRODUCER_E170_RETURN")["e170_c"] == "7", "reentrant e170 result changed")

    c280 = unique_event(parsed["reentrant"], "S2_UPSTREAM_C280")
    require(c280.get("index_inputs_proven") == "false", "reentrant c280 unexpectedly claims proven index inputs")
    require(not parsed["corrected"]["payload"].get("artifacts") and not parsed["reentrant"]["payload"].get("artifacts"), "unexpected binary artifact requires review")
    class_dump_members = [name for archive in parsed.values() for name in archive["members"] if re.search(r"class.*(bin|dump|raw|json)$", name, re.I)]
    require(not class_dump_members, "unreviewed class-plane dump found")
    return {"retained_class_pixels": extracted, "class_dump_members": class_dump_members, "reentrant_c280_index_inputs_proven": False}


def parse_old_neighborhood() -> dict[tuple[int, int], list[int]]:
    require(OLD_LOG.is_file(), "missing old class-neighborhood log")
    result: dict[tuple[int, int], list[int]] = {}
    pattern = re.compile(r"^class_neighbor xy=(\d+),(\d+) .* class=(\d+),(\d+),(\d+),(\d+) ")
    for line in OLD_LOG.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            values = [int(item) for item in match.groups()]
            result[(values[0], values[1])] = values[2:]
    require(len(result) == 25, "old neighborhood is not the expected 5x5 capture")
    return result


def run_aex(completion: str) -> dict[str, Any]:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls()
    smoother = SmootherStruct(loader, 128, 850)
    smoother.set_src_pixel(X, Y - 1, SOURCE["previous"])
    smoother.set_src_pixel(X, Y, SOURCE["center"])
    smoother.set_src_pixel(X, Y + 2, SOURCE["second"])
    fill = (255, 255, 255, 255) if completion == "one" else (0, 0, 0, 0)
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            smoother.set_class_pixel(X + dx, Y + dy, *fill)
    smoother.set_class_pixel(X, Y, *KNOWN["center"])
    smoother.set_class_pixel(X, Y - 1, *KNOWN["previous"])
    smoother.set_class_pixel(X - 1, Y, *KNOWN["left"])
    result = call_c280_entry(loader, smoother, X, Y)
    return {"completion": completion, "count": result["count"], "vertices": result["vertices"]}


def run_replays(adapter: Path) -> dict[str, Any]:
    code, _ = load_function_code()
    e170 = execute_function(code, KNOWN, DESCRIPTOR)
    require(e170 == 7, "extracted e170 replay no longer returns 7")
    completions: dict[str, Any] = {}
    for name in ("zero", "one"):
        aex = run_aex(name)
        portable = json.loads(subprocess.check_output([str(adapter), name], text=True))
        require(portable.get("completion") == name, f"portable completion identity mismatch for {name}")
        require(aex["count"] == portable.get("count"), f"actual AEX and portable c280 count disagree for {name}")
        require(len(aex["vertices"]) == len(portable.get("vertices", [])), f"actual AEX and portable c280 shape disagree for {name}")
        for aex_vertex, portable_vertex in zip(aex["vertices"], portable["vertices"]):
            require(len(aex_vertex["rgba"]) == len(portable_vertex.get("rgba", [])) == 4, f"invalid vertex shape for {name}")
            require(all(abs(a - b) <= 1e-6 for a, b in zip(aex_vertex["rgba"], portable_vertex["rgba"])), f"actual AEX and portable RGBA disagree for {name}")
            require(abs(aex_vertex["weight"] - portable_vertex.get("weight", float("inf"))) <= 1e-6, f"actual AEX and portable weight disagree for {name}")
        completions[name] = {"aex": aex, "portable": portable, "match": True}
    require(completions["zero"]["aex"]["count"] == 0, "zero completion discriminator changed")
    require(completions["one"]["aex"]["count"] == 3, "one completion discriminator changed")
    return {"e170_extracted_code_result": e170, "completions": completions, "c280_counts_differ": True}


def render_markdown(result: dict[str, Any]) -> str:
    conflicts = result["old_neighborhood_conflicts"]
    lines = [
        "# OLMSmoother2 case0012 class-plane return replay",
        "",
        "## Verdict",
        "",
        f"`{result['verdict']}`",
        "",
        "The three Windows return ZIPs do not contain the missing live neighbor class bytes. The corrected and reentrant returns retain only center, previous-row, and left pixels. Their process addresses are not backed by a memory dump in any archive.",
        "",
        "## Fail-Closed Intake",
        "",
        "- All three ZIP hashes, member paths, required members, JSON schema, and trace token structure were validated.",
        "- The initial return is superseded because its hard-coded sample disagrees with the corrected live-RDX return.",
        "- The reentrant return remains `exact_bind_failure`; its render result is invalid and its c280 event says `index_inputs_proven=false`.",
        "- No archive contains a class-plane binary, raw dump, or structured neighborhood artifact.",
        "",
        "## Reconstruction Test",
        "",
        f"The older 5x5 log conflicts with corrected live bytes at {len(conflicts)} of the three retained coordinates: " + ", ".join(item["xy"] for item in conflicts) + ". It therefore cannot be spliced into the corrected run as host state.",
        "",
        "Two local completions preserve the corrected descriptor and all three retained pixels. Extracted `FUN_18000e170` returns `7` for the retained inputs in both cases. Actual AEX and the portable implementation agree per completion, but c280 returns count `0` for the zero completion and count `3` for the one completion. Thus the captured evidence admits different downstream polygons.",
        "",
        "## Conclusion",
        "",
        "The missing live neighbor bytes cannot be extracted from these ZIPs or uniquely reconstructed from checked-in classplane/descriptor evidence. A same-run neighborhood memory capture is still required.",
        "",
        "## Reproduction",
        "",
        "```sh",
        "tmp=$(mktemp -d)",
        "clang++ -std=c++17 -O2 -I cli/OLMSmoother2/shim -I mac/OLMSmoother2 \\",
        "  tools/emulation/smoother2_case0012_classplane_replay_adapter_20260717.cpp -o \"$tmp/adapter\"",
        "python3 tools/emulation/test_olmsmoother2_case0012_classplane_return_replay_20260717.py \\",
        "  --adapter \"$tmp/adapter\" \\",
        "  --output-json refs/conformance/olmsmoother2_case0012_classplane_return_replay_20260717.json \\",
        "  --output-md refs/conformance/olmsmoother2_case0012_classplane_return_replay_20260717.md",
        "test $? -eq 2",
        "```",
        "",
        "## Claims Not Made",
        "",
        "- No Windows replay or recovered Windows class plane.",
        "- No After Effects host correctness claim.",
        "- No AE exact claim.",
        "- No production change and no ledger change.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    parsed = {label: read_archive(label, relative, digest) for label, (relative, digest) in ARCHIVES.items()}
    intake = validate_returns(parsed)
    old = parse_old_neighborhood()
    coordinate_map = {"center": (X, Y), "previous": (X, Y - 1), "left": (X - 1, Y)}
    conflicts = [
        {"name": name, "xy": f"{xy[0]},{xy[1]}", "old": old[xy], "corrected": KNOWN[name]}
        for name, xy in coordinate_map.items() if old[xy] != KNOWN[name]
    ]
    require(len(conflicts) == 2, "old-neighborhood conflict discriminator changed")
    replay = run_replays(args.adapter)
    archives = {label: {key: value for key, value in archive.items() if key in ("path", "sha256", "status")} for label, archive in parsed.items()}
    result = {
        "verdict": "BLOCKED_CASE0012_LIVE_CLASSPLANE_NOT_RECOVERABLE_LOCALLY",
        "scope": "fail-closed return parsing and local actual-AEX/portable ambiguity replay; not Windows or AE exact",
        "archives": archives,
        "intake": intake,
        "descriptor": DESCRIPTOR,
        "binary_grounding": {
            "aex_path": str(AEX_PATH.relative_to(ROOT)),
            "aex_sha256": hashlib.sha256(AEX_PATH.read_bytes()).hexdigest(),
            "extracted_predicate": "FUN_18000e170",
            "portable_source": "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp",
            "adapter_source": "tools/emulation/smoother2_case0012_classplane_replay_adapter_20260717.cpp",
        },
        "old_neighborhood_source": str(OLD_LOG.relative_to(ROOT)),
        "old_neighborhood_conflicts": conflicts,
        "replay": replay,
        "conclusion": "Missing live neighbor class bytes are absent from all three returns and are not uniquely reconstructible from checked-in evidence.",
        "required_next_witness": "same-run class-plane neighborhood bytes around the corrected c280 sample, captured before process exit",
        "claims_not_made": ["No Windows replay", "No recovered Windows class plane", "No After Effects host correctness claim", "No AE exact claim", "No production or ledger change"],
    }
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
