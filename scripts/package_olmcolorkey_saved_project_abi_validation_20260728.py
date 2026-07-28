#!/usr/bin/env python3
"""Package a fail-closed Mac AE saved-project ABI validation harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STEM = "olmcolorkey_saved_project_abi_validation_20260728"
DEFAULT_OUTPUT = ROOT / "refs/runtime_trace_packages" / f"{STEM}.zip"

STRUCTURAL_ROWS = [
    ("COLOR_KEEP_DISK_ID", 1, "leaf"),
    ("THRESHOLD_DISK_ID", 2, "leaf"),
    ("THRESHOLD_GROUP_START_DISK_ID", 3, "structural"),
    ("PREMULTIPLIED_DISK_ID", 4, "leaf"),
    ("COLOR_SPACE_DISK_ID", 5, "leaf"),
    ("FORCE_LOWER_PRECISION_DISK_ID", 0x20A, "leaf"),
    ("PER_COLOR_DISK_ID", 6, "leaf"),
    ("PER_COMPONENT_DISK_ID", 7, "leaf"),
    ("THRESHOLD_R_DISK_ID", 8, "leaf"),
    ("THRESHOLD_G_DISK_ID", 9, "leaf"),
    ("THRESHOLD_B_DISK_ID", 10, "leaf"),
    ("THRESHOLD_GROUP_END_DISK_ID", 11, "structural"),
    ("EDGE_THIN_GROUP_START_DISK_ID", 12, "structural"),
    ("EDGE_THIN_AMOUNT_DISK_ID", 0x0D, "leaf"),
    ("EDGE_THIN_DISTANCE_TYPE_DISK_ID", 0x0E, "leaf"),
    ("EDGE_THIN_GROUP_END_DISK_ID", 20, "structural"),
    ("EDGE_BLUR_GROUP_START_DISK_ID", 16, "structural"),
    ("EDGE_BLUR_AMOUNT_DISK_ID", 0x11, "leaf"),
    ("EDGE_BLUR_DISTANCE_TYPE_DISK_ID", 0x12, "leaf"),
    ("EDGE_BLUR_DIRECTION_DISK_ID", 0x13, "leaf"),
    ("EDGE_BLUR_GROUP_END_DISK_ID", 1016, "structural"),
    ("NUMBER_OF_COLORS_DISK_ID", 0x15, "leaf"),
    ("ENABLE_REPLACE_DISK_ID", 0x20B, "leaf"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def runner_source() -> str:
    return r'''#!/usr/bin/env python3
"""Preflight the packaged saved-project ABI request. Never controls or launches AE."""
from __future__ import annotations
import argparse, datetime, hashlib, json, plistlib, secrets
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQUEST = json.loads((HERE / "request_manifest.json").read_text(encoding="utf-8"))

def fail(message):
    raise SystemExit("FAIL_CLOSED: " + message)

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()

def required_file(raw, label):
    if not raw: fail(label + " path is required")
    p = Path(raw).expanduser().resolve()
    if not p.is_file(): fail(label + " is missing or not a file: " + str(p))
    return p

def plugin_identity(raw):
    p = Path(raw).expanduser().resolve()
    bundle = p if p.is_dir() else p.parents[2] if len(p.parents) > 2 else p
    binary = bundle / "Contents/MacOS/OLMColorKey"
    info = bundle / "Contents/Info.plist"
    if bundle.name != "OLMColorKey.plugin" or not binary.is_file() or not info.is_file():
        fail("exact OLMColorKey.plugin bundle, Info.plist, and Mach-O are required")
    with info.open("rb") as f: plist = plistlib.load(f)
    if plist.get("CFBundleExecutable") != "OLMColorKey":
        fail("CFBundleExecutable is not OLMColorKey")
    files = []
    for item in sorted(x for x in bundle.rglob("*") if x.is_file()):
        files.append({"path": str(item.relative_to(bundle)), "sha256": sha256(item), "size": item.stat().st_size})
    bundle_hash = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"bundle_path": str(bundle), "bundle_tree_sha256": bundle_hash,
            "macho_path": str(binary), "macho_sha256": sha256(binary), "bundle_files": files}

def expected_contract(raw):
    if not raw:
        return None
    path = required_file(raw, "expected readback contract")
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc: fail("expected readback contract is not valid JSON: " + str(exc))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        fail("expected readback contract schema_version must be 1")
    cases = value.get("cases")
    if not isinstance(cases, list) or not cases: fail("expected contract requires non-empty cases")
    roles = {x.get("role") for x in cases if isinstance(x, dict)}
    required_roles = {"windows_saved_distinctive_values", "prefix_mac_saved"}
    if roles != required_roles: fail("expected contract must contain exactly both project roles")
    for case in cases:
        effects = case.get("effects")
        if not isinstance(effects, list) or not effects: fail("each expected case requires effects")
        for effect in effects:
            if not isinstance(effect.get("selector"), dict): fail("each effect requires an exact selector")
            properties = effect.get("properties")
            if not isinstance(properties, list) or not properties: fail("each effect requires properties")
            for prop in properties:
                required = ("property_index", "match_name", "value", "keyframes")
                if not isinstance(prop, dict) or any(k not in prop for k in required):
                    fail("every expected property requires index, match_name, value, and keyframes")
    return {"path": str(path), "sha256": sha256(path), "contract": value}

def atomic_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--windows-saved-project")
    ap.add_argument("--prefix-mac-saved-project")
    ap.add_argument("--plugin-path")
    ap.add_argument("--output-dir", default=str(HERE / "return"))
    ap.add_argument("--expected-contract")
    ns = ap.parse_args(argv)
    windows = required_file(ns.windows_saved_project, "Windows-saved distinctive-values project")
    prefix = required_file(ns.prefix_mac_saved_project, "pre-fix Mac-saved project")
    if windows == prefix: fail("the two project inputs must be distinct paths")
    windows_hash, prefix_hash = sha256(windows), sha256(prefix)
    if windows_hash == prefix_hash: fail("the two project inputs must have distinct content hashes")
    plugin = plugin_identity(ns.plugin_path or "")
    contract = expected_contract(ns.expected_contract)
    out = Path(ns.output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    nonce = secrets.token_hex(16)
    run_dir = out / ("preflight-" + nonce)
    run_dir.mkdir()
    projects = [
        {"role": "windows_saved_distinctive_values", "path": str(windows), "sha256": windows_hash, "size": windows.stat().st_size},
        {"role": "prefix_mac_saved", "path": str(prefix), "sha256": prefix_hash, "size": prefix.stat().st_size},
    ]
    preflight = {"kind": REQUEST["kind"] + "_preflight", "schema_version": 1,
                 "status": "preflight_only_no_abi_exact_claim", "abi_exact_claim": False,
                 "abi_exact_claim_reason": "execution disabled: named AppleScript application dispatch cannot be proven bound to a validated PID",
                 "run_nonce": nonce,
                 "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 "request_sha256": sha256(HERE / "request_manifest.json"),
                 "plugin": plugin, "projects": projects, "expected_contract": contract,
                 "freshness_policy": {"isolated_run_directory": str(run_dir),
                    "required_return_nonce": nonce, "preexisting_result_or_png_accepted": False},
                 "unmet_exact_claim_requirements": [
                    "process-specific AE dispatch", "same-process exact loaded plug-in proof",
                    "returned project role/path/hash equality", "fresh nonce-bound outputs",
                    "all effects/cases exact match-name/value/keyframe comparison"]}
    atomic_json(run_dir / "preflight.json", preflight)
    print("[OK] preflight only; AE was not launched or controlled: " + str(run_dir))
    return 0
if __name__ == "__main__": raise SystemExit(main())
'''


def jsx_source() -> str:
    return '''/* Execution intentionally disabled.
This package cannot bind ExtendScript execution to a prevalidated AE PID.
It therefore cannot safely collect or claim ABI-exact evidence. */
throw new Error("FAIL_CLOSED: packaged AE execution is disabled");
'''


def build(output: Path, support: Path) -> None:
    support.mkdir(parents=True, exist_ok=True)
    rows = [
        {"ordinal": i + 1, "symbol": name, "disk_id": disk_id, "kind": kind}
        for i, (name, disk_id, kind) in enumerate(STRUCTURAL_ROWS)
    ]
    manifest = {
        "kind": "olmcolorkey_saved_project_abi_validation_request",
        "schema_version": 1,
        "status": "request_only_no_abi_exact_claim",
        "abi_exact_claim": False,
        "inputs": [
            {"role": "windows_saved_distinctive_values", "required": True, "sha256_required": True},
            {"role": "prefix_mac_saved", "required": True, "sha256_required": True},
        ],
        "plugin_identity": {
            "bundle_name": "OLMColorKey.plugin", "executable": "OLMColorKey",
            "bundle_tree_sha256_required": True, "macho_sha256_required": True,
        },
        "ae_identity": {"pid_required": True, "process_start_required": True, "executable_path_required": True},
        "capture_contract": {
            "project_path_and_sha256": True, "renderer_and_bits_per_channel": True,
            "property_index_match_name_and_expected_disk_id": True,
            "leaf_values_and_keyframes_where_scriptable": True,
            "structural_rows": rows, "same_run_render_path_and_sha256": True,
            "disk_id_limitation": "AE scripting does not expose PF disk IDs; disk IDs are exact expected registration identities, while property index/match name/value/keyframes are reopen readback.",
        },
        "verdict_gate": {
            "abi_exact_claim_default": False,
            "execution_supported": False,
            "required_for_any_future_claim": [
                "exact_target_process", "per_run_nonce", "exact_plugin_loaded",
                "exact_project_roles_paths_hashes", "fresh_outputs",
                "full_explicit_match_name_value_keyframe_contract", "all_effects_and_cases_validate"
            ],
        },
        "safety": {
            "launches_ae_by_default": False, "execution_path_removed": True,
            "installs_or_modifies_plugin": False,
            "modifies_input_projects": False,
        },
    }
    (support / "request_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (support / "run_saved_project_abi_validation.py").write_text(runner_source(), encoding="utf-8")
    (support / "run_saved_project_abi_validation.jsx").write_text(jsx_source(), encoding="utf-8")
    (support / "README.md").write_text(
        "Fail-closed OLMColorKey saved-project ABI request packager. The runner is preflight-only and never "
        "launches or controls AE. Execution was removed because named AppleScript application dispatch cannot "
        "be proven bound to a validated PID. This package never makes an ABI-exact claim.\n",
        encoding="utf-8",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(support.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(support))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support-dir", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix=STEM + "_") as raw:
        support = args.support_dir or Path(raw) / STEM
        if support.exists():
            shutil.rmtree(support)
        build(args.output.resolve(), support.resolve())
        print(f"[OK] wrote {args.output.resolve()}")
        if args.support_dir:
            print(f"[OK] support tree {support.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
