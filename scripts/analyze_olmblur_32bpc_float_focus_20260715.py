#!/usr/bin/env python3
"""Audit the OLMBlur-only 32bpc Windows return and Mac cross-host gate.

This is evidence analysis only.  It never applies a tolerance and never turns
PNG or prose candidate evidence into an AE-exact result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr  # noqa: E402

CASE_IDS = [f"olmblur__case_{i:04d}" for i in range(1, 8)]
CASE_RE = re.compile(r"olmblur__case_(\d{4})")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_explicit_aex_hash(root: Path) -> str | None:
    if not root.is_dir():
        return None
    keys = {"aex_sha256", "plugin_aex_sha256", "loaded_aex_sha256", "loaded_plugin_aex_sha256"}
    for path in sorted(root.rglob("*.json")):
        try:
            value = load(path)
        except (OSError, ValueError):
            continue
        stack = [value]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                for key, candidate in item.items():
                    if key.lower() in keys and isinstance(candidate, str) and len(candidate) == 64:
                        return candidate.lower()
                    stack.append(candidate)
            elif isinstance(item, list):
                stack.extend(item)
    return None


def case_number(case_id: str) -> str:
    match = CASE_RE.fullmatch(case_id)
    if not match:
        raise VerificationError(f"unexpected focused case id: {case_id}")
    return match.group(1)


def artifact(root: Path, case_id: str, before: bool) -> Path:
    token = f"olmblur__case_{case_number(case_id)}"
    matches = [
        p for p in root.glob(f"*{token}*.exr")
        if p.is_file() and p.stem.endswith("_before_effects") == before
    ]
    label = "_before_effects.exr" if before else ".exr"
    if len(matches) != 1:
        raise VerificationError(f"{root}: expected one {token}{label}, found {len(matches)}")
    return matches[0]


def audit(spec_path: Path, windows_root: Path, mac_root: Path | None) -> dict[str, Any]:
    spec = load(spec_path)
    if spec.get("request_id") != "olmblur_32bpc_mac_windows_float_focus_20260711":
        raise VerificationError("wrong focused request")
    if spec.get("scope") != {"bit_depth": "32bpc", "plugin_filters": ["OLMBlur"], "feature_filters": [], "plugin_count": 1, "case_count": 7}:
        raise VerificationError("focused request scope is not the seven-case OLMBlur 32bpc scope")
    cases = [case["id"] for case in spec["cases"]]
    if cases != CASE_IDS:
        raise VerificationError(f"focused case order differs: {cases!r}")

    rows = []
    for case_id in CASE_IDS:
        effect = artifact(windows_root, case_id, False)
        control = artifact(windows_root, case_id, True)
        effect_info = inspect_float_rgba_exr(effect, (1920, 1080))
        control_info = inspect_float_rgba_exr(control, (1920, 1080))
        rows.append({
            "case_id": case_id,
            "windows_effect": effect_info,
            "windows_no_effect": control_info,
            "windows_effect_control_distinct": effect_info["sha256"] != control_info["sha256"],
        })

    windows_aex = find_explicit_aex_hash(windows_root)
    mac_present = bool(mac_root and mac_root.is_dir() and list(mac_root.rglob("*.exr")))
    mac_aex = find_explicit_aex_hash(mac_root) if mac_root else None
    return {
        "schema": "olmblur_32bpc_float_focus_audit.v1",
        "request_id": spec["request_id"],
        "plugin": "OLMBlur",
        "bit_depth": "32bpc",
        "comparison_policy": {"mode": "raw_float32_words", "tolerance": None, "png_evidence_allowed": False},
        "windows_return": {
            "root": str(windows_root),
            "cases": rows,
            "case_count": len(rows),
            "all_float_rgba_exr": True,
            "all_1920x1080": True,
            "loaded_aex_sha256": windows_aex,
            "loaded_aex_hash_present": windows_aex is not None,
        },
        "mac_candidate": {
            "root": str(mac_root) if mac_root else None,
            "float_exr_imported": mac_present,
            "loaded_aex_sha256": mac_aex,
            "loaded_aex_hash_present": mac_aex is not None,
        },
        "reported_but_not_reverified": {
            "source": "refs/conformance/olmblur_32bpc_mac_ae_candidate_20260711.md",
            "mac_effect_float_exr_cases": 7,
            "mac_no_effect_vs_windows_exact_cases": ["0001", "0002", "0003", "0004"],
            "mac_no_effect_vs_windows_input_conversion_cases": ["0005", "0006", "0007"],
            "windows_vs_mac_effect_differing_cases": ["0001", "0002", "0003", "0004", "0005", "0006", "0007"],
            "classification": "prose-only candidate record; EXRs and machine-readable Mac provenance are not imported",
        },
        "proven": [
            "The focused request is exactly seven OLMBlur cases with 32bpc SOFTWARE requirements.",
            "The imported Windows return has effect-on and before-effects FLOAT RGBA EXRs for all seven cases.",
            "The imported Windows EXRs are valid uncompressed float-preserving 1920x1080 artifacts.",
            "Mac adapter and complete-worker fixture evidence remain local binary/worker evidence, not cross-host AE exactness.",
            "The prior Mac candidate note reports seven effect EXRs and four exact no-effect controls, but its Mac EXRs are not independently re-verifiable from imported workspace artifacts.",
        ],
        "gates": {
            "windows_float_return_complete": True,
            "windows_loaded_aex_hash": windows_aex is not None,
            "mac_float_effect_and_control_imported": mac_present,
            "raw_cross_host_float_equality": False,
            "ae_exact": False,
        },
        "smallest_missing_cross_host_gate": {
            "status": "blocked",
            "required": [
                "A same-contract Mac effect-on and effect-disabled FLOAT RGBA EXR pair for one focused case, with case/parameter/input identity.",
                "The loaded Windows OLMBlur AEX SHA-256 bound to the imported or recaptured Windows effect output.",
                "A machine-readable raw FLOAT32 word comparison for that paired case; expand to all seven before a seven-case AE-exact claim.",
            ],
            "why": "Without the Mac artifacts and loaded Windows AEX identity, the existing Windows-versus-Mac effect deltas cannot be attributed to the current Mac worker.",
        },
        "claims_forbidden": ["AE exact", "source tuning from the current PNG/EXR residuals"],
    }


def markdown(report: dict[str, Any]) -> str:
    win = report["windows_return"]
    mac = report["mac_candidate"]
    lines = [
        "# OLMBlur 32bpc float focus audit",
        "",
        "Verdict: `blocked; no AE exact claim`",
        "",
        "## Proven",
        "",
    ]
    lines.extend(f"- {item}" for item in report["proven"])
    lines += [
        "",
        "## Imported return",
        "",
        f"- Windows FLOAT RGBA EXR cases: `{len(win['cases'])}/7`.",
        f"- Windows loaded AEX SHA-256: `{win['loaded_aex_sha256'] or 'missing'}`.",
        f"- Mac OLMBlur FLOAT EXR bundle imported: `{mac['float_exr_imported']}`.",
        f"- Mac loaded AEX SHA-256: `{mac['loaded_aex_sha256'] or 'missing'}`.",
        "- Prior Mac candidate note: seven effect outputs reported; no-effect controls reported exact for `0001..0004` and input-conversion differences for `0005..0007`.",
        "",
        "| case | Windows effect/control hashes distinct |",
        "|---|---:|",
    ]
    lines.extend(f"| `{row['case_id']}` | {row['windows_effect_control_distinct']} |" for row in win["cases"])
    lines += [
        "",
        "## Smallest missing cross-host gate",
        "",
        "Provide one same-contract Mac effect-on/effect-disabled FLOAT RGBA EXR pair with case and parameter identity, bind the loaded Windows OLMBlur AEX SHA-256, and run a machine-readable raw FLOAT32 word comparison. Expand that passing gate to all seven cases before any seven-case `AE exact` claim.",
        "",
        "Current effect deltas remain unattributed. No source change or tuning is justified by this return.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--focused-spec", type=Path, required=True)
    parser.add_argument("--windows-reference-dir", type=Path, required=True)
    parser.add_argument("--mac-candidate-dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = audit(args.focused_spec, args.windows_reference_dir, args.mac_candidate_dir)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        args.output.with_suffix(".md").write_text(markdown(report), encoding="utf-8")
        print(f"[OK] wrote {args.output}")
        print(f"[OK] wrote {args.output.with_suffix('.md')}")
        return 0
    except (OSError, ValueError, KeyError, VerificationError) as exc:
        print(f"[FAIL] {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
