/*
  Dump OLM Color Key property names/matchNames from the installed macOS plug-in.

  Run from After Effects:
    osascript -e 'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file ".../scripts/ae_dump_colorkey_props.jsx" with override'
*/
(function () {
    function writeText(path, text) {
        var file = new File(path);
        file.encoding = "UTF-8";
        if (!file.open("w")) {
            throw new Error("could not write " + path);
        }
        file.write(text);
        file.close();
    }

    function esc(value) {
        if (value === null || value === undefined) {
            return "";
        }
        return String(value).replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\r/g, "\\r").replace(/\n/g, "\\n");
    }

    function propValue(prop) {
        try {
            return String(prop.value);
        } catch (e) {
            return "";
        }
    }

    function propValueType(prop) {
        try {
            if (prop.propertyValueType === null || prop.propertyValueType === undefined) {
                return -1;
            }
            return Number(prop.propertyValueType);
        } catch (e) {
            return -1;
        }
    }

    var repoRoot = File($.fileName).parent.parent;
    var outPath = repoRoot.fsName + "/handoff/ae_pixel_validation_20260618/OLMColorKey_props_dump.json";
    var comp = app.project.items.addComp("dump_olmcolorkey_props", 64, 64, 1.0, 1.0, 24.0);
    var solid = comp.layers.addSolid([1, 0, 0], "source", 64, 64, 1.0);
    var parade = solid.property("ADBE Effect Parade");
    var effect = null;
    var names = ["OLM Color Key", "OLM OLM Color Key"];
    var errors = [];
    for (var n = 0; n < names.length && !effect; n++) {
        try {
            effect = parade.addProperty(names[n]);
        } catch (e) {
            errors.push(names[n] + ": " + e.toString());
        }
    }
    if (!effect) {
        writeText(outPath, "{\n  \"errors\": [\"" + esc(errors.join(" | ")) + "\"]\n}\n");
        app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
        app.quit();
        return;
    }

    var json = "{\n";
    json += "  \"effect_name\": \"" + esc(effect.name) + "\",\n";
    json += "  \"effect_match_name\": \"" + esc(effect.matchName) + "\",\n";
    json += "  \"num_properties\": " + effect.numProperties + ",\n";
    json += "  \"properties\": [\n";
    for (var i = 1; i <= effect.numProperties; i++) {
        var prop = effect.property(i);
        json += "    {\"index\": " + i +
                ", \"name\": \"" + esc(prop.name) +
                "\", \"match_name\": \"" + esc(prop.matchName) +
                "\", \"property_value_type\": " + propValueType(prop) +
                ", \"value\": \"" + esc(propValue(prop)) + "\"}" +
                (i < effect.numProperties ? "," : "") + "\n";
    }
    json += "  ]\n";
    json += "}\n";
    writeText(outPath, json);
    app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
    app.quit();
}());
