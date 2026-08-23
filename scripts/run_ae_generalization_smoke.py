#!/usr/bin/env python3
"""Prepare and optionally run a non-destructive AE generalization smoke campaign.

The runner never installs or replaces a plug-in.  It will only render when the
installed MediaCore binary is byte-identical to a selected local build, unless
the caller explicitly asks to test the already-installed binary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEDIACORE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"
APP = Path("/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app")
PLUGINS = {
    "colorkeep": {"binary": "ColorKeep", "match": "OLM Color Keep", "name": "Color Keep",
                  "depths": (8, 16, 32), "route": "Smart", "tuple": "supported defaults",
                  "excluded": [("Classic 32", "Classic 32 bpc is not declared")]},
    "blur": {"binary": "OLMBlur", "match": "OLM OLM Blur", "name": "OLM Blur",
             "depths": (8, 16, 32), "route": "Smart", "tuple": "supported defaults"},
    "colorkey": {"binary": "OLMColorKey", "match": "OLM Color Key", "name": "OLM Color Key",
                 "depths": (8, 16, 32), "route": "Smart", "tuple": "pixel-local defaults (Edge Thin/Blur 0)"},
    "directional": {"binary": "OLMDirectionalBlur", "match": "OLM Directional Blur", "name": "OLM DirectionalBlur",
                    "depths": (8,), "route": "host-selected Classic/Smart", "tuple": "front-only baseline",
                    "render_queue_8": True,
                    "params": [("OLM Directional Blur-0005", "Blur Strength", 48)],
                    "params_by_size": {
                        "4k": [("OLM Directional Blur-0005", "Blur Strength", 8)],
                    }},
    "distance": {"binary": "OLMDistanceGradation", "match": "OLM Distance Gradation", "name": "Distance Gradation",
                 "depths": (8, 16, 32), "route": "Smart", "tuple": "Blur None + Constant interpolation",
                 "params": [("OLM Distance Gradation-0009", "Interpolation Mode", 1),
                            ("OLM Distance Gradation-0011", "Blur Mode", 1)]},
    "kirakira": {"binary": "OLMKiraKira", "match": "OLM OLM Kira Kira", "name": "OLM Kira Kira",
                 "depths": (8, 16, 32), "route": "Smart",
                 "tuple": "closed Mode 2 Highlight radius 3 tuple",
                 "params": [("OLM OLM Kira Kira-0003", "Vertical Length", 0),
                            ("OLM OLM Kira Kira-0004", "Horizontal Length", 0),
                            ("OLM OLM Kira Kira-0005", "Diagonal Length", 0),
                            ("OLM OLM Kira Kira-0026", "Diagonal 2 length", 0),
                            ("OLM OLM Kira Kira-0006", "Highlight Radius", 3)]},
    "radial": {"binary": "OLMRadialBlur", "match": "OLM RadialBlur", "name": "OLM RadialBlur",
               "depths": (8, 16, 32), "route": "Smart", "tuple": "centered Zoom baseline",
               "params": [("OLM RadialBlur-0004", "Strength", 4)]},
    "smoother": {"binary": "OLMSmoother", "match": "OLM Smoother", "name": "OLM Smoother",
                 "depths": (8, 16), "route": "Smart", "tuple": "Use Key off default",
                 "excluded": [("Classic 32", "Classic 32 bpc is not declared")]},
    "smoother2": {"binary": "OLMSmoother2", "match": "OLM Smoother v2", "name": "OLM Smoother v2",
                  "depths": (8, 16, 32), "route": "Smart", "tuple": "v2 defaults",
                  "params": [("OLM Smoother v2-0001", "Enable Color Key", 0),
                             ("OLM Smoother v2-0015", "Invert Color Key", 0),
                             ("OLM Smoother v2-0003", "Smoothness", 100),
                             ("OLM Smoother v2-0004", "Extra Smooth", 0),
                             ("OLM Smoother v2-0005", "Smooth Range", 2),
                             ("OLM Smoother v2-0006", "Smoother Version", 2),
                             ("OLM Smoother v2-0007", "Gamma Correction", 1),
                             ("OLM Smoother v2-0008", "Gamma Value", 2.4),
                             ("OLM Smoother v2-0009", "Number of Gamma Colors", 1)],
                  "excluded": [("Classic generic", "Classic remains limited/rejected")]},
    "toon": {"binary": "OLMToonDilate", "match": "ADBE OLMToonDilate", "name": "OLM Toon Dilate",
             "depths": (8, 16, 32), "route": "Smart", "tuple": "finite nonnegative Search Radius default",
             "excluded": [("Classic numerical", "Classic is intentionally a no-op")]},
}
DEPTHS = (8, 16, 32)
SIZES = ((1920, 1080, "hd"), (3840, 2160, "4k"))
EXR_TEMPLATE = "OLM EXR 32 Float"
PNG16_TEMPLATE = "TIFF シーケンス (アルファ付き)"


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def executable(bundle: Path, binary_name: str) -> Path:
    return bundle / "Contents/MacOS" / binary_name


def after_effects_running() -> bool:
    executable_path = APP / "Contents/MacOS/After Effects"
    return subprocess.run(
        ["pgrep", "-f", f"^{executable_path}$"], capture_output=True
    ).returncode == 0


def plugin_state(key: str) -> dict[str, object]:
    spec = PLUGINS[key]
    binary = str(spec["binary"])
    installed = executable(MEDIACORE / f"{binary}.plugin", binary)
    candidates = []
    for config in ("Debug", "Release"):
        path = executable(ROOT / f"mac/{binary}/Mac/build/{config}/{binary}.plugin", binary)
        candidates.append({"config": config, "path": str(path), "sha256": sha256(path)})
    installed_hash = sha256(installed)
    matches = [row["config"] for row in candidates if row["sha256"] and row["sha256"] == installed_hash]
    return {
        "key": key,
        "binary": binary,
        "effect_match_name": spec["match"],
        "effect_name": spec["name"],
        "declared_depths": spec["depths"],
        "execution_route": spec["route"],
        "supported_tuple": spec["tuple"],
        "render_queue_8": bool(spec.get("render_queue_8", False)),
        "params": spec.get("params", ()),
        "params_by_size": spec.get("params_by_size", {}),
        "installed_path": str(installed),
        "installed_sha256": installed_hash,
        "local_candidates": candidates,
        "matching_local_configs": matches,
        "current_build_installed": bool(matches),
    }


def apply_parameter_profile(state: dict[str, object], profile: str) -> None:
    if profile == "baseline":
        return
    if profile == "colorkeep-count100" and state.get("key") == "colorkeep":
        state["supported_tuple"] = (
            "Enabled Color Num 100 with the 100th color matching input pixel (1,0)"
        )
        state["params"] = (
            ("OLM Color Keep-0001", "Enabled Color Num", 100),
            ("OLM Color Keep-0101", "Color", [17 / 255, 5 / 255, 1 / 255]),
        )
        state["params_by_size"] = {}
        return
    if profile == "blur-legacy-repeat10" and state.get("key") == "blur":
        state["supported_tuple"] = (
            "Amount 5 Smoothness 100 Repeat 10 Bias Vertical Legacy on"
        )
        state["params"] = (
            ("OLM OLM Blur-0005", "Blur Amount", 5),
            ("OLM OLM Blur-0006", "Blur Smoothness", 100),
            ("OLM OLM Blur-0003", "Number of Repeat", 10),
            ("OLM OLM Blur-0004", "Bias Direction", 1),
            ("OLM OLM Blur-0007", "Legacy", 1),
        )
        state["params_by_size"] = {}
        return
    if profile == "colorkey-edge-blur" and state.get("key") == "colorkey":
        state["supported_tuple"] = (
            "single enabled input-matched key with Edge Blur Amount 4 "
            "Distance Type 1 Direction Around"
        )
        state["params"] = (
            ("OLM Color Key-0017", "Amount", 4),
            ("OLM Color Key-0018", "Distance Type", 1),
            ("OLM Color Key-0019", "Direction", 2),
            ("OLM Color Key-0524", "Use Color 1", 1),
            ("OLM Color Key-0022", "Color 1", [17 / 255, 5 / 255, 1 / 255]),
        )
        state["params_by_size"] = {}
        return
    if profile == "distance-linear-gaussian" and state.get("key") == "distance":
        state["supported_tuple"] = (
            "Inside RGB invert threshold 4 with Linear interpolation and "
            "Gaussian Blur Size 1"
        )
        state["params"] = (
            ("OLM Distance Gradation-0001", "Invert", 1),
            ("OLM Distance Gradation-0002", "In/Out", 1),
            ("OLM Distance Gradation-0003", "Inside Threshold", 4),
            ("OLM Distance Gradation-0005", "Render Mode", 1),
            ("OLM Distance Gradation-0006", "Use Background Color", 0),
            ("OLM Distance Gradation-0009", "Interpolation Mode", 2),
            ("OLM Distance Gradation-0011", "Blur Mode", 3),
            ("OLM Distance Gradation-0012", "Blur Size", 1),
        )
        state["params_by_size"] = {}
        return
    if profile != "directional-dual" or state.get("key") != "directional":
        raise ValueError(f"parameter profile {profile!r} is not valid for {state.get('key')!r}")
    state["declared_depths"] = (8, 16, 32)
    state["execution_route"] = "Smart"
    state["supported_tuple"] = (
        "neutral Dual Angle 37.25 Gain 0.75 Front/Back Strength 2"
    )
    state["params"] = (
        ("OLM Directional Blur-0001", "Angle", 37.25),
        ("OLM Directional Blur-0002", "Brightness Gain", 0.75),
        ("OLM Directional Blur-0005", "Front Blur Strength", 2),
        ("OLM Directional Blur-0010", "Back Blur Strength", 2),
    )
    state["params_by_size"] = {}


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def write_pattern_png(path: Path, width: int, height: int) -> None:
    """Write a deterministic, non-fixture RGBA gradient using stdlib only."""
    compressor = zlib.compressobj(6)
    compressed = bytearray()
    for y in range(height):
        row = bytearray(1 + width * 4)
        for x in range(width):
            at = 1 + x * 4
            row[at:at + 4] = bytes(((x * 17 + y * 3) & 255,
                                    (x * 5 + y * 11) & 255,
                                    (x ^ y) & 255,
                                    0 if (x + y) % 29 == 0 else 255))
        compressed.extend(compressor.compress(row))
    compressed.extend(compressor.flush())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" +
                     png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) +
                     png_chunk(b"IDAT", bytes(compressed)) + png_chunk(b"IEND", b""))


def effective_params(state: dict[str, object], size_name: str):
    return state.get("params_by_size", {}).get(size_name, state.get("params", ()))


def prepare_request(base: Path, state: dict[str, object], depth: int,
                    width: int, height: int, size_name: str) -> tuple[Path, str]:
    case_id = f"{state['key']}_arbitrary_{size_name}_{depth}bpc"
    request = base / case_id
    source_name = f"{case_id}_before_effects.png"
    output_name = f"{case_id}.png"
    write_pattern_png(request / "input" / source_name, width, height)
    params = [{"match_name": match, "name": name, "value": value}
              for match, name, value in effective_params(state, size_name)]
    case = {
        "id": case_id, "time": 0, "before_effects_frame": source_name,
        "effects": [{"name": state["effect_name"], "match_name": state["effect_match_name"], "params": params}],
    }
    reference = {
        "schema": 2, "kind": "ae_effect_reference_manifest", "platform": "mac-smoke",
        "project": {"bits_per_channel": depth},
        "comp": {"width": width, "height": height, "duration": 1, "frame_rate": 24},
        "cases": [case],
    }
    manifest = {
        "kind": "olm_ae_generalization_smoke_request", "reference_manifest": "reference_manifest.json",
        "input_dir": "input", "effect_match_name": state["effect_match_name"],
        "effect_name": state["effect_name"],
        "beta_execution_route": state["execution_route"],
        "beta_supported_tuple": state["supported_tuple"],
        "cases": [{"id": case_id, "before_effects_frame": source_name, "frame": output_name}],
    }
    (request / "reference_manifest.json").write_text(json.dumps(reference, indent=2) + "\n")
    (request / "request_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return request, case_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--plugin", action="append", choices=tuple(PLUGINS),
                        help="Limit the campaign to one plug-in key; repeat for multiple plug-ins.")
    parser.add_argument("--prepare-inputs", action="store_true",
                        help="Materialize the large HD/4K request inputs without launching AE.")
    parser.add_argument("--run-installed", action="store_true",
                        help="Explicitly test installed binaries even if they differ from local builds.")
    parser.add_argument("--profile", choices=("quick", "full"), default="full",
                        help="quick runs HD at each plug-in's first declared depth; full runs the declared 54-case matrix.")
    parser.add_argument(
        "--parameter-profile",
        choices=("baseline", "directional-dual", "colorkeep-count100",
                 "blur-legacy-repeat10", "colorkey-edge-blur",
                 "distance-linear-gaussian"),
        default="baseline",
        help="Select a bounded major-operations profile without changing the baseline 54-cell matrix.",
    )
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--ae-env", action="append", default=[], metavar="NAME=VALUE",
                        help="Pass an environment variable to the single-case AE runner; repeatable.")
    args = parser.parse_args()
    selected_keys = args.plugin or list(PLUGINS)
    states = [plugin_state(key) for key in selected_keys]
    if args.parameter_profile != "baseline":
        required_plugin = {
            "directional-dual": "directional",
            "colorkeep-count100": "colorkeep",
            "blur-legacy-repeat10": "blur",
            "colorkey-edge-blur": "colorkey",
            "distance-linear-gaussian": "distance",
        }[args.parameter_profile]
        if selected_keys != [required_plugin]:
            parser.error(
                f"--parameter-profile {args.parameter_profile} requires exactly "
                f"--plugin {required_plugin}"
            )
        apply_parameter_profile(states[0], args.parameter_profile)
    report: dict[str, object] = {
        "kind": "olm_ae_generalization_smoke_campaign", "schema": 1,
        "profile": args.profile,
        "parameter_profile": args.parameter_profile,
        "selected_plugin_keys": selected_keys,
        "policy": {"mutates_mediacore": False, "closes_unsaved_project": False,
                   "isolated_plugin_path_supported": False},
        "host": {"app_path": str(APP), "app_present": APP.is_dir(),
                 "after_effects_running": after_effects_running()},
        "plugins": states, "matrix": [], "unsupported_routes": [],
        "status": "prepared", "blockers": [],
    }
    if not APP.is_dir():
        report["blockers"].append("After Effects 2026 application is absent")
    mismatched = [str(row["binary"]) for row in states if not row["current_build_installed"]]
    if mismatched and not args.run_installed:
        report["blockers"].append(
            "installed binaries are not byte-identical to Debug/Release local builds: " + ", ".join(mismatched))
    if args.run and report["host"]["after_effects_running"]:
        report["blockers"].append(
            "After Effects is already running; refusing because force-new-project could discard unsaved work")

    owned_temp = None
    if args.output_dir:
        base = args.output_dir.resolve()
        base.mkdir(parents=True, exist_ok=True)
    else:
        owned_temp = tempfile.TemporaryDirectory(prefix="olm_ae_generalization_smoke_")
        base = Path(owned_temp.name)
    requests = base / "requests"
    results = base / "results"

    if args.run and report["blockers"]:
        report["status"] = "blocked_before_host_launch"
    else:
        for state in states:
            for route, reason in PLUGINS[str(state["key"])].get("excluded", ()):
                report["unsupported_routes"].append({
                    "plugin": state["binary"], "route": route, "reason": reason,
                })
            excluded_depths = sorted(set(DEPTHS) - set(state["declared_depths"]))
            for depth in excluded_depths:
                reason = "docs/BETA_SUPPORT.md does not declare this depth for the selected native AE route"
                report["unsupported_routes"].append({
                    "plugin": state["binary"], "depth": depth,
                    "reason": reason,
                })
            selected_depths = (state["declared_depths"][0],) if args.profile == "quick" else state["declared_depths"]
            selected_sizes = (SIZES[0],) if args.profile == "quick" else SIZES
            for depth in selected_depths:
                for width, height, size_name in selected_sizes:
                    case_id = f"{state['key']}_arbitrary_{size_name}_{depth}bpc"
                    output_mode = (
                        "png_render_queue" if depth == 8 and state.get("render_queue_8") else
                        "png" if depth == 8 else
                        "png16_render_queue" if depth == 16 else
                        "exr_render_queue"
                    )
                    output_template = "" if output_mode == "png" else (
                        EXR_TEMPLATE if output_mode == "exr_render_queue" else PNG16_TEMPLATE
                    )
                    row = {"plugin": state["binary"], "depth": depth, "width": width,
                           "height": height, "case_id": case_id, "status": "planned",
                           "output_mode": output_mode,
                           "output_template": output_template,
                           "execution_route": state["execution_route"],
                           "supported_tuple": state["supported_tuple"],
                           "parameter_overrides": [
                               {"match_name": match, "name": name, "value": value}
                               for match, name, value in effective_params(state, size_name)
                           ]}
                    if args.run or args.prepare_inputs:
                        request, case_id = prepare_request(requests, state, depth, width, height, size_name)
                        row["status"] = "prepared"
                    if args.run:
                        command = [sys.executable, str(ROOT / "scripts/run_ae_single_case.py"),
                                   "--request-dir", str(request), "--case-id", case_id,
                                   "--output-dir", str(results / case_id), "--app-name", args.app_name,
                                   "--timeout", str(args.timeout), "--ae-env", "OLM_AE_FORCE_NEW_PROJECT=1",
                                   "--ae-env", "OLM_AE_FORCE_SOFTWARE=1",
                                   "--ae-env", "OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT=1"]
                        if output_mode == "png_render_queue":
                            command.extend(("--output-mode", "png_render_queue",
                                            "--output-template", PNG16_TEMPLATE))
                        elif depth == 16:
                            command.extend(("--output-mode", "png16_render_queue",
                                            "--output-template", PNG16_TEMPLATE))
                        elif depth == 32:
                            command.extend(("--output-mode", "exr_render_queue",
                                            "--output-template", EXR_TEMPLATE))
                        for value in args.ae_env:
                            command.extend(("--ae-env", value))
                        completed = subprocess.run(command, text=True, capture_output=True)
                        row.update(status="passed" if completed.returncode == 0 else "failed",
                                   returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
                    report["matrix"].append(row)
        if args.run:
            report["status"] = "completed" if all(r["status"] == "passed" for r in report["matrix"]) else "completed_with_failures"

    report_path = base / "campaign_result.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"[INFO] report: {report_path}")
    if owned_temp:
        print("[INFO] temporary campaign artifacts are removed when this process exits")
    return 0 if report["status"] in ("prepared", "completed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
