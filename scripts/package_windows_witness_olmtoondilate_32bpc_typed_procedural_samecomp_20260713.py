#!/usr/bin/env python3
"""Compile the common-core 32bpc same-comp typed-procedural fixture package.

Default output targets OLM Toon Dilate. The generator is parameterized so the
same package shape can be re-used for OLM Color Key without touching the shared
Windows witness launcher.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from textwrap import dedent
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.windows_witness.compiler import compile_witness  # noqa: E402
from tools.windows_witness.core import canonical_json, deterministic_zip, sha256_file  # noqa: E402


DATE_TAG = "20260713"
OUTPUT_TEMPLATE = "OLM EXR 32 Float"
REQUIRED_AE = "26.3"
FIXTURE_SOURCE = ROOT / "scripts" / "ae_generate_32bpc_typed_procedural_fixture.jsx"
COMPARE_FLOAT_SOURCE = ROOT / "scripts" / "compare_float_exr.py"
VERIFY_FLOAT_SOURCE = ROOT / "scripts" / "verify_32bpc_float_return.py"
TOONDILATE_FLOAT_HOOK_RVA = "0x1a6800"
TOONDILATE_SEARCH_RADIUS = 13.0
TOONDILATE_SEARCH_RADIUS_BITS = "0x41500000"

TOONDILATE_PARAMETERS = [
    {
        "name": "Search Radius",
        "match_name": "ADBE OLMToonDilate-0001",
        "property_index": 1,
        "property_value_type": "OneD",
        "minimum": 0.0,
        "maximum": 100.0,
        "value": TOONDILATE_SEARCH_RADIUS,
        "readback_tolerance": 0.0001,
    }
]

SOURCE_LAYERS = [
    {"name": "solid_background", "kind": "solid", "bounds": [0, 0, 64, 64], "rgb": [0, 0, 0], "alpha": 1.0},
    {"name": "rect_integer_a25", "kind": "solid", "bounds": [4, 4, 20, 16], "rgb": [1, 0, 0], "alpha": 0.25},
    {"name": "rect_integer_a50", "kind": "solid", "bounds": [28, 4, 20, 16], "rgb": [0, 1, 0], "alpha": 0.5},
    {"name": "rect_integer_a75", "kind": "solid", "bounds": [4, 28, 20, 16], "rgb": [0, 0, 1], "alpha": 0.75},
    {"name": "rect_integer_a100", "kind": "solid", "bounds": [28, 28, 20, 16], "rgb": [1, 1, 1], "alpha": 1.0},
]

FIXTURE_CONTRACT = {
    "manifest_kind": "olm_32bpc_typed_procedural_fixture",
    "project_bits_per_channel": 32,
    "working_space": "None",
    "linear_blending": False,
    "dimensions": [64, 64],
    "frame": 0,
    "source_policy": "AE-generated solids only; no footage imported",
    "render_policy": "same comp, only branch enabled state changes",
    "source_layers": SOURCE_LAYERS,
    "output_names": {
        "no_effect": "effect_no_effect_00000.exr",
        "effect_on": "effect_effect_on_00000.exr",
    },
}

EFFECTS: dict[str, dict[str, str]] = {
    "toondilate": {
        "effect_name": "OLM Toon Dilate",
        "effect_slug": "toondilate",
        "plugin_name": "OLMToonDilate.aex",
        "plugin_sha256": "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3",
        "default_aex_path": r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMToonDilate.aex",
        "default_mac_plugin_path": "/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMToonDilate.plugin",
        "request_id": f"olmtoondilate_32bpc_typed_procedural_samecomp_{DATE_TAG}",
        "package_dir": f"windows_witness_olmtoondilate_32bpc_typed_procedural_samecomp_{DATE_TAG}",
        "case_id": "olmtoondilate_typed_procedural_64x64",
        "witness_id": "olmtypedprocedural-toondilate-samecomp-v1",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_paths(effect_key: str) -> tuple[Path, Path]:
    package_dir = ROOT / "refs" / "runtime_trace_packages" / EFFECTS[effect_key]["package_dir"]
    return package_dir, package_dir.with_suffix(".zip")


def build_spec(effect_key: str) -> dict[str, Any]:
    effect = EFFECTS[effect_key]
    return {
        "schema_version": 1,
        "description": (
            "Same-comp 32bpc typed-procedural fixture that generates deterministic float "
            "source pixels inside After Effects, pauses for the common witness launcher, "
            "then renders no-effect and effect-on EXR outputs from one comp."
        ),
        "request_id": effect["request_id"],
        "run_id_prefix": "typedproc-" + effect["effect_slug"],
        "plugin": {
            "name": effect["effect_name"],
            "module_filename": effect["plugin_name"],
            "aex_sha256": effect["plugin_sha256"],
            "default_aex_path": effect["default_aex_path"],
        },
        "host": {
            "afterfx_path": r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\AfterFX.exe",
            "cdb_path": r"C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe",
        },
        "project": {
            "bits_per_channel": 32,
            "renderer": "Software",
            "environment": {
                "OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT": "1",
            },
        },
        "renderer": {"source": "renderer.jsx"},
        "request_assets": {"source": "request"},
        "cdb": {
            "armed_marker": "TYPED_PROC_CDB_ARMED",
            "arm_timeout_seconds": 60,
            "capture_timeout_seconds": 120,
        },
        "cases": [
            {
                "id": effect["case_id"],
                "cdb_template": "probe.cdb.in",
                "bits_per_channel": 32,
                "template_values": {
                    "witness_id": effect["witness_id"],
                    "effect_slug": effect["effect_slug"],
                    "effect_name": effect["effect_name"],
                    "hook_rva": TOONDILATE_FLOAT_HOOK_RVA,
                    "search_radius_bits": TOONDILATE_SEARCH_RADIUS_BITS,
                },
                "addresses": {"float_render_hook": TOONDILATE_FLOAT_HOOK_RVA},
                "exports": [
                    {
                        "source": f"exports/{{case_id}}/{FIXTURE_CONTRACT['output_names']['no_effect']}",
                        "archive_path": "return/{case_id}/effect_no_effect_00000.exr",
                        "required": True,
                    },
                    {
                        "source": f"exports/{{case_id}}/{FIXTURE_CONTRACT['output_names']['effect_on']}",
                        "archive_path": "return/{case_id}/effect_effect_on_00000.exr",
                        "required": True,
                    },
                    {
                        "source": "exports/{case_id}/fixture_manifest.json",
                        "archive_path": "return/{case_id}/fixture_manifest.json",
                        "required": True,
                    },
                    {
                        "source": "exports/{case_id}/fixture_result.json",
                        "archive_path": "return/{case_id}/fixture_result.json",
                        "required": True,
                    },
                    {
                        "source": "exports/{case_id}/fixture.aep",
                        "archive_path": "return/{case_id}/fixture.aep",
                        "required": True,
                    },
                ],
            }
        ],
        "validation": {
            "identity_fields": [
                "run_id",
                "ae_pid",
                "module_base",
                "aex_sha256",
                "project_bpc",
                "renderer",
                "case_id",
                "witness_id",
                "effect",
            ],
            "events": [
                {
                    "name": "toondilate_float_render_live",
                    "prefix": "TOONDILATE_FLOAT_RENDER_LIVE",
                    "cardinality": {"scope": "per_case", "min": 1, "max": 1},
                    "required_fields": [
                        "run_id",
                        "ae_pid",
                        "module_base",
                        "aex_sha256",
                        "project_bpc",
                        "renderer",
                        "case_id",
                        "witness_id",
                        "effect",
                        "hook_rva",
                        "hook_ip",
                        "in_data_ptr",
                        "input_world_ptr",
                        "output_world_ptr",
                        "radius_ptr",
                        "radius_bits",
                        "input_pixels_ptr",
                        "output_pixels_ptr",
                        "input_width",
                        "input_height",
                        "input_rowbytes",
                        "output_width",
                        "output_height",
                        "output_rowbytes",
                    ],
                    "field_constraints": {
                        "witness_id": {"equals": effect["witness_id"]},
                        "effect": {"equals": "toondilate"},
                        "hook_rva": {"equals": TOONDILATE_FLOAT_HOOK_RVA},
                        "radius_bits": {"equals": TOONDILATE_SEARCH_RADIUS_BITS},
                        "hook_ip": {"pattern": r"^0x[0-9a-fA-F]{8,16}$"},
                        "in_data_ptr": {"pattern": r"^0x[1-9a-fA-F][0-9a-fA-F]{7,15}$"},
                        "input_world_ptr": {"pattern": r"^0x[1-9a-fA-F][0-9a-fA-F]{7,15}$"},
                        "output_world_ptr": {"pattern": r"^0x[1-9a-fA-F][0-9a-fA-F]{7,15}$"},
                        "radius_ptr": {"pattern": r"^0x[1-9a-fA-F][0-9a-fA-F]{7,15}$"},
                        "input_pixels_ptr": {"pattern": r"^0x[1-9a-fA-F][0-9a-fA-F]{7,15}$"},
                        "output_pixels_ptr": {"pattern": r"^0x[1-9a-fA-F][0-9a-fA-F]{7,15}$"},
                        "input_width": {"equals": 64},
                        "input_height": {"equals": 64},
                        "output_width": {"equals": 64},
                        "output_height": {"equals": 64},
                        "input_rowbytes": {"equals": 1024},
                        "output_rowbytes": {"equals": 1024},
                    },
                }
            ],
        },
        "return_bundle": {
            "json_name": f"RETURN_{effect['effect_slug'].upper()}_TYPED_PROCEDURAL_32BPC.json",
            "zip_name": f"RETURN_{effect['effect_slug'].upper()}_TYPED_PROCEDURAL_32BPC.zip",
            "include_logs": [],
        },
    }


def request_manifest(effect_key: str) -> dict[str, Any]:
    effect = EFFECTS[effect_key]
    return {
        "request_id": effect["request_id"],
        "kind": "olm_typed_procedural_samecomp_request",
        "schema_version": 1,
        "generated_at": "2026-07-13",
        "required_ae_major_minor": REQUIRED_AE,
        "output_template": OUTPUT_TEMPLATE,
        "generator_supports": ["toondilate"],
        "fixture_contract": FIXTURE_CONTRACT,
        "cases": [
            {
                "id": effect["case_id"],
                "effect_name": effect["effect_name"],
                "effect_slug": effect["effect_slug"],
                "plugin_name": effect["plugin_name"],
                "plugin_sha256": effect["plugin_sha256"],
                "default_mac_plugin_path": effect["default_mac_plugin_path"],
                "witness_id": effect["witness_id"],
                "parameters": TOONDILATE_PARAMETERS,
                "live_hook": {
                    "function": "FUN_1801a6800",
                    "rva": TOONDILATE_FLOAT_HOOK_RVA,
                    "semantic": "32bpc PF_PixelFloat ToonDilate render core",
                    "radius_argument": "fifth argument, float pointer at entry RSP+0x28",
                },
            }
        ],
    }


def renderer_source() -> str:
    return dedent(
        r'''/*
  Same-comp typed-procedural witness renderer.

  Required environment:
    OLM_AE_REQUEST_DIR
    OLM_AE_CASE_ID
    OLM_AE_OUTPUT_DIR
    OLM_AE_LOG_PATH
    OLM_AE_RESULT_JSON
    OLM_AE_READY_MARKER
    OLM_AE_CONTINUE_MARKER
*/
(function () {
    function getenv(name) {
        try { return $.getenv(name) || ""; } catch (_) { return ""; }
    }

    function fail(message) { throw new Error("typed procedural same-comp renderer: " + message); }

    function ensureFolder(path) {
        var folder = new Folder(path);
        if (!folder.exists && !folder.create()) fail("cannot create folder " + path);
        return folder;
    }

    function writeText(path, text) {
        var file = new File(path);
        file.encoding = "UTF-8";
        if (!file.open("w")) fail("cannot write " + path);
        file.write(text);
        file.close();
    }

    function appendText(path, text) {
        var file = new File(path);
        file.encoding = "UTF-8";
        if (!file.open("a")) fail("cannot append " + path);
        file.write(text);
        file.close();
    }

    function readText(path) {
        var file = new File(path);
        file.encoding = "UTF-8";
        if (!file.open("r")) fail("cannot read " + path);
        var text = file.read();
        file.close();
        return text;
    }

    function parseJson(path) {
        return eval("(" + readText(path) + ")");
    }

    function parseFields(text) {
        var fields = {};
        var tokens = String(text || "").split(/\s+/);
        for (var i = 0; i < tokens.length; i++) {
            var split = tokens[i].indexOf("=");
            if (split > 0) fields[tokens[i].substring(0, split)] = tokens[i].substring(split + 1);
        }
        return fields;
    }

    function quote(value) {
        return '"' + String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"')
            .replace(/\r/g, "\\r").replace(/\n/g, "\\n") + '"';
    }

    function requireAbsent(path) {
        var file = new File(path);
        if (file.exists) fail("stale artifact exists: " + path);
    }

    function addIntegerRect(comp, spec) {
        if (spec.x !== Math.floor(spec.x) || spec.y !== Math.floor(spec.y) ||
            spec.width !== Math.floor(spec.width) || spec.height !== Math.floor(spec.height)) {
            fail("non-integer rectangle " + spec.name);
        }
        var layer = comp.layers.addSolid(spec.color, spec.name, spec.width, spec.height, 1.0, 1.0 / 24.0);
        layer.position.setValue([spec.x + spec.width / 2, spec.y + spec.height / 2]);
        layer.opacity.setValue(spec.alpha * 100.0);
        return layer;
    }

    function renderOne(comp, outputDir, filename, template) {
        var sequenceName = filename.replace(/\.exr$/i, "_[#####].exr");
        var sequenceFile = new File(outputDir + "/" + sequenceName);
        var renderedFile = new File(outputDir + "/" + filename.replace(/\.exr$/i, "_00000.exr"));
        requireAbsent(sequenceFile.fsName);
        requireAbsent(renderedFile.fsName);
        var item = app.project.renderQueue.items.add(comp);
        item.timeSpanStart = 0;
        item.timeSpanDuration = 1.0 / 24.0;
        var module = item.outputModule(1);
        module.applyTemplate(template);
        module.file = sequenceFile;
        app.project.renderQueue.render();
        if (!renderedFile.exists) fail("render did not produce " + renderedFile.fsName);
        item.remove();
        return renderedFile;
    }

    function findCase(request, caseId) {
        var cases = request.cases || [];
        for (var i = 0; i < cases.length; i++) {
            if (cases[i].id === caseId) return cases[i];
        }
        return null;
    }

    function waitForContinue(path, timeoutSeconds) {
        var marker = new File(path);
        var deadline = new Date().getTime() + timeoutSeconds * 1000;
        while (new Date().getTime() < deadline) {
            if (marker.exists) return readText(path);
            $.sleep(250);
        }
        fail("continue marker timeout");
    }

    var requestDir = getenv("OLM_AE_REQUEST_DIR");
    var caseId = getenv("OLM_AE_CASE_ID");
    var outputDir = getenv("OLM_AE_OUTPUT_DIR");
    var logPath = getenv("OLM_AE_LOG_PATH");
    var resultPath = getenv("OLM_AE_RESULT_JSON");
    var readyMarkerPath = getenv("OLM_AE_READY_MARKER");
    var continueMarkerPath = getenv("OLM_AE_CONTINUE_MARKER");
    var keepOpen = getenv("OLM_AE_KEEP_OPEN") === "1";
    var skipLivePause = getenv("OLM_AE_SKIP_LIVE_PAUSE") === "1";
    var pauseTimeoutSeconds = Number(getenv("OLM_AE_PAUSE_TIMEOUT_SECONDS") || 300);
    var suppressStarted = false;
    var result = {
        kind: "olm_typed_procedural_samecomp_renderer_result",
        status: "error",
        ae_version: String(app.version || ""),
        case_id: caseId,
        effect_name: "",
        effect_slug: "",
        output_dir: outputDir,
        output_template: "",
        project_bits_per_channel: -1,
        project_gpu_accel_type: {current_name: "", raw: -1},
        working_space: "",
        linear_blending: true,
        project_path: "",
        fixture_manifest: "fixture_manifest.json",
        parameters_requested: [],
        parameters_readback: [],
        run_binding: {},
        outputs: [],
        same_source_comp: false,
        error: ""
    };

    try {
        if (!requestDir || !caseId || !outputDir || !logPath || !resultPath || !readyMarkerPath || !continueMarkerPath) {
            fail("request/case/output/log/result/ready/continue bindings are required");
        }
        ensureFolder(outputDir);
        ensureFolder(new File(logPath).parent.fsName);
        writeText(logPath, "typed procedural same-comp start " + (new Date()).toUTCString() + "\n");
        requireAbsent(readyMarkerPath);
        requireAbsent(continueMarkerPath);
        requireAbsent(resultPath);
        var request = parseJson(requestDir + "/request_manifest.json");
        var requestCase = findCase(request, caseId);
        if (!requestCase) fail("missing case in request manifest: " + caseId);
        result.effect_name = String(requestCase.effect_name || "");
        result.effect_slug = String(requestCase.effect_slug || "");
        result.output_template = String(request.output_template || "");
        if (result.effect_name !== "OLM Toon Dilate") {
            fail("unsupported effect " + result.effect_name);
        }
        var requestedParameters = requestCase.parameters || [];
        if (requestedParameters.length !== 1 || requestedParameters[0].name !== "Search Radius") {
            fail("request must contain the bounded Search Radius parameter");
        }
        result.parameters_requested = requestedParameters;
        if (!result.output_template) fail("request output_template is required");

        app.beginSuppressDialogs();
        suppressStarted = true;
        try {
            if (app.project) app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
        } catch (closeError) {
            appendText(logPath, "close warning " + closeError.toString() + "\n");
        }
        app.newProject();
        if (!app.project) fail("AE did not create a new project");
        var project = app.project;
        if (project.items.numItems !== 0) fail("new project is not empty");
        if (project.renderQueue.numItems !== 0) fail("render queue is not empty");
        project.bitsPerChannel = 32;
        project.workingSpace = "";
        project.linearBlending = false;
        try {
            project.gpuAccelType = GpuAccelType.SOFTWARE;
        } catch (gpuSetError) {
            fail("cannot set project gpuAccelType SOFTWARE: " + gpuSetError.toString());
        }
        if (Number(project.bitsPerChannel) !== 32) fail("AE did not accept 32bpc");
        if (String(project.workingSpace) !== "") fail("working space is not None");
        if (project.linearBlending) fail("linear blending is enabled");
        var gpuName = String(project.gpuAccelType).toUpperCase();
        var gpuRaw = Number(project.gpuAccelType);
        if (gpuName !== "SOFTWARE") fail("host-observed gpuAccelType is " + gpuName + ", not SOFTWARE");
        result.project_bits_per_channel = Number(project.bitsPerChannel);
        result.project_gpu_accel_type = {current_name: gpuName, raw: gpuRaw};
        result.working_space = "None";
        result.linear_blending = Boolean(project.linearBlending);
        appendText(logPath, "gpuAccelType=" + gpuName + " raw=" + gpuRaw + "\n");

        var width = 64;
        var height = 64;
        var sourceComp = project.items.addComp("OLM_TYPED_SOURCE_64x64", width, height, 1.0, 1.0 / 24.0, 24.0);
        sourceComp.layers.addSolid([0.0, 0.0, 0.0], "solid_background", width, height, 1.0, 1.0 / 24.0);
        var rects = [
            {name: "rect_integer_a25", x: 4, y: 4, width: 20, height: 16, color: [1.0, 0.0, 0.0], alpha: 0.25},
            {name: "rect_integer_a50", x: 28, y: 4, width: 20, height: 16, color: [0.0, 1.0, 0.0], alpha: 0.50},
            {name: "rect_integer_a75", x: 4, y: 28, width: 20, height: 16, color: [0.0, 0.0, 1.0], alpha: 0.75},
            {name: "rect_integer_a100", x: 28, y: 28, width: 20, height: 16, color: [1.0, 1.0, 1.0], alpha: 1.00}
        ];
        for (var i = rects.length - 1; i >= 0; i--) addIntegerRect(sourceComp, rects[i]);

        var renderComp = project.items.addComp("OLM_TYPED_EFFECT_AB_64x64", width, height, 1.0, 1.0 / 24.0, 24.0);
        var sourceLayer = renderComp.layers.add(sourceComp);
        sourceLayer.name = "generated_source_only";
        var effectLayer = renderComp.layers.add(sourceComp);
        effectLayer.name = "generated_source_effect_on";
        result.same_source_comp = (sourceLayer.source === effectLayer.source);
        if (!result.same_source_comp) fail("A/B layers do not share the same source comp");
        var effect = effectLayer.property("ADBE Effect Parade").addProperty(result.effect_name);
        if (!effect) fail("AE could not add " + result.effect_name);
        var radiusSpec = requestedParameters[0];
        var radiusProperty = effect.property(Number(radiusSpec.property_index));
        if (!radiusProperty) fail("Search Radius property index is unavailable");
        if (String(radiusProperty.matchName) !== String(radiusSpec.match_name)) {
            fail("Search Radius matchName drifted: " + String(radiusProperty.matchName));
        }
        var requestedRadius = Number(radiusSpec.value);
        if (requestedRadius < Number(radiusSpec.minimum) || requestedRadius > Number(radiusSpec.maximum)) {
            fail("Search Radius request is outside its declared bounds");
        }
        radiusProperty.setValue(requestedRadius);
        var radiusReadback = Number(radiusProperty.value);
        if (Math.abs(radiusReadback - requestedRadius) > Number(radiusSpec.readback_tolerance)) {
            fail("Search Radius readback mismatch: " + radiusReadback);
        }
        result.parameters_readback = [{
            name: String(radiusSpec.name),
            match_name: String(radiusProperty.matchName),
            property_index: Number(radiusSpec.property_index),
            requested: requestedRadius,
            readback: radiusReadback,
            minimum: Number(radiusSpec.minimum),
            maximum: Number(radiusSpec.maximum)
        }];
        sourceLayer.enabled = true;
        effectLayer.enabled = false;

        var projectPath = outputDir + "/fixture.aep";
        var manifestPath = outputDir + "/fixture_manifest.json";
        requireAbsent(projectPath);
        requireAbsent(manifestPath);
        project.saveAs(new File(projectPath));
        result.project_path = projectPath;

        var readyText = "case_id=" + caseId + " effect_loaded=1 parameters_applied=1 " +
            "search_radius_requested=" + requestedRadius + " search_radius_readback=" + radiusReadback +
            " renderer_observed=" + gpuName + " linear_blending=0 effect=" + result.effect_slug + "\n";
        writeText(readyMarkerPath, readyText);
        var continueText = skipLivePause ? getenv("OLM_AE_RUN_BINDING") : waitForContinue(continueMarkerPath, pauseTimeoutSeconds);
        if (!skipLivePause && continueText.indexOf("continue") === -1) fail("continue marker did not contain continue");
        result.run_binding = parseFields(continueText);
        if (!skipLivePause) {
            var bindingFields = ["run_id", "ae_pid", "module_base", "aex_sha256"];
            for (var bindingIndex = 0; bindingIndex < bindingFields.length; bindingIndex++) {
                if (!result.run_binding[bindingFields[bindingIndex]]) fail("continue marker lacks " + bindingFields[bindingIndex]);
            }
        }

        var noEffect = renderOne(renderComp, outputDir, "effect_no_effect.exr", result.output_template);
        sourceLayer.enabled = false;
        effectLayer.enabled = true;
        var effectOn = renderOne(renderComp, outputDir, "effect_effect_on.exr", result.output_template);
        var manifest = "{\n" +
            "  \"kind\": " + quote("olm_32bpc_typed_procedural_fixture") + ",\n" +
            "  \"schema_version\": 1,\n" +
            "  \"ae_version\": " + quote(String(app.version)) + ",\n" +
            "  \"project_bits_per_channel\": 32,\n" +
            "  \"working_space\": \"None\",\n" +
            "  \"linear_blending\": false,\n" +
            "  \"project_gpu_accel_type\": {\"current_name\": " + quote(gpuName) + ", \"raw\": " + String(gpuRaw) + "},\n" +
            "  \"dimensions\": [64, 64],\n" +
            "  \"frame\": 0,\n" +
            "  \"effect\": " + quote(result.effect_name) + ",\n" +
            "  \"parameters_requested\": [{\"name\": \"Search Radius\", \"match_name\": \"ADBE OLMToonDilate-0001\", \"property_index\": 1, \"property_value_type\": \"OneD\", \"minimum\": 0, \"maximum\": 100, \"value\": 13, \"readback_tolerance\": 0.0001}],\n" +
            "  \"parameters_readback\": [{\"name\": \"Search Radius\", \"match_name\": \"ADBE OLMToonDilate-0001\", \"property_index\": 1, \"requested\": 13, \"readback\": " + String(radiusReadback) + ", \"minimum\": 0, \"maximum\": 100}],\n" +
            "  \"source_policy\": \"AE-generated solids only; no footage imported\",\n" +
            "  \"render_policy\": \"same comp, only branch enabled state changes\",\n" +
            "  \"outputs\": {\n" +
            "    \"no_effect\": \"effect_no_effect_00000.exr\",\n" +
            "    \"effect_on\": \"effect_effect_on_00000.exr\"\n" +
            "  },\n" +
            "  \"source_layers\": [\n" +
            "    {\"name\": \"solid_background\", \"kind\": \"solid\", \"bounds\": [0, 0, 64, 64], \"rgb\": [0, 0, 0], \"alpha\": 1.0},\n" +
            "    {\"name\": \"rect_integer_a25\", \"kind\": \"solid\", \"bounds\": [4, 4, 20, 16], \"rgb\": [1, 0, 0], \"alpha\": 0.25},\n" +
            "    {\"name\": \"rect_integer_a50\", \"kind\": \"solid\", \"bounds\": [28, 4, 20, 16], \"rgb\": [0, 1, 0], \"alpha\": 0.5},\n" +
            "    {\"name\": \"rect_integer_a75\", \"kind\": \"solid\", \"bounds\": [4, 28, 20, 16], \"rgb\": [0, 0, 1], \"alpha\": 0.75},\n" +
            "    {\"name\": \"rect_integer_a100\", \"kind\": \"solid\", \"bounds\": [28, 28, 20, 16], \"rgb\": [1, 1, 1], \"alpha\": 1.0}\n" +
            "  ]\n" +
            "}\n";
        writeText(manifestPath, manifest);
        writeText(outputDir + "/fixture_result.json", "{\n" +
            "  \"kind\": " + quote("olm_32bpc_typed_procedural_fixture_result") + ",\n" +
            "  \"status\": \"ok\",\n" +
            "  \"ae_version\": " + quote(String(app.version)) + ",\n" +
            "  \"effect\": " + quote(result.effect_name) + ",\n" +
            "  \"manifest\": \"fixture_manifest.json\",\n" +
            "  \"renderer_class\": " + quote(gpuName) + ",\n" +
            "  \"linear_blending\": false,\n" +
            "  \"parameters_readback\": [{\"name\": \"Search Radius\", \"readback\": " + String(radiusReadback) + "}],\n" +
            "  \"outputs\": [" + quote(noEffect.fsName) + "," + quote(effectOn.fsName) + "],\n" +
            "  \"error\": \"\"\n}\n");
        result.outputs = [noEffect.fsName, effectOn.fsName];
        result.status = "ok";
    } catch (error) {
        result.error = error.toString();
    } finally {
        try {
            writeText(resultPath, "{\n" +
                "  \"kind\": " + quote(result.kind) + ",\n" +
                "  \"status\": " + quote(result.status) + ",\n" +
                "  \"ae_version\": " + quote(result.ae_version) + ",\n" +
                "  \"case_id\": " + quote(result.case_id) + ",\n" +
                "  \"effect_name\": " + quote(result.effect_name) + ",\n" +
                "  \"effect_slug\": " + quote(result.effect_slug) + ",\n" +
                "  \"output_dir\": " + quote(result.output_dir) + ",\n" +
                "  \"output_template\": " + quote(result.output_template) + ",\n" +
                "  \"project_bits_per_channel\": " + String(result.project_bits_per_channel) + ",\n" +
                "  \"project_gpu_accel_type\": {\"current_name\": " + quote(result.project_gpu_accel_type.current_name) + ", \"raw\": " + String(result.project_gpu_accel_type.raw) + "},\n" +
                "  \"working_space\": " + quote(result.working_space) + ",\n" +
                "  \"linear_blending\": " + (result.linear_blending ? "true" : "false") + ",\n" +
                "  \"project_path\": " + quote(result.project_path) + ",\n" +
                "  \"fixture_manifest\": " + quote(result.fixture_manifest) + ",\n" +
                "  \"same_source_comp\": " + (result.same_source_comp ? "true" : "false") + ",\n" +
                "  \"parameters_requested\": [{\"name\": \"Search Radius\", \"match_name\": \"ADBE OLMToonDilate-0001\", \"property_index\": 1, \"property_value_type\": \"OneD\", \"minimum\": 0, \"maximum\": 100, \"value\": 13, \"readback_tolerance\": 0.0001}],\n" +
                "  \"parameters_readback\": [" + (result.parameters_readback.length ? "{\"name\": \"Search Radius\", \"match_name\": \"ADBE OLMToonDilate-0001\", \"property_index\": 1, \"requested\": 13, \"readback\": " + String(result.parameters_readback[0].readback) + ", \"minimum\": 0, \"maximum\": 100}" : "") + "],\n" +
                "  \"run_binding\": {\"run_id\": " + quote(result.run_binding.run_id || "") + ", \"ae_pid\": " + quote(result.run_binding.ae_pid || "") + ", \"module_base\": " + quote(result.run_binding.module_base || "") + ", \"aex_sha256\": " + quote(result.run_binding.aex_sha256 || "") + "},\n" +
                "  \"outputs\": [" + (result.outputs.length ? quote(result.outputs[0]) + "," + quote(result.outputs[1]) : "") + "],\n" +
                "  \"error\": " + quote(result.error) + "\n" +
                "}\n");
        } catch (_) {}
        try { if (suppressStarted) app.endSuppressDialogs(false); } catch (_) {}
    }

    if (!keepOpen) {
        try { app.quit(); } catch (_) {}
    }
    if (result.status !== "ok") fail(result.error || "unknown failure");
}());
'''
    )


def probe_source() -> str:
    return dedent(
        '''\
        .effmach amd64
        .expr /s masm
        .logopen /t "{{TRACE_PATH}}"
        .echo TYPED_PROC_CDB_ARMED
        bp {{ADDRESS:float_render_hook}} ".printf @@QUOTE@@TOONDILATE_FLOAT_RENDER_LIVE run_id={{RUN_ID}} ae_pid={{AE_PID}} module_base={{MODULE_BASE}} aex_sha256={{AEX_SHA256}} project_bpc={{PROJECT_BPC}} renderer={{RENDERER}} case_id={{CASE_ID}} witness_id={{CASE_VALUE:witness_id}} effect={{CASE_VALUE:effect_slug}} hook_rva={{CASE_VALUE:hook_rva}} hook_ip=0x%I64x in_data_ptr=0x%I64x input_world_ptr=0x%I64x output_world_ptr=0x%I64x radius_ptr=0x%I64x radius_bits=0x%08x input_pixels_ptr=0x%I64x output_pixels_ptr=0x%I64x input_width=%u input_height=%u input_rowbytes=%u output_width=%u output_height=%u output_rowbytes=%u\\n@@QUOTE@@, @rip, @rcx, @r8, @r9, poi(@rsp+0x28), dwo(poi(@rsp+0x28)), poi(@r8+0x18), poi(@r9+0x18), dwo(@r8+0x24), dwo(@r8+0x28), dwo(@r8+0x20), dwo(@r9+0x24), dwo(@r9+0x28), dwo(@r9+0x20); .logclose; bc *; .detach; q"
        g
        '''
    ).replace("@@QUOTE@@", r'\"')


def validator_source() -> str:
    return dedent(
        r'''#!/usr/bin/env python3
"""Validate same-comp typed-procedural artifacts and bind them to a render record."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = PACKAGE_ROOT / "request" / "fixture"
sys.path.insert(0, str(FIXTURE_ROOT))

from compare_float_exr import compare  # noqa: E402
from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr  # noqa: E402


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def fail(contract: dict[str, Any], stage: str, reason: str, missing: list[str], last: str = "") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "exact_bind_failure",
        "request_id": contract["request_id"],
        "failure": {
            "stage": stage,
            "reason": reason,
            "missing_fields": sorted(set(missing)),
            "last_observation": last,
        },
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_path(path: Path) -> str:
    return os.path.normcase(os.path.realpath(os.path.abspath(str(path))))


def relative_to_work(path: Path, work: Path) -> str:
    return path.resolve().relative_to(work.resolve()).as_posix()


def expected_case_event(status: dict[str, Any], case_id: str) -> dict[str, str] | None:
    for row in status.get("events", []):
        if row.get("prefix") == "TOONDILATE_FLOAT_RENDER_LIVE" and row.get("fields", {}).get("case_id") == case_id:
            return row["fields"]
    return None


def expected_parameters() -> list[dict[str, Any]]:
    return [{
        "name": "Search Radius",
        "match_name": "ADBE OLMToonDilate-0001",
        "property_index": 1,
        "property_value_type": "OneD",
        "minimum": 0.0,
        "maximum": 100.0,
        "value": 13.0,
        "readback_tolerance": 0.0001,
    }]


def expected_readback() -> list[dict[str, Any]]:
    return [{
        "name": "Search Radius",
        "match_name": "ADBE OLMToonDilate-0001",
        "property_index": 1,
        "requested": 13.0,
        "readback": 13.0,
        "minimum": 0.0,
        "maximum": 100.0,
    }]


def enrich(contract: dict[str, Any], status: dict[str, Any], work: Path) -> dict[str, Any]:
    if status.get("status") != "answered":
        return status
    request = read_json(PACKAGE_ROOT / "request" / "request_manifest.json")
    fixture_path = FIXTURE_ROOT / "ae_generate_32bpc_typed_procedural_fixture.jsx"
    fixture_sha = sha256(fixture_path)
    renderer_sha = sha256(PACKAGE_ROOT / "scripts" / "renderer.jsx")
    cases = request.get("cases", [])
    if not isinstance(cases, list) or not cases:
        return fail(contract, "request_manifest", "request manifest has no cases", ["request.cases"])
    fixture_contract = request.get("fixture_contract", {})
    if fixture_contract.get("output_names") != {"no_effect": "effect_no_effect_00000.exr", "effect_on": "effect_effect_on_00000.exr"}:
        return fail(contract, "request_manifest", "fixture output names drifted", ["request.fixture_contract.output_names"])

    run = status.get("run", {})
    if not isinstance(run, dict):
        return fail(contract, "run_identity", "validated status lacks run identity", ["status.run"])
    records = []
    summaries = []
    ae_version = ""
    for case in cases:
        case_id = case["id"]
        fields = expected_case_event(status, case_id)
        if fields is None:
            return fail(contract, "typed_trace_binding", "trace did not bind the live 32bpc ToonDilate hook", [case_id + ":TOONDILATE_FLOAT_RENDER_LIVE"])
        if fields.get("witness_id") != case["witness_id"]:
            return fail(contract, "typed_trace_binding", "witness_id drifted", ["witness_id"], json.dumps(fields, sort_keys=True))
        if fields.get("effect") != case["effect_slug"]:
            return fail(contract, "typed_trace_binding", "effect slug drifted", ["effect"], json.dumps(fields, sort_keys=True))
        try:
            hook_ip = int(fields["hook_ip"], 16)
            module_base = int(str(run["module_base"]), 16)
        except (KeyError, TypeError, ValueError):
            return fail(contract, "typed_trace_binding", "live hook address is not parseable", ["hook_ip", "run.module_base"], json.dumps(fields, sort_keys=True))
        if hook_ip - module_base != 0x1A6800:
            return fail(contract, "typed_trace_binding", "live instruction pointer is not module_base+0x1a6800", ["hook_ip-module_base"], json.dumps(fields, sort_keys=True))
        if fields.get("radius_bits", "").lower() != "0x41500000":
            return fail(contract, "typed_trace_binding", "live core radius is not float32 13.0", ["radius_bits=0x41500000"], json.dumps(fields, sort_keys=True))
        case_root = work / "exports" / case_id
        project_path = case_root / "fixture.aep"
        result_path = work / ("ae_result_" + case_id + ".json")
        fixture_result_path = case_root / "fixture_result.json"
        fixture_manifest_path = case_root / "fixture_manifest.json"
        no_effect_path = case_root / fixture_contract["output_names"]["no_effect"]
        effect_on_path = case_root / fixture_contract["output_names"]["effect_on"]
        log_path = work / ("ae_" + case_id + ".log")
        required = [project_path, result_path, fixture_result_path, fixture_manifest_path, no_effect_path, effect_on_path, log_path]
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            return fail(contract, "typed_artifact_binding", "required typed-procedural artifacts are missing", missing)

        result = read_json(result_path)
        fixture_result = read_json(fixture_result_path)
        fixture_manifest = read_json(fixture_manifest_path)
        ae_version = str(result.get("ae_version") or ae_version)
        result_issues: list[str] = []
        if result.get("status") != "ok":
            result_issues.append("ae_result.status=ok")
        if result.get("case_id") != case_id:
            result_issues.append("ae_result.case_id")
        if result.get("effect_name") != case["effect_name"]:
            result_issues.append("ae_result.effect_name")
        if result.get("effect_slug") != case["effect_slug"]:
            result_issues.append("ae_result.effect_slug")
        if result.get("output_template") != request["output_template"]:
            result_issues.append("ae_result.output_template")
        if result.get("project_bits_per_channel") != 32:
            result_issues.append("ae_result.project_bits_per_channel=32")
        if result.get("project_gpu_accel_type", {}).get("current_name") != "SOFTWARE":
            result_issues.append("ae_result.project_gpu_accel_type.current_name=SOFTWARE")
        if result.get("working_space") != "None":
            result_issues.append("ae_result.working_space=None")
        if result.get("linear_blending") is not False:
            result_issues.append("ae_result.linear_blending=false")
        if result.get("parameters_requested") != expected_parameters():
            result_issues.append("ae_result.parameters_requested")
        if result.get("parameters_readback") != expected_readback():
            result_issues.append("ae_result.parameters_readback")
        expected_binding = {
            "run_id": str(run["run_id"]),
            "ae_pid": str(run["ae_pid"]),
            "module_base": str(run["module_base"]),
            "aex_sha256": str(run["aex_sha256"]),
        }
        if result.get("run_binding") != expected_binding:
            result_issues.append("ae_result.run_binding")
        if result.get("same_source_comp") is not True:
            result_issues.append("ae_result.same_source_comp=true")
        if normalized_path(Path(str(result.get("output_dir", "")))) != normalized_path(case_root):
            result_issues.append("ae_result.output_dir")
        if normalized_path(Path(str(result.get("project_path", "")))) != normalized_path(project_path):
            result_issues.append("ae_result.project_path")
        actual_outputs = [normalized_path(Path(path)) for path in result.get("outputs", [])]
        expected_outputs = [normalized_path(no_effect_path), normalized_path(effect_on_path)]
        if actual_outputs != expected_outputs:
            result_issues.append("ae_result.outputs")
        if fixture_result.get("status") != "ok":
            result_issues.append("fixture_result.status=ok")
        if fixture_result.get("effect") != case["effect_name"]:
            result_issues.append("fixture_result.effect")
        if fixture_result.get("manifest") != "fixture_manifest.json":
            result_issues.append("fixture_result.manifest")
        if fixture_result.get("renderer_class") != "SOFTWARE":
            result_issues.append("fixture_result.renderer_class=SOFTWARE")
        if fixture_result.get("linear_blending") is not False:
            result_issues.append("fixture_result.linear_blending=false")
        if fixture_result.get("parameters_readback") != [{"name": "Search Radius", "readback": 13.0}]:
            result_issues.append("fixture_result.parameters_readback")
        if result_issues:
            return fail(contract, "typed_result_identity", "renderer result drifted from the typed fixture contract", result_issues, json.dumps(result, sort_keys=True))

        manifest_issues: list[str] = []
        required_pairs = {
            "kind": "olm_32bpc_typed_procedural_fixture",
            "project_bits_per_channel": 32,
            "working_space": "None",
            "linear_blending": False,
            "project_gpu_accel_type": {"current_name": "SOFTWARE", "raw": result["project_gpu_accel_type"]["raw"]},
            "dimensions": [64, 64],
            "frame": 0,
            "effect": case["effect_name"],
            "parameters_requested": expected_parameters(),
            "parameters_readback": expected_readback(),
            "source_policy": "AE-generated solids only; no footage imported",
            "render_policy": "same comp, only branch enabled state changes",
            "outputs": fixture_contract["output_names"],
            "source_layers": fixture_contract["source_layers"],
        }
        for key, expected in required_pairs.items():
            if fixture_manifest.get(key) != expected:
                manifest_issues.append("fixture_manifest." + key)
        if manifest_issues:
            return fail(contract, "typed_fixture_manifest", "fixture manifest drifted", manifest_issues, json.dumps(fixture_manifest, sort_keys=True))

        try:
            no_effect_info = inspect_float_rgba_exr(no_effect_path, expected_dimensions=(64, 64))
            effect_on_info = inspect_float_rgba_exr(effect_on_path, expected_dimensions=(64, 64))
            delta = compare(no_effect_path, effect_on_path)
        except (OSError, ValueError, VerificationError) as exc:
            return fail(contract, "typed_float_validation", str(exc), ["typed_float_rgba_exr"])

        record_case = {
            "id": case_id,
            "effect": case["effect_name"],
            "plugin": {
                "name": contract["plugin"]["module_filename"],
                "path": contract["plugin"]["default_aex_path"],
                "sha256": run["aex_sha256"],
            },
            "renderer_class": "SOFTWARE",
            "linear_blending": False,
            "parameters_requested": expected_parameters(),
            "parameters_readback": expected_readback(),
            "live_hook": {
                "rva": fields["hook_rva"],
                "ip": fields["hook_ip"],
                "radius_bits": fields["radius_bits"],
                "input_pixels_ptr": fields["input_pixels_ptr"],
                "output_pixels_ptr": fields["output_pixels_ptr"],
            },
            "fixture_contract": fixture_contract,
            "outputs": {
                "no_effect": {
                    "path": relative_to_work(no_effect_path, work),
                    "sha256": no_effect_info["sha256"],
                },
                "effect_on": {
                    "path": relative_to_work(effect_on_path, work),
                    "sha256": effect_on_info["sha256"],
                },
            },
        }
        summary = {
            "case_id": case_id,
            "effect_name": case["effect_name"],
            "witness_id": case["witness_id"],
            "no_effect": no_effect_info,
            "effect_on": effect_on_info,
            "no_effect_vs_effect_on": delta,
        }
        records.append(record_case)
        summaries.append(summary)

    status["typed_procedural_record"] = {
        "kind": "olm_32bpc_typed_procedural_render_record",
        "schema": 1,
        "platform": "windows",
        "record_role": "return",
        "request_id": contract["request_id"],
        "required_ae_major_minor": request["required_ae_major_minor"],
        "ae_version": ae_version,
        "output_template": request["output_template"],
        "fixture_jsx_sha256": fixture_sha,
        "renderer_jsx_sha256": renderer_sha,
        "renderer_class": "SOFTWARE",
        "linear_blending": False,
        "cases": records,
    }
    status["typed_procedural_cases"] = summaries
    status["cross_host_compare_ready"] = True
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    contract = read_json(args.contract)
    status = enrich(contract, read_json(args.status), args.work.resolve())
    write_json(args.status, status)
    print(json.dumps({"status": status["status"]}, sort_keys=True))
    return 0 if status["status"] == "answered" else 2


if __name__ == "__main__":
    raise SystemExit(main())
'''
    )


def compare_helper_source() -> str:
    return dedent(
        r'''#!/usr/bin/env python3
"""Compare two typed-procedural render records or witness returns fail-closed."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


def extract_zip(path: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if path.is_dir():
        return path.resolve(), None
    if path.is_file() and path.suffix.lower() == ".zip":
        temp = tempfile.TemporaryDirectory(prefix="typed_proc_common_core_")
        root = Path(temp.name)
        with zipfile.ZipFile(path) as archive:
            archive.extractall(root)
        children = [item for item in root.iterdir()]
        if len(children) == 1 and children[0].is_dir():
            return children[0], temp
        return root, temp
    if path.is_file() and path.suffix.lower() == ".json":
        return path.parent.resolve(), None
    raise ValueError(f"unsupported input: {path}")


def read_record_payload(locator: Path) -> tuple[dict[str, Any], Path, tempfile.TemporaryDirectory[str] | None]:
    root, temp = extract_zip(locator)
    candidates = [locator.resolve()] if locator.is_file() and locator.suffix.lower() == ".json" else []
    candidates.extend(sorted(root.rglob("*.json")))
    for candidate in candidates:
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            if payload.get("kind") == "olm_32bpc_typed_procedural_render_record":
                return payload, candidate.parent.resolve(), temp
            nested = payload.get("typed_procedural_record")
            if isinstance(nested, dict) and nested.get("kind") == "olm_32bpc_typed_procedural_render_record":
                return nested, candidate.parent.resolve(), temp
    raise ValueError(f"{locator}: no typed-procedural render record found")


def helper_root(*roots: Path) -> Path:
    script_root = Path(__file__).resolve().parent / "request" / "fixture"
    if script_root.is_dir():
        return script_root
    for root in roots:
        direct = root / "request" / "fixture"
        if direct.is_dir():
            return direct
        for candidate in root.rglob("verify_32bpc_float_return.py"):
            return candidate.parent
    raise ValueError("could not locate request/fixture helpers in the provided records")


def resolve_output(root: Path, relative: str) -> Path:
    choices = [relative]
    if relative.startswith("exports/"):
        choices.append("return/" + relative[len("exports/"):])
    if relative.startswith("return/"):
        choices.append("exports/" + relative[len("return/"):])
    for choice in choices:
        path = (root / choice).resolve()
        if path.is_file():
            return path
    raise ValueError(f"{root}: missing output {relative}")


def require_case_map(record: dict[str, Any], root: Path, inspect_float_rgba_exr) -> dict[str, dict[str, Any]]:
    if record.get("schema") != 1:
        raise ValueError("render record schema must be 1")
    if record.get("required_ae_major_minor") != "26.3":
        raise ValueError("render record must pin AE 26.3")
    if record.get("output_template") != "OLM EXR 32 Float":
        raise ValueError("render record must pin OLM EXR 32 Float")
    if record.get("platform") not in {"windows", "macos"}:
        raise ValueError("render record platform must be windows or macos")
    if record.get("renderer_class") != "SOFTWARE":
        raise ValueError("render record renderer_class must be SOFTWARE")
    if record.get("linear_blending") is not False:
        raise ValueError("render record linear_blending must be false")
    cases = record.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("render record has no cases")
    output: dict[str, dict[str, Any]] = {}
    for case in cases:
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("case id is required")
        contract = case.get("fixture_contract")
        if contract != {
            "manifest_kind": "olm_32bpc_typed_procedural_fixture",
            "project_bits_per_channel": 32,
            "working_space": "None",
            "linear_blending": False,
            "dimensions": [64, 64],
            "frame": 0,
            "source_policy": "AE-generated solids only; no footage imported",
            "render_policy": "same comp, only branch enabled state changes",
            "source_layers": [
                {"name": "solid_background", "kind": "solid", "bounds": [0, 0, 64, 64], "rgb": [0, 0, 0], "alpha": 1.0},
                {"name": "rect_integer_a25", "kind": "solid", "bounds": [4, 4, 20, 16], "rgb": [1, 0, 0], "alpha": 0.25},
                {"name": "rect_integer_a50", "kind": "solid", "bounds": [28, 4, 20, 16], "rgb": [0, 1, 0], "alpha": 0.5},
                {"name": "rect_integer_a75", "kind": "solid", "bounds": [4, 28, 20, 16], "rgb": [0, 0, 1], "alpha": 0.75},
                {"name": "rect_integer_a100", "kind": "solid", "bounds": [28, 28, 20, 16], "rgb": [1, 1, 1], "alpha": 1.0},
            ],
            "output_names": {"no_effect": "effect_no_effect_00000.exr", "effect_on": "effect_effect_on_00000.exr"},
        }:
            raise ValueError(f"{case_id}: fixture contract drifted")
        if case.get("renderer_class") != "SOFTWARE" or case.get("linear_blending") is not False:
            raise ValueError(f"{case_id}: renderer/linear-light provenance drifted")
        expected_parameters = [{"name": "Search Radius", "match_name": "ADBE OLMToonDilate-0001", "property_index": 1, "property_value_type": "OneD", "minimum": 0.0, "maximum": 100.0, "value": 13.0, "readback_tolerance": 0.0001}]
        expected_readback = [{"name": "Search Radius", "match_name": "ADBE OLMToonDilate-0001", "property_index": 1, "requested": 13.0, "readback": 13.0, "minimum": 0.0, "maximum": 100.0}]
        if case.get("parameters_requested") != expected_parameters or case.get("parameters_readback") != expected_readback:
            raise ValueError(f"{case_id}: parameter provenance drifted")
        plugin = case.get("plugin", {})
        expected_plugin_name = "OLMToonDilate.aex" if record["platform"] == "windows" else "OLMToonDilate.plugin"
        if plugin.get("name") != expected_plugin_name:
            raise ValueError(f"{case_id}: plugin identity name drifted")
        plugin_sha = plugin.get("sha256")
        if not isinstance(plugin_sha, str) or len(plugin_sha) != 64 or any(ch not in "0123456789abcdef" for ch in plugin_sha.lower()):
            raise ValueError(f"{case_id}: plugin identity sha256 is missing or invalid")
        if record["platform"] == "windows" and plugin_sha.lower() != "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3":
            raise ValueError(f"{case_id}: Windows plugin identity hash drifted")
        resolved_outputs: dict[str, dict[str, Any]] = {}
        for name in ("no_effect", "effect_on"):
            row = case.get("outputs", {}).get(name)
            if not isinstance(row, dict) or not isinstance(row.get("path"), str):
                raise ValueError(f"{case_id}: missing outputs.{name}")
            path = resolve_output(root, row["path"])
            inspected = inspect_float_rgba_exr(path, expected_dimensions=(64, 64))
            if row.get("sha256") != inspected["sha256"]:
                raise ValueError(f"{case_id}: sha256 drifted for outputs.{name}")
            resolved_outputs[name] = {"path": path, "inspection": inspected}
        output[case_id] = {
            "effect": case["effect"],
            "outputs": resolved_outputs,
            "fixture_contract": contract,
        }
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    temps: list[tempfile.TemporaryDirectory[str]] = []
    try:
        left_record, left_root, left_temp = read_record_payload(args.left)
        right_record, right_root, right_temp = read_record_payload(args.right)
        if left_temp is not None:
            temps.append(left_temp)
        if right_temp is not None:
            temps.append(right_temp)
        if left_record.get("platform") == right_record.get("platform"):
            raise ValueError("compare requires two different platforms")
        if left_record.get("fixture_jsx_sha256") != right_record.get("fixture_jsx_sha256"):
            raise ValueError("fixture_jsx_sha256 mismatch between records")
        if left_record.get("renderer_jsx_sha256") != right_record.get("renderer_jsx_sha256"):
            raise ValueError("renderer_jsx_sha256 mismatch between records")
        left_helper = helper_root(left_root, right_root)
        if str(left_helper) not in sys.path:
            sys.path.insert(0, str(left_helper))
        from compare_float_exr import compare  # noqa: E402
        from verify_32bpc_float_return import inspect_float_rgba_exr  # noqa: E402

        left_cases = require_case_map(left_record, left_root, inspect_float_rgba_exr)
        right_cases = require_case_map(right_record, right_root, inspect_float_rgba_exr)
        if set(left_cases) != set(right_cases):
            raise ValueError("case sets differ between records")
        rows = []
        for case_id in sorted(left_cases):
            left_case = left_cases[case_id]
            right_case = right_cases[case_id]
            if left_case["effect"] != right_case["effect"]:
                raise ValueError(f"{case_id}: effect mismatch")
            no_effect = compare(left_case["outputs"]["no_effect"]["path"], right_case["outputs"]["no_effect"]["path"])
            effect_on = compare(left_case["outputs"]["effect_on"]["path"], right_case["outputs"]["effect_on"]["path"])
            if no_effect["mismatched_values"] != 0:
                raise ValueError(f"{case_id}: no_effect is not raw-float-bit exact across hosts")
            if effect_on["mismatched_values"] != 0:
                raise ValueError(f"{case_id}: effect_on is not raw-float-bit exact across hosts")
            rows.append(
                {
                    "id": case_id,
                    "effect": left_case["effect"],
                    "no_effect_cross_host": no_effect,
                    "effect_on_cross_host": effect_on,
                    "status": "raw-float-bits-exact",
                }
            )
        result = {
            "status": "pass",
            "fixture_jsx_sha256": left_record["fixture_jsx_sha256"],
            "platforms": [left_record["platform"], right_record["platform"]],
            "cases": rows,
        }
    except Exception as exc:  # noqa: BLE001 - command-line tool should print the exact reason.
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    finally:
        for temp in temps:
            temp.cleanup()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for row in result["cases"]:
            print(f"[PASS] {row['id']} no_effect=0 effect_on=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    )


def mac_runner_source() -> str:
    return dedent(
        r'''#!/usr/bin/env python3
"""Run the typed-procedural fixture on macOS AE and write a reference record."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parent
FIXTURE_ROOT = PACKAGE_ROOT / "request" / "fixture"
sys.path.insert(0, str(FIXTURE_ROOT))

from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr  # noqa: E402


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_fixture(ae_app: str, fixture_jsx: Path, env: dict[str, str]) -> None:
    script = [
        "osascript",
        "-e",
        "with timeout of 3600 seconds",
        "-e",
        f'tell application "{ae_app}" to DoScriptFile POSIX file "{fixture_jsx}" with override',
        "-e",
        "end timeout",
    ]
    subprocess.run(script, check=True, env=env)


def main() -> int:
    request = read_json(PACKAGE_ROOT / "request" / "request_manifest.json")
    case = request["cases"][0]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ae-app", default="Adobe After Effects 2025")
    parser.add_argument("--output-dir", type=Path, default=PACKAGE_ROOT / "mac_run")
    parser.add_argument("--plugin-binary", type=Path, default=None)
    parser.add_argument("--record-name", default="reference_record.json")
    args = parser.parse_args()

    fixture_jsx = FIXTURE_ROOT / "ae_generate_32bpc_typed_procedural_fixture.jsx"
    renderer_jsx = PACKAGE_ROOT / "scripts" / "renderer.jsx"
    output_dir = args.output_dir.resolve()
    case_root = output_dir / "cases" / case["id"]
    case_root.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["OLM_AE_REQUEST_DIR"] = str(PACKAGE_ROOT / "request")
    env["OLM_AE_CASE_ID"] = case["id"]
    env["OLM_AE_OUTPUT_DIR"] = str(case_root)
    env["OLM_AE_LOG_PATH"] = str(output_dir / "mac_renderer.log")
    env["OLM_AE_RESULT_JSON"] = str(output_dir / "mac_renderer_result.json")
    env["OLM_AE_READY_MARKER"] = str(output_dir / "mac_ready.marker")
    env["OLM_AE_CONTINUE_MARKER"] = str(output_dir / "mac_continue.marker")
    env["OLM_AE_SKIP_LIVE_PAUSE"] = "1"
    env["OLM_AE_RUN_BINDING"] = "platform=macos"
    env["OLM_AE_KEEP_OPEN"] = "0"
    run_fixture(args.ae_app, renderer_jsx, env)

    result = read_json(case_root / "fixture_result.json")
    manifest = read_json(case_root / "fixture_manifest.json")
    renderer_result = read_json(output_dir / "mac_renderer_result.json")
    if result.get("status") != "ok":
        raise SystemExit("fixture_result.json did not report ok")
    if renderer_result.get("status") != "ok":
        raise SystemExit("mac_renderer_result.json did not report ok")
    if renderer_result.get("project_gpu_accel_type", {}).get("current_name") != "SOFTWARE":
        raise SystemExit("macOS host did not observe SOFTWARE renderer")
    if renderer_result.get("linear_blending") is not False:
        raise SystemExit("macOS host did not observe linear blending off")
    try:
        no_effect = inspect_float_rgba_exr(case_root / request["fixture_contract"]["output_names"]["no_effect"], expected_dimensions=(64, 64))
        effect_on = inspect_float_rgba_exr(case_root / request["fixture_contract"]["output_names"]["effect_on"], expected_dimensions=(64, 64))
    except (OSError, ValueError, VerificationError) as exc:
        raise SystemExit(str(exc)) from exc

    plugin_path = args.plugin_binary.resolve() if args.plugin_binary else None
    if plugin_path is None or not plugin_path.is_file():
        raise SystemExit("--plugin-binary must identify the exact OLMToonDilate Mach-O binary")
    record = {
        "kind": "olm_32bpc_typed_procedural_render_record",
        "schema": 1,
        "platform": "macos",
        "record_role": "reference",
        "request_id": request["request_id"],
        "required_ae_major_minor": request["required_ae_major_minor"],
        "ae_version": result.get("ae_version", ""),
        "output_template": request["output_template"],
        "fixture_jsx_sha256": sha256(fixture_jsx),
        "renderer_jsx_sha256": sha256(renderer_jsx),
        "renderer_class": "SOFTWARE",
        "linear_blending": False,
        "cases": [
            {
                "id": case["id"],
                "effect": case["effect_name"],
                "plugin": {
                    "name": "OLMToonDilate.plugin",
                    "path": str(plugin_path),
                    "sha256": sha256(plugin_path),
                },
                "renderer_class": "SOFTWARE",
                "linear_blending": False,
                "parameters_requested": case["parameters"],
                "parameters_readback": renderer_result["parameters_readback"],
                "fixture_contract": request["fixture_contract"],
                "outputs": {
                    "no_effect": {"path": str((case_root / request["fixture_contract"]["output_names"]["no_effect"]).resolve()), "sha256": no_effect["sha256"]},
                    "effect_on": {"path": str((case_root / request["fixture_contract"]["output_names"]["effect_on"]).resolve()), "sha256": effect_on["sha256"]},
                },
                "fixture_manifest": manifest,
            }
        ],
    }
    record_path = output_dir / args.record_name
    record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "record": str(record_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    )


def package_readme(effect_key: str) -> str:
    effect = EFFECTS[effect_key]
    return dedent(
        f"""\
        # {effect['request_id']} Windows Witness

        This package uses the shared `tools/windows_witness` launcher and a paused
        same-comp renderer to generate the 64x64 typed-procedural float fixture
        fully inside After Effects. It imports no PNG, EXR, or footage source.

        Integrity model: the Windows machine and operator are trusted. The package
        rejects incomplete, stale, or internally inconsistent evidence; it is not
        a cryptographic attestation against deliberate fabrication of every log,
        project, and render artifact.

        The Windows path is one-click from an interactive desktop PowerShell:

        ```powershell
        .\\artifacts\\run_witness.ps1
        ```

        Success returns:

        - `return/{effect['case_id']}/effect_no_effect_00000.exr`
        - `return/{effect['case_id']}/effect_effect_on_00000.exr`
        - `return/{effect['case_id']}/fixture_manifest.json`
        - `return/{effect['case_id']}/fixture.aep`
        - `{build_spec(effect_key)['return_bundle']['json_name']}`

        On macOS, a reference record can be created with:

        ```bash
        python3 ./run_mac_reference.py --ae-app "Adobe After Effects 2025"
        ```

        Cross-host comparison accepts either a plain render record or the common
        witness return JSON/ZIP:

        ```bash
        python3 ./compare_cross_host_typed_procedural_fixture.py <mac-record-or-zip> <windows-return-or-zip> --json
        ```
        """
    )


def stage_spec(stage: Path, effect_key: str) -> Path:
    request_dir = stage / "request"
    fixture_dir = request_dir / "fixture"
    fixture_dir.mkdir(parents=True)
    (stage / "witness-spec.json").write_text(json.dumps(build_spec(effect_key), indent=2) + "\n", encoding="utf-8")
    (stage / "renderer.jsx").write_text(renderer_source(), encoding="utf-8", newline="\n")
    (stage / "probe.cdb.in").write_text(probe_source(), encoding="ascii", newline="\n")
    (request_dir / "request_manifest.json").write_text(json.dumps(request_manifest(effect_key), indent=2) + "\n", encoding="utf-8")
    shutil.copy2(FIXTURE_SOURCE, fixture_dir / FIXTURE_SOURCE.name)
    shutil.copy2(COMPARE_FLOAT_SOURCE, fixture_dir / COMPARE_FLOAT_SOURCE.name)
    shutil.copy2(VERIFY_FLOAT_SOURCE, fixture_dir / VERIFY_FLOAT_SOURCE.name)
    return stage / "witness-spec.json"


def refresh_manifest_and_zip(package: Path, archive: Path) -> None:
    manifest_path = package / "package-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = []
    for path in sorted(
        (item for item in package.rglob("*") if item.is_file() and item != manifest_path),
        key=lambda item: item.relative_to(package).as_posix(),
    ):
        files.append(
            {
                "path": path.relative_to(package).as_posix(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    manifest["files"] = files
    manifest_path.write_bytes(canonical_json(manifest))
    deterministic_zip(package, archive)


def install_postprocess(package: Path, archive: Path, effect_key: str) -> None:
    launcher_path = package / "artifacts" / "run_witness.ps1"
    launcher = launcher_path.read_text(encoding="utf-8")
    old = """$validated = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
if ($validated -is [pscustomobject]) {
  $validated | Add-Member -NotePropertyName capture_diagnostics -NotePropertyValue @($captureDiagnostics) -Force
}
Finish $validated $(if ($validateCode -eq 0 -and $validated.status -eq 'answered') { 0 } else { 2 })
"""
    new = """$validated = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
if ($validateCode -eq 0 -and $validated.status -eq 'answered') {
  $typedValidator = Join-Path $PackageRoot 'scripts\\validate_typed_procedural_return.py'
  & py -3 $typedValidator --contract $contractPath --status $statusPath --work $work
  $validateCode = $LASTEXITCODE
  $validated = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
}
if ($validated -is [pscustomobject]) {
  $validated | Add-Member -NotePropertyName capture_diagnostics -NotePropertyValue @($captureDiagnostics) -Force
}
Finish $validated $(if ($validateCode -eq 0 -and $validated.status -eq 'answered') { 0 } else { 2 })
"""
    if launcher.count(old) != 1:
        raise RuntimeError("common launcher validation tail changed")
    launcher = launcher.replace(old, new)
    old_continue = "Set-Content -LiteralPath $continue -Value 'continue' -Encoding ASCII"
    new_continue = "$continueBinding = \"continue run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$hash\"\n  Set-Content -LiteralPath $continue -Value $continueBinding -Encoding ASCII"
    if old_continue not in launcher:
        raise RuntimeError("common launcher continue binding changed")
    launcher = launcher.replace(old_continue, new_continue, 1)
    old_ready = "$readyText -notmatch 'effect_loaded=1' -or $readyText -notmatch 'parameters_applied=1'"
    new_ready = "$readyText -notmatch 'effect_loaded=1' -or $readyText -notmatch 'parameters_applied=1' -or $readyText -notmatch 'search_radius_requested=13' -or $readyText -notmatch 'search_radius_readback=13' -or $readyText -notmatch 'renderer_observed=SOFTWARE' -or $readyText -notmatch 'linear_blending=0'"
    if launcher.count(old_ready) != 1:
        raise RuntimeError("common launcher readiness predicate changed")
    launcher_path.write_text(launcher.replace(old_ready, new_ready), encoding="utf-8", newline="\n")
    (package / "scripts" / "validate_typed_procedural_return.py").write_text(
        validator_source(), encoding="utf-8", newline="\n"
    )
    compare_path = package / "compare_cross_host_typed_procedural_fixture.py"
    compare_path.write_text(compare_helper_source(), encoding="utf-8", newline="\n")
    mac_path = package / "run_mac_reference.py"
    mac_path.write_text(mac_runner_source(), encoding="utf-8", newline="\n")
    (package / "README.md").write_text(package_readme(effect_key), encoding="utf-8", newline="\n")
    refresh_manifest_and_zip(package, archive)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--effect", choices=["toondilate"], default="toondilate")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--zip", dest="zip_path", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    default_output_dir, default_zip_path = package_paths(args.effect)
    output_dir = args.output_dir.resolve() if args.output_dir else default_output_dir
    zip_path = args.zip_path.resolve() if args.zip_path else default_zip_path
    with tempfile.TemporaryDirectory(prefix="typed_proc_common_core_spec_") as raw_stage:
        spec_path = stage_spec(Path(raw_stage), args.effect)
        package, archive = compile_witness(spec_path, output_dir, zip_path)
    install_postprocess(package, archive, args.effect)
    print(
        json.dumps(
            {
                "status": "ok",
                "compiler": "tools.windows_witness.compile",
                "effect": args.effect,
                "package": str(package),
                "zip": str(archive),
                "zip_sha256": sha256(archive),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
