#!/usr/bin/env python3
"""Replay the three accepted Windows ColorKeep boundary rows in fresh Mac AE hosts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import plistlib
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip"
RETURN = ROOT / "refs/returns/windows/RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip"
WINDOWS_JSX = ROOT / "scripts/ae_render_olm_windows_ae_release_boundary_20260806.jsx"
APP = Path("/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app")
AE_BINARY = APP / "Contents/MacOS/After Effects"
PLUGIN = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin"
PLUGIN_BINARY = PLUGIN / "Contents/MacOS/ColorKeep"
MANIFEST = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
EXPECTED_AE_VERSION = "26.3.0"
ROW_PREFIX = "colorkeep__discovery_3__colorkeep_opaque_cells_red_darkgray__"
DEPTHS = (8, 16, 32)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_members(path: Path) -> dict[str, bytes]:
    members: dict[str, bytes] = {}
    folded: set[str] = set()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            pure = PurePosixPath(name)
            if name.startswith("/") or any(part in ("", ".", "..") for part in pure.parts):
                raise RuntimeError(f"unsafe ZIP member: {name}")
            if name.casefold() in folded:
                raise RuntimeError(f"duplicate Windows ZIP member: {name}")
            folded.add(name.casefold())
            members[name] = archive.read(info)
    return members


def write_member(root: Path, name: str, payload: bytes) -> Path:
    path = root.joinpath(*PurePosixPath(name).parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def load_comparator():
    source = ROOT / "scripts/compare_float_exr.py"
    tools = ROOT / "handoffs/windows_batch/olm_windows_all_plugins_reference_campaign_20260731_r5/tools"
    sys.path.insert(0, str(tools))
    spec = importlib.util.spec_from_file_location("olm_colorkeep_float_compare", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load strict FLOAT32 EXR comparator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ae_pids() -> list[int]:
    result = subprocess.run(
        ["pgrep", "-f", f"^{AE_BINARY}$"], capture_output=True, text=True
    )
    return [int(item) for item in result.stdout.split() if item.isdigit()]


def wait_for(predicate, timeout: float, description: str):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.2)
    raise RuntimeError(f"timeout waiting for {description}")


def mapped_exact(pid: int, path: Path) -> bool:
    result = subprocess.run(["vmmap", str(pid)], capture_output=True, text=True, timeout=120)
    return result.returncode == 0 and any(str(path.resolve()) in line for line in result.stdout.splitlines())


def verify_preflight() -> tuple[dict, str]:
    if not REQUEST.is_file() or not RETURN.is_file() or not WINDOWS_JSX.is_file():
        raise RuntimeError("request, return, or canonical JSX is missing")
    verify = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_windows_ae_release_boundary_minimal_20260806.py"), str(RETURN), str(REQUEST)],
        cwd=ROOT, capture_output=True, text=True, timeout=300,
    )
    if verify.returncode:
        raise RuntimeError(f"Windows return rejected: {verify.stdout}{verify.stderr}")
    accepted = json.loads(verify.stdout)
    if accepted.get("status") != "accepted":
        raise RuntimeError("Windows return did not reach accepted state")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    row = next((item for item in manifest["plugins"] if item["plugin"] == "ColorKeep"), None)
    if row is None or row.get("installed_bundle") != str(PLUGIN):
        raise RuntimeError("ColorKeep installed identity manifest row missing")
    plugin_hash = sha256(PLUGIN_BINARY)
    if plugin_hash != row.get("sha256"):
        raise RuntimeError(f"installed ColorKeep hash drift: {plugin_hash}")
    file_info = subprocess.run(["file", str(PLUGIN_BINARY)], capture_output=True, text=True, check=True).stdout
    if "x86_64" not in file_info or "arm64" not in file_info:
        raise RuntimeError("installed ColorKeep is not Universal x86_64+arm64")
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(PLUGIN)], check=True, capture_output=True)
    with (APP / "Contents/Info.plist").open("rb") as stream:
        version = plistlib.load(stream).get("CFBundleShortVersionString")
    if version != EXPECTED_AE_VERSION:
        raise RuntimeError(f"AE version drift: {version!r}")
    return accepted, plugin_hash


def prepare(root: Path) -> tuple[dict, dict[str, bytes]]:
    request_members = normalized_members(REQUEST)
    returned = normalized_members(RETURN)
    contract = json.loads(request_members["BATCH_CONTRACT.json"])
    wanted = [row for row in contract["acquire"] if row["row_id"].startswith(ROW_PREFIX)]
    if [row["depth"] for row in wanted] != list(DEPTHS):
        raise RuntimeError("ColorKeep request rows drifted")
    needed = {"BATCH_CONTRACT.json", "inputs/opaque_cells_rgba8.png", "inputs/preserve_rgb_template.aep"}
    for name in needed:
        write_member(root, name, request_members[name])
    source_hashes = {row["source_sha256"] for row in wanted}
    template_hashes = {
        row["project_contract"]["input_interpretation"]["template_sha256"] for row in wanted
    }
    if source_hashes != {hashlib.sha256(request_members["inputs/opaque_cells_rgba8.png"]).hexdigest()}:
        raise RuntimeError("ColorKeep source member hash drift")
    if template_hashes != {hashlib.sha256(request_members["inputs/preserve_rgb_template.aep"]).hexdigest()}:
        raise RuntimeError("Preserve-RGB template member hash drift")
    # Preserve the canonical Windows row logic. macOS ExtendScript does not
    # observe a marker created while a script is running, so continue directly
    # after writing ready.json. The orchestrator proves vmmap concurrently while
    # AE renders, then quits the still-live process after the result is read.
    # The extra readback is observational and does not alter the render path.
    jsx = WINDOWS_JSX.read_text(encoding="utf-8")
    old_poll = 'while(!marker.exists&&(new Date()).getTime()<deadline) $.sleep(100); if(!marker.exists) die("continue timeout");'
    new_poll = '/* macOS orchestrator: module mapping is sampled concurrently during render */'
    if jsx.count(old_poll) != 1:
        raise RuntimeError("canonical JSX marker poll anchor drift")
    jsx = jsx.replace(old_poll, new_poll)
    old_quit = 'try { app.quit(); } catch(_) {}'
    if jsx.count(old_quit) != 1:
        raise RuntimeError("canonical JSX quit anchor drift")
    jsx = jsx.replace(old_quit, '/* macOS orchestrator quits after post-render mapping/result checks */')
    old_replace = 'footage[0].replace(new File(root+"/"+row.source_member)); footage[0].mainSource.alphaMode=AlphaMode.STRAIGHT;'
    new_replace = old_replace + ' var sourceInterpretation={alphaMode:Number(footage[0].mainSource.alphaMode),premulColor:footage[0].mainSource.premulColor,preserveRGB:footage[0].mainSource.preserveRGB,colorProfileName:footage[0].mainSource.colorProfileName};'
    if jsx.count(old_replace) != 1:
        raise RuntimeError("canonical JSX source replacement anchor drift")
    jsx = jsx.replace(old_replace, new_replace)
    old_summary = 'linear_blending:pr.linearBlending,parameters_before:before,parameters_after:after,'
    new_summary = 'linear_blending:pr.linearBlending,source_interpretation:sourceInterpretation,parameters_before:before,parameters_after:after,'
    if jsx.count(old_summary) != 1:
        raise RuntimeError("canonical JSX result anchor drift")
    jsx = jsx.replace(old_summary, new_summary)
    old_no = 'var no=render(comp,effect,false,out+"/no_effect.exr",template,cs.render_time_span_start_seconds,cs.render_time_span_duration_seconds);'
    old_yes = 'var yes=render(comp,effect,true,out+"/effect_on.exr",template,cs.render_time_span_start_seconds,cs.render_time_span_duration_seconds);'
    if jsx.count(old_no) != 1 or jsx.count(old_yes) != 1:
        raise RuntimeError("canonical JSX render anchors drift")
    jsx = jsx.replace(old_no, 'app.beginSuppressDialogs(); ' + old_no)
    jsx = jsx.replace(old_yes, old_yes + ' app.endSuppressDialogs(false);')
    (root / "render_row.jsx").write_text(jsx, encoding="utf-8")
    for row in wanted:
        base = f"outputs/{row['row_id']}"
        for leaf in ("no_effect.exr", "effect_on.exr", "attestation.json", "ae_result.json"):
            write_member(root / "windows", f"{base}/{leaf}", returned[f"{base}/{leaf}"])
    return contract, returned


def wrapper_source(values: dict[str, str], payload: Path) -> str:
    lines = [f"$.setenv({json.dumps(key)},{json.dumps(value)});" for key, value in values.items()]
    lines.append(f"$.evalFile(new File({json.dumps(str(payload))}));")
    return "\n".join(lines) + "\n"


def run_row(root: Path, row: dict, plugin_hash: str) -> dict:
    if ae_pids():
        raise RuntimeError(f"fresh-host gate failed before {row['row_id']}: {ae_pids()}")
    row_root = root / "mac" / "outputs" / row["row_id"]
    row_root.mkdir(parents=True, exist_ok=True)
    ready = row_root / "ready.json"
    marker = row_root / "continue.marker"
    result = row_root / "ae_result.json"
    wrapper = row_root / "wrapper.jsx"
    nonce = hashlib.sha256(f"{row['row_id']}:{time.time_ns()}".encode()).hexdigest()
    env = {
        "OLM_BOUNDARY_ROOT": str(root),
        "OLM_BOUNDARY_ROW_ID": row["row_id"],
        "OLM_BOUNDARY_ROW_OUTPUT": str(row_root),
        "OLM_BOUNDARY_RESULT": str(result),
        "OLM_BOUNDARY_READY": str(ready),
        "OLM_BOUNDARY_CONTINUE": str(marker),
        "OLM_BOUNDARY_NONCE": nonce,
        "OLM_BOUNDARY_OUTPUT_TEMPLATE": "OLM EXR 32 Float",
    }
    wrapper.write_text(wrapper_source(env, root / "render_row.jsx"), encoding="utf-8")
    command = (
        'with timeout of 7200 seconds\n'
        'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file '
        + json.dumps(str(wrapper)) + " with override\nend timeout\n"
    )
    launched_at = dt.datetime.now(dt.timezone.utc).isoformat()
    process = subprocess.Popen(["osascript"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert process.stdin is not None
    process.stdin.write(command)
    process.stdin.close()
    wait_for(ready.is_file, 300, f"{row['row_id']} ready marker")
    pids = wait_for(lambda: ae_pids() if len(ae_pids()) == 1 else None, 30, "one AE process")
    pid = pids[0]
    if not mapped_exact(pid, PLUGIN_BINARY):
        process.kill()
        raise RuntimeError(f"ColorKeep exact module path absent from fresh AE PID {pid}")
    if sha256(PLUGIN_BINARY) != plugin_hash:
        process.kill()
        raise RuntimeError("ColorKeep binary changed during row")
    try:
        returncode = process.wait(timeout=7200)
    except subprocess.TimeoutExpired:
        process.kill()
        raise RuntimeError(f"AE row timed out: {row['row_id']}")
    stderr = process.stderr.read() if process.stderr else ""
    try:
        if returncode or not result.is_file():
            raise RuntimeError(f"AE row failed ({returncode}): {stderr}")
        payload = json.loads(result.read_text(encoding="utf-8"))
        if payload.get("status") != "ok" or payload.get("parameters_before") != payload.get("parameters_after"):
            raise RuntimeError(f"AE row result rejected: {payload}")
        if not mapped_exact(pid, PLUGIN_BINARY):
            raise RuntimeError(f"ColorKeep mapping disappeared before row completion in PID {pid}")
    finally:
        subprocess.run(
            ["osascript", "-e", 'tell application "Adobe After Effects 2026" to quit saving no'],
            capture_output=True, text=True, timeout=120,
        )
    wait_for(lambda: not ae_pids(), 120, "fresh AE process exit")
    return {"pid": pid, "launched_at_utc": launched_at, "module_path": str(PLUGIN_BINARY.resolve()), "module_sha256": plugin_hash, "module_mapped_exact": True, "ae_result": payload}


def compare_rows(root: Path, contract: dict, plugin_hash: str, runs: dict[str, dict]) -> dict:
    comparator = load_comparator()
    rows = []
    for row in contract["acquire"]:
        if not row["row_id"].startswith(ROW_PREFIX):
            continue
        row_id = row["row_id"]
        pairs = {}
        for leaf in ("no_effect", "effect_on"):
            reference = root / "windows" / "outputs" / row_id / f"{leaf}.exr"
            candidate_source = Path(runs[row_id]["ae_result"][f"{leaf}_source"])
            result = comparator.compare(reference, candidate_source)
            pairs[leaf] = {
                **result,
                "exact": result["mismatched_values"] == 0,
                "windows_sha256": sha256(reference),
                "mac_sha256": sha256(candidate_source),
            }
        windows_off, width, height = comparator.read_planes(root / "windows" / "outputs" / row_id / "no_effect.exr")
        windows_on, _, _ = comparator.read_planes(root / "windows" / "outputs" / row_id / "effect_on.exr")
        mac_off, _, _ = comparator.read_planes(Path(runs[row_id]["ae_result"]["no_effect_source"]))
        mac_on, _, _ = comparator.read_planes(Path(runs[row_id]["ae_result"]["effect_on_source"]))
        retained = 0
        rejected = 0
        keep_mask_mismatches = 0
        cross_off_alpha_mismatches = 0
        cross_on_alpha_mismatches = 0
        windows_relation_mismatches = 0
        mac_relation_mismatches = 0
        explained_cross_effect_mismatches = 0
        unexplained_cross_effect_mismatches = 0
        zero = b"\0\0\0\0"
        for offset in range(0, width * height * 4, 4):
            win_keep = windows_on["A"][offset:offset + 4] == windows_off["A"][offset:offset + 4]
            mac_keep = mac_on["A"][offset:offset + 4] == mac_off["A"][offset:offset + 4]
            retained += int(win_keep)
            rejected += int(not win_keep)
            keep_mask_mismatches += int(win_keep != mac_keep)
            cross_off_alpha_mismatches += int(windows_off["A"][offset:offset + 4] != mac_off["A"][offset:offset + 4])
            cross_on_alpha_mismatches += int(windows_on["A"][offset:offset + 4] != mac_on["A"][offset:offset + 4])
            for channel in "RGBA":
                wo = windows_off[channel][offset:offset + 4]
                wn = windows_on[channel][offset:offset + 4]
                mo = mac_off[channel][offset:offset + 4]
                mn = mac_on[channel][offset:offset + 4]
                windows_relation_mismatches += int(wn != (wo if win_keep else zero))
                mac_relation_mismatches += int(mn != (mo if mac_keep else zero))
                if wn != mn:
                    if win_keep and mac_keep and wo != mo:
                        explained_cross_effect_mismatches += 1
                    else:
                        unexplained_cross_effect_mismatches += 1
        relation = {
            "pixel_count": width * height,
            "retained_pixels": retained,
            "rejected_pixels": rejected,
            "cross_host_keep_mask_mismatches": keep_mask_mismatches,
            "cross_host_no_effect_alpha_mismatches": cross_off_alpha_mismatches,
            "cross_host_effect_on_alpha_mismatches": cross_on_alpha_mismatches,
            "windows_effect_is_exact_control_or_zero_mismatches": windows_relation_mismatches,
            "mac_effect_is_exact_control_or_zero_mismatches": mac_relation_mismatches,
            "cross_effect_values_explained_by_retained_control_rgb_difference": explained_cross_effect_mismatches,
            "cross_effect_values_unexplained_by_control_or_keep_mask": unexplained_cross_effect_mismatches,
        }
        relation["plugin_relation_exact"] = all(relation[key] == 0 for key in (
            "cross_host_keep_mask_mismatches",
            "cross_host_no_effect_alpha_mismatches",
            "cross_host_effect_on_alpha_mismatches",
            "windows_effect_is_exact_control_or_zero_mismatches",
            "mac_effect_is_exact_control_or_zero_mismatches",
            "cross_effect_values_unexplained_by_control_or_keep_mask",
        ))
        rows.append({
            "row_id": row_id,
            "depth": row["depth"],
            "execution_row_sha256": row["execution_row_sha256"],
            "source_sha256": row["source_sha256"],
            "windows_aex_sha256": row["aex_sha256"],
            "mac_plugin_sha256": plugin_hash,
            "fresh_mac_process": runs[row_id]["pid"],
            "mac_module_mapping": {key: runs[row_id][key] for key in ("module_path", "module_sha256", "module_mapped_exact")},
            "parameters_before": runs[row_id]["ae_result"]["parameters_before"],
            "parameters_after": runs[row_id]["ae_result"]["parameters_after"],
            "source_interpretation": runs[row_id]["ae_result"].get("source_interpretation"),
            "comparisons": pairs,
            "pixel_exact": all(item["exact"] for item in pairs.values()),
            "same_host_control_relation": relation,
        })
    raw_exact = len(rows) == 3 and all(row["pixel_exact"] for row in rows)
    relation_exact = len(rows) == 3 and all(row["same_host_control_relation"]["plugin_relation_exact"] for row in rows)
    return {
        "kind": "colorkeep_windows_mac_ae_boundary_intake",
        "schema_version": 1,
        "status": "raw_exact" if raw_exact else ("host_color_transform_boundary_plugin_relation_exact" if relation_exact else "plugin_relation_mismatch"),
        "raw_cross_host_pixel_exact": raw_exact,
        "plugin_relation_exact_after_same_host_control": relation_exact,
        "causal_boundary": "When raw exact is false but plugin relation is exact, every enabled-output difference is inherited from the corresponding retained no-effect RGB value; selection mask, alpha, rejection-to-zero, and kept control values are exact within each host.",
        "claim_boundary": "ColorKeep colorkeep_opaque_cells_red_darkgray only, AE 26.3x87, Software, None working space, linear blending off, straight Preserve-RGB input, PF8/PF16/PF32, frame 24; not generalized.",
        "windows_return": str(RETURN.relative_to(ROOT)),
        "windows_return_sha256": sha256(RETURN),
        "request": str(REQUEST.relative_to(ROOT)),
        "request_sha256": sha256(REQUEST),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="explicitly launch and quit fresh AE once per depth")
    parser.add_argument("--run-root", type=Path, default=ROOT / "tmp/colorkeep_windows_boundary_mac_20260806")
    parser.add_argument("--report", type=Path, default=ROOT / "refs/conformance/colorkeep_windows_mac_ae_boundary_20260806.json")
    args = parser.parse_args()
    try:
        accepted, plugin_hash = verify_preflight()
        run_root = args.run_root.resolve()
        if run_root.exists():
            shutil.rmtree(run_root)
        run_root.mkdir(parents=True)
        contract, _ = prepare(run_root)
        summary = {"status": "preflight_passed_not_executed", "windows_rows_accepted": len(accepted["rows"]), "plugin_sha256": plugin_hash, "run_root": str(run_root)}
        if not args.execute:
            print(json.dumps(summary, indent=2))
            return 0
        runs = {}
        for row in contract["acquire"]:
            if row["row_id"].startswith(ROW_PREFIX):
                runs[row["row_id"]] = run_row(run_root, row, plugin_hash)
        report = compare_rows(run_root, contract, plugin_hash, runs)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0 if report["status"] in ("raw_exact", "host_color_transform_boundary_plugin_relation_exact") else 1
    except Exception as exc:
        print(f"[FAIL_CLOSED] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
