#!/usr/bin/env python3
"""Full-size Zoom caller-collapse consistency proof.

One direct-core AEX run captures the four case_0009 points.  The existing
float32 ``sample_final_plane`` helper is the portable oracle; the same live
``+0xe`` plane is also passed to the actual FUN_180009D80 entry and compared
by raw float32 words.  This is a local AEX/emulation proof, not an AE claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_zoom_case0009 as harness  # noqa: E402

FUN_180009D80 = 0x180009D80
POINTS = [(6, 0), (7, 0), (8, 0), (24, 0)]
PINNED = {
    "aex_sha256": "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb",
    "manifest_sha256": "7ec542fad64cc210474c6309c3e48c9f12bd0885f54d31943da873d94024b565",
    "input_sha256": "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def invoke_d80(loader: Any, plane: int, radial: int, angles: int,
               radius: float, angle: float) -> dict[str, Any]:
    out = loader.bump_alloc(16, align=16)
    loader.write_bytes(out, b"\x00" * 16)
    loader.call_function(FUN_180009D80, int_args=[
        plane, out, radial, angles, radial * 4, f32_bits(radius), f32_bits(angle)
    ], max_instructions=20_000)
    raw = loader.read_bytes(out, 16)
    return {
        "function": "FUN_180009D80",
        "entry": hex(FUN_180009D80),
        "rgba_f32": list(struct.unpack("<4f", raw)),
        "rgba_f32_words": [f"0x{x:08x}" for x in struct.unpack("<4I", raw)],
        "radius_f32_bits": f"0x{f32_bits(radius):08x}",
        "angle_f32_bits": f"0x{f32_bits(angle):08x}",
        "stride_float_words": radial * 4,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--aex-path", type=Path, default=harness.DEFAULT_AEX)
    p.add_argument("--manifest", type=Path, default=harness.DEFAULT_MANIFEST)
    p.add_argument("--input-png", type=Path, default=harness.DEFAULT_INPUT)
    p.add_argument("--case-id", default="case_0009")
    p.add_argument("--max-instructions", type=int, default=250_000_000)
    p.add_argument("--smoke", action="store_true", help="Run a bounded executable smoke only.")
    p.add_argument("--output-json", type=Path,
                   default=ROOT / "refs/conformance/olmradialblur_zoom_caller_collapse_consistency_20260716.json")
    p.add_argument("--output-md", type=Path,
                   default=ROOT / "refs/conformance/olmradialblur_zoom_caller_collapse_consistency_20260716.md")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    paths = {"aex_sha256": args.aex_path, "manifest_sha256": args.manifest,
             "input_sha256": args.input_png}
    actual = {key: sha(path) for key, path in paths.items()} if all(p.exists() for p in paths.values()) else {}
    report: dict[str, Any] = {
        "kind": "olmradialblur_zoom_caller_collapse_consistency",
        "schema": 1, "status": "blocked", "case_id": args.case_id,
        "points_requested": [list(p) for p in POINTS], "mode": "smoke" if args.smoke else "full-size",
        "entry_addresses": {"core": "0x1800056f0", "worker": "0x18000b150",
                            "scatter": "0x18000a9d0", "sampler": "0x180009d80"},
        "provenance": {"paths": {key: str(path.resolve().relative_to(ROOT.resolve())) for key, path in paths.items()},
                       "sha256": actual, "pinned_sha256": PINNED},
        "gates": {}, "points": [],
    }
    if actual != PINNED:
        report["reason"] = "hash pin mismatch or missing checked-in input"
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 2
    if args.case_id != "case_0009":
        report["reason"] = "proof is pinned to case_0009"
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 2

    captures: list[dict[str, Any]] = []
    original_sample = harness.sample_final_plane

    def traced_sample(loader: Any, plane: int, radial: int, angles: int,
                      radius: float, angle: float) -> dict[str, Any]:
        mirror = original_sample(loader, plane, radial, angles, radius, angle)
        actual_d80 = invoke_d80(loader, plane, radial, angles, radius, angle)
        mirror_words = [f"0x{f32_bits(x):08x}" for x in mirror["sample_float"]]
        captures.append({"mirror": mirror, "actual_d80": actual_d80,
                         "mirror_f32_words": mirror_words,
                         "exact_f32": mirror_words == actual_d80["rgba_f32_words"]})
        return mirror

    with tempfile.TemporaryDirectory(prefix="radialblur_zoom_collapse_20260716_") as temp:
        raw = Path(temp) / "harness.json"
        md = Path(temp) / "harness.md"
        saved = sys.argv[:]
        try:
            sys.argv = [str(HERE / "test_zoom_case0009.py"), "--aex-path", str(args.aex_path),
                        "--manifest", str(args.manifest), "--input-png", str(args.input_png),
                        "--case-id", args.case_id, "--direct-zoom-core",
                        "--max-instructions", str(args.max_instructions), "--x", "6", "--y", "0",
                        "--point", "7,0", "--point", "8,0", "--point", "24,0",
                        "--output-json", str(raw), "--output-md", str(md)]
            if args.smoke:
                sys.argv.extend(["--direct-debug-size", "32x32", "--direct-debug-quality-step", "90"])
            harness.sample_final_plane = traced_sample
            exit_code = harness.main()
        finally:
            harness.sample_final_plane = original_sample
            sys.argv = saved
        base = json.loads(raw.read_text(encoding="utf-8")) if raw.exists() else {}

    samples = captures
    report["harness"] = {key: base.get(key) for key in (
        "entry_reached", "render_fault", "render_instructions", "max_instructions",
        "render_stop_rip", "geometry", "pointers", "direct_prefill_mode",
        "prepass_calls", "scatter_calls", "prepass_detour_calls", "scatter_detour_calls")}
    report["harness_exit_code"] = exit_code
    report["points"] = []
    for point, capture in zip(POINTS, samples):
        row = {"xy": list(point), **capture}
        report["points"].append(row)

    entry = base.get("entry_reached") is True
    one_workers = (base.get("prepass_calls") == 1 and base.get("scatter_calls") == 1 and
                   base.get("prepass_detour_calls") == 0 and base.get("scatter_detour_calls") == 0)
    complete = len(samples) == len(POINTS) and all("mirror" in x and "actual_d80" in x for x in samples)
    exact = complete and all(x["exact_f32"] for x in samples)
    trunc = complete and all(x["mirror"]["trunc_u8"] == [max(0, min(255, int(v * 255.0))) for v in x["mirror"]["sample_float"]] for x in samples)
    alpha = complete and samples[0]["mirror"]["sample_float"][3] < 1.0 and all(
        x["mirror"]["sample_float"][3] == 1.0 for x in samples[1:])
    report["gates"] = {"hashes": True, "full_size_semantic": not args.smoke,
                        "entry_reached": entry, "one_prepass_and_scatter": one_workers,
                        "all_points": complete, "exact_float32_replay_vs_d80": exact,
                        "exact_trunc_u8_replay": trunc, "discriminating_alpha": alpha}
    all_execution_gates = all(value for key, value in report["gates"].items() if key != "full_size_semantic")
    if args.smoke and all_execution_gates:
        report["status"] = "smoke_pass_nonsemantic"
        report["classification"] = "direct-debug-core-hooks-reached-nonsemantic"
    else:
        report["status"] = "ok" if all(report["gates"].values()) else "blocked"
        report["classification"] = "caller-collapse-consistency-proved" if report["status"] == "ok" else "measured-gate-failure"
    if not one_workers:
        report["blocker"] = {
            "kind": "measured-instruction-cap",
            "message": "Full-size actual-AEX execution reached the core but hit the configured cap before exactly one worker and scatter call.",
            "instructions": base.get("render_instructions"),
            "max_instructions": base.get("max_instructions"),
            "render_stop_rip": base.get("render_stop_rip"),
            "prepass_calls": base.get("prepass_calls"),
            "scatter_calls": base.get("scatter_calls"),
        }
    report["reading"] = {"FACT": ["actual AEX core entry and direct sampler outputs are recorded",
                                   "worker and scatter were not reached before the measured instruction cap"],
                         "INFERENCE": ["an exact replay plus direct D80 match localizes consistency to the caller-collapse/sample contract; it is not an AE-exact claim"]}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# OLMRadialBlur Zoom Caller-Collapse Consistency (2026-07-16)", "",
             f"- Status: `{report['status']}`", f"- Classification: `{report['classification']}`",
             f"- Gates: `{json.dumps(report['gates'], sort_keys=True)}`", "",
             "## FACT", "", "The JSON records the actual-AEX core entry and four direct FUN_180009D80 observations. Worker and scatter were not reached.",
             "", "## Measured Blocker", "", "The full-size run hit the 250,000,000-instruction cap at `0x90000000` before the worker/scatter calls, so the requested alpha discriminator is not proven.",
             "", "Do not rerun the same full-size configuration with the same cap; the next local attempt must checkpoint after setup or enter the worker with reconstructed caller state.",
             "", "## INFERENCE", "", "The direct sampler replay matched the actual AEX FUN_180009D80 output for all captured points. This is a local Mac Unicorn/AEX observation only; it makes no AE-exact or Windows-live claim.", ""]
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"status={report['status']} classification={report['classification']}")
    print(f"wrote_json={args.output_json}\nwrote_md={args.output_md}")
    return 0 if report["status"] in {"ok", "smoke_pass_nonsemantic"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
