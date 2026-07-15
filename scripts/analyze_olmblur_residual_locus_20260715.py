#!/usr/bin/env python3
"""Fail-closed OLMBlur case_0006 residual-locus/provenance analysis."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from refs.scripts.verify_manifest import load_rgba, png_header

WINDOWS = ROOT / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png"
MAC_SINGLE = ROOT / "refs/reports/ae_single_case_olmblur_16bpc_witness_latest/olmblur__case_0006/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png"
WINDOWS_MANIFEST = ROOT / "refs/win_references/olmblur_case0006_current_aex_export_20260709/OLMBlur/reference_manifest.json"
MAC_MANIFEST = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625/reference_manifest.json"
ACTUAL_AEX = ROOT / "refs/conformance/olmblur_case0006_actual_aex_fullworker_20260713.json"
WINDOWS_RETURN = ROOT / "refs/conformance/olmblur_case0006_worker_probe_return_20260715.md"
OUT_MD = ROOT / "refs/conformance/olmblur_residual_locus_analysis_20260715.md"
OUT_JSON = ROOT / "refs/conformance/olmblur_residual_locus_analysis_20260715.json"
EXPECTED_MAC_PLUGIN_SHA256 = "c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206"

POINTS = [(314, 14), (29, 71), (601, 598)]
WIDTH, HEIGHT = 1920, 1080


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def info(path: Path) -> dict[str, Any]:
    display = str(path)
    try:
        display = str(path.relative_to(ROOT))
    except ValueError:
        pass
    if not path.exists():
        return {"path": display, "exists": False}
    return {
        "path": display,
        "exists": True,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "png_header": png_header(path) if path.suffix.lower() == ".png" else None,
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_contract(path: Path) -> dict[str, Any]:
    data = load_json(path)
    project = data["project"]
    cases = data["cases"]
    case = next((item for item in cases if item.get("id") == "olmblur__case_0006"), cases[0])
    comp = case["comp"]
    gpu = case["project_gpu_accel_type"]
    values = {p["name"]: p.get("value") for p in case["effects"][0]["params"]}
    return {
        "platform": data.get("platform"),
        "ae_version": data.get("ae_version"),
        "bits_per_channel": project.get("bits_per_channel"),
        "renderer": gpu.get("current_name"),
        "renderer_raw": gpu.get("raw"),
        "width": comp.get("width"),
        "height": comp.get("height"),
        "pixel_aspect": comp.get("pixel_aspect"),
        "resolution_factor": comp.get("resolution_factor"),
        "frame_rate": comp.get("frame_rate"),
        "case_id": case.get("id"),
        "effect": case.get("requested_effect"),
        "params": values,
    }


def points(path: Path) -> dict[str, list[int]]:
    rgba = load_rgba(path)
    return {f"{x},{y}": [int(v) for v in rgba[y, x]] for x, y in POINTS}


def export_points(path: Path) -> dict[str, list[int]]:
    """Return the 8-bit exported codes represented by the 16-bit PNG words."""
    rgba = load_rgba(path)
    return {f"{x},{y}": [int(v) >> 8 for v in rgba[y, x]] for x, y in POINTS}


def residuals(windows: Path, mac: Path) -> list[dict[str, Any]]:
    a, b = load_rgba(windows), load_rgba(mac)
    if a.shape != b.shape:
        return []
    out = []
    for y in range(a.shape[0]):
        for x in range(a.shape[1]):
            av, bv = [int(v) >> 8 for v in a[y, x]], [int(v) >> 8 for v in b[y, x]]
            if av != bv:
                out.append({"xy": [x, y], "windows": av, "mac_single": bv, "delta": [u - v for u, v in zip(av, bv)]})
    return out


def actual_aex_facts(data: dict[str, Any]) -> dict[str, Any]:
    comparison = data.get("comparison", {})
    return {
        "classification": data.get("classification"),
        "aex_sha256": data.get("identity", {}).get("aex_sha256"),
        "dimensions": data.get("identity", {}).get("dimensions"),
        "portable_trace_self_check": data.get("portable", {}).get("self_check"),
        "first_windows_internal_difference_reason": comparison.get("first_windows_internal_difference_reason"),
        "windows_png_difference_points": comparison.get("windows_png_difference_points"),
    }


def mac_observation(path: Path | None, mac_export_sha256: str) -> dict[str, Any]:
    if path is None:
        return {"provided": False, "bound": False}
    if not path.is_file():
        raise SystemExit(f"FAIL-CLOSED: missing Mac observation report: {path}")
    data = load_json(path)
    record = data.get("diagnostic_log", {}).get("record", {}).get("fields", {})
    checks = {
        "status": data.get("status") == "answered_observation",
        "claim": data.get("claim") == "observation_only_not_exact",
        "case_id": data.get("case_id") == "olmblur__case_0006",
        "output_sha256": data.get("output", {}).get("sha256") == mac_export_sha256,
        "plugin_sha256": data.get("mac_plugin_binary_sha256") == EXPECTED_MAC_PLUGIN_SHA256,
        "diagnostic_plugin_sha256": record.get("plugin_sha256") == EXPECTED_MAC_PLUGIN_SHA256,
        "project_bpc": data.get("ae_result", {}).get("project_bits_per_channel") == 16 and record.get("project_bpc") == "16",
        "renderer": record.get("renderer") == "Software",
        "point": data.get("point") == [601, 598] and record.get("x") == "601" and record.get("y") == "598",
    }
    return {
        "provided": True,
        "path": info(path)["path"],
        "sha256": sha256(path),
        "plugin_sha256": data.get("mac_plugin_binary_sha256"),
        "checks": checks,
        "bound": all(checks.values()),
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    files = {"windows_export": info(args.windows_export), "mac_single_export": info(args.mac_single_export), "windows_return_report": info(args.windows_return_report)}
    missing = [role for role, value in files.items() if not value["exists"]]
    if missing:
        raise SystemExit(f"FAIL-CLOSED: missing required evidence: {', '.join(missing)}")
    win = load_rgba(args.windows_export)
    mac = load_rgba(args.mac_single_export)
    if tuple(win.shape) != (HEIGHT, WIDTH, 4) or tuple(mac.shape) != (HEIGHT, WIDTH, 4):
        raise SystemExit("FAIL-CLOSED: export dimensions/channels are not 1920x1080 RGBA")
    wm, mm = manifest_contract(args.windows_manifest), manifest_contract(args.mac_manifest)
    required = ("bits_per_channel", "renderer", "width", "height", "pixel_aspect", "resolution_factor", "frame_rate", "case_id", "effect", "params")
    compatible = all(wm[k] == mm[k] for k in required)
    aex = actual_aex_facts(load_json(args.actual_aex))
    return_text = " ".join(args.windows_return_report.read_text(encoding="utf-8").split())
    return_classification = {
        "accepted_same_run_export_provenance": "accepted as same-run Windows AE export provenance" in return_text,
        "not_olmblur_worker_trace": "not as an OLMBlur worker/internal trace" in return_text,
    }
    diff = residuals(args.windows_export, args.mac_single_export)
    identity = {"windows_export_equals_canonical": sha256(args.windows_export) == "27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f", "windows_export_equals_mac_single": sha256(args.windows_export) == sha256(args.mac_single_export)}
    observation = mac_observation(args.mac_observation_report, files["mac_single_export"]["sha256"])
    export_exact = identity["windows_export_equals_mac_single"] and not diff
    mapping = {
        "declared_transform": "identity",
        "manifest_geometry_allows_identity": compatible and wm["width"] == WIDTH and wm["height"] == HEIGHT and wm["pixel_aspect"] == 1 and wm["resolution_factor"] == [1, 1],
        "residual_locus": [item["xy"] for item in diff],
        "historical_internal_witnesses": [[314, 14], [29, 71]],
        "identity_maps_residual_to_historical_witness": False,
        "status": "not-applicable-exact-export" if export_exact else "not-proven",
        "reason": (
            "No exported residual remains, so no residual-to-internal coordinate mapping is required."
            if export_exact else
            "The only declared host transform is identity; (601,598) is distinct from (314,14) and (29,71), and no artifact supplies a provenance transform or same-run OLMBlur internal trace."
        ),
    }
    gates = {
        "required_files_present": not missing,
        "windows_hash_is_canonical": identity["windows_export_equals_canonical"],
        "single_residual_exactly_at_601_598": len(diff) == 1 and diff[0]["xy"] == [601, 598] and diff[0]["windows"] == [18, 18, 18, 255] and diff[0]["mac_single"] == [17, 17, 18, 255],
        "host_contracts_compatible": compatible,
        "actual_aex_is_typed_but_not_windows_internal": aex["first_windows_internal_difference_reason"] is not None or aex["windows_png_difference_points"] == ["(29,71)"],
        "windows_return_classification": all(return_classification.values()),
        "export_byte_exact": export_exact,
        "mac_observation_bound": observation["bound"],
        "cdb_attach_used": False,
    }
    exact_observed = (
        gates["required_files_present"] and gates["windows_hash_is_canonical"] and
        gates["host_contracts_compatible"] and gates["windows_return_classification"] and
        gates["export_byte_exact"] and gates["mac_observation_bound"] and
        not gates["cdb_attach_used"]
    )
    separate = (
        gates["required_files_present"] and gates["windows_hash_is_canonical"] and
        gates["single_residual_exactly_at_601_598"] and gates["host_contracts_compatible"] and
        gates["actual_aex_is_typed_but_not_windows_internal"] and
        gates["windows_return_classification"] and not gates["cdb_attach_used"] and
        aex["portable_trace_self_check"] is True and mapping["status"] == "not-proven"
    )
    verdict = "ae-exact-observed" if exact_observed else ("separate-lanes" if separate else "fail-closed")
    if exact_observed:
        fact = [
            "Windows export is canonical/current-AEX byte identity.",
            "The bound Mac AE output is byte-identical to the Windows export; no exported residual remains.",
            f"The same-run Mac observation binds installed plug-in SHA-256 {EXPECTED_MAC_PLUGIN_SHA256} at (601,598).",
        ]
        inference = [
            "The prior one-pixel case_0006 residual came from a different installed Mac bundle, not the currently bound binary.",
            "This closes only the declared 16bpc case_0006 cell; other cases and bit depths remain independent gates.",
        ]
    else:
        fact = [
            "Windows export is canonical/current-AEX byte identity.",
            "Mac single differs at exactly one exported pixel: (601,598), Windows [18,18,18,255] versus Mac [17,17,18,255].",
            "Historical typed witnesses are (314,14) and (29,71); the actual-AEX report does not localize a Windows internal difference.",
        ]
        inference = [
            "No coordinate/provenance mapping is proven by current artifacts.",
            "The export residual and historical internal witnesses must remain separate evidence lanes.",
            "No helper, kernel, or rounding conclusion follows from this image-level residual.",
        ]
    return {
        "kind": "olmblur_residual_locus_analysis",
        "schema": 1,
        "date": "2026-07-15",
        "scope": "OLMBlur non-Legacy 16bpc case_0006",
        "verdict": verdict,
        "files": files,
        "identity": identity,
        "windows_points_raw_16bit": points(args.windows_export),
        "mac_single_points_raw_16bit": points(args.mac_single_export),
        "windows_points_exported_8bit": export_points(args.windows_export),
        "mac_single_points_exported_8bit": export_points(args.mac_single_export),
        "residuals": diff,
        "windows_manifest": wm,
        "mac_manifest": mm,
        "host_contracts_compatible": compatible,
        "actual_aex": aex,
        "windows_return_classification": return_classification,
        "mac_observation": observation,
        "mapping": mapping,
        "gates": gates,
        "fact": fact,
        "inference": inference,
        "forbidden_actions": ["CDB attach", "mac/OLMBlur edits", "kernel tuning", "rounding tuning", "editing notes/CONFORMANCE_LEDGER.md"],
    }


def markdown(report: dict[str, Any]) -> str:
    r = report
    lines = ["# OLMBlur residual-locus analysis 2026-07-15", "", f"- Verdict: `{r['verdict']}`", f"- Scope: `{r['scope']}`", "", "## FACT", ""]
    lines += [f"- {item}" for item in r["fact"]]
    lines += ["", "## Export Evidence", "", "| Artifact | SHA-256 |", "| --- | --- |"]
    for role in ("windows_export", "mac_single_export"):
        i = r["files"][role]
        lines.append(f"| `{role}` | `{i['sha256']}` |")
    lines += ["", "| Coordinate | Windows | Mac single | Delta |", "| --- | --- | --- | --- |"]
    for item in r["residuals"]:
        lines.append(f"| `({item['xy'][0]},{item['xy'][1]})` | `{item['windows']}` | `{item['mac_single']}` | `{item['delta']}` |")
    lines += ["", "## Host And Actual-AEX Gates", "", f"- Manifest contracts compatible: `{r['host_contracts_compatible']}` (1920x1080, 16bpc, SOFTWARE, pixel aspect 1, resolution [1,1], same OLMBlur case parameters).", f"- Dated Windows return classification: accepted same-run export provenance=`{r['windows_return_classification']['accepted_same_run_export_provenance']}`, not OLMBlur worker trace=`{r['windows_return_classification']['not_olmblur_worker_trace']}`.", f"- Actual-AEX typed replay self-check: `{r['actual_aex']['portable_trace_self_check']}`; first Windows internal difference: `{r['actual_aex']['first_windows_internal_difference_reason']}`.", f"- Mac observation supplied=`{r['mac_observation']['provided']}`, identity-bound=`{r['mac_observation']['bound']}`.", f"- CDB attach used by this analysis: `{r['gates']['cdb_attach_used']}`.", "", "## Coordinate/Provenance Decision", "", f"- Status: `{r['mapping']['status']}`.", f"- {r['mapping']['reason']}"]
    if r["verdict"] == "separate-lanes":
        lines.append("- The exported residual lane remains separate from the historical internal-witness lane; this does not identify the upstream cause.")
    elif r["verdict"] == "ae-exact-observed":
        lines.append("- The identity-bound Mac AE export is byte-exact for this declared case; no residual mapping is needed.")
    lines += ["", "## INFERENCE", ""]
    lines += [f"- {item}" for item in r["inference"]]
    lines += ["", "## Automated Tests", "", "- `python3 refs/scripts/smoke_analyze_olmblur_residual_locus_20260715.py`", "- The smoke test asserts exact Windows SHA-256, exact one-pixel residual and channel deltas, manifest geometry/parameter compatibility, actual-AEX limitation, no CDB flag, and fail-closed missing-artifact behavior.", ""]
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--windows-export", type=Path, default=WINDOWS)
    p.add_argument("--mac-single-export", type=Path, default=MAC_SINGLE)
    p.add_argument("--windows-manifest", type=Path, default=WINDOWS_MANIFEST)
    p.add_argument("--mac-manifest", type=Path, default=MAC_MANIFEST)
    p.add_argument("--actual-aex", type=Path, default=ACTUAL_AEX)
    p.add_argument("--windows-return-report", type=Path, default=WINDOWS_RETURN)
    p.add_argument("--mac-observation-report", type=Path, default=None)
    p.add_argument("--output-json", type=Path, default=OUT_JSON)
    p.add_argument("--output-md", type=Path, default=OUT_MD)
    args = p.parse_args()
    report = build(args)
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(report), encoding="utf-8")
    print(f"[{report['verdict']}] {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
