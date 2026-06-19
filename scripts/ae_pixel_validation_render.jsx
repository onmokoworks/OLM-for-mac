/*
  Render bundled AE pixel-validation requests with the installed macOS OLM
  plug-ins. This script is intentionally small and host-facing: it recreates
  each reference case from request/reference manifests, applies the effect,
  writes PNGs, and emits a summary JSON.

  Run from a live After Effects instance:
    osascript -e 'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file ".../scripts/ae_pixel_validation_render.jsx" with override'
*/
(function () {
    var __repoRootForBoot = File($.fileName).parent.parent;
    var __bootFolder = new Folder(__repoRootForBoot.fsName + "/handoff/ae_pixel_validation_20260618");
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
        if (typeof JSON !== "undefined" && JSON.parse) {
            return JSON.parse(text);
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

    function waitForFreshFile(file, since, tries, sleepMs) {
        for (var i = 0; i < tries; i++) {
            if (file.exists && file.modified && file.modified.getTime() >= since.getTime()) {
                return true;
            }
            $.sleep(sleepMs);
        }
        return file.exists && file.modified && file.modified.getTime() >= since.getTime();
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
            for (var p = 0; p < pathFull.length; p++) {
                if (pathFull[p].match_name === "ADBE Effect Built In Params") {
                    skip = true;
                }
            }
            if (skip || pathFull.length < 2) {
                continue;
            }
            var leaf = pathFull[pathFull.length - 1];
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
        if (!waitForFreshFile(png, renderStarted, 40, 250)) {
            summary.errors.push(caseSpec.id + ": PNG was not written");
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
        var alias = requestManifest.request_id.replace(/^ae_pixel_/, "").replace(/_20[0-9][0-9][0-9][0-9][0-9][0-9]$/, "");
        var resultRoot = ensureFolder(outputBase.fsName + "/" + alias);
        var summary = {
            request_id: requestManifest.request_id,
            effect_name: requestManifest.effect_name,
            output_dir: resultRoot.fsName,
            rendered: [],
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
        return "{\n" +
            "  \"kind\": \"olm_ae_pixel_validation_render_result\",\n" +
            "  \"request_id\": \"" + esc(summary.request_id) + "\",\n" +
            "  \"effect_name\": \"" + esc(summary.effect_name) + "\",\n" +
            "  \"output_dir\": \"" + esc(summary.output_dir) + "\",\n" +
            "  \"rendered\": " + jsonStringArray(summary.rendered) + ",\n" +
            "  \"warnings\": " + jsonStringArray(summary.warnings) + ",\n" +
            "  \"errors\": " + jsonStringArray(summary.errors) + "\n" +
            "}\n";
    }

    var repoRoot = File($.fileName).parent.parent;
    var base = ensureFolder(repoRoot.fsName + "/handoff/ae_pixel_validation_20260618");
    var requestsBase = ensureFolder(base.fsName + "/requests");
    var resultsBase = ensureFolder(base.fsName + "/results");
    var progressLog = base.fsName + "/AE_PIXEL_VALIDATION_PROGRESS.log";
    writeText(progressLog, "start " + (new Date()).toString() + "\n");
    var requestIds = [
        "ae_pixel_olmblur_20260606",
        "ae_pixel_olmcolorkey_20260606",
        "ae_pixel_olmtoondilate_20260606",
        "ae_pixel_olmdistancegradation_20260606",
        "ae_pixel_olmdistancegradation_extended_20260618",
        "ae_pixel_olmdistancegradation_blur_20260618"
    ];
    var requestListFile = new File(base.fsName + "/REQUEST_IDS.txt");
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
    writeText(base.fsName + "/AE_PIXEL_VALIDATION_BATCH_RESULT.json", top);
    try {
        app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
    } catch (closeError) {
    }
    app.quit();
}());
