#!/usr/bin/env python3
"""Package a one-case OLMDirectionalBlur 8bpc Mac AE validation.

This is intentionally a package/compare tool. It never launches After Effects,
builds a plug-in, or installs anything. A later operator may run the staged JSX
manually, then use ``--compare-return`` against its JSON return.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import plistlib
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
WINDOWS_DIR = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur"
WINDOWS_MANIFEST = WINDOWS_DIR / "reference_manifest.json"
STEM = "olmdirectionalblur_8bpc_mac_validation_20260718"
PLUGIN_NAME = "OLMDirectionalBlur.plugin"
EXECUTABLE_NAME = "OLMDirectionalBlur"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(message: str) -> "NoReturn":
    raise ValueError(message)


def load_case() -> tuple[dict, dict]:
    data = json.loads(WINDOWS_MANIFEST.read_text(encoding="utf-8"))
    if data.get("platform") != "windows" or data.get("comp", {}).get("bpc") != 8:
        fail("canonical reference is not the Windows 8bpc manifest")
    cases = [case for case in data.get("cases", []) if case.get("id") == "case_0001"]
    if len(cases) != 1:
        fail("canonical case_0001 is missing or duplicated")
    case = cases[0]
    effects = case.get("effects", [])
    if len(effects) != 1 or effects[0].get("match_name") != "OLM Directional Blur":
        fail("canonical case effect identity drifted")
    return data, case


def check_png(path: Path, expected: tuple[int, int]) -> None:
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        fail(f"{path}: not PNG")
    if len(raw) < 33 or raw[12:16] != b"IHDR":
        fail(f"{path}: missing IHDR")
    width, height, depth, color, compression, filt, interlace = struct.unpack(">IIBBBBB", raw[16:29])
    if (width, height) != expected:
        fail(f"{path}: dimensions {(width, height)} != {expected}")
    if (depth, color, compression, filt, interlace) != (8, 6, 0, 0, 0):
        fail(f"{path}: expected non-interlaced 8-bit RGBA PNG")


def png_dimensions(path: Path) -> tuple[int, int]:
    raw = path.read_bytes()
    if len(raw) < 29 or raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
        fail(f"{path}: missing PNG IHDR")
    return struct.unpack(">II", raw[16:24])


def decoded_rgba(path: Path) -> bytes:
    with Image.open(path) as image:
        return image.convert("RGBA").tobytes()


def plugin_identity(plugin: Path) -> dict:
    if plugin.name != PLUGIN_NAME or not plugin.is_dir():
        fail(f"--plugin-path must be an existing {PLUGIN_NAME} bundle")
    binary = plugin / "Contents/MacOS" / EXECUTABLE_NAME
    plist = plugin / "Contents/Info.plist"
    if not binary.is_file() or not plist.is_file():
        fail("plugin bundle is missing Contents/MacOS/OLMDirectionalBlur or Contents/Info.plist")
    try:
        info = plistlib.loads(plist.read_bytes())
    except (OSError, plistlib.InvalidFileException) as exc:
        fail(f"invalid plugin Info.plist: {exc}")
    if info.get("CFBundleExecutable") != EXECUTABLE_NAME or info.get("CFBundleName") != "OLMDirectionalBlur":
        fail("plugin Info.plist identity mismatch")
    return {
        "bundle_name": PLUGIN_NAME,
        "bundle_path_source": str(plugin.resolve()),
        "executable_path_source": str(binary.resolve()),
        "executable_name": EXECUTABLE_NAME,
        "executable_sha256": sha256(binary),
        "info_plist_sha256": sha256(plist),
        "install_performed": False,
    }


def request_manifest(manifest: dict, case: dict, plugin: dict) -> dict:
    effect = case["effects"][0]
    plugin_prefix = f"{effect['match_name']}-"
    params = [
        {"match_name": item["match_name"], "name": item["name"], "value": item["value"]}
        for item in effect["params"]
        if item.get("match_name", "").startswith(plugin_prefix)
        and item.get("property_value_type") in {"OneD", "LAYER_INDEX"}
    ]
    input_dimensions = png_dimensions(WINDOWS_DIR / case["before_effects_frame"])
    output_dimensions = png_dimensions(WINDOWS_DIR / case["frame"])
    if input_dimensions != output_dimensions:
        fail("canonical case input/output dimensions differ")
    if manifest["comp"]["width"] != input_dimensions[0] * 2 or manifest["comp"]["height"] != input_dimensions[1] * 2:
        fail("canonical case is not the expected half-resolution capture")
    return {
        "kind": "olmdirectionalblur_8bpc_mac_validation_request",
        "schema_version": 1,
        "request_id": STEM,
        "status": "package_only_no_ae_launch_no_install",
        "case": {
            "id": case["id"],
            "source_case_id": case["id"],
            "frame": 0,
            "input": {
                "path": str((WINDOWS_DIR / case["before_effects_frame"]).relative_to(ROOT)),
                "sha256": sha256(WINDOWS_DIR / case["before_effects_frame"]),
            },
            "windows_effect_output": {
                "path": str((WINDOWS_DIR / case["frame"]).relative_to(ROOT)),
                "sha256": sha256(WINDOWS_DIR / case["frame"]),
            },
            "source_comp": {"width": manifest["comp"]["width"], "height": manifest["comp"]["height"], "frame_rate": manifest["comp"]["frame_rate"]},
            "comp": {"width": manifest["comp"]["width"], "height": manifest["comp"]["height"], "pixel_aspect": 1, "frame_rate": manifest["comp"]["frame_rate"], "resolution_factor": [2, 2]},
            "render": {"width": input_dimensions[0], "height": input_dimensions[1]},
            "effect": {"name": effect["name"], "match_name": effect["match_name"], "params": params},
        },
        "windows_reference": {
            "manifest": str(WINDOWS_MANIFEST.relative_to(ROOT)),
            "ae_version": manifest["ae_version"],
            "renderer": "SOFTWARE",
            "bits_per_channel": 8,
            "output_format": "PNG",
        },
        "plugin_identity": plugin,
        "acceptance": {
            "comparison": "decoded_rgba_pixel_exact",
            "control_gate": "Mac no_effect must equal canonical before_effects before effect output is considered",
            "ae_exact_claim": False,
            "fail_closed": [
                "missing or changed canonical input/reference",
                "plugin bundle identity, executable, or plist mismatch",
                "installed Adobe plug-in path",
                "AE/project/renderer/8bpc contract drift",
                "missing control/effect return, wrong dimensions/PNG format, or hash mismatch",
                "any nonzero decoded RGBA pixel delta",
                "missing vmmap exact-path loaded-plugin proof",
            ],
        },
    }


def jsx_source(request: dict) -> str:
    case = request["case"]
    params = json.dumps(case["effect"]["params"], separators=(",", ":"))
    expected_plugin_hash = request["plugin_identity"]["executable_sha256"]
    return f'''(function () {{
    // Staged by {STEM}; the package command never executes this file.
    var CASE = {json.dumps(case, separators=(",", ":"))};
    var PARAMS = {params};
    var EXPECTED_PLUGIN_SHA256 = "{expected_plugin_hash}";
    function fail(message) {{ throw new Error("FAIL_CLOSED: " + message); }}
    function env(name) {{ try {{ return $.getenv(name) || ""; }} catch (e) {{ return ""; }} }}
    function write(path, text) {{ var f = new File(path); f.encoding = "UTF-8"; if (!f.open("w")) fail("cannot write " + path); f.write(text); f.close(); }}
    function shquote(value) {{ return "'" + String(value).replace(/'/g, "'\\\\''") + "'"; }}
    function hash(path) {{ var m = system.callSystem("/usr/bin/shasum -a 256 " + shquote(path)).match(/^([0-9a-fA-F]{{64}})\\s/); if (!m) fail("cannot hash " + path); return m[1].toLowerCase(); }}
    function find(group, matchName) {{ for (var i = 1; i <= group.numProperties; i++) {{ var p = group.property(i); if (p.matchName === matchName) return p; if (p.numProperties > 0) {{ var found = find(p, matchName); if (found) return found; }} }} return null; }}
    function setParams(effect) {{ for (var i = 0; i < PARAMS.length; i++) {{ var item = PARAMS[i], p = find(effect, item.match_name); if (!p) fail("missing " + item.match_name); p.setValue(item.value); }} }}
    function render(comp, effect, enabled, outputDir, name) {{ effect.enabled = enabled; var path = outputDir + "/" + name; var rendered = new File(path); if (rendered.exists && !rendered.remove()) fail("cannot remove stale render " + path); comp.saveFrameToPng(0, rendered); for (var wait = 0; wait < 1800; wait++) {{ rendered = new File(path); if (rendered.exists) break; $.sleep(100); }} if (!rendered.exists) fail("missing render " + path); var result = {{path: rendered.fsName, sha256: hash(rendered.fsName), effect_enabled: enabled}}; return result; }}
    var inputDir = env("OLM_AE_MAC_INPUT_DIR_20260718"), outputDir = env("OLM_AE_MAC_OUTPUT_DIR_20260718"), pluginPath = env("OLM_AE_MAC_PLUGIN_PATH_20260718"), resultPath = env("OLM_AE_MAC_RESULT_JSON_20260718");
    if (!inputDir || !outputDir || !pluginPath || !resultPath) fail("required environment missing");
    var plugin = new Folder(pluginPath), binary = new File(pluginPath + "/Contents/MacOS/OLMDirectionalBlur");
    if (!plugin.exists || plugin.name !== "{PLUGIN_NAME}" || !binary.exists) fail("plugin identity mismatch");
    var stagedHash = hash(binary.fsName); if (stagedHash !== EXPECTED_PLUGIN_SHA256) fail("staged plugin changed after package hash");
    var project = app.newProject(); project.bitsPerChannel = 8; project.linearBlending = false; try {{ project.gpuAccelType = GpuAccelType.SOFTWARE; }} catch (e) {{ fail("cannot set SOFTWARE"); }}
    var rendererRaw = Number(project.gpuAccelType), workingSpaceRaw = project.workingSpace, workingSpaceText = String(workingSpaceRaw);
    if (Number(project.bitsPerChannel) !== 8 || rendererRaw !== Number(GpuAccelType.SOFTWARE) || (workingSpaceText !== "" && workingSpaceText !== "None")) fail("project contract drift: bpc=" + project.bitsPerChannel + " renderer_raw=" + rendererRaw + " working_space_raw=" + workingSpaceText);
    var input = new File(inputDir + "/case_0001_before_effects_fullres_nearest.png"); if (!input.exists || hash(input.fsName) !== CASE.host_input.sha256) fail("host input identity mismatch");
    var footage = project.importFile(new ImportOptions(input));
    var comp = project.items.addComp(CASE.id, CASE.comp.width, CASE.comp.height, CASE.comp.pixel_aspect, 1, CASE.comp.frame_rate); comp.resolutionFactor = CASE.comp.resolution_factor;
    var layer = comp.layers.add(footage);
    var effect = layer.property("ADBE Effect Parade").addProperty(CASE.effect.match_name); if (!effect || effect.matchName !== CASE.effect.match_name) fail("effect identity mismatch"); setParams(effect);
    var control = render(comp, effect, false, outputDir, "case_0001__no_effect.png");
    var enabled = render(comp, effect, true, outputDir, "case_0001__effect_on.png");
    write(resultPath, JSON.stringify({{kind:"olmdirectionalblur_8bpc_mac_validation_return", schema_version:1, status:"candidate_return_pending_external_vmmap_proof", ae_exact_claim:false, request_id:"{STEM}", platform:"macOS", ae_version:app.version, project:{{bits_per_channel:project.bitsPerChannel, renderer:"SOFTWARE", renderer_raw:rendererRaw, working_space:"None", working_space_raw:workingSpaceRaw, working_space_raw_type:typeof workingSpaceRaw, linear_blending:project.linearBlending}}, staged_plugin:{{filename:plugin.name, path:binary.fsName, sha256:stagedHash, expected_sha256:EXPECTED_PLUGIN_SHA256}}, loaded_plugin_proof:{{status:"required", method:"vmmap_exact_path"}}, cases:[{{id:CASE.id, input:CASE.input, outputs:{{no_effect:control, effect_on:enabled}}}}]}}) + "\\n");
    try {{ project.close(CloseOptions.DO_NOT_SAVE_CHANGES); }} catch (e) {{}}
}}());
'''


def package(args: argparse.Namespace) -> int:
    manifest, case = load_case()
    identity = plugin_identity(args.plugin_path)
    request = request_manifest(manifest, case, identity)
    out = args.output_dir.resolve()
    if out.exists() and any(out.iterdir()):
        fail(f"output directory is non-empty: {out}")
    (out / "input").mkdir(parents=True, exist_ok=True)
    (out / "windows_reference").mkdir(parents=True, exist_ok=True)
    (out / "return").mkdir(parents=True, exist_ok=True)
    shutil.copy2(WINDOWS_DIR / case["before_effects_frame"], out / "input/case_0001_before_effects.png")
    host_input = out / "input/case_0001_before_effects_fullres_nearest.png"
    with Image.open(WINDOWS_DIR / case["before_effects_frame"]) as image:
        image.convert("RGBA").resize(
            (manifest["comp"]["width"], manifest["comp"]["height"]),
            Image.Resampling.NEAREST,
        ).save(host_input)
    request["case"]["host_input"] = {
        "path": "input/case_0001_before_effects_fullres_nearest.png",
        "sha256": sha256(host_input),
        "construction": "canonical 960x540 decoded RGBA nearest-neighbor 2x expansion",
    }
    shutil.copy2(WINDOWS_DIR / case["frame"], out / "windows_reference/case_0001.png")
    shutil.copy2(WINDOWS_MANIFEST, out / "windows_reference/reference_manifest.json")
    shutil.copytree(args.plugin_path, out / "plugin" / PLUGIN_NAME)
    (out / f"{STEM}_request.json").write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    (out / f"{STEM}_run.jsx").write_text(jsx_source(request), encoding="utf-8")
    wrapper = "\n".join([
        "$.setenv(%s, %s);" % (json.dumps("OLM_AE_MAC_INPUT_DIR_20260718"), json.dumps(str((out / "input").resolve()))),
        "$.setenv(%s, %s);" % (json.dumps("OLM_AE_MAC_OUTPUT_DIR_20260718"), json.dumps(str((out / "return").resolve()))),
        "$.setenv(%s, %s);" % (json.dumps("OLM_AE_MAC_PLUGIN_PATH_20260718"), json.dumps(identity["bundle_path_source"])),
        "$.setenv(%s, %s);" % (json.dumps("OLM_AE_MAC_RESULT_JSON_20260718"), json.dumps(str((out / "return" / "mac_validation_return.json").resolve()))),
        "$.evalFile(new File(%s));" % json.dumps(str((out / f"{STEM}_run.jsx").resolve())),
        "",
    ])
    (out / f"{STEM}_wrapper.jsx").write_text(wrapper, encoding="utf-8")
    package_meta = {"kind": "olmdirectionalblur_8bpc_mac_validation_package", "package_only": True, "ae_launched": False, "install_performed": False, "plugin": identity, "request": f"{STEM}_request.json"}
    (out / f"{STEM}_package.json").write_text(json.dumps(package_meta, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] wrote isolated package: {out}")
    return 0


def ae_process_proof(plugin_binary: Path, run=subprocess.run) -> dict[str, object]:
    found = run(["pgrep", "-x", "After Effects"], text=True, capture_output=True, timeout=10)
    pids = [int(value) for value in found.stdout.split() if value.isdigit()]
    if found.returncode != 0 or len(pids) != 1:
        raise RuntimeError(f"expected exactly one After Effects process, found {pids!r}")
    pid = pids[0]
    started = run(["ps", "-p", str(pid), "-o", "lstart="], text=True, capture_output=True, timeout=10)
    if started.returncode != 0 or not started.stdout.strip():
        raise RuntimeError("cannot read After Effects process start time")
    started_text = " ".join(started.stdout.split())
    started_at = dt.datetime.strptime(started_text, "%a %b %d %H:%M:%S %Y").timestamp()
    if plugin_binary.stat().st_mtime > started_at + 1:
        raise RuntimeError("plugin binary was modified after After Effects started; restart AE before validation")
    mapped = run(["vmmap", str(pid)], text=True, capture_output=True, timeout=120)
    resolved = str(plugin_binary.resolve())
    exact_mapping = any(re.search(r"\s" + re.escape(resolved) + r"$", line) for line in mapped.stdout.splitlines())
    if mapped.returncode != 0 or not exact_mapping:
        raise RuntimeError("requested OLMDirectionalBlur binary is not mapped in the After Effects process")
    return {
        "method": "vmmap_exact_path",
        "pid": pid,
        "process_started_local": started_text,
        "module_path": resolved,
        "module_sha256": sha256(plugin_binary),
        "binary_predates_process_start": True,
    }


def compare(args: argparse.Namespace) -> int:
    request = json.loads(args.request.read_text(encoding="utf-8"))
    failures: list[str] = []
    if request.get("status") != "package_only_no_ae_launch_no_install": failures.append("request is not the dated package contract")
    data = json.loads(args.return_json.read_text(encoding="utf-8"))
    if data.get("kind") != "olmdirectionalblur_8bpc_mac_validation_return": failures.append("return kind mismatch")
    if data.get("schema_version") != 1: failures.append("return schema mismatch")
    if data.get("request_id") != request.get("request_id"): failures.append("return request id mismatch")
    if data.get("status") != "candidate_return_pending_external_vmmap_proof": failures.append("return status mismatch")
    if data.get("platform") != "macOS": failures.append("return platform mismatch")
    if data.get("ae_exact_claim") is not False: failures.append("ae_exact_claim must be false")
    project = data.get("project", {})
    if (
        project.get("bits_per_channel") != 8
        or project.get("renderer") != "SOFTWARE"
        or project.get("renderer_raw") != 1816
        or project.get("working_space") != "None"
        or project.get("working_space_raw") not in {"", "None"}
        or project.get("working_space_raw_type") != "string"
        or project.get("linear_blending") is not False
    ):
        failures.append("project contract drift")
    expected_hash = request["plugin_identity"]["executable_sha256"]
    plugin = args.plugin_path.resolve()
    plugin_binary = plugin / "Contents/MacOS" / EXECUTABLE_NAME
    if plugin.name != PLUGIN_NAME or not plugin.is_dir() or not plugin_binary.is_file(): failures.append("operator plugin path is not a valid bundle")
    expected_path = request["plugin_identity"].get("executable_path_source")
    if str(plugin_binary.resolve()) != expected_path: failures.append("operator plugin path differs from packaged source path")
    staged = data.get("staged_plugin", {})
    if staged.get("filename") != PLUGIN_NAME or staged.get("expected_sha256") != expected_hash or staged.get("sha256") != expected_hash: failures.append("staged plugin identity/hash mismatch")
    proof = None
    if plugin_binary.is_file() and str(plugin_binary.resolve()) == expected_path:
        try:
            proof = ae_process_proof(plugin_binary)
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            failures.append(f"loaded plugin vmmap proof failed: {exc}")
    if proof is not None and (proof["module_sha256"] != expected_hash):
        failures.append("loaded plugin vmmap hash mismatch")
    cases = data.get("cases", [])
    if len(cases) != 1 or cases[0].get("id") != request["case"]["id"]: failures.append("case identity mismatch")
    case = cases[0] if cases else {}
    if case.get("input", {}).get("sha256") != request["case"]["input"]["sha256"]: failures.append("input hash mismatch")
    output_dir = args.return_json.parent
    expected = {"no_effect": request["case"]["input"], "effect_on": request["case"]["windows_effect_output"]}
    output_hashes = {}
    for branch, ref in expected.items():
        item = case.get("outputs", {}).get(branch, {})
        path = Path(item.get("path", "")); path = path if path.is_absolute() else output_dir / path
        if not path.is_file(): failures.append(f"missing {branch} PNG"); continue
        try: check_png(path, (request["case"]["render"]["width"], request["case"]["render"]["height"]))
        except ValueError as exc: failures.append(str(exc)); continue
        digest = sha256(path); output_hashes[branch] = digest
        if item.get("sha256") != digest: failures.append(f"{branch} hash mismatch")
        reference = ROOT / ref["path"] if branch == "effect_on" else ROOT / request["case"]["input"]["path"]
        if not reference.is_file() or sha256(reference) != ref["sha256"]: failures.append(f"canonical {branch} reference missing/changed")
        elif decoded_rgba(path) != decoded_rgba(reference): failures.append(f"{branch} decoded RGBA pixel delta")
    report = {"kind": "olmdirectionalblur_8bpc_mac_validation_report", "schema_version": 1, "status": "pass" if not failures else "fail_closed", "ae_exact_claim": False, "failures": failures, "pixel_exact": not failures, "loaded_plugin_proof": proof, "output_hashes": output_hashes}
    target = args.report or output_dir / f"{STEM}_report.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(("[OK]" if not failures else "[FAIL_CLOSED]") + f" wrote {target}")
    return 0 if not failures else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-path", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--compare-return", type=Path, dest="return_json")
    parser.add_argument("--request", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        if args.return_json:
            if not args.request or not args.plugin_path: parser.error("--compare-return requires --request and --plugin-path")
            return compare(args)
        if not args.plugin_path or not args.output_dir: parser.error("package mode requires --plugin-path and --output-dir")
        return package(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL_CLOSED] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
