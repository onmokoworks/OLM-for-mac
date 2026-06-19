/*
  Minimal AE-host validation for the OLM macOS port.

  Run with After Effects:
    /Applications/Adobe\ After\ Effects\ 2026/Adobe\ After\ Effects\ 2026.app/Contents/MacOS/After\ Effects -r scripts/ae_host_minimal_validation.jsx

  Environment:
    OLM_AE_VALIDATION_OUTPUT=/path/to/AE_VALIDATION_RESULT.json
*/
(function () {
    function getenv(name) {
        try {
            return $.getenv(name);
        } catch (e) {
            return null;
        }
    }

    function esc(s) {
        if (s === null || s === undefined) {
            return "";
        }
        return String(s)
            .replace(/\\/g, "\\\\")
            .replace(/"/g, "\\\"")
            .replace(/\r/g, "\\r")
            .replace(/\n/g, "\\n");
    }

    function boolJson(v) {
        if (v === true) {
            return "true";
        }
        if (v === false) {
            return "false";
        }
        return "null";
    }

    function writeText(path, text) {
        var file = new File(path);
        file.encoding = "UTF-8";
        file.open("w");
        file.write(text);
        file.close();
    }

    function shell(command) {
        try {
            return system.callSystem(command).replace(/[\r\n]+$/g, "");
        } catch (e) {
            return "";
        }
    }

    function waitForFile(file, tries, sleepMs) {
        for (var i = 0; i < tries; i++) {
            if (file.exists) {
                return true;
            }
            $.sleep(sleepMs);
        }
        return file.exists;
    }

    var output = getenv("OLM_AE_VALIDATION_OUTPUT");
    var resultFolder = null;
    if (!output || output === "") {
        var repoRoot = File($.fileName).parent.parent;
        resultFolder = new Folder(repoRoot.fsName + "/handoff/ae_host_validation_20260618");
        if (!resultFolder.exists) {
            resultFolder.create();
        }
        output = resultFolder.fsName + "/AE_VALIDATION_RESULT_minimal_load_apply_20260618.json";
    } else {
        resultFolder = new File(output).parent;
        if (!resultFolder.exists) {
            resultFolder.create();
        }
    }
    var pngFolder = new Folder(resultFolder.fsName + "/minimal_render_png");
    if (!pngFolder.exists) {
        pngFolder.create();
    }

    var effects = [
        { name: "ColorKeep", menu: "Color Keep", matchNames: ["OLM Color Keep", "Color Keep"] },
        { name: "OLMBlur", menu: "OLM Blur", matchNames: ["OLM OLM Blur", "OLM Blur"] },
        { name: "OLMColorKey", menu: "OLM Color Key", matchNames: ["OLM Color Key"] },
        { name: "OLMDirectionalBlur", menu: "OLM DirectionalBlur", matchNames: ["OLM Directional Blur", "OLM DirectionalBlur"] },
        { name: "OLMRadialBlur", menu: "OLM RadialBlur", matchNames: ["OLM RadialBlur"] },
        { name: "OLMKiraKira", menu: "OLM Kira Kira", matchNames: ["OLM OLM Kira Kira", "OLM Kira Kira"] },
        { name: "OLMToonDilate", menu: "OLM Toon Dilate", matchNames: ["ADBE OLMToonDilate", "OLM Toon Dilate"] },
        { name: "OLMDistanceGradation", menu: "Distance Gradation", matchNames: ["OLM Distance Gradation", "Distance Gradation"] },
        { name: "OLMSmoother", menu: "OLM Smoother", matchNames: ["OLM Smoother"] },
        { name: "OLMSmoother2", menu: "OLM Smoother v2", matchNames: ["OLM Smoother v2"] }
    ];

    var results = [];
    var project = app.project;
    if (!project) {
        project = app.newProject();
    }

    app.beginUndoGroup("OLM minimal validation");
    for (var i = 0; i < effects.length; i++) {
        var spec = effects[i];
        var entry = {
            name: spec.name,
            loaded: false,
            applied: false,
            render_succeeded: null,
            effect_menu_name: spec.menu,
            error: "",
            returned_artifacts: []
        };
        try {
            var comp = project.items.addComp("olm_validate_" + spec.name, 64, 64, 1.0, 1.0, 24.0);
            var layer = comp.layers.addSolid([0.25, 0.5, 0.75], "source", 64, 64, 1.0, 1.0);
            var parade = layer.property("ADBE Effect Parade");
            var applied = null;
            var errors = [];
            for (var j = 0; j < spec.matchNames.length; j++) {
                try {
                    applied = parade.addProperty(spec.matchNames[j]);
                    if (applied) {
                        entry.loaded = true;
                        entry.applied = true;
                        entry.effect_menu_name = applied.name;
                        break;
                    }
                } catch (candidateError) {
                    errors.push(spec.matchNames[j] + ": " + candidateError.toString());
                }
            }
            if (!applied) {
                entry.error = errors.join(" | ");
            } else {
                try {
                    var png = new File(pngFolder.fsName + "/" + spec.name + ".png");
                    comp.saveFrameToPng(0.0, png);
                    if (waitForFile(png, 20, 250)) {
                        entry.render_succeeded = true;
                        entry.returned_artifacts.push("minimal_render_png/" + spec.name + ".png");
                    } else {
                        entry.render_succeeded = false;
                        entry.error = entry.error + (entry.error ? " | " : "") + "render: saveFrameToPng returned but no PNG was written";
                    }
                } catch (renderError) {
                    entry.render_succeeded = false;
                    entry.error = entry.error + (entry.error ? " | " : "") + "render: " + renderError.toString();
                }
            }
        } catch (e) {
            entry.error = e.toString();
        }
        results.push(entry);
    }
    app.endUndoGroup();

    var json = "";
    var macosVersion = shell("/usr/bin/sw_vers -productVersion");
    var machine = shell("/usr/bin/uname -m");
    var gpuName = "UNKNOWN";
    var gpuRaw = -1;
    try {
        gpuRaw = Number(app.project.gpuAccelType);
        gpuName = String(app.project.gpuAccelType);
        if (gpuName === "" || gpuName === "undefined") {
            gpuName = "UNKNOWN";
        }
        if (isNaN(gpuRaw)) {
            gpuRaw = -1;
        }
    } catch (gpuError) {
    }
    json += "{\n";
    json += "  \"kind\": \"olm_ae_host_validation_result\",\n";
    json += "  \"package_configuration\": \"Debug\",\n";
    json += "  \"ae_version\": \"" + esc(app.version) + "\",\n";
    json += "  \"macos_version\": \"" + esc(macosVersion) + "\",\n";
    json += "  \"machine\": \"" + esc(machine) + "\",\n";
    json += "  \"project_gpu_accel_type\": { \"current_name\": \"" + esc(gpuName) + "\", \"raw\": " + gpuRaw + " },\n";
    json += "  \"clean_ae_launch_after_install\": true,\n";
    json += "  \"install_path\": \"~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/\",\n";
    json += "  \"notes\": \"Automated minimal load/apply/render validation using a 64x64 solid and CompItem.saveFrameToPng. This is a host smoke, not full pixel-reference validation.\",\n";
    json += "  \"plugins\": [\n";
    for (var k = 0; k < results.length; k++) {
        var r = results[k];
        json += "    {\n";
        json += "      \"name\": \"" + esc(r.name) + "\",\n";
        json += "      \"loaded\": " + boolJson(r.loaded) + ",\n";
        json += "      \"applied\": " + boolJson(r.applied) + ",\n";
        json += "      \"render_succeeded\": " + boolJson(r.render_succeeded) + ",\n";
        json += "      \"effect_menu_name\": \"" + esc(r.effect_menu_name) + "\",\n";
        json += "      \"error\": \"" + esc(r.error) + "\",\n";
        json += "      \"returned_artifacts\": [";
        for (var a = 0; a < r.returned_artifacts.length; a++) {
            json += "\"" + esc(r.returned_artifacts[a]) + "\"" + (a + 1 < r.returned_artifacts.length ? ", " : "");
        }
        json += "]\n";
        json += "    }" + (k + 1 < results.length ? "," : "") + "\n";
    }
    json += "  ]\n";
    json += "}\n";

    writeText(output, json);
    try {
        app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
    } catch (closeError) {
    }
    app.quit();
}());
