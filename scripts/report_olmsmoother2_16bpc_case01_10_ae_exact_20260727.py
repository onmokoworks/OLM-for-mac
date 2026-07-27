#!/usr/bin/env python3
"""Materialize the fail-closed Smoother2 16bpc case01..10 AE-exact record."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_float_exr import read_planes  # noqa: E402

CHANNELS = ("A", "B", "G", "R")
EXPECTED_MAC_PLUGIN = "bad3472d3ce808bdd69f0fa55be493c3d2f76cd7ad8c49b519f03347b3e2cd7b"
EXPECTED_WINDOWS_PLUGIN = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"
EXPECTED_ARCHIVE = "4ab10cb69e45cfec56c0d68116dc2263e34595f9800c91ed0c8f9a0745599187"


class VerificationError(RuntimeError):
    pass


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise VerificationError(f"{path}: expected JSON object")
    return value


def compare_exr(reference: Path, candidate: Path) -> dict:
    left, lw, lh = read_planes(reference)
    right, rw, rh = read_planes(candidate)
    if (lw, lh) != (rw, rh):
        raise VerificationError(f"dimension mismatch: {reference} {(lw, lh)} != {candidate} {(rw, rh)}")
    counts: dict[str, int] = {}
    maxima: dict[str, int] = {}
    for channel in CHANNELS:
        count = 0
        maximum = 0
        for offset in range(0, len(left[channel]), 4):
            a = left[channel][offset : offset + 4]
            b = right[channel][offset : offset + 4]
            if a != b:
                count += 1
                maximum = max(maximum, abs(int.from_bytes(a, "little") - int.from_bytes(b, "little")))
        counts[channel] = count
        maxima[channel] = maximum
    return {
        "dimensions": [lw, lh],
        "compared_float32_words": lw * lh * 4,
        "mismatched_values": sum(counts.values()),
        "mismatched_values_by_channel": counts,
        "max_raw_u32_delta": max(maxima.values()),
        "max_raw_u32_delta_by_channel": maxima,
    }


def compare_png(reference: Path, candidate: Path) -> dict:
    left = Image.open(reference).convert("RGBA")
    right = Image.open(candidate).convert("RGBA")
    if left.size != right.size:
        raise VerificationError(f"PNG dimension mismatch: {reference} != {candidate}")
    a = left.tobytes()
    b = right.tobytes()
    return {
        "dimensions": list(left.size),
        "mismatched_values": sum(x != y for x, y in zip(a, b)),
        "max_diff": max((abs(x - y) for x, y in zip(a, b)), default=0),
        "reference_sha256": digest(reference),
        "candidate_sha256": digest(candidate),
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def reconstruct_case02_bits() -> dict:
    center = struct.unpack("<f", struct.pack("<f", 1278 / 32768))[0]
    sample = struct.unpack("<f", struct.pack("<f", 29768 / 32768))[0]
    weight = struct.unpack("<f", bytes.fromhex("80114a3d"))[0]
    blend = struct.unpack("<f", struct.pack("<f", 1.0 - weight))[0]
    initial = struct.unpack("<f", struct.pack("<f", blend * center))[0]
    product = struct.unpack("<f", struct.pack("<f", weight * sample))[0]
    separated = struct.unpack("<f", struct.pack("<f", initial + product))[0]
    separated_bits = struct.unpack("<I", struct.pack("<f", separated))[0]
    # Exact binary64 evaluation followed by one float32 rounding models FMADD
    # for these already-float32 operands.
    fused = struct.unpack("<f", struct.pack("<f", float(weight) * float(sample) + float(initial)))[0]
    fused_bits = struct.unpack("<I", struct.pack("<f", fused))[0]
    require(fused_bits == 0x3DA7B7FF, f"unexpected reconstructed FMADD bits: {fused_bits:#x}")
    require(separated_bits == 0x3DA7B800, f"unexpected separated bits: {separated_bits:#x}")
    return {
        "pixel": {"x": 362, "y": 670, "channel": "G"},
        "center_pf16_code": 1278,
        "center_f32_u32": "0x3d1fc000",
        "sample_pf16_code": 29768,
        "sample_f32_u32": "0x3f689000",
        "weight_f32_u32": "0x3d4a1180",
        "mac_arm64_fmadd_reconstruction_u32": f"0x{fused_bits:08x}",
        "windows_mulss_addss_reconstruction_u32": f"0x{separated_bits:08x}",
        "windows_cdb_cce0_g_u32": "0x3da7b800",
        "windows_pf16_argb_words": ["0x8000", "0x1792", "0x0a7c", "0x00cf"],
        "old_mac_pf16_g_code": 2683,
        "windows_and_fixed_mac_pf16_g_code": 2684,
    }


def build(args: argparse.Namespace) -> tuple[dict, str]:
    win_manifest_path = args.windows_root / "windows_return.json"
    mac_manifest_path = args.mac_16_root / "mac_validation_return.json"
    win = load_json(win_manifest_path)
    mac = load_json(mac_manifest_path)
    require(win.get("ae_version") == "26.3x87", "Windows AE version")
    require(mac.get("ae_version") == "26.3x87", "Mac AE version")
    require((win.get("plugin") or {}).get("sha256") == EXPECTED_WINDOWS_PLUGIN, "Windows AEX identity")
    require((mac.get("plugin") or {}).get("sha256") == EXPECTED_MAC_PLUGIN, "Mac plug-in identity")
    require(len(win.get("cases", [])) == 10 and len(mac.get("cases", [])) == 10, "case cardinality")
    win_cases = {row["suffix"]: row for row in win["cases"]}
    mac_cases = {row["suffix"]: row for row in mac["cases"]}
    rows = []
    for number in range(1, 11):
        suffix = f"{number:02d}"
        w = win_cases[suffix]
        m = mac_cases[suffix]
        require(w["id"] == m["id"], f"case{suffix} id")
        require(w["source"]["sha256"] == m["input"]["sha256"], f"case{suffix} source identity")
        require(w["project"]["bits_per_channel"] == m["project"]["bits_per_channel"] == 16, f"case{suffix} depth")
        require(w["project"]["renderer"] == m["project"]["renderer"] == "SOFTWARE", f"case{suffix} renderer")
        require(w["project"]["working_space"] in ("", "None") and m["project"]["working_space_raw"] in ("", "None"), f"case{suffix} working space")
        require(w["project"]["linear_blending"] is False and m["project"]["linear_blending"] is False, f"case{suffix} linear")
        require(w["exit_code"] == 0 and w["same_process_pair"], f"case{suffix} process contract")
        for key in ("depth_warning_occurrences", "preserve_rgb_occurrences", "output_module_occurrences", "float32_occurrences"):
            require(w["log"][key] == 2, f"case{suffix} {key}")
        case_dir_w = args.windows_root / "aerender_cases" / f"case{suffix}"
        case_dir_m = args.mac_16_root / f"case{suffix}"
        branches = {}
        for branch, win_name, win_key in (
            ("no_effect", "no_effect.exr00000", "no_effect_control"),
            ("effect_on", "effect_on.exr00000", "effect_on"),
        ):
            wp = case_dir_w / win_name
            mp = case_dir_m / f"{branch}.exr"
            require(digest(wp) == w["outputs"][win_key]["sha256"], f"case{suffix} Windows {branch} hash")
            require(digest(mp) == m["outputs"][branch]["sha256"], f"case{suffix} Mac {branch} hash")
            comparison = compare_exr(wp, mp)
            require(comparison["mismatched_values"] == 0 and comparison["max_raw_u32_delta"] == 0, f"case{suffix} {branch} not exact")
            branches[branch] = {
                "windows_sha256": digest(wp),
                "mac_sha256": digest(mp),
                **comparison,
            }
        rows.append(
            {
                "suffix": suffix,
                "id": w["id"],
                "input_sha256": w["source"]["sha256"],
                "windows_aep_sha256": w["project"]["sha256"],
                "windows_aerender_pid": w["aerender_pid"],
                "windows_stdout_sha256": w["log"]["stdout_sha256"],
                **branches,
            }
        )

    # The fresh-path 8bpc run must remain byte-identical to all 12 references.
    request = args.mac_8_root / "requests" / "ae_pixel_olmsmoother2_current_aex_20260726_r3"
    result = args.mac_8_root / "results" / "olmsmoother2_current_aex_20260726_r3"
    png_rows = [compare_png(path, result / path.name) for path in sorted((request / "expected").glob("*.png"))]
    require(len(png_rows) == 12, "8bpc case cardinality")
    require(all(row["mismatched_values"] == 0 and row["max_diff"] == 0 for row in png_rows), "8bpc regression")

    # The fresh-path 32bpc run is compared to the prior Mac planes already
    # bound to the committed 20/20 Windows exact record.
    regression32 = []
    for number in range(1, 11):
        suffix = f"{number:02d}"
        old_root = Path(f"/tmp/olmsmoother2_case{suffix}_32bpc_mac_20260727/return")
        new_root = args.mac_32_root / f"case{suffix}"
        branches = {}
        for branch in ("no_effect", "effect_on"):
            old = list(old_root.glob(f"*__{branch}.exr"))
            require(len(old) == 1, f"32bpc case{suffix} old {branch} cardinality")
            comparison = compare_exr(old[0], new_root / f"{branch}.exr")
            require(comparison["mismatched_values"] == 0 and comparison["max_raw_u32_delta"] == 0, f"32bpc case{suffix} {branch}")
            branches[branch] = comparison
        regression32.append({"suffix": suffix, **branches})

    trace_text = args.windows_trace.read_text(encoding="utf-8", errors="replace")
    for token in ("S2_CASE02_PF16_CCE0_HIT", "3e3c925e 3da7b800 3bcf790e 3f800000", "8000 1792 0a7c 00cf"):
        require(token in trace_text, f"Windows trace token missing: {token}")
    report = {
        "kind": "olmsmoother2_16bpc_case01_10_ae_exact",
        "schema_version": 1,
        "status": "AE exact",
        "date": "2026-07-27",
        "contract": {
            "ae_version": "26.3x87",
            "bits_per_channel": 16,
            "renderer": "SOFTWARE",
            "working_space": "None",
            "linear_blending": False,
            "input_interpretation": "Preserve RGB",
            "output_template": "OLM EXR 32 Float",
            "sample_type": "FLOAT32",
            "compression": "none",
        },
        "binaries": {"windows_aex_sha256": EXPECTED_WINDOWS_PLUGIN, "mac_plugin_sha256": EXPECTED_MAC_PLUGIN},
        "intake": {
            "windows_return_archive_sha256": EXPECTED_ARCHIVE,
            "windows_manifest_sha256": digest(win_manifest_path),
            "mac_manifest_sha256": digest(mac_manifest_path),
            "windows_trace_sha256": digest(args.windows_trace),
        },
        "case02_runtime_localization": reconstruct_case02_bits(),
        "implementation": {
            "source": "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp",
            "change": "PF16 now uses the existing volatile separated scalar MUL then ADD composite path already used by PF32; PF8 remains on the frozen composite body.",
        },
        "cases": rows,
        "summary": {
            "cases": 10,
            "raw_gates": 20,
            "exact_raw_gates": 20,
            "float32_words_per_gate": 1920 * 1080 * 4,
            "total_mismatched_values": 0,
            "max_raw_u32_delta": 0,
        },
        "regressions": {
            "8bpc": {"cases": 12, "exact_cases": 12, "max_diff": 0, "fresh_request_root": True},
            "32bpc": {
                "cases": 10,
                "raw_gates": 20,
                "exact_raw_gates": 20,
                "total_mismatched_values": 0,
                "max_raw_u32_delta": 0,
                "reference_chain": "fresh Mac planes vs prior Mac planes bound to refs/conformance/olmsmoother2_32bpc_case01_10_ae_exact_20260727.json",
            },
        },
    }
    lines = [
        "# OLMSmoother2 16bpc case-01..10 AE exact",
        "",
        "The declared Preserve-RGB 16bpc case set is Windows/Mac AE `26.3x87` exact.",
        "Each case uses one Windows `aerender` process with an AEP-embedded",
        "no-effect/effect-on pair, and every log proves the 16bpc depth warning,",
        "`Preserve RGB`, `OLM EXR 32 Float`, and FLOAT32 output twice.",
        "",
        "- Raw gates: `20/20` exact.",
        "- Words per gate: `8,294,400`.",
        "- Total mismatched words: `0`.",
        "- Maximum raw-u32 delta: `0`.",
        f"- Windows AEX: `{EXPECTED_WINDOWS_PLUGIN}`.",
        f"- Final Mac plug-in: `{EXPECTED_MAC_PLUGIN}`.",
        "",
        "## Last residual",
        "",
        "Before the fix, case-02 effect-on differed at only G `(362,670)`: Windows",
        "stored PF16 code `2684`, Mac `2683`. Windows CDB captured cce0 G",
        "`0x3da7b800` and PF16 ARGB words `8000 1792 0a7c 00cf`. The Mac AE trace",
        "uniquely reconstructs the contracted ARM64 result as `0x3da7b7ff`; the",
        "Windows `MULSS` then `ADDSS` order produces `0x3da7b800`. Routing PF16",
        "through the existing separated scalar composite path closes the word.",
        "A hash-identical fresh footage path was required to bypass stale AE frame",
        "reuse without changing Adobe preferences or caches.",
        "",
        "## Regression",
        "",
        "- Frozen 8bpc suite: `12/12`, `max_diff=0`.",
        "- Declared 32bpc set: fresh Mac `20/20` raw gates identical to the prior",
        "  Mac planes already bound to the committed Windows exact record.",
        "- The final source keeps PF8 on its original composite body.",
        "",
        "Machine-readable evidence:",
        "`refs/conformance/olmsmoother2_16bpc_case01_10_ae_exact_20260727.json`.",
    ]
    return report, "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows-root", type=Path, required=True)
    parser.add_argument("--mac-16-root", type=Path, required=True)
    parser.add_argument("--mac-8-root", type=Path, required=True)
    parser.add_argument("--mac-32-root", type=Path, required=True)
    parser.add_argument("--windows-trace", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--md-out", type=Path, required=True)
    args = parser.parse_args()
    report, markdown = build(args)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.md_out.write_text(markdown, encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
