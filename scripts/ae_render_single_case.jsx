/*
  Render one AE pixel-validation case with detailed logging.

  Environment:
    OLM_AE_REQUEST_DIR=/abs/path/to/request_dir
    OLM_AE_CASE_ID=olmcolorkey__case_0009
    OLM_AE_OUTPUT_DIR=/abs/path/to/output_dir
    OLM_AE_LOG_PATH=/abs/path/to/log.txt
    OLM_AE_RESULT_JSON=/abs/path/to/result.json

  Preferred entrypoint:
    python3 scripts/run_ae_single_case.py --request-dir ... --case-id ...
    The wrapper sets the ExtendScript environment for you and avoids stale
    manual-launch failures.

  Run from a live After Effects instance:
    osascript -e 'with timeout of 3600 seconds' \
      -e 'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file "/abs/path/scripts/ae_render_single_case.jsx" with override' \
      -e 'end timeout'
*/
(function () {
    function getenv(name) {
        try {
            return $.getenv(name);
        } catch (e) {
            return "";
        }
    }

    function ensureFolder(path) {
        var folder = new Folder(path);
        if (!folder.exists) {
            folder.create();
        }
        return folder;
    }

    function bytesMatch(value, expected) {
        if (!value || value.length !== expected.length) {
            return false;
        }
        for (var i = 0; i < expected.length; i++) {
            if ((value.charCodeAt(i) & 255) !== expected[i]) {
                return false;
            }
        }
        return true;
    }

    function hasCompletePngTrailer(file) {
        if (!file.exists || Number(file.length || 0) < 20) {
            return false;
        }
        var opened = false;
        try {
            file.encoding = "BINARY";
            if (!file.open("r")) {
                return false;
            }
            opened = true;
            var signature = file.read(8);
            if (!bytesMatch(signature, [137, 80, 78, 71, 13, 10, 26, 10])) {
                return false;
            }
            // AE 26.3 returns false for negative SEEK_END offsets. Use the
            // observed byte length and an absolute offset instead.
            file.seek(Number(file.length) - 12, 0);
            return bytesMatch(file.read(12), [0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130]);
        } catch (_) {
            return false;
        } finally {
            if (opened) {
                try { file.close(); } catch (_) {}
            }
        }
    }

    function waitForStableFile(file, since, timeoutMs, sleepMs, stableWindowMs) {
        // AE writes the PNG asynchronously. ExtendScript may cache metadata on
        // an existing File object, so observe the path through a fresh object
        // on every poll.
        var watchedPath = file.fsName;
        var startedWaiting = new Date();
        var sinceMs = since.getTime() - 2000;
        var lastSize = -1;
        var lastModified = -1;
        var stableStartedMs = 0;
        var stablePolls = 0;
        var polls = 0;
        var observation = { status: "timeout", timeout_ms: timeoutMs, waited_ms: 0, polls: 0, stable_polls: 0, stable_for_ms: 0, stable_window_ms: stableWindowMs, size_bytes: 0, modified_ms: 0, format_complete: false, crc_validated: false };
        while (true) {
            polls++;
            file = new File(watchedPath);
            var nowMs = (new Date()).getTime();
            var exists = file.exists;
            var size = exists ? Number(file.length || 0) : 0;
            var modified = exists && file.modified ? file.modified.getTime() : 0;
            var fresh = exists && (!file.modified || modified >= sinceMs);
            if (fresh && size > 0) {
                if (size === lastSize && modified === lastModified) {
                    stablePolls++;
                } else {
                    stablePolls = 1;
                    stableStartedMs = nowMs;
                }
                var stableForMs = nowMs - stableStartedMs;
                var formatComplete = stableForMs >= stableWindowMs && hasCompletePngTrailer(file);
                var verifiedFile = new File(watchedPath);
                var verifiedSize = verifiedFile.exists ? Number(verifiedFile.length || 0) : 0;
                var verifiedModified = verifiedFile.exists && verifiedFile.modified ? verifiedFile.modified.getTime() : 0;
                if (stableForMs >= stableWindowMs && formatComplete && verifiedSize === size && verifiedModified === modified) {
                    observation.status = "stable";
                    observation.waited_ms = nowMs - startedWaiting.getTime();
                    observation.polls = polls;
                    observation.stable_polls = stablePolls;
                    observation.stable_for_ms = stableForMs;
                    observation.size_bytes = size;
                    observation.modified_ms = modified;
                    observation.format_complete = true;
                    return observation;
                }
                lastSize = size;
                lastModified = modified;
            } else {
                stablePolls = 0;
                stableStartedMs = 0;
                lastSize = -1;
                lastModified = -1;
            }
            if (nowMs - startedWaiting.getTime() >= timeoutMs) {
                observation.waited_ms = nowMs - startedWaiting.getTime();
                observation.polls = polls;
                observation.stable_polls = stablePolls;
                observation.stable_for_ms = stableStartedMs ? nowMs - stableStartedMs : 0;
                observation.size_bytes = size;
                observation.modified_ms = modified;
                observation.format_complete = fresh && size > 0 && hasCompletePngTrailer(file);
                observation.status = exists ? (size > 0 ? "unstable" : "empty") : "missing";
                return observation;
            }
            $.sleep(sleepMs);
        }
    }

    function writeText(path, text) {
        var file = new File(path);
        file.encoding = "UTF-8";
        if (!file.open("w")) {
            throw new Error("could not write " + path);
        }
        file.write(text);
        file.close();
    }

    function appendText(path, text) {
        var file = new File(path);
        file.encoding = "UTF-8";
        if (file.open("a")) {
            file.write(text);
            file.close();
        }
    }

    function shellDoubleQuote(value) {
        return "\"" + String(value).replace(/([\\\"$`])/g, "\\$1") + "\"";
    }

    function readText(path) {
        var file = new File(path);
        file.encoding = "UTF-8";
        if (!file.open("r")) {
            throw new Error("could not open " + path);
        }
        var text = file.read();
        file.close();
        return text;
    }

    function parseJson(path) {
        var text = readText(path);
        // AE 26.3's ExtendScript JSON.parse can hang on the generated
        // reference_manifest.json size. These manifests are local artifacts
        // created by our own tooling, so use the legacy parser here.
        return eval("(" + text + ")");
    }

    function parseJsonText(text) {
        if (!text) {
            return {};
        }
        return eval("(" + text + ")");
    }

    function esc(value) {
        if (value === null || value === undefined) {
            return "";
        }
        return String(value).replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\r/g, "\\r").replace(/\n/g, "\\n");
    }

    function importFootage(path) {
        var file = new File(path);
        file = new File(file.fsName);
        var options = new ImportOptions(file);
        return app.project.importFile(options);
    }

    function isArrayValue(value) {
        return Object.prototype.toString.call(value) === "[object Array]";
    }

    function coerceValue(value) {
        if (isArrayValue(value)) {
            var arr = [];
            for (var i = 0; i < value.length; i++) {
                arr.push(value[i]);
            }
            return arr;
        }
        return value;
    }

    function valueToLog(value) {
        if (isArrayValue(value)) {
            return "[" + value.join(",") + "]";
        }
        return String(value);
    }

    function childByMatchOrName(group, matchName, name) {
        if (!group || !group.numProperties) {
            return null;
        }
        for (var i = 1; i <= group.numProperties; i++) {
            var prop = group.property(i);
            if (prop && matchName && prop.matchName === matchName) {
                return prop;
            }
        }
        for (var j = 1; j <= group.numProperties; j++) {
            var namedProp = group.property(j);
            if (namedProp && name && namedProp.name === name) {
                return namedProp;
            }
        }
        return null;
    }

    function findCase(referenceManifest, id) {
        var cases = referenceManifest.cases || [];
        for (var i = 0; i < cases.length; i++) {
            if (cases[i].id === id) {
                return cases[i];
            }
        }
        return null;
    }

    var requestDir = getenv("OLM_AE_REQUEST_DIR");
    var caseId = getenv("OLM_AE_CASE_ID");
    var outputDir = getenv("OLM_AE_OUTPUT_DIR");
    var logPath = getenv("OLM_AE_LOG_PATH");
    var resultJson = getenv("OLM_AE_RESULT_JSON");
    var overrideJson = getenv("OLM_AE_PARAM_OVERRIDES_JSON");
    var outputMode = getenv("OLM_AE_OUTPUT_MODE");
    var outputTemplate = getenv("OLM_AE_OUTPUT_TEMPLATE");
    var keepOpen = getenv("OLM_AE_KEEP_OPEN") === "1";
    var disableEffect = getenv("OLM_AE_DISABLE_EFFECT") === "1";
    var disableProjectColorManagement = getenv("OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT") === "1";
    var forceNewProject = getenv("OLM_AE_FORCE_NEW_PROJECT") === "1";
    var forceSoftware = getenv("OLM_AE_FORCE_SOFTWARE") === "1";
    var inputAlphaMode = String(getenv("OLM_AE_INPUT_ALPHA_MODE") || "").toUpperCase();
    var inputFileOverride = getenv("OLM_AE_INPUT_FILE_OVERRIDE");
    var pauseBeforeRender = getenv("OLM_AE_PAUSE_BEFORE_RENDER") === "1";
    var readyMarkerPath = getenv("OLM_AE_READY_MARKER");
    var continueMarkerPath = getenv("OLM_AE_CONTINUE_MARKER");
    var pauseTimeoutSeconds = Number(getenv("OLM_AE_PAUSE_TIMEOUT_SECONDS") || 300);

    if (!requestDir) {
        requestDir = File($.fileName).parent.parent.fsName +
            "/handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmcolorkey_exact_20260625";
    }
    if (!caseId) {
        caseId = "olmcolorkey__case_0009";
    }
    if (!outputDir) {
        outputDir = File($.fileName).parent.parent.fsName + "/handoff/ae_pixel_validation_20260618/single_case_output";
    }
    if (!logPath) {
        logPath = File($.fileName).parent.parent.fsName + "/handoff/ae_pixel_validation_20260618/AE_SINGLE_CASE.log";
    }
    if (!resultJson) {
        resultJson = File($.fileName).parent.parent.fsName + "/handoff/ae_pixel_validation_20260618/AE_SINGLE_CASE_RESULT.json";
    }

    ensureFolder(new File(outputDir).parent.fsName);
    ensureFolder(outputDir);
    writeText(logPath, "start " + (new Date()).toString() + "\n");

    var summary = {
        kind: "olm_ae_single_case_result",
        ae_version: app.version,
        request_dir: requestDir,
        case_id: caseId,
        output_dir: outputDir,
        output_png: "",
        output_exr: "",
        png_observation: { status: "not_started", timeout_ms: 120000, waited_ms: 0, polls: 0, stable_polls: 0, stable_for_ms: 0, stable_window_ms: 2000, size_bytes: 0, modified_ms: 0, format_complete: false, crc_validated: false },
        project_bits_per_channel: -1,
        project_working_space: "unknown",
        project_linear_blending: false,
        input_alpha_mode: inputAlphaMode || "default",
        effect_disabled: disableEffect,
        status: "unknown",
        error: "",
        warnings: []
    };

    try {
        appendText(logPath, "load request manifests\n");
        var requestManifest = parseJson(requestDir + "/request_manifest.json");
        var referenceManifest = parseJson(requestDir + "/" + requestManifest.reference_manifest);
        if (!inputAlphaMode) {
            var captureInfo = referenceManifest.current_reference_capture || {};
            inputAlphaMode = String(
                captureInfo.input_alpha_mode || referenceManifest.input_alpha_mode || ""
            ).toUpperCase();
            if (inputAlphaMode) {
                summary.input_alpha_mode = inputAlphaMode;
                appendText(logPath, "inputAlphaMode.manifest=" + inputAlphaMode + "\n");
            }
        }
        var caseRef = findCase(referenceManifest, caseId);
        if (!caseRef) {
            throw new Error("missing case in reference manifest: " + caseId);
        }
        var requestCase = null;
        var requestCases = requestManifest.cases || [];
        for (var rc = 0; rc < requestCases.length; rc++) {
            if (requestCases[rc].id === caseId) {
                requestCase = requestCases[rc];
                break;
            }
        }
        if (!requestCase) {
            throw new Error("missing case in request manifest: " + caseId);
        }

        if (forceNewProject) {
            if (app.project) {
                try {
                    app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
                    appendText(logPath, "closed pre-existing project\n");
                } catch (closeExistingError) {
                    appendText(logPath, "pre-existing project close warning " + closeExistingError.toString() + "\n");
                }
            }
            app.newProject();
        } else if (!app.project) {
            app.newProject();
        }
        if (forceSoftware) {
            try {
                app.project.gpuAccelType = GpuAccelType.SOFTWARE;
                appendText(logPath, "gpuAccelType=SOFTWARE\n");
            } catch (gpuError) {
                summary.warnings.push("gpuAccelType: " + gpuError.toString());
            }
        }
        if (disableProjectColorManagement) {
            try {
                appendText(logPath, "workingSpace.before=" + app.project.workingSpace + "\n");
                appendText(logPath, "linearBlending.before=" + app.project.linearBlending + "\n");
                app.project.workingSpace = "";
                app.project.linearBlending = false;
                appendText(logPath, "workingSpace.after=" + app.project.workingSpace + "\n");
                appendText(logPath, "linearBlending.after=" + app.project.linearBlending + "\n");
            } catch (colorManagementError) {
                summary.warnings.push("projectColorManagement: " + colorManagementError.toString());
            }
        }
        try {
            var requestedBits = null;
            var requestedBitsSource = "";
            if (referenceManifest.project && referenceManifest.project.bits_per_channel) {
                requestedBits = Number(referenceManifest.project.bits_per_channel);
                requestedBitsSource = "project.bits_per_channel";
            } else if (referenceManifest.comp && referenceManifest.comp.bpc) {
                requestedBits = Number(referenceManifest.comp.bpc);
                requestedBitsSource = "comp.bpc";
            }
            if (requestedBits) {
                app.project.bitsPerChannel = requestedBits;
                appendText(logPath, "bitsPerChannel=" + app.project.bitsPerChannel + " source=" + requestedBitsSource + "\n");
            }
            summary.project_bits_per_channel = Number(app.project.bitsPerChannel);
            summary.project_working_space = String(app.project.workingSpace);
            summary.project_linear_blending = app.project.linearBlending ? true : false;
        } catch (bitsError) {
            summary.warnings.push("bitsPerChannel: " + bitsError.toString());
        }

        var inputFilename = inputFileOverride || requestCase.before_effects_frame;
        var inputPath = requestDir + "/" + requestManifest.input_dir + "/" + inputFilename;
        appendText(logPath, "inputFilename=" + inputFilename + (inputFileOverride ? " source=override\n" : " source=before_effects_frame\n"));
        appendText(logPath, "import " + inputPath + "\n");
        var footage = importFootage(inputPath);
        if (inputAlphaMode) {
            try {
                if (inputAlphaMode === "PREMULTIPLIED") {
                    footage.mainSource.alphaMode = AlphaMode.PREMULTIPLIED;
                    footage.mainSource.premulColor = [0, 0, 0];
                } else if (inputAlphaMode === "STRAIGHT") {
                    footage.mainSource.alphaMode = AlphaMode.STRAIGHT;
                } else if (inputAlphaMode === "IGNORE") {
                    footage.mainSource.alphaMode = AlphaMode.IGNORE;
                } else {
                    throw new Error("unsupported OLM_AE_INPUT_ALPHA_MODE: " + inputAlphaMode);
                }
                appendText(logPath, "inputAlphaMode=" + inputAlphaMode + " actual=" + footage.mainSource.alphaMode + "\n");
            } catch (alphaModeError) {
                throw new Error("input alpha interpretation failed: " + alphaModeError.toString());
            }
        }
        var compInfo = referenceManifest.comp || {};
        var comp = app.project.items.addComp(
            "single_" + caseId,
            Number(compInfo.width || footage.width || 1920),
            Number(compInfo.height || footage.height || 1080),
            1.0,
            Number(compInfo.duration || 1.0),
            Number(compInfo.frame_rate || 24.0)
        );
        var layer = comp.layers.add(footage);
        layer.startTime = 0;
        appendText(logPath, "comp/layer ready\n");

        if (disableEffect) {
            appendText(logPath, "effect disabled by OLM_AE_DISABLE_EFFECT\n");
        } else {
            var effectParade = layer.property("ADBE Effect Parade");
            var effectCandidates = [requestManifest.effect_match_name, requestManifest.effect_name];
            if (caseRef.effects && caseRef.effects.length > 0) {
                effectCandidates.unshift(caseRef.effects[0].match_name);
                effectCandidates.push(caseRef.effects[0].name);
            }
            var effect = null;
            var addErrors = [];
            for (var ec = 0; ec < effectCandidates.length; ec++) {
                var candidateName = effectCandidates[ec];
                if (!candidateName) {
                    continue;
                }
                try {
                    appendText(logPath, "try add effect " + candidateName + "\n");
                    effect = effectParade.addProperty(candidateName);
                    if (effect) {
                        appendText(logPath, "effect added " + effect.name + " / " + effect.matchName + "\n");
                        break;
                    }
                } catch (addError) {
                    addErrors.push(candidateName + ": " + addError.toString());
                }
            }
            if (!effect) {
                throw new Error("could not add effect: " + addErrors.join(" | "));
            }

            var params = (caseRef.effects && caseRef.effects.length > 0) ? (caseRef.effects[0].params || []) : [];
            var overrides = parseJsonText(overrideJson);
            for (var p = 0; p < params.length; p++) {
            var param = params[p];
            if (param.value === null || param.value === undefined) {
                continue;
            }
            var skip = false;
            if (param.match_name === "ADBE Effect Mask Opacity" || param.match_name === "ADBE Force CPU GPU") {
                skip = true;
            }
            var pathFull = param.path_full || [];
            for (var pf = 0; pf < pathFull.length; pf++) {
                if (pathFull[pf].match_name === "ADBE Effect Built In Params") {
                    skip = true;
                }
            }
            if (skip) {
                continue;
            }
            var leaf = null;
            if (pathFull.length >= 2) {
                leaf = pathFull[pathFull.length - 1];
            } else if (param.match_name || param.name) {
                leaf = { match_name: param.match_name, name: param.name };
            }
            if (!leaf) {
                continue;
            }
            var prop = childByMatchOrName(effect, leaf.match_name, leaf.name || param.name);
            if (!prop) {
                summary.warnings.push("missing property " + (leaf.match_name || param.name));
                continue;
            }
            var overrideKey = leaf.match_name || param.match_name || param.name || "";
            var overrideName = param.name || (leaf.name || "");
            var value = param.value;
            if (overrideKey && overrides.hasOwnProperty(overrideKey)) {
                value = overrides[overrideKey];
                appendText(logPath, "override match=" + overrideKey + " value=" + valueToLog(value) + "\n");
            } else if (overrideName && overrides.hasOwnProperty(overrideName)) {
                value = overrides[overrideName];
                appendText(logPath, "override name=" + overrideName + " value=" + valueToLog(value) + "\n");
            }
            var rawValue = coerceValue(value);
            appendText(
                logPath,
                "set.begin index=" + p +
                    " match=" + (leaf.match_name || "") +
                    " name=" + (prop.name || "") +
                    " propMatch=" + (prop.matchName || "") +
                    " valueType=" + prop.propertyValueType +
                    " value=" + valueToLog(rawValue) + "\n"
            );
            try {
                prop.setValue(rawValue);
            } catch (setError) {
                appendText(
                    logPath,
                    "set.error index=" + p +
                        " match=" + (leaf.match_name || "") +
                        " name=" + (prop.name || "") +
                        " propMatch=" + (prop.matchName || "") +
                        " valueType=" + prop.propertyValueType +
                        " value=" + valueToLog(rawValue) +
                        " error=" + setError.toString() + "\n"
                );
                throw setError;
            }
                appendText(logPath, "set.ok index=" + p + " match=" + (leaf.match_name || prop.name) +
                    " actual=" + valueToLog(coerceValue(prop.value)) + "\n");
            }
        }

        if (pauseBeforeRender) {
            if (!readyMarkerPath || !continueMarkerPath) {
                throw new Error("pause handshake requires OLM_AE_READY_MARKER and OLM_AE_CONTINUE_MARKER");
            }
            var continueMarker = new File(continueMarkerPath);
            if (continueMarker.exists) {
                continueMarker.remove();
            }
            writeText(
                readyMarkerPath,
                "ready case_id=" + caseId + " pid_host=AfterFX effect_loaded=1 parameters_applied=1\n"
            );
            appendText(logPath, "pause.ready marker=" + readyMarkerPath + "\n");
            var pauseDeadline = (new Date()).getTime() + Math.max(1, pauseTimeoutSeconds) * 1000;
            while (!continueMarker.exists && (new Date()).getTime() < pauseDeadline) {
                $.sleep(100);
            }
            if (!continueMarker.exists) {
                throw new Error("pause handshake timed out waiting for " + continueMarkerPath);
            }
            appendText(logPath, "pause.continue marker=" + continueMarkerPath + "\n");
        }

        if (outputMode === "exr_render_queue" || outputMode === "png16_render_queue") {
            if (!outputTemplate) {
                throw new Error("OLM_AE_OUTPUT_TEMPLATE is required for render-queue output");
            }
            var renderExtension = outputMode === "exr_render_queue" ? ".exr" : ".tif";
            var renderBase = outputDir + "/" + caseId + renderExtension;
            var renderSequence = renderBase.substring(0, renderBase.length - renderExtension.length) + "_[#####]" + renderExtension;
            var rendered = new File(renderSequence.replace("[#####]", "00000"));
            if (rendered.exists && (!rendered.remove() || rendered.exists)) {
                throw new Error("could not remove stale render-queue output: " + rendered.fsName);
            }
            var rqItem = app.project.renderQueue.items.add(comp);
            rqItem.timeSpanStart = Number(caseRef.time || 0);
            rqItem.timeSpanDuration = 1.0 / Number(comp.frameRate || 24.0);
            var outputModule = rqItem.outputModule(1);
            outputModule.applyTemplate(outputTemplate);
            outputModule.file = new File(renderSequence);
            appendText(logPath, "renderQueue template=" + outputTemplate + " output=" + renderSequence + "\n");
            app.project.renderQueue.render();
            appendText(logPath, "renderQueue status=" + rqItem.status + " elapsed_seconds=" + rqItem.elapsedSeconds + "\n");
            rendered = new File(rendered.fsName);
            if (!rendered.exists) {
                throw new Error("render-queue output was not written status=" + rqItem.status + ": " + renderSequence);
            }
            if (outputMode === "exr_render_queue") {
                summary.output_exr = rendered.fsName;
            } else {
                var convertedPng = new File(outputDir + "/" + requestCase.frame);
                if (convertedPng.exists && (!convertedPng.remove() || convertedPng.exists)) {
                    throw new Error("could not remove stale converted PNG: " + convertedPng.fsName);
                }
                var conversion = system.callSystem(
                    "/usr/bin/sips -s format png " + shellDoubleQuote(rendered.fsName) +
                    " --out " + shellDoubleQuote(convertedPng.fsName)
                );
                convertedPng = new File(convertedPng.fsName);
                if (!convertedPng.exists || Number(convertedPng.length || 0) <= 0) {
                    throw new Error("TIFF-to-PNG conversion failed: " + conversion);
                }
                if (!rendered.remove() || rendered.exists) {
                    throw new Error("could not remove intermediate TIFF: " + rendered.fsName);
                }
                summary.output_png = convertedPng.fsName;
                rendered = convertedPng;
            }
            try { rqItem.remove(); } catch (_) {}
            appendText(logPath, "render-queue output exists " + rendered.fsName + "\n");
        } else {
            var outputPath = outputDir + "/" + requestCase.frame;
            var png = new File(outputPath);
            if (png.exists && (!png.remove() || png.exists)) {
                throw new Error("could not remove stale PNG: " + png.fsName);
            }
            summary.output_png = outputPath;
            appendText(logPath, "saveFrameToPng " + outputPath + "\n");
            var renderStarted = new Date();
            comp.saveFrameToPng(Number(caseRef.time || 0), png);
            appendText(logPath, "saveFrameToPng returned\n");
            summary.png_observation = waitForStableFile(png, renderStarted, 120000, 250, 2000);
            appendText(logPath, "png observation " + summary.png_observation.status + " waited_ms=" + summary.png_observation.waited_ms + " size_bytes=" + summary.png_observation.size_bytes + "\n");
            if (summary.png_observation.status !== "stable") {
                throw new Error("PNG was not stably written (" + summary.png_observation.status + "): " + outputPath);
            }
            appendText(logPath, "png exists\n");
        }
        summary.status = "ok";
    } catch (error) {
        summary.status = "error";
        summary.error = error.toString();
        appendText(logPath, "error " + error.toString() + "\n");
    }

    writeText(
        resultJson,
        "{\n" +
            "  \"kind\": \"" + esc(summary.kind) + "\",\n" +
            "  \"ae_version\": \"" + esc(summary.ae_version) + "\",\n" +
            "  \"request_dir\": \"" + esc(summary.request_dir) + "\",\n" +
            "  \"case_id\": \"" + esc(summary.case_id) + "\",\n" +
            "  \"output_dir\": \"" + esc(summary.output_dir) + "\",\n" +
            "  \"output_png\": \"" + esc(summary.output_png) + "\",\n" +
            "  \"output_exr\": \"" + esc(summary.output_exr) + "\",\n" +
            "  \"png_observation\": {\"status\": \"" + esc(summary.png_observation.status) + "\", \"timeout_ms\": " + summary.png_observation.timeout_ms + ", \"waited_ms\": " + summary.png_observation.waited_ms + ", \"polls\": " + summary.png_observation.polls + ", \"stable_polls\": " + summary.png_observation.stable_polls + ", \"stable_for_ms\": " + summary.png_observation.stable_for_ms + ", \"stable_window_ms\": " + summary.png_observation.stable_window_ms + ", \"size_bytes\": " + summary.png_observation.size_bytes + ", \"modified_ms\": " + summary.png_observation.modified_ms + ", \"format_complete\": " + (summary.png_observation.format_complete ? "true" : "false") + ", \"crc_validated\": " + (summary.png_observation.crc_validated ? "true" : "false") + "},\n" +
            "  \"project_bits_per_channel\": " + summary.project_bits_per_channel + ",\n" +
            "  \"project_working_space\": \"" + esc(summary.project_working_space) + "\",\n" +
            "  \"project_linear_blending\": " + (summary.project_linear_blending ? "true" : "false") + ",\n" +
            "  \"input_alpha_mode\": \"" + esc(summary.input_alpha_mode) + "\",\n" +
            "  \"effect_disabled\": " + (summary.effect_disabled ? "true" : "false") + ",\n" +
            "  \"status\": \"" + esc(summary.status) + "\",\n" +
            "  \"error\": \"" + esc(summary.error) + "\",\n" +
            "  \"warnings\": [\"" + esc(summary.warnings.join("\" , \"")) + "\"]\n" +
            "}\n"
    );
    appendText(logPath, "done status=" + summary.status + "\n");
    if (!keepOpen) {
        try {
            app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
        } catch (closeError) {
            appendText(logPath, "close warning " + closeError.toString() + "\n");
        }
        try {
            app.quit();
        } catch (quitError) {
            appendText(logPath, "quit warning " + quitError.toString() + "\n");
        }
    }
}());
