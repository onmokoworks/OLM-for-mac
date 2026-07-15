/*
  Render bundled AE pixel-validation requests with the installed macOS OLM
  plug-ins. This script is intentionally small and host-facing: it recreates
  each reference case from request/reference manifests, applies the effect,
  writes PNGs, and emits a summary JSON.

  Run from a live After Effects instance:
    osascript -e 'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file ".../scripts/ae_pixel_validation_render.jsx" with override'
*/
(function () {
    function getenv(name) {
        try {
            return $.getenv(name);
        } catch (e) {
            return "";
        }
    }

    var __repoRootForBoot = File($.fileName).parent.parent;
    var __basePath = getenv("OLM_AE_BASE_DIR") || (__repoRootForBoot.fsName + "/handoff/ae_pixel_validation_20260618");
    var __bootFolder = new Folder(__basePath);
    if (!__bootFolder.exists) {
        __bootFolder.create();
    }
    var __bootLog = new File(__bootFolder.fsName + "/AE_PIXEL_VALIDATION_BOOT.log");
    __bootLog.encoding = "UTF-8";
    __bootLog.open("w");
    __bootLog.write("boot " + app.version + "\n");
    __bootLog.close();

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
        return eval("(" + text + ")");
    }

    function parseJsonText(text) {
        if (!text) {
            return null;
        }
        return eval("(" + text + ")");
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

    function esc(value) {
        if (value === null || value === undefined) {
            return "";
        }
        return String(value).replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\r/g, "\\r").replace(/\n/g, "\\n");
    }

    function shell(command) {
        try {
            return system.callSystem(command).replace(/[\r\n]+$/g, "");
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

    function waitForStableFile(file, since, timeoutMs, sleepMs) {
        var startedWaiting = new Date();
        var sinceMs = since.getTime() - 2000;
        var lastSize = -1;
        var lastModified = -1;
        var stablePolls = 0;
        var polls = 0;
        var observation = { status: "timeout", timeout_ms: timeoutMs, waited_ms: 0, polls: 0, stable_polls: 0, size_bytes: 0, modified_ms: 0 };
        while (true) {
            polls++;
            var exists = file.exists;
            var size = exists ? Number(file.length || 0) : 0;
            var modified = exists && file.modified ? file.modified.getTime() : 0;
            var fresh = exists && (!file.modified || modified >= sinceMs);
            if (fresh && size > 0) {
                stablePolls = (size === lastSize && modified === lastModified) ? stablePolls + 1 : 1;
                if (stablePolls >= 2) {
                    observation.status = "stable";
                    observation.waited_ms = (new Date()).getTime() - startedWaiting.getTime();
                    observation.polls = polls;
                    observation.stable_polls = stablePolls;
                    observation.size_bytes = size;
                    observation.modified_ms = modified;
                    return observation;
                }
                lastSize = size;
                lastModified = modified;
            } else {
                stablePolls = 0;
                lastSize = -1;
                lastModified = -1;
            }
            if ((new Date()).getTime() - startedWaiting.getTime() >= timeoutMs) {
                observation.waited_ms = (new Date()).getTime() - startedWaiting.getTime();
                observation.polls = polls;
                observation.stable_polls = stablePolls;
                observation.size_bytes = size;
                observation.modified_ms = modified;
                observation.status = exists ? (size > 0 ? "unstable" : "empty") : "missing";
                return observation;
            }
            $.sleep(sleepMs);
        }
    }

    function childByMatchOrName(group, matchName, name) {
        if (!group || !group.numProperties) {
            return null;
        }
        for (var i = 1; i <= group.numProperties; i++) {
            var prop = group.property(i);
            if (!prop) {
                continue;
            }
            if (matchName && prop.matchName === matchName) {
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

    function isArrayValue(value) {
        return Object.prototype.toString.call(value) === "[object Array]";
    }

    function coerceValue(prop, value) {
        if (isArrayValue(value)) {
            var arr = [];
            for (var i = 0; i < value.length; i++) {
                arr.push(value[i]);
            }
            return arr;
        }
        return value;
    }

    function setEffectParams(effect, params, errors, valueScaleByMatchName) {
        for (var i = 0; i < params.length; i++) {
            var param = params[i];
            if (param.value === null || param.value === undefined) {
                continue;
            }
            var pathFull = param.path_full || [];
            var skip = false;
            if (param.match_name === "ADBE Effect Mask Opacity" || param.match_name === "ADBE Force CPU GPU") {
                skip = true;
            }
            for (var p = 0; p < pathFull.length; p++) {
                if (pathFull[p].match_name === "ADBE Effect Built In Params") {
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
                leaf = {
                    match_name: param.match_name,
                    name: param.name
                };
            }
            if (!leaf) {
                continue;
            }
            var prop = childByMatchOrName(effect, leaf.match_name, leaf.name || param.name);
            if (!prop) {
                errors.push("missing property " + (leaf.match_name || param.name));
                continue;
            }
            try {
                var value = param.value;
                if (valueScaleByMatchName && valueScaleByMatchName[leaf.match_name] !== undefined) {
                    value = Number(value) * Number(valueScaleByMatchName[leaf.match_name]);
                }
                prop.setValue(coerceValue(prop, value));
            } catch (e) {
                errors.push("set " + (leaf.match_name || param.name) + ": " + e.toString());
            }
        }
    }

    function importFootage(path) {
        var file = new File(path);
        var options = new ImportOptions(file);
        return app.project.importFile(options);
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

    function renderCase(requestRoot, resultRoot, requestManifest, referenceManifest, caseSpec, summary, progressLog) {
        appendText(progressLog, "case " + requestManifest.request_id + " " + caseSpec.id + "\n");
        var caseRef = findCase(referenceManifest, caseSpec.id);
        if (!caseRef) {
            summary.errors.push(caseSpec.id + ": missing reference manifest case");
            return false;
        }
        var inputPath = requestRoot.fsName + "/" + requestManifest.input_dir + "/" + caseSpec.before_effects_frame;
        var outputPath = resultRoot.fsName + "/" + caseSpec.frame;
        var footage = importFootage(inputPath);
        var compInfo = referenceManifest.comp || {};
        var sourceWidth = Number(footage.width || compInfo.width || 1920);
        var sourceHeight = Number(footage.height || compInfo.height || 1080);
        var compWidth = Number(compInfo.width || sourceWidth);
        var width = sourceWidth;
        var height = sourceHeight;
        var downsampleScaleX = 1.0;
        if (compWidth > sourceWidth) {
            downsampleScaleX = sourceWidth / compWidth;
        }
        var duration = Number(compInfo.duration || 1.0);
        var frameRate = Number(compInfo.frame_rate || 24.0);
        var comp = app.project.items.addComp("pixel_" + requestManifest.request_id + "_" + caseSpec.id, width, height, 1.0, duration, frameRate);
        var layer = comp.layers.add(footage);
        layer.startTime = 0;

        var effectParade = layer.property("ADBE Effect Parade");
        var effectCandidates = [requestManifest.effect_match_name];
        if (caseRef.effects && caseRef.effects.length > 0) {
            effectCandidates.push(caseRef.effects[0].match_name);
            effectCandidates.push(caseRef.effects[0].name);
        }
        effectCandidates.push(requestManifest.effect_name);
        var effect = null;
        var addErrors = [];
        for (var ec = 0; ec < effectCandidates.length; ec++) {
            if (!effectCandidates[ec]) {
                continue;
            }
            try {
                effect = effectParade.addProperty(effectCandidates[ec]);
                if (effect) {
                    break;
                }
            } catch (addError) {
                addErrors.push(effectCandidates[ec] + ": " + addError.toString());
            }
        }
        if (!effect) {
            throw new Error("could not add effect: " + addErrors.join(" | "));
        }
        var paramErrors = [];
        var valueScaleByMatchName = {};
        if (requestManifest.effect_match_name === "OLM OLM Blur" && downsampleScaleX !== 1.0) {
            valueScaleByMatchName["OLM OLM Blur-0005"] = downsampleScaleX;
        }
        if ((requestManifest.effect_match_name === "OLM OLM Toon Dilate" ||
             requestManifest.effect_match_name === "ADBE OLMToonDilate") &&
            downsampleScaleX !== 1.0) {
            valueScaleByMatchName["ADBE OLMToonDilate-0001"] = downsampleScaleX;
        }
        if (caseRef.effects && caseRef.effects.length > 0) {
            setEffectParams(effect, caseRef.effects[0].params || [], paramErrors, valueScaleByMatchName);
        }
        var png = new File(outputPath);
        if (png.exists) {
            try {
                png.remove();
            } catch (removeError) {
                summary.errors.push(caseSpec.id + ": could not remove stale PNG " + removeError.toString());
                return false;
            }
        }
        var renderStarted = new Date();
        try {
            comp.saveFrameToPng(Number(caseRef.time || 0), png);
        } catch (e) {
            summary.errors.push(caseSpec.id + ": render threw " + e.toString());
            return false;
        }
        var observation = waitForStableFile(png, renderStarted, 120000, 250);
        summary.png_observations[caseSpec.id] = observation;
        appendText(progressLog, "png_observation " + caseSpec.id + " status=" + observation.status + " waited_ms=" + observation.waited_ms + " size_bytes=" + observation.size_bytes + "\n");
        if (observation.status !== "stable") {
            summary.errors.push(caseSpec.id + ": PNG was not stably written (" + observation.status + ")");
            return false;
        }
        if (paramErrors.length) {
            summary.warnings.push(caseSpec.id + ": " + paramErrors.join(" | "));
        }
        summary.rendered.push(caseSpec.frame);
        appendText(progressLog, "case_done " + requestManifest.request_id + " " + caseSpec.id + "\n");
        return true;
    }

    function renderRequest(requestRoot, outputBase, progressLog) {
        var requestManifest = parseJson(requestRoot.fsName + "/request_manifest.json");
        var referenceManifest = parseJson(requestRoot.fsName + "/" + requestManifest.reference_manifest);
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
            try {
                app.project.bitsPerChannel = requestedBits;
                appendText(progressLog, "bits_per_channel " + requestedBits + " source=" + requestedBitsSource + "\n");
            } catch (bitsError) {
                appendText(progressLog, "bits_per_channel_warning " + bitsError.toString() + "\n");
            }
        }
        var alias = requestManifest.request_id.replace(/^ae_pixel_/, "").replace(/_20[0-9][0-9][0-9][0-9][0-9][0-9]$/, "");
        var resultRoot = ensureFolder(outputBase.fsName + "/" + alias);
        var summary = {
            request_id: requestManifest.request_id,
            effect_name: requestManifest.effect_name,
            output_dir: resultRoot.fsName,
            rendered: [],
            png_observations: {},
            warnings: [],
            errors: []
        };
        var cases = requestManifest.cases || [];
        for (var i = 0; i < cases.length; i++) {
            renderCase(requestRoot, resultRoot, requestManifest, referenceManifest, cases[i], summary, progressLog);
        }
        writeText(resultRoot.fsName + "/AE_PIXEL_VALIDATION_RENDER_RESULT.json", jsonSummary(summary));
        return summary;
    }

    function jsonStringArray(values) {
        var parts = [];
        for (var i = 0; i < values.length; i++) {
            parts.push("\"" + esc(values[i]) + "\"");
        }
        return "[" + parts.join(", ") + "]";
    }

    function jsonSummary(summary) {
        var observationParts = [];
        for (var observationId in summary.png_observations) {
            if (summary.png_observations.hasOwnProperty(observationId)) {
                var observation = summary.png_observations[observationId];
                observationParts.push("\"" + esc(observationId) + "\":{\"status\":\"" + esc(observation.status) + "\",\"timeout_ms\":" + observation.timeout_ms + ",\"waited_ms\":" + observation.waited_ms + ",\"polls\":" + observation.polls + ",\"stable_polls\":" + observation.stable_polls + ",\"size_bytes\":" + observation.size_bytes + ",\"modified_ms\":" + observation.modified_ms + "}");
            }
        }
        return "{\n" +
            "  \"kind\": \"olm_ae_pixel_validation_render_result\",\n" +
            "  \"request_id\": \"" + esc(summary.request_id) + "\",\n" +
            "  \"effect_name\": \"" + esc(summary.effect_name) + "\",\n" +
            "  \"output_dir\": \"" + esc(summary.output_dir) + "\",\n" +
            "  \"rendered\": " + jsonStringArray(summary.rendered) + ",\n" +
            "  \"png_observations\": {" + observationParts.join(",") + "},\n" +
            "  \"warnings\": " + jsonStringArray(summary.warnings) + ",\n" +
            "  \"errors\": " + jsonStringArray(summary.errors) + "\n" +
            "}\n";
    }

    var repoRoot = File($.fileName).parent.parent;
    var base = ensureFolder(__basePath);
    var requestsBase = ensureFolder(getenv("OLM_AE_REQUESTS_BASE") || (base.fsName + "/requests"));
    var resultsBase = ensureFolder(getenv("OLM_AE_RESULTS_BASE") || (base.fsName + "/results"));
    var progressLog = getenv("OLM_AE_PROGRESS_LOG") || (base.fsName + "/AE_PIXEL_VALIDATION_PROGRESS.log");
    var batchResultPath = getenv("OLM_AE_BATCH_RESULT_JSON") || (base.fsName + "/AE_PIXEL_VALIDATION_BATCH_RESULT.json");
    writeText(progressLog, "start " + (new Date()).toString() + "\n");
    var requestIds = [
        "ae_pixel_olmblur_20260606",
        "ae_pixel_olmcolorkey_20260606",
        "ae_pixel_olmtoondilate_20260606",
        "ae_pixel_olmdistancegradation_20260606",
        "ae_pixel_olmdistancegradation_extended_20260618",
        "ae_pixel_olmdistancegradation_blur_20260618"
    ];
    var requestIdsJson = getenv("OLM_AE_REQUEST_IDS_JSON");
    if (requestIdsJson) {
        var parsedIds = parseJsonText(requestIdsJson);
        if (parsedIds && parsedIds.length) {
            requestIds = parsedIds;
        }
    } else {
        var requestListFile = new File(getenv("OLM_AE_REQUEST_IDS_FILE") || (base.fsName + "/REQUEST_IDS.txt"));
        if (requestListFile.exists && requestListFile.open("r")) {
            var lines = requestListFile.read().split(/[\r\n]+/);
            requestListFile.close();
            var selected = [];
            for (var li = 0; li < lines.length; li++) {
                if (lines[li]) {
                    selected.push(lines[li]);
                }
            }
            if (selected.length) {
                requestIds = selected;
            }
        }
    }

    var summaries = [];
    try {
        app.beginUndoGroup("OLM AE pixel validation render");
        for (var r = 0; r < requestIds.length; r++) {
            appendText(progressLog, "request " + requestIds[r] + "\n");
            summaries.push(renderRequest(new Folder(requestsBase.fsName + "/" + requestIds[r]), resultsBase, progressLog));
            appendText(progressLog, "done " + requestIds[r] + "\n");
        }
        app.endUndoGroup();
    } catch (topError) {
        appendText(progressLog, "fatal " + topError.toString() + "\n");
        try {
            app.endUndoGroup();
        } catch (undoError) {
        }
    }

    var top = "{\n";
    top += "  \"kind\": \"olm_ae_pixel_validation_batch_render_result\",\n";
    top += "  \"ae_version\": \"" + esc(app.version) + "\",\n";
    top += "  \"macos_version\": \"" + esc(shell("/usr/bin/sw_vers -productVersion")) + "\",\n";
    top += "  \"machine\": \"" + esc(shell("/usr/bin/uname -m")) + "\",\n";
    top += "  \"requests\": [\n";
    for (var s = 0; s < summaries.length; s++) {
        top += "    " + jsonSummary(summaries[s]).replace(/\n/g, "\n    ").replace(/\n    $/, "");
        top += (s + 1 < summaries.length ? "," : "") + "\n";
    }
    top += "  ]\n";
    top += "}\n";
    writeText(batchResultPath, top);
    try {
        app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
    } catch (closeError) {
    }
    app.quit();
}());
