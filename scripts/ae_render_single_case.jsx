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

    function waitForFreshFile(file, since, tries, sleepMs) {
        var sinceMs = since.getTime() - 2000;
        for (var i = 0; i < tries; i++) {
            if (file.exists && (!file.modified || file.modified.getTime() >= sinceMs)) {
                return true;
            }
            $.sleep(sleepMs);
        }
        return file.exists && (!file.modified || file.modified.getTime() >= sinceMs);
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
        status: "unknown",
        error: "",
        warnings: []
    };

    try {
        appendText(logPath, "load request manifests\n");
        var requestManifest = parseJson(requestDir + "/request_manifest.json");
        var referenceManifest = parseJson(requestDir + "/" + requestManifest.reference_manifest);
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

        if (!app.project) {
            app.newProject();
        }
        try {
            if (referenceManifest.project && referenceManifest.project.bits_per_channel) {
                app.project.bitsPerChannel = Number(referenceManifest.project.bits_per_channel);
                appendText(logPath, "bitsPerChannel=" + app.project.bitsPerChannel + "\n");
            }
        } catch (bitsError) {
            summary.warnings.push("bitsPerChannel: " + bitsError.toString());
        }

        var inputPath = requestDir + "/" + requestManifest.input_dir + "/" + requestCase.before_effects_frame;
        appendText(logPath, "import " + inputPath + "\n");
        var footage = importFootage(inputPath);
        var compInfo = referenceManifest.comp || {};
        var comp = app.project.items.addComp(
            "single_" + caseId,
            Number(footage.width || compInfo.width || 1920),
            Number(footage.height || compInfo.height || 1080),
            1.0,
            Number(compInfo.duration || 1.0),
            Number(compInfo.frame_rate || 24.0)
        );
        var layer = comp.layers.add(footage);
        layer.startTime = 0;
        appendText(logPath, "comp/layer ready\n");

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
            appendText(logPath, "set.ok index=" + p + " match=" + (leaf.match_name || prop.name) + "\n");
        }

        var outputPath = outputDir + "/" + requestCase.frame;
        var png = new File(outputPath);
        if (png.exists) {
            png.remove();
        }
        summary.output_png = outputPath;
        appendText(logPath, "saveFrameToPng " + outputPath + "\n");
        var renderStarted = new Date();
        comp.saveFrameToPng(Number(caseRef.time || 0), png);
        appendText(logPath, "saveFrameToPng returned\n");
        if (!waitForFreshFile(png, renderStarted, 120, 250)) {
            throw new Error("PNG was not written: " + outputPath);
        }
        appendText(logPath, "png exists\n");
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
            "  \"status\": \"" + esc(summary.status) + "\",\n" +
            "  \"error\": \"" + esc(summary.error) + "\",\n" +
            "  \"warnings\": [\"" + esc(summary.warnings.join("\" , \"")) + "\"]\n" +
            "}\n"
    );
    appendText(logPath, "done status=" + summary.status + "\n");
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
}());
