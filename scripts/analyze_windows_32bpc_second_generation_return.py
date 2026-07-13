#!/usr/bin/env python3
"""Validate and compare the focused Windows 32bpc second-generation return."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

from compare_float_exr import compare


EXPECTED = {
    "olmcolorkey__case_0002": {
        "effect": "OLM Color Key",
        "sha256": "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c",
    },
    "olmtoondilate__case_0001": {
        "effect": "ADBE OLMToonDilate",
        "sha256": "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd().resolve()))
    except ValueError:
        return path.name


def locate_exr(root: Path, case_id: str, mode: str) -> Path:
    matches = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() == ".exr" and case_id in str(path) and mode in str(path)]
    if len(matches) != 1:
        raise ValueError(f"{case_id}/{mode}: expected one EXR, got {len(matches)}")
    return matches[0]


def analyze(source: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="olm32_secondgen_") as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(source) as archive:
            archive.extractall(root)
        manifest_path = next(iter(root.rglob("return_manifest.json")), None)
        if manifest_path is None:
            raise ValueError("return_manifest.json missing")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        gates = {
            "kind": manifest.get("kind") == "olm_32bpc_second_generation_return",
            "rendered": manifest.get("status") == "rendered" and manifest.get("rendered") is True,
            "ae_version": manifest.get("ae_version") == "26.3x87",
            "renderer": manifest.get("renderer") == "SOFTWARE",
            "depth": manifest.get("bits_per_channel") == 32,
            "linear_light": manifest.get("linear_light") is False,
            "template": manifest.get("output_template") == "OLM EXR 32 Float",
        }
        rows = manifest.get("results")
        if not isinstance(rows, list) or len(rows) != 4:
            raise ValueError("expected four result rows")
        by_key = {(row.get("case_id"), row.get("mode")): row for row in rows}
        cases: dict[str, object] = {}
        for case_id, expected in EXPECTED.items():
            effect_row = by_key.get((case_id, "effect_on"))
            control_row = by_key.get((case_id, "no_effect"))
            if not isinstance(effect_row, dict) or not isinstance(control_row, dict):
                raise ValueError(f"{case_id}: effect/control rows missing")
            row_gates = []
            for mode, row in (("effect_on", effect_row), ("no_effect", control_row)):
                plugin = row.get("plugin", {})
                result = row.get("result", {})
                exr = locate_exr(root, case_id, mode)
                row_gates.append(
                    row.get("effect") == expected["effect"]
                    and plugin.get("sha256") == expected["sha256"]
                    and result.get("status") == "ok"
                    and result.get("project_bits_per_channel") == 32
                    and result.get("project_working_space") == "None"
                    and result.get("project_linear_blending") is False
                    and result.get("effect_disabled") is (mode == "no_effect")
                    and row.get("exr_sha256") == sha256(exr)
                )
            effect = locate_exr(root, case_id, "effect_on")
            control = locate_exr(root, case_id, "no_effect")
            delta = compare(control, effect)
            cases[case_id] = {
                "row_contracts_pass": all(row_gates),
                "effect_vs_no_effect": delta,
                "plugin_delta_exact": delta["mismatched_values"] == 0,
                "effect_sha256": sha256(effect),
                "control_sha256": sha256(control),
            }
        status = "accepted_plugin_delta_exact" if all(gates.values()) and all(case["row_contracts_pass"] and case["plugin_delta_exact"] for case in cases.values()) else "rejected"
        return {
            "schema": "olm.windows-32bpc-second-generation-analysis/1",
            "source": display_path(source),
            "source_sha256": sha256(source),
            "status": status,
            "host_gates": gates,
            "cases": cases,
            "scope": "Windows effect delta only; cross-host AE exact requires Windows-control versus Mac-control equality",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = analyze(args.source.resolve())
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f"[FAIL] {exc}")
        return 2
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["status"] == "accepted_plugin_delta_exact" else 1


if __name__ == "__main__":
    raise SystemExit(main())
