/*
  Fresh-host load/apply/render smoke for the ten installed OLM plug-ins.

  This payload is launched only by
  run_olm_all10_current_install_fresh_ae_smoke_20260812.py.  The Python
  runner pins the installed identity before launch, captures one persisted
  vmmap while this script waits, and then acknowledges the script so AE can
  quit normally.

  This is deliberately a host smoke.  It is not pixel-reference evidence.
*/
(function () {
    function fail(message) {
        throw new Error("FAIL_CLOSED: " + message);
    }

    function env(name) {
        try {
            return $.getenv(name);
        } catch (_) {
            return null;
        }
    }

    function escapeJson(value) {
        return String(value)
            .replace(/\\/g, "\\\\")
            .replace(/\"/g, "\\\"")
            .replace(/\r/g, "\\r")
            .replace(/\n/g, "\\n")
            .replace(/\t/g, "\\t");
    }

    function json(value) {
        if (value === null || value === undefined) {
            return "null";
        }
        if (typeof value === "boolean" || typeof value === "number") {
            return String(value);
        }
        if (typeof value === "string") {
            return "\"" + escapeJson(value) + "\"";
        }
        if (Object.prototype.toString.call(value) === "[object Array]") {
            var entries = [];
            for (var i = 0; i < value.length; i++) {
                entries.push(json(value[i]));
            }
            return "[" + entries.join(",") + "]";
        }
        var properties = [];
        for (var key in value) {
            if (value.hasOwnProperty(key)) {
                properties.push("\"" + escapeJson(key) + "\":" + json(value[key]));
            }
        }
        return "{" + properties.join(",") + "}";
    }

    function writeText(path, text) {
        var file = new File(path);
        file.encoding = "UTF-8";
        if (!file.open("w")) {
            fail("cannot write " + path);
        }
        file.write(text);
        file.close();
    }

    function waitForFile(file, attempts, sleepMs) {
        for (var i = 0; i < attempts; i++) {
            if (file.exists) {
                return true;
            }
            $.sleep(sleepMs);
        }
        return file.exists;
    }

    function removeStale(file) {
        if (file.exists && !file.remove()) {
            fail("cannot remove stale output " + file.fsName);
        }
    }

    var resultPath = env("OLM_ALL10_AE_RESULT");
    var pngDirPath = env("OLM_ALL10_AE_PNG_DIR");
    var vmmapAckPath = env("OLM_ALL10_AE_VMMAP_ACK");
    var runNonce = env("OLM_ALL10_AE_RUN_NONCE");
    if (!resultPath || !pngDirPath || !vmmapAckPath || !runNonce) {
        fail("required environment is absent");
    }

    var pngDir = new Folder(pngDirPath);
    if (!pngDir.exists && !pngDir.create()) {
        fail("cannot create PNG directory");
    }

    var specs = [
        { plugin: "OLMBlur", matchNames: ["OLM OLM Blur", "OLM Blur"], width: 64, height: 36, depth: 32, enabledHostFrame: true },
        { plugin: "ColorKeep", matchNames: ["OLM Color Keep", "Color Keep"], width: 11, height: 7, depth: 32 },
        { plugin: "OLMColorKey", matchNames: ["OLM Color Key"], width: 4, height: 4, depth: 32 },
        { plugin: "OLMDirectionalBlur", matchNames: ["OLM Directional Blur", "OLM DirectionalBlur"], width: 64, height: 36, depth: 32, enabledHostFrame: true },
        { plugin: "OLMDistanceGradation", matchNames: ["OLM Distance Gradation", "Distance Gradation"], width: 17, height: 11, depth: 32 },
        { plugin: "OLMKiraKira", matchNames: ["OLM OLM Kira Kira", "OLM Kira Kira"], width: 5, height: 4, depth: 8 },
        { plugin: "OLMRadialBlur", matchNames: ["OLM RadialBlur"], width: 9, height: 7, depth: 32 },
        { plugin: "OLMSmoother", matchNames: ["OLM Smoother"], width: 17, height: 11, depth: 16 },
        { plugin: "OLMSmoother2", matchNames: ["OLM Smoother v2"], width: 17, height: 11, depth: 32 },
        { plugin: "OLMToonDilate", matchNames: ["ADBE OLMToonDilate", "OLM Toon Dilate"], width: 64, height: 36, depth: 32, enabledHostFrame: true }
    ];

    var project = app.newProject();
    if (!project) {
        fail("newProject returned null");
    }
    project.linearBlending = false;
    project.workingSpace = "";
    project.gpuAccelType = GpuAccelType.SOFTWARE;
    if (Number(project.gpuAccelType) !== Number(GpuAccelType.SOFTWARE) || project.linearBlending) {
        fail("SOFTWARE project contract readback");
    }

    var rows = [];
    var startedEpochMs = new Date().getTime();
    app.beginSuppressDialogs();
    try {
        for (var s = 0; s < specs.length; s++) {
            var spec = specs[s];
            var row = {
                plugin: spec.plugin,
                loaded: false,
                applied: false,
                render_succeeded: false,
                host_smoke_expectation: spec.enabledHostFrame === true ? "enabled_host_frame_render" : "disabled_host_frame_render",
                effect_enabled_host_frame_attempted: spec.enabledHostFrame === true,
                effect_enabled_host_frame_succeeded: false,
                numerical_render_expected: false,
                numerical_render_supported: false,
                numerical_render_attempted: false,
                effect_enabled_numerical_render_attempted: false,
                numerical_render_succeeded: null,
                host_frame_render_succeeded: false,
                effect_disabled_during_host_frame: spec.enabledHostFrame !== true,
                effect_can_enable_after_add: false,
                effect_enabled_during_render: null,
                match_name: null,
                effect_name: null,
                depth: spec.depth,
                dimensions: [spec.width, spec.height],
                output_path: null,
                output_size: null,
                output_modified_epoch_ms: null,
                error: ""
            };
            try {
                project.bitsPerChannel = spec.depth;
                if (Number(project.bitsPerChannel) !== spec.depth) {
                    fail("depth readback " + spec.plugin);
                }
                var comp = project.items.addComp(
                    "olm_all10_fresh_" + spec.plugin,
                    spec.width,
                    spec.height,
                    1.0,
                    1.0,
                    24.0
                );
                var layer = comp.layers.addSolid(
                    [26 / 255, 191 / 255, 204 / 255],
                    "rgba_26_191_204_opaque",
                    spec.width,
                    spec.height,
                    1.0,
                    1.0
                );
                var parade = layer.property("ADBE Effect Parade");
                var effect = null;
                var errors = [];
                for (var m = 0; m < spec.matchNames.length; m++) {
                    try {
                        effect = parade.addProperty(spec.matchNames[m]);
                        if (effect) {
                            break;
                        }
                    } catch (candidateError) {
                        errors.push(spec.matchNames[m] + ": " + candidateError.toString());
                    }
                }
                if (!effect) {
                    throw new Error("effect registration/add failed: " + errors.join(" | "));
                }
                row.loaded = true;
                row.applied = true;
                row.match_name = String(effect.matchName);
                row.effect_name = String(effect.name);
                var expectedMatch = false;
                for (var em = 0; em < spec.matchNames.length; em++) {
                    if (row.match_name === spec.matchNames[em]) expectedMatch = true;
                }
                if (!expectedMatch) throw new Error("unexpected effect matchName " + row.match_name);
                effect.enabled = true;
                row.effect_can_enable_after_add = effect.enabled === true;
                if (!row.effect_can_enable_after_add) {
                    throw new Error("effect could not be enabled");
                }
                // The production admission guards intentionally reject many
                // default tuples and some numerical routes can wait inside the
                // host.  This aggregate smoke proves registration/add and host
                // frame rendering only; numerical owner routes have their own
                // hash-bound fixtures.  Disable before saveFrameToPng so this
                // result never masquerades as a numerical render claim.
                effect.enabled = spec.enabledHostFrame === true;
                row.effect_enabled_during_render = effect.enabled;

                var png = new File(pngDir.fsName + "/" + spec.plugin + ".png");
                removeStale(png);
                comp.saveFrameToPng(0.0, png);
                if (!waitForFile(png, 80, 250)) {
                    throw new Error("saveFrameToPng returned without a PNG");
                }
                png = new File(png.fsName);
                if (png.length <= 0) {
                    throw new Error("PNG is empty");
                }
                var modifiedEpochMs = png.modified ? png.modified.getTime() : 0;
                if (modifiedEpochMs + 1000 < startedEpochMs) {
                    throw new Error("PNG is older than this host payload");
                }
                row.render_succeeded = true;
                row.host_frame_render_succeeded = true;
                row.effect_enabled_host_frame_succeeded = spec.enabledHostFrame === true ? true : false;
                row.output_path = png.fsName;
                row.output_size = png.length;
                row.output_modified_epoch_ms = modifiedEpochMs;
            } catch (pluginError) {
                row.error = pluginError.toString();
            }
            rows.push(row);
        }
    } finally {
        app.endSuppressDialogs(false);
    }

    var allPassed = rows.length === specs.length;
    for (var r = 0; r < rows.length; r++) {
        allPassed = allPassed && rows[r].loaded && rows[r].applied &&
            rows[r].effect_can_enable_after_add &&
            rows[r].effect_enabled_during_render === rows[r].effect_enabled_host_frame_attempted &&
            rows[r].render_succeeded;
    }
    var returned = {
        schema: "olm.all10-fresh-ae-host-return/1",
        status: allPassed ? "ok" : "fail_closed",
        run_nonce: runNonce,
        started_epoch_ms: startedEpochMs,
        completed_epoch_ms: new Date().getTime(),
        ae_version: String(app.version),
        os: String($.os),
        project: {
            renderer: "SOFTWARE",
            renderer_raw: Number(project.gpuAccelType),
            working_space: String(project.workingSpace),
            linear_blending: project.linearBlending
        },
        plugins: rows,
        claim_boundary: "Fresh installed host load/add and exact mapping for all ten; effect-enabled host frame render only for OLMBlur, OLMDirectionalBlur, and OLMToonDilate; effect-disabled host frame render for the other seven. No pixel-exact, Windows-equivalence, typed-plane, padding, or public-owner numerical-exact claim."
    };
    writeText(resultPath, json(returned) + "\n");

    // Keep the project and every loaded module alive until the Python runner
    // has persisted one vmmap.  Timeout is fail-closed but still quits AE.
    var ack = new File(vmmapAckPath);
    waitForFile(ack, 720, 250);
    try {
        project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
    } catch (_) {
    }
    app.quit();
}());
