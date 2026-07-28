#!/usr/bin/env python3
"""Byte-exact local discriminator: OLMSmoother v1 vs Smoother2 forced-v1."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = ROOT / "handoffs/windows_batch/olmsmoother_v1_bitdepth_16_32bpc_software_20260715.zip"
DEFAULT_V1 = ROOT / "plugins_2025/OLMSmoother.aex"
DEFAULT_V2 = ROOT / "plugins_2025/OLMSmoother2.aex"

PINNED_AEX = {
    "v1": "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82",
    "v2_forced_v1": "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7",
}
PINNED_INPUTS = {
    "case_0001": "166cafc8aaa2bb2d78ed26a12fe95b6dcf0f6eeeabd7f3a4daaf0ceece500e4c",
    "case_0002": "dd9c1adc8920f6785e5d4449545c29e5f3b60761244dae6d34293b401e0f0c9c",
    "case_0003": "7dc50c17733999bb952a69f65d6dfe60249694dd449fd9a0acb67411ba30570b",
}

V1_SURFACE = [
    (1, "Use Color Key", 4),
    (2, "Color Key", 5),
    (3, "Do Smooth Range", 1),
]
V2_SURFACE = [
    (1, "Enable Color Key", 4), (2, "Color Key", 5),
    (3, "Invert Color Key", 4), (4, "Smoothness", 1),
    (5, "Extra Smooth", 1), (6, "Smooth Range", 1),
    (7, "Smoother Version", 7), (8, "Gamma Correction", 7),
    (9, "Gamma Value", 10), (10, "Number of Gamma Colors", 1),
    (11, "Gamma Color", 5), (12, "Gamma Color", 5),
    (13, "Gamma Color", 5), (14, "Gamma Color", 5),
    (15, "Gamma Color", 5),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_json(command: list[str], timeout: int) -> dict[str, Any]:
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if completed.returncode:
        raise RuntimeError(json.dumps({
            "reason": "worker_process_failed", "returncode": completed.returncode,
            "stderr": completed.stderr[-2000:], "command_mode": command[1] if len(command) > 1 else None,
        }, sort_keys=True))
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(json.dumps({
            "reason": "worker_non_json_output", "stdout_tail": completed.stdout[-2000:],
        }, sort_keys=True)) from exc


def require_setup(worker: Path, aex: Path, expected: list[tuple[int, str, int]], timeout: int) -> dict[str, Any]:
    result = run_json([str(worker), "setup", str(aex)], timeout)
    observed = [(p.get("slot"), p.get("name"), p.get("param_type")) for p in result.get("parameters", [])]
    if result.get("global_setup_error") != 0 or result.get("params_setup_error") != 0:
        raise RuntimeError(json.dumps({"reason": "setup_error", "setup": result}, sort_keys=True))
    if observed != expected:
        raise RuntimeError(json.dumps({
            "reason": "parameter_surface_mismatch", "expected": expected, "observed": observed,
        }, sort_keys=True))
    return result


def argb_color(rgba: list[float]) -> tuple[int, int, int, int]:
    r, g, b, a = (int(float(x) * 255.0 + 0.5) for x in rgba)
    return a, r, g, b


def assignments(case: dict[str, Any]) -> dict[str, list[str]]:
    params = case["effect"]["params"]
    by_name = {p["name"]: p["value"] for p in params}
    use_key = int(by_name["Use Color Key"])
    color = argb_color(by_name["Color Key"])
    tolerance = int(by_name["Do Smooth Range"])
    color_text = ",".join(map(str, color))
    # Complete, explicit compatibility policy. The three v1 controls map
    # directly; every v2-only control is pinned instead of left implicit.
    return {
        "v1": [
            f"Use Color Key@1={use_key}",
            f"Color Key@2={color_text}",
            f"Do Smooth Range@3={tolerance}",
        ],
        "v2_forced_v1": [
            f"Enable Color Key@1={use_key}",
            f"Color Key@2={color_text}",
            "Invert Color Key@3=0",
            "Smoothness@4=100",
            "Extra Smooth@5=0",
            f"Smooth Range@6={tolerance}",
            "Smoother Version@7=1",
            "Gamma Correction@8=1",
            "Gamma Value@9=2.4000000953674316",
            "Number of Gamma Colors@10=1",
            "Gamma Color@11=255,0,0,0",
            "Gamma Color@12=255,0,0,0",
            "Gamma Color@13=255,0,0,0",
            "Gamma Color@14=255,0,0,0",
            "Gamma Color@15=255,0,0,0",
        ],
    }


def image_plane(path: Path) -> tuple[tuple[int, int], bytes]:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        return rgba.size, rgba.tobytes()


def premultiply_rgba(raw: bytes) -> bytes:
    out = bytearray(raw)
    for offset in range(0, len(out), 4):
        alpha = out[offset + 3]
        for channel in range(3):
            out[offset + channel] = (out[offset + channel] * alpha + 127) // 255
    return bytes(out)


def diff(left: bytes, right: bytes) -> dict[str, int | bool]:
    if len(left) != len(right):
        return {"exact": False, "byte_count_left": len(left), "byte_count_right": len(right)}
    mismatches = sum(a != b for a, b in zip(left, right))
    return {
        "exact": mismatches == 0,
        "mismatched_bytes": mismatches,
        "max_abs_diff": max((abs(a - b) for a, b in zip(left, right)), default=0),
    }


def expected_readback(label: str, mapped: list[str]) -> list[dict[str, Any]]:
    result = []
    color_slots = {2} if label == "v1" else {2, 11, 12, 13, 14, 15}
    for assignment in mapped:
        selector, encoded = assignment.split("=", 1)
        name, slot_text = selector.rsplit("@", 1)
        slot = int(slot_text)
        if slot in color_slots:
            result.append({"name": name, "slot": slot, "color": [int(x) for x in encoded.split(",")]})
        else:
            result.append({"name": name, "slot": slot, "value": float(encoded)})
    return result


def require_render_readback(
    result: dict[str, Any], label: str, case_id: str, input_hash: str, mapped: list[str],
) -> None:
    expected = expected_readback(label, mapped)
    observed = result.get("parameter_values")
    gates = {
        "guards_intact": result.get("guards_intact") is True,
        "pixel_format_argb8": result.get("pixel_format") == "argb8",
        "input_identity": result.get("input_png_sha256") == input_hash,
        "parameter_readback": observed == expected,
        "raw_plane_sized": result.get("raw_pixel_bytes") == result.get("pixel_bytes"),
    }
    if not all(gates.values()):
        raise RuntimeError(json.dumps({
            "reason": "render_readback_gate_failed", "binary": label, "case": case_id,
            "gates": gates, "expected_parameters": expected, "observed_parameters": observed,
        }, sort_keys=True))


def normalize_sha256(value: Any) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9A-Fa-f]{64}", value) is None:
        raise ValueError(f"invalid SHA-256 digest: {value!r}")
    return value.lower()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", type=Path, required=True)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--v1-aex", type=Path, default=DEFAULT_V1)
    parser.add_argument("--v2-aex", type=Path, default=DEFAULT_V2)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=1200)
    args = parser.parse_args()
    report: dict[str, Any] = {
        "schema": "olm.smoother-v1-discriminator/1",
        "verdict": "blocked",
        "claim_boundary": (
            "local AEXCompat PF8 raw-buffer SHA-256 identity plus decoded worker-PNG RGBA "
            "and round-premultiplied decoded PNG comparisons; not AE exact"
        ),
        "cases": [],
    }
    try:
        for label, path in (("v1", args.v1_aex), ("v2_forced_v1", args.v2_aex)):
            actual = sha256(path)
            if actual != PINNED_AEX[label]:
                raise RuntimeError(json.dumps({
                    "reason": "aex_identity_mismatch", "binary": label,
                    "expected_sha256": PINNED_AEX[label], "actual_sha256": actual,
                }, sort_keys=True))
        report["identity"] = {
            "worker_sha256": sha256(args.worker),
            "v1_aex_sha256": sha256(args.v1_aex),
            "v2_aex_sha256": sha256(args.v2_aex),
        }
        report["setup"] = {
            "v1": require_setup(args.worker, args.v1_aex, V1_SURFACE, args.timeout),
            "v2_forced_v1": require_setup(args.worker, args.v2_aex, V2_SURFACE, args.timeout),
        }
        with tempfile.TemporaryDirectory(prefix="olm_smoother_v1_discriminator_") as temp_name:
            temp = Path(temp_name)
            with zipfile.ZipFile(args.request) as archive:
                archive.extractall(temp / "request")
            request = json.loads((temp / "request/request.json").read_text())
            by_id = {case["id"]: case for case in request["cases"]}
            for case_id, expected_hash in PINNED_INPUTS.items():
                case = by_id[case_id]
                source = temp / "request" / case["input"]["path"]
                actual_hash = sha256(source)
                if actual_hash != expected_hash or case["input"]["sha256"] != expected_hash:
                    raise RuntimeError(json.dumps({
                        "reason": "input_identity_mismatch", "case": case_id,
                        "expected_sha256": expected_hash, "actual_sha256": actual_hash,
                        "manifest_sha256": case["input"]["sha256"],
                    }, sort_keys=True))
                mapped = assignments(case)
                planes: dict[str, bytes] = {}
                raw_plane_hashes: dict[str, str] = {}
                render_records = {}
                size = None
                for label, aex in (("v1", args.v1_aex), ("v2_forced_v1", args.v2_aex)):
                    output = temp / f"{case_id}.{label}.png"
                    result = run_json(
                        [str(args.worker), "render-png", str(aex), str(source), str(output), *mapped[label]],
                        args.timeout,
                    )
                    if result.get("render_error") != 0 or not output.is_file():
                        raise RuntimeError(json.dumps({
                            "reason": "binary_not_renderable", "binary": label, "case": case_id,
                            "render_error": result.get("render_error"), "worker_result": result,
                        }, sort_keys=True))
                    require_render_readback(result, label, case_id, expected_hash, mapped[label])
                    try:
                        raw_hash = normalize_sha256(result.get("raw_pixel_sha256"))
                    except ValueError:
                        raise RuntimeError(json.dumps({
                            "reason": "raw_pf8_hash_unavailable", "binary": label, "case": case_id,
                            "raw_pixel_sha256": result.get("raw_pixel_sha256"),
                        }, sort_keys=True))
                    raw_plane_hashes[label] = raw_hash
                    current_size, planes[label] = image_plane(output)
                    size = size or current_size
                    if current_size != size or len(planes[label]) != size[0] * size[1] * 4:
                        raise RuntimeError(json.dumps({
                            "reason": "pf8_plane_readback_failed", "binary": label,
                            "case": case_id, "size": current_size,
                        }, sort_keys=True))
                    render_records[label] = {"assignments": mapped[label], "worker_result": result}
                raw_hash_gate = {
                    "exact": raw_plane_hashes["v1"] == raw_plane_hashes["v2_forced_v1"],
                    "v1_sha256": raw_plane_hashes["v1"],
                    "v2_forced_v1_sha256": raw_plane_hashes["v2_forced_v1"],
                }
                decoded = diff(planes["v1"], planes["v2_forced_v1"])
                exported = diff(
                    premultiply_rgba(planes["v1"]),
                    premultiply_rgba(planes["v2_forced_v1"]),
                )
                report["cases"].append({
                    "id": case_id, "input_sha256": expected_hash, "size": size,
                    "render_readback": render_records, "raw_pf8_argb_sha256": raw_hash_gate,
                    "decoded_worker_png_rgba": decoded,
                    "round_premultiplied_export_rgba": exported,
                })
        report["verdict"] = (
            "raw_hash_and_decoded_outputs_equivalent_for_declared_inputs"
            if all(c["raw_pf8_argb_sha256"]["exact"]
                   and c["decoded_worker_png_rgba"]["exact"]
                   and c["round_premultiplied_export_rgba"]["exact"]
                   for c in report["cases"])
            else "discriminated"
        )
    except Exception as exc:
        try:
            report["failure"] = json.loads(str(exc))
        except json.JSONDecodeError:
            report["failure"] = {"reason": "harness_exception", "detail": str(exc)}
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report["verdict"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
