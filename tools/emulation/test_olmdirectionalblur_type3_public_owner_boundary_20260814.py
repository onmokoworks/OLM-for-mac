#!/usr/bin/env python3
"""Bind the fixed Type-3 Layer public route to exported-Smart evidence."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
CLOSURE_TOOL = ROOT / "tools/emulation/test_olmdirectionalblur_type3_layer_source_guard_closure_20260813.py"
CLOSURE_REPORT = ROOT / "refs/conformance/olmdirectionalblur_type3_layer_source_guard_closure_20260813.json"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_type3_public_owner_boundary_20260814.json"
NOTE = REPORT.with_suffix(".md")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_closure():
    spec = importlib.util.spec_from_file_location("dblur_type3_closure", CLOSURE_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import Type-3 closure")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate() -> dict[str, object]:
    closure = json.loads(CLOSURE_REPORT.read_text())
    module = load_closure()
    if not module.validate_report(closure):
        raise RuntimeError("Type-3 exported-Smart closure is invalid")
    rows = [
        {
            "depth": row["depth"],
            "source_sha256": row["input_active_sha256"],
            "layer_sha256": row["layer_active_sha256"],
            "windows_exported_smart_sha256": row["output_active_sha256"],
            "mac_public_effectmain_sha256": row["output_active_sha256"],
            "raw_exact": row["raw_exact"],
            "output_padding_preserved": row["output_padding_preserved"],
        }
        for row in closure["positives"]
    ]
    return {
        "schema": "olmdirectionalblur.type3-public-owner-boundary/2",
        "status": "PASS_TYPE3_EXPORTED_SMART_PUBLIC_RAW_EXACT_3",
        "identities": {
            "production_source_sha256": sha256(SOURCE),
            "closure_tool_sha256": sha256(CLOSURE_TOOL),
            "closure_report_sha256": sha256(CLOSURE_REPORT),
        },
        "rows": rows,
        "rows_sha256": canonical_sha(rows),
        "boundary": {
            "windows_oracle_entry": "AEX exported Smart entry under pinned repository AEXCompat/Unicorn worker",
            "windows_exported_smart_entry_proven": True,
            "mac_public_effectmain_exercised": True,
            "native_windows_exercised": False,
            "native_after_effects_exercised": False,
            "production_policy": "only the fixed 16x16 same-source Type-3 Layer tuple is admitted at PF8/PF16/PF32; mutations and unlisted routes fail closed",
        },
    }


def validate(report: dict[str, object], live: bool = True) -> bool:
    try:
        if set(report) != {"schema", "status", "identities", "rows", "rows_sha256", "boundary"}:
            return False
        if report["schema"] != "olmdirectionalblur.type3-public-owner-boundary/2":
            return False
        if report["status"] != "PASS_TYPE3_EXPORTED_SMART_PUBLIC_RAW_EXACT_3":
            return False
        expected_identities = {
            "production_source_sha256": sha256(SOURCE),
            "closure_tool_sha256": sha256(CLOSURE_TOOL),
            "closure_report_sha256": sha256(CLOSURE_REPORT),
        }
        if set(report["identities"]) != set(expected_identities):
            return False
        if live and report["identities"] != expected_identities:
            return False
        rows = report["rows"]
        if not isinstance(rows, list) or len(rows) != 3:
            return False
        if canonical_sha(rows) != report["rows_sha256"]:
            return False
        closure = json.loads(CLOSURE_REPORT.read_text())
        expected_rows = [
            {
                "depth": row["depth"], "source_sha256": row["input_active_sha256"],
                "layer_sha256": row["layer_active_sha256"],
                "windows_exported_smart_sha256": row["output_active_sha256"],
                "mac_public_effectmain_sha256": row["output_active_sha256"],
                "raw_exact": True, "output_padding_preserved": True,
            }
            for row in closure["positives"]
        ]
        if rows != expected_rows:
            return False
        return report["boundary"] == {
            "windows_oracle_entry": "AEX exported Smart entry under pinned repository AEXCompat/Unicorn worker",
            "windows_exported_smart_entry_proven": True,
            "mac_public_effectmain_exercised": True,
            "native_windows_exercised": False,
            "native_after_effects_exercised": False,
            "production_policy": "only the fixed 16x16 same-source Type-3 Layer tuple is admitted at PF8/PF16/PF32; mutations and unlisted routes fail closed",
        }
    except (KeyError, TypeError, OSError, ValueError):
        return False


def note(report: dict[str, object]) -> str:
    return f"""# OLMDirectionalBlur Type-3 public-owner boundary

The fixed 16x16 same-source Type-3 Layer tuple is raw exact between the Windows
AEX exported Smart entry under the pinned repository AEXCompat/Unicorn worker
and Mac public EffectMain at PF8/PF16/PF32. PF16 uses SDK transport
`round(byte*32768/255)`; the superseded `byte*128` fixture was not a public
Smart oracle. Source/Layer mutations and unlisted routes remain fail-closed.

No native Windows or After Effects run is claimed. Status: **{report['status']}**.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    report = json.loads(REPORT.read_text()) if args.validate_only else generate()
    if not validate(report):
        raise RuntimeError("stored Type-3 owner-boundary report is invalid")
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    markdown = note(report)
    if args.write:
        REPORT.write_text(encoded)
        NOTE.write_text(markdown)
    elif not args.validate_only:
        if REPORT.read_text() != encoded or NOTE.read_text() != markdown:
            raise RuntimeError("stored Type-3 owner-boundary artifacts differ from live")
    print(report["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
