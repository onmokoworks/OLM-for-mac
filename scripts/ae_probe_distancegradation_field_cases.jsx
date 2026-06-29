/*
  Render a few OLMDistanceGradation 16bpc cases with Use Background Color
  forced off so Mac AE exposes the internal field through output alpha.
*/
(function () {
    var CASE_IDS = [
        "olmdistancegradation_extended__case_0020",
        "olmdistancegradation_extended__case_0021",
        "olmdistancegradation_extended__case_0022",
        "olmdistancegradation_extended__case_0023",
        "olmdistancegradation_extended__case_0027",
        "olmdistancegradation_extended__case_0028"
    ];

    function readText(path) {
        var file = new File(path);
        file.encoding = "UTF-8";
        if (!file.open("r")) throw new Error("could not open " + path);
        var text = file.read();
        file.close();
        return text;
    }

    function parseJson(path) {
        var text = readText(path);
        if (typeof JSON !== "undefined" && JSON.parse) return JSON.parse(text);
        return eval("(" + text + ")");
    }

    function writeText(path, text) {
        var file = new File(path);
        file.encoding = "UTF-8";
        if (!file.open("w")) throw new Error("could not write " + path);
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
        if (value === null || value === undefined) return "";
        return String(value).replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\r/g, "\\r").replace(/\n/g, "\\n");
    }

    function ensureFolder(path) {
        var folder = new Folder(path);
        if (!folder.exists) folder.create();
        return folder;
    }

    function waitForFreshFile(file, since, tries, sleepMs) {
        var sinceMs = since.getTime() - 2000;
        for (var i = 0; i < tries; i++) {
            if (file.exists && (!file.modified || file.modified.getTime() >= sinceMs)) return true;
            $.sleep(sleepMs);
        }
        return file.exists && (!file.modified || file.modified.getTime() >= sinceMs);
    }

    function childByMatchOrName(group, matchName, name) {
        if (!group || !group.numProperties) return null;
        for (var i = 1; i <= group.numProperties; i++) {
            var prop = group.property(i);
            if (prop && matchName && prop.matchName === matchName) return prop;
        }
        for (var j = 1; j <= group.numProperties; j++) {
            var namedProp = group.property(j);
            if (namedProp && name && namedProp.name === name) return namedProp;
        }
        return null;
    }

    function isArrayValue(value) {
        return Object.prototype.toString.call(value) === "[object Array]";
    }

    function coerceValue(value) {
        if (isArrayValue(value)) {
            var arr = [];
            for (var i = 0; i < value.length; i++) arr.push(value[i]);
            return arr;
        }
        return value;
    }

    function findCase(manifest, id) {
        for (var i = 0; i < manifest.cases.length; i++) {
            if (manifest.cases[i].id === id) return manifest.cases[i];
        }
        throw new Error("missing case " + id);
    }

    function cloneParams(params) {
        var out = [];
        for (var i = 0; i < params.length; i++) {
            var src = params[i];
            var copied = {};
            for (var k in src) if (src.hasOwnProperty(k)) copied[k] = src[k];
            out.push(copied);
        }
        return out;
    }

    function overrideParam(params, matchName, value) {
        for (var i = 0; i < params.length; i++) {
            if (params[i].match_name === matchName) {
                params[i].value = value;
                return;
            }
        }
        throw new Error("missing override param " + matchName);
    }

    function setParams(effect, params, log) {
        for (var i = 0; i < params.length; i++) {
            var param = params[i];
            if (param.value === null || param.value === undefined) continue;
            var pathFull = param.path_full || [];
            var skip = false;
            if (param.match_name === "ADBE Effect Mask Opacity" || param.match_name === "ADBE Force CPU GPU") skip = true;
            for (var p = 0; p < pathFull.length; p++) {
                if (pathFull[p].match_name === "ADBE Effect Built In Params") skip = true;
            }
            if (skip) continue;
            var leaf = null;
            if (pathFull.length >= 2) {
                leaf = pathFull[pathFull.length - 1];
            } else if (param.match_name || param.name) {
                leaf = {match_name: param.match_name, name: param.name};
            }
            if (!leaf) continue;
            var prop = childByMatchOrName(effect, leaf.match_name, leaf.name || param.name);
            if (!prop) {
                log.push({match_name: leaf.match_name, name: param.name, requested: param.value, error: "missing"});
                continue;
            }
            try {
                prop.setValue(coerceValue(param.value));
                log.push({match_name: prop.matchName, name: prop.name, requested: param.value, actual: String(prop.value)});
            } catch (e) {
                log.push({match_name: prop.matchName, name: prop.name, requested: param.value, actual: "", error: e.toString()});
            }
        }
    }

    var repoRoot = File($.fileName).parent.parent;
    var requestRoot = repoRoot.fsName + "/handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625";
    var requestManifest = parseJson(requestRoot + "/request_manifest.json");
    var referenceManifest = parseJson(requestRoot + "/" + requestManifest.reference_manifest);
    var outputRoot = ensureFolder(repoRoot.fsName + "/handoff/ae_pixel_validation_20260618/probes/distancegradation_field_cases");
    var progressPath = outputRoot.fsName + "/progress.log";
    var summaryPath = outputRoot.fsName + "/summary.json";

    writeText(progressPath, "");
    try {
        if (referenceManifest.project && referenceManifest.project.bits_per_channel) {
            app.project.bitsPerChannel = Number(referenceManifest.project.bits_per_channel);
        }
    } catch (bitsError) {}

    var json = "{\n  \"cases\": [\n";
    for (var c = 0; c < CASE_IDS.length; c++) {
        var caseId = CASE_IDS[c];
        appendText(progressPath, "start " + caseId + "\n");
        var caseRef = findCase(referenceManifest, caseId);
        var inputPath = requestRoot + "/" + requestManifest.input_dir + "/" + caseRef.before_effects_frame;
        var footage = app.project.importFile(new ImportOptions(new File(inputPath)));
        var comp = app.project.items.addComp("probe_field_" + c, footage.width, footage.height, 1.0, 1.0, 24.0);
        var layer = comp.layers.add(footage);
        var effect = layer.property("ADBE Effect Parade").addProperty("Distance Gradation");
        var params = cloneParams(caseRef.effects[0].params || []);
        overrideParam(params, "OLM Distance Gradation-0006", 0);
        var setLog = [];
        setParams(effect, params, setLog);
        var outPng = new File(outputRoot.fsName + "/" + caseId + "__no_bg.png");
        if (outPng.exists) {
            try { outPng.remove(); } catch (eRemove) {}
        }
        var started = new Date();
        comp.saveFrameToPng(0.0, outPng);
        var wrote = waitForFreshFile(outPng, started, 120, 250);

        json += "    {\n";
        json += "      \"case_id\": \"" + esc(caseId) + "\",\n";
        json += "      \"png\": \"" + esc(outPng.fsName) + "\",\n";
        json += "      \"written\": " + (wrote ? "true" : "false") + ",\n";
        json += "      \"set_log\": [\n";
        for (var i = 0; i < setLog.length; i++) {
            json += "        {\"match_name\": \"" + esc(setLog[i].match_name) + "\", \"name\": \"" + esc(setLog[i].name) + "\", \"requested\": \"" + esc(setLog[i].requested) + "\", \"actual\": \"" + esc(setLog[i].actual) + "\", \"error\": \"" + esc(setLog[i].error) + "\"}" + (i + 1 < setLog.length ? "," : "") + "\n";
        }
        json += "      ]\n";
        json += "    }" + (c + 1 < CASE_IDS.length ? "," : "") + "\n";
        appendText(progressPath, "done " + caseId + "\n");
    }
    json += "  ]\n}\n";
    writeText(summaryPath, json);
    app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
    app.quit();
}());
