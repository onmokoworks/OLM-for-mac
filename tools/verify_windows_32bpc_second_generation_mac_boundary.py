#!/usr/bin/env python3
"""Verify the Mac-side boundary for the Windows 32bpc second-generation return.

This intentionally separates same-host effect/control deltas from cross-host
EXR comparisons.  A cross-host effect mismatch is diagnostic only until the
Windows and Mac no-effect controls are exact.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_windows_32bpc_second_generation_return import analyze, locate_exr  # noqa: E402
from compare_float_exr import compare  # noqa: E402


CASES = ("olmcolorkey__case_0002", "olmtoondilate__case_0001")


def find_mac_exr(roots: list[Path], case_id: str, mode: str) -> Path:
    matches: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.exr"):
            text = str(path).lower()
            if case_id.lower() not in text:
                continue
            if mode == "effect_on":
                wanted = "effect_on" in text or "effect-on" in text
            else:
                wanted = "no_effect" in text or "no-effect" in text or "manual_no_effect" in text
            if wanted:
                matches.append(path)
    unique = sorted(set(matches))
    if len(unique) != 1:
        raise ValueError(f"Mac {case_id}/{mode}: expected one EXR, got {len(unique)}")
    return unique[0]


def boundary_verdict(
    windows_plugin_delta_exact: bool,
    mac_host_noop_exact: bool,
    cross_host_control_exact: bool,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not windows_plugin_delta_exact:
        reasons.append("Windows effect/control delta is not exact")
    if not mac_host_noop_exact:
        reasons.append("Mac effect/control delta is not exact")
    if not cross_host_control_exact:
        reasons.append("Windows/Mac no-effect controls differ; EXR import boundary is unresolved")
    if reasons:
        return "AE exact refused", reasons
    return "cross-host controls exact; AE exact still unclaimed", [
        "This verifier does not promote an AE exact claim"
    ]


def verify(source: Path, mac_roots: list[Path]) -> dict[str, Any]:
    windows = analyze(source)
    if windows["status"] != "accepted_plugin_delta_exact":
        raise ValueError("Windows return did not pass its dedicated analyzer")
    cases: dict[str, Any] = {}
    mac_noop_exact = True
    cross_host_control_exact = True
    for case_id in CASES:
        with tempfile.TemporaryDirectory(prefix="olm32_boundary_") as tmp:
            extracted = Path(tmp)
            with zipfile.ZipFile(source) as archive:
                archive.extractall(extracted)
            windows_effect = locate_exr(extracted, case_id, "effect_on")
            windows_control = locate_exr(extracted, case_id, "no_effect")
            mac_effect = find_mac_exr(mac_roots, case_id, "effect_on")
            mac_control = find_mac_exr(mac_roots, case_id, "no_effect")
            windows_delta = compare(windows_control, windows_effect)
            mac_delta = compare(mac_control, mac_effect)
            control_cross_host = compare(windows_control, mac_control)
            effect_cross_host = compare(windows_effect, mac_effect)
            host_exact = mac_delta["mismatched_values"] == 0
            control_exact = control_cross_host["mismatched_values"] == 0
            mac_noop_exact &= host_exact
            cross_host_control_exact &= control_exact
            cases[case_id] = {
                "windows_effect_control": windows_delta,
                "mac_effect_control": mac_delta,
                "windows_control_vs_mac_control": control_cross_host,
                "windows_effect_vs_mac_effect_diagnostic": effect_cross_host,
                "mac_host_noop_exact": host_exact,
                "cross_host_control_exact": control_exact,
                "effect_cross_host_is_attributable": control_exact,
                "paths": {
                    "mac_effect": str(mac_effect),
                    "mac_control": str(mac_control),
                },
            }
    verdict, reasons = boundary_verdict(
        windows_plugin_delta_exact=True,
        mac_host_noop_exact=mac_noop_exact,
        cross_host_control_exact=cross_host_control_exact,
    )
    return {
        "schema": "olm.windows-32bpc-second-generation-mac-boundary/1",
        "source": str(source),
        "windows_plugin_delta_exact": True,
        "mac_host_noop_exact": mac_noop_exact,
        "cross_host_control_exact": cross_host_control_exact,
        "ae_exact_claim": False,
        "verdict": verdict,
        "reasons": reasons,
        "scope": "Mac/Windows EXR import boundary; no AE exact claim",
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--windows-return", required=True, type=Path)
    parser.add_argument("--mac-root", action="append", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.windows_return.resolve(), [path.resolve() for path in args.mac_root])
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f"[FAIL] {exc}")
        return 2
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["verdict"] == "cross-host controls exact; AE exact still unclaimed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
