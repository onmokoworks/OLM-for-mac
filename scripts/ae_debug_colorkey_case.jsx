/*
  Apply one OLM Color Key reference case and dump selected property values after
  setting. CASE_ID can be changed below when diagnosing host/CLI drift.
*/
(function () {
    var CASE_ID = "case_0006";

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

    function esc(value) {
        if (value === null || value === undefined) return "";
        return String(value).replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\r/g, "\\r").replace(/\n/g, "\\n");
    }

    function childByMatchOrName(group, matchName, name) {
        for (var i = 1; i <= group.numProperties; i++) {
            var prop = group.property(i);
            if (matchName && prop.matchName === matchName) return prop;
        }
        for (var j = 1; j <= group.numProperties; j++) {
            var namedProp = group.property(j);
            if (name && namedProp.name === name) return namedProp;
        }
        return null;
    }

    function propValue(prop) {
        try {
            var value = prop.value;
            if (Object.prototype.toString.call(value) === "[object Array]") return value.join(",");
            return String(value);
        } catch (e) {
            return "";
        }
    }

    function findCase(manifest, id) {
        for (var i = 0; i < manifest.cases.length; i++) {
            if (manifest.cases[i].id === id) return manifest.cases[i];
        }
        throw new Error("missing case " + id);
    }

    function setParams(effect, params, log) {
        for (var i = 0; i < params.length; i++) {
            var param = params[i];
            if (param.value === null || param.value === undefined) continue;
            var pathFull = param.path_full || [];
            if (pathFull.length < 2) continue;
            var skip = false;
            for (var p = 0; p < pathFull.length; p++) {
                if (pathFull[p].match_name === "ADBE Effect Built In Params") skip = true;
            }
            if (skip) continue;
            var leaf = pathFull[pathFull.length - 1];
            var prop = childByMatchOrName(effect, leaf.match_name, leaf.name || param.name);
            if (!prop) {
                log.push({match_name: leaf.match_name, name: param.name, requested: param.value, error: "missing"});
                continue;
            }
            try {
                prop.setValue(param.value);
                log.push({match_name: prop.matchName, name: prop.name, requested: param.value, actual: propValue(prop)});
            } catch (e) {
                log.push({match_name: prop.matchName, name: prop.name, requested: param.value, actual: propValue(prop), error: e.toString()});
            }
        }
    }

    var repoRoot = File($.fileName).parent.parent;
    var requestRoot = repoRoot.fsName + "/handoff/ae_pixel_validation_20260618/requests/ae_pixel_olmcolorkey_20260606";
    var requestManifest = parseJson(requestRoot + "/request_manifest.json");
    var referenceManifest = parseJson(requestRoot + "/" + requestManifest.reference_manifest);
    var caseRef = findCase(referenceManifest, CASE_ID);
    var inputPath = requestRoot + "/" + requestManifest.input_dir + "/" + CASE_ID + "_before_effects.png";
    var footage = app.project.importFile(new ImportOptions(new File(inputPath)));
    var comp = app.project.items.addComp("debug_colorkey_" + CASE_ID, footage.width, footage.height, 1.0, 1.0, 24.0);
    var layer = comp.layers.add(footage);
    var effect = layer.property("ADBE Effect Parade").addProperty("OLM Color Key");
    var log = [];
    setParams(effect, caseRef.effects[0].params || [], log);

    var selected = ["OLM Color Key-0005", "OLM Color Key-0013", "OLM Color Key-0014", "OLM Color Key-0017", "OLM Color Key-0018", "OLM Color Key-0019", "OLM Color Key-0522"];
    var out = "{\n  \"case_id\": \"" + esc(CASE_ID) + "\",\n  \"selected\": [\n";
    for (var s = 0; s < selected.length; s++) {
        var prop = childByMatchOrName(effect, selected[s], null);
        out += "    {\"match_name\": \"" + esc(selected[s]) + "\", \"name\": \"" + esc(prop ? prop.name : "") + "\", \"value\": \"" + esc(prop ? propValue(prop) : "<missing>") + "\"}" + (s + 1 < selected.length ? "," : "") + "\n";
    }
    out += "  ],\n  \"set_log\": [\n";
    for (var l = 0; l < log.length; l++) {
        out += "    {\"match_name\": \"" + esc(log[l].match_name) + "\", \"name\": \"" + esc(log[l].name) + "\", \"requested\": \"" + esc(log[l].requested) + "\", \"actual\": \"" + esc(log[l].actual) + "\", \"error\": \"" + esc(log[l].error) + "\"}" + (l + 1 < log.length ? "," : "") + "\n";
    }
    out += "  ]\n}\n";
    writeText(repoRoot.fsName + "/handoff/ae_pixel_validation_20260618/OLMColorKey_case_debug.json", out);
    app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
    app.quit();
}());
