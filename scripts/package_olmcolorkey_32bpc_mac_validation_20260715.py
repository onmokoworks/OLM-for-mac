#!/usr/bin/env python3
"""Build the fail-closed OLMColorKey 32bpc Mac validation package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST_INDEX = ROOT / "refs/mac_validation_requests/olmcolorkey_32bpc_mac_validation_20260715.json"
WINDOWS_MANIFEST = ROOT / "refs/win_references/olm_reference_return_windows_20260703_32bpc_full_probe_exr_rerun/OLMbit-depthconformancebatch/reference_manifest.json"
WINDOWS_FLOAT_ROOT = ROOT / "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"
STEM = "olmcolorkey_32bpc_mac_validation_20260715"
DEFAULT_OUTPUT = ROOT / "refs/runtime_trace_packages" / f"{STEM}.zip"
MAC_PLUGIN_NAME = "OLMColorKey.plugin"
MAC_PLUGIN_BINARY_NAME = "OLMColorKey"
OUTPUT_TEMPLATE = "OLM EXR 32 Float"
CAPTURE_API = "OutputModule.getSettings(GetSettingsFormat.STRING)"
SEMANTIC_INTENT = {
    "channels": "RGB+Alpha",
    "sample_type": "32-bit float",
    "preserve_rgb": True,
    "linear_light_conversion": False,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_plugin_binary(path: Path) -> tuple[Path, Path]:
    """Return the validated bundle and its actual Mach-O executable."""
    supplied = path.expanduser().resolve()
    if supplied.is_dir():
        if supplied.name != MAC_PLUGIN_NAME:
            raise ValueError(f"plugin path must name {MAC_PLUGIN_NAME}")
        bundle = supplied
        binary = bundle / "Contents" / "MacOS" / MAC_PLUGIN_BINARY_NAME
    elif supplied.is_file():
        if supplied.name != MAC_PLUGIN_BINARY_NAME or supplied.parent.name != "MacOS" or supplied.parent.parent.name != "Contents":
            raise ValueError(f"binary path must be {MAC_PLUGIN_NAME}/Contents/MacOS/{MAC_PLUGIN_BINARY_NAME}")
        bundle = supplied.parent.parent.parent
        if bundle.name != MAC_PLUGIN_NAME:
            raise ValueError(f"binary path must be inside {MAC_PLUGIN_NAME}")
        binary = supplied
    else:
        raise FileNotFoundError(supplied)
    if not bundle.is_dir() or not binary.is_file():
        raise FileNotFoundError(f"missing {MAC_PLUGIN_BINARY_NAME} inside {bundle}")
    return bundle, binary


def load_cases() -> tuple[dict, list[dict]]:
    data = json.loads(WINDOWS_MANIFEST.read_text(encoding="utf-8"))
    cases = [case for case in data["cases"] if case["id"].startswith("olmcolorkey__")]
    if len(cases) != 9:
        raise ValueError(f"expected 9 OLMColorKey cases, found {len(cases)}")
    for case in cases:
        if case.get("render_set_id") != "software_32bpc":
            raise ValueError(f"case {case['id']} is not the Windows Software 32bpc set")
        if case.get("effects", [{}])[0].get("match_name") != "OLM Color Key":
            raise ValueError(f"case {case['id']} is not OLM Color Key")
    return data, cases


def compact_case(case: dict, input_name: str) -> dict:
    effect = case["effects"][0]
    params = []
    for param in effect.get("params", []):
        if param.get("value") is not None:
            params.append({"match_name": param["match_name"], "value": param["value"]})
    return {
        "id": case["id"],
        "input": input_name,
        "input_sha256": sha256(WINDOWS_MANIFEST.parent / input_name),
        "frame": case.get("time", 0),
        "comp": case["comp"],
        "effect": {
            "name": effect["name"],
            "match_name": effect["match_name"],
            "property_index": effect["property_index"],
            "params": params,
        },
    }


def windows_float_pairs(source_cases: list[dict]) -> list[dict]:
    pairs = []
    for case in source_cases:
        before = WINDOWS_FLOAT_ROOT / f"{Path(case['before_effects_frame']).stem}.exr"
        effect = WINDOWS_FLOAT_ROOT / f"{Path(case['frame']).stem}.exr"
        if not before.is_file() or not effect.is_file():
            raise FileNotFoundError(f"missing Windows FLOAT32 pair for {case['id']}")
        pairs.append({"id": case["id"], "no_effect": {"path": str(before.relative_to(ROOT)), "sha256": sha256(before)}, "effect_on": {"path": str(effect.relative_to(ROOT)), "sha256": sha256(effect)}})
    return pairs


def jsx_source(cases: list[dict]) -> str:
    cases_json = json.dumps(cases, separators=(",", ":"), ensure_ascii=True)
    return r'''/* OLMColorKey 32bpc Mac validation. AE host only; never installs a plug-in. */
(function () {
    var cases = CASES_JSON, MAC_PLUGIN_NAME = "OLMColorKey.plugin", MAC_PLUGIN_BINARY_NAME = "OLMColorKey";
    function env(name) { try { return $.getenv(name) || ""; } catch (e) { return ""; } }
    function fail(message) { throw new Error("FAIL_CLOSED: " + message); }
    function quote(value) { return '"' + String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r/g, "\\r").replace(/\n/g, "\\n") + '"'; }
    function stable(value) {
        if (value === null) return "null";
        if (typeof value === "string") return quote(value);
        if (typeof value === "number") { if (!isFinite(value)) fail("non-finite settings value"); return String(value); }
        if (typeof value === "boolean") return value ? "true" : "false";
        if (value instanceof Array) { var a = []; for (var i = 0; i < value.length; i++) a.push(stable(value[i])); return "[" + a.join(",") + "]"; }
        if (typeof value === "object") { var keys = []; for (var k in value) if (value.hasOwnProperty(k)) keys.push(k); keys.sort(); var o = []; for (var j = 0; j < keys.length; j++) o.push(quote(keys[j]) + ":" + stable(value[keys[j]])); return "{" + o.join(",") + "}"; }
        fail("unsupported JSON value");
    }
    function write(path, text) { var f = new File(path); f.encoding = "UTF-8"; if (!f.open("w")) fail("cannot write " + path); f.write(text); f.close(); }
    function shell(command) { try { return system.callSystem(command).replace(/[\r\n]+$/g, ""); } catch (e) { return ""; } }
    function shQuote(path) { return "'" + String(path).replace(/'/g, "'\\''") + "'"; }
    function hash(path) { var out = shell("/usr/bin/shasum -a 256 " + shQuote(path)); var m = out.match(/^([0-9a-fA-F]{64})\s/); if (!m) fail("cannot hash " + path); return m[1].toLowerCase(); }
    function findProperty(group, matchName) {
        for (var i = 1; i <= group.numProperties; i++) {
            var p = group.property(i);
            if (p.matchName === matchName) return p;
            if (p.numProperties && p.numProperties > 0) { var nested = findProperty(p, matchName); if (nested) return nested; }
        }
        return null;
    }
    function setParams(effect, params) {
        for (var i = 0; i < params.length; i++) {
            var p = findProperty(effect, params[i].match_name);
            if (!p) fail("missing effect property " + params[i].match_name);
            try { p.setValue(params[i].value); } catch (e) { fail("cannot set " + params[i].match_name + ": " + e.toString()); }
        }
    }
    function capture(module, outputPath, caseId, branch) {
        if (!module.getSettings || typeof GetSettingsFormat === "undefined" || typeof GetSettingsFormat.STRING === "undefined") fail("Output Module settings API unavailable");
        var settings = module.getSettings(GetSettingsFormat.STRING);
        if (!settings || typeof settings !== "object") fail("empty Output Module settings");
        var serialized = stable(settings);
        if (serialized === "{}") fail("empty Output Module settings");
        var record = { kind: "olm_output_module_settings_capture", schema_version: 1,
            output_template: OUTPUT_TEMPLATE, capture_api: CAPTURE_API, semantic_intent: SEMANTIC_INTENT, settings: settings };
        var path = outputPath.replace(/\.exr$/i, "_output_module_settings.json");
        write(path, stable(record) + "\n");
        return { path: path, sha256: hash(path), serialization: serialized, settings: settings };
    }
    function render(comp, outputDir, name, enabled, effect, caseId) {
        effect.enabled = enabled;
        var item = app.project.renderQueue.items.add(comp);
        item.timeSpanStart = 0; item.timeSpanDuration = 1.0 / comp.frameRate;
        var module = item.outputModule(1);
        module.applyTemplate(OUTPUT_TEMPLATE);
        var outputPath = outputDir + "/" + name;
        var captureRecord = capture(module, outputPath, caseId, enabled ? "effect_on" : "no_effect");
        module.file = new File(outputPath);
        app.project.renderQueue.render();
        if (!new File(outputPath).exists) fail("missing rendered output " + outputPath);
        var outputHash = hash(outputPath);
        item.remove();
        return { path: outputPath, sha256: outputHash, output_module_settings: captureRecord };
    }
    function resolvePluginIdentity(value) {
        var suppliedFile = new File(value), bundle;
        if (suppliedFile.exists && suppliedFile.name === MAC_PLUGIN_BINARY_NAME && suppliedFile.parent.name === "MacOS" && suppliedFile.parent.parent.name === "Contents") {
            bundle = new Folder(suppliedFile.parent.parent.parent.fsName);
        } else {
            bundle = new Folder(value);
        }
        if (!bundle.exists || bundle.name !== MAC_PLUGIN_NAME) fail("plugin identity path/name mismatch");
        var binary = new File(bundle.fsName + "/Contents/MacOS/" + MAC_PLUGIN_BINARY_NAME);
        if (!binary.exists || binary.name !== MAC_PLUGIN_BINARY_NAME) fail("plugin binary missing");
        return { bundle: bundle, binary: binary };
    }
    function identity() {
        var pluginPath = env("OLM_AE_MAC_PLUGIN_PATH"), expectedPluginHash = env("OLM_AE_MAC_PLUGIN_SHA256");
        if (!pluginPath) fail("OLM_AE_MAC_PLUGIN_PATH is required");
        var resolved = resolvePluginIdentity(pluginPath), file = resolved.binary;
        if (!/^[0-9a-fA-F]{64}$/.test(expectedPluginHash)) fail("OLM_AE_MAC_PLUGIN_SHA256 is required");
        var loadedHash = hash(file.fsName); if (loadedHash !== expectedPluginHash.toLowerCase()) fail("plugin changed after preflight hash");
        return { filename: resolved.bundle.name, bundle_path: resolved.bundle.fsName, path: file.fsName, sha256: loadedHash, expected_sha256: expectedPluginHash.toLowerCase() };
    }
    var outputDir = env("OLM_AE_MAC_OUTPUT_DIR");
    var manifestPath = env("OLM_AE_MAC_RESULT_JSON");
    if (!outputDir || !manifestPath) fail("output and result paths are required");
    var folder = new Folder(outputDir); if (!folder.exists) folder.create();
    var plugin = identity(), results = [], project = app.newProject();
    project.bitsPerChannel = 32;
    if (Number(project.bitsPerChannel) !== 32) fail("project is not 32bpc");
    try { project.gpuAccelType = GpuAccelType.SOFTWARE; } catch (e) { fail("cannot set SOFTWARE renderer: " + e.toString()); }
    if (String(project.gpuAccelType).toUpperCase() !== "SOFTWARE") fail("renderer is not SOFTWARE");
    project.linearBlending = false;
    if (project.workingSpace !== "None") fail("working space is not None");
    for (var c = 0; c < cases.length; c++) {
        var spec = cases[c], compSpec = spec.comp;
        var input = new File(env("OLM_AE_MAC_INPUT_DIR") + "/" + spec.input);
        if (!input.exists) fail("missing input " + spec.input);
        if (hash(input.fsName) !== spec.input_sha256) fail("input hash mismatch for " + spec.id);
        var footage = project.importFile(new ImportOptions(input));
        var comp = project.items.addComp(spec.id, compSpec.width, compSpec.height, compSpec.pixel_aspect, compSpec.duration, compSpec.frame_rate);
        var layer = comp.layers.add(footage), parade = layer.property("ADBE Effect Parade");
        var effect = parade.addProperty(spec.effect.match_name);
        if (!effect || effect.matchName !== spec.effect.match_name || effect.name !== spec.effect.name) fail("plugin effect identity mismatch for " + spec.id);
        setParams(effect, spec.effect.params);
        var noEffect = render(comp, outputDir, spec.id + "__no_effect.exr", false, effect, spec.id);
        var effectOn = render(comp, outputDir, spec.id + "__effect_on.exr", true, effect, spec.id);
        if (noEffect.output_module_settings.serialization !== effectOn.output_module_settings.serialization) fail("settings differ for " + spec.id);
        results.push({ id: spec.id, input: spec.input, plugin: plugin, effect: { name: effect.name, match_name: effect.matchName, enabled: true, params: spec.effect.params },
            outputs: { no_effect: noEffect, effect_on: effectOn }, no_effect_control_passed: true });
    }
    var result = { kind: "olmcolorkey_32bpc_mac_validation_return", schema_version: 1, status: "candidate_return_only",
        ae_exact_claim: false, ae_exact_claim_reason: "Mac/Windows raw-float comparison has not been returned", platform: "macOS", ae_version: app.version,
        project: { bits_per_channel: project.bitsPerChannel, working_space: "None", linear_blending: project.linearBlending, renderer: "SOFTWARE" },
        output_module: { template_name: OUTPUT_TEMPLATE, capture_api: CAPTURE_API, semantic_intent: SEMANTIC_INTENT }, plugin: plugin, cases: results };
    write(manifestPath, stable(result) + "\n");
    try { project.close(CloseOptions.DO_NOT_SAVE_CHANGES); } catch (e) {}
}());
'''.replace("CASES_JSON", cases_json).replace("OUTPUT_TEMPLATE", json.dumps(OUTPUT_TEMPLATE)).replace("CAPTURE_API", json.dumps(CAPTURE_API)).replace("SEMANTIC_INTENT", json.dumps(SEMANTIC_INTENT, separators=(",", ":")))


def build(output: Path, support: Path) -> None:
    if not REQUEST_INDEX.exists():
        raise FileNotFoundError(REQUEST_INDEX)
    reference, source_cases = load_cases()
    source_dir = WINDOWS_MANIFEST.parent
    compact = []
    for case in source_cases:
        input_name = case["before_effects_frame"]
        source = source_dir / input_name
        if not source.exists():
            raise FileNotFoundError(source)
        compact.append(compact_case(case, input_name))
    support.mkdir(parents=True, exist_ok=True)
    input_dir = support / "input"
    input_dir.mkdir(exist_ok=True)
    for case in compact:
        shutil.copy2(source_dir / case["input"], input_dir / case["input"])
    ref_copy = support / "windows_reference_manifest.json"
    shutil.copy2(WINDOWS_MANIFEST, ref_copy)
    manifest = {
        "kind": "olmcolorkey_32bpc_mac_validation_request",
        "schema_version": 1,
        "request_id": STEM,
        "status": "request_only_no_ae_exact_claim",
        "source_windows_manifest_sha256": sha256(ref_copy),
        "windows_float32_pairs": windows_float_pairs(source_cases),
        "cases": compact,
        "required_ae": {"major_minor": "26.3", "renderer": "SOFTWARE", "bits_per_channel": 32, "working_space": "None", "linear_blending": False},
        "plugin_identity": {"filename": MAC_PLUGIN_NAME, "binary_filename": MAC_PLUGIN_BINARY_NAME, "sha256_required": True, "path_must_be_explicit": True, "path_may_be_bundle_or_binary": True, "preflight_hash_must_equal_loaded_hash": True},
        "output_module": {"template_name": OUTPUT_TEMPLATE, "capture_api": CAPTURE_API, "semantic_intent": SEMANTIC_INTENT, "settings_sha256_must_match_per_case": True},
        "return_contract": {"outputs_per_case": ["no_effect", "effect_on"], "format": "FLOAT EXR", "sha256_required": True, "header_metadata_required": True, "raw_float_comparison_manifest_required": True},
        "fail_closed": ["reject missing or stale inputs", "reject plugin identity mismatch", "reject project or renderer drift", "reject missing no-effect control", "reject missing or unequal settings captures", "reject non-EXR or missing hashes", "do not claim AE exact before Mac/Windows raw-float comparison"],
    }
    (support / "request_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(REQUEST_INDEX, support / "mac_validation_request_index.json")
    (support / "run_mac_olmcolorkey_32bpc_validation.jsx").write_text(jsx_source(compact), encoding="utf-8")
    (support / "README.md").write_text("This is a Mac AE validation request only. It does not install or launch AE. Run the packaged Python runner on a Mac with AE already installed and the explicit OLMColorKey.plugin path. A return remains candidate evidence until compared against the Windows FLOAT EXR set.\n", encoding="utf-8")
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(support.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(support))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    support = args.support_dir or (ROOT / "refs/runtime_trace_packages" / STEM)
    if support.exists():
        shutil.rmtree(support)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    build(args.output, support)
    print(f"[OK] wrote {args.output}")
    print(f"[OK] support tree {support}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
