(function () {
    function quote(value) {
        return '"' + String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r/g, "\\r").replace(/\n/g, "\\n") + '"';
    }

    function writeText(path, text) {
        var file = new File(path);
        if (!file.open("w")) {
            throw new Error("Cannot open output: " + path);
        }
        file.encoding = "UTF-8";
        file.write(text);
        file.close();
    }

    var outputPath = $.getenv("OLM_AE_OUTPUT_MODULE_PROBE");
    if (!outputPath) {
        throw new Error("OLM_AE_OUTPUT_MODULE_PROBE is required");
    }

    var previousSuppress = app.beginSuppressDialogs();
    var comp = null;
    var item = null;
    try {
        if (!app.project) {
            app.newProject();
        }
        comp = app.project.items.addComp("OLM_OutputModuleProbe", 16, 16, 1, 1, 24);
        comp.layers.addSolid([0, 0, 0], "probe", 16, 16, 1, 1);
        item = app.project.renderQueue.items.add(comp);
        var module = item.outputModule(1);
        var templates = module.templates;
        var templateRows = [];
        var templateSettingsRows = [];
        var formatAttemptRows = [];
        for (var i = 0; i < templates.length; i++) {
            templateRows.push(quote(templates[i]));
            try {
                module.applyTemplate(templates[i]);
                var templateSettings = module.getSettings(GetSettingsFormat.STRING_SETTABLE).toSource();
                templateSettingsRows.push(
                    "{\"name\": " + quote(templates[i]) +
                    ", \"settings_source\": " + quote(templateSettings) + "}"
                );
            } catch (templateError) {
                templateSettingsRows.push(
                    "{\"name\": " + quote(templates[i]) +
                    ", \"error\": " + quote(templateError.toString()) + "}"
                );
            }
        }
        var formatCandidates = ["OpenEXR", "OpenEXR Sequence", "ProEXR"];
        for (var j = 0; j < formatCandidates.length; j++) {
            try {
                module.setSettings({"Format": formatCandidates[j]});
                var formatSettings = module.getSettings(GetSettingsFormat.STRING_SETTABLE).toSource();
                formatAttemptRows.push(
                    "{\"format\": " + quote(formatCandidates[j]) +
                    ", \"settings_source\": " + quote(formatSettings) + "}"
                );
            } catch (formatError) {
                formatAttemptRows.push(
                    "{\"format\": " + quote(formatCandidates[j]) +
                    ", \"error\": " + quote(formatError.toString()) + "}"
                );
            }
        }
        var settingsText = "";
        try {
            settingsText = module.getSettings(GetSettingsFormat.STRING_SETTABLE).toSource();
        } catch (settingsError) {
            settingsText = "settings-error: " + settingsError.toString();
        }
        var body = "{\n" +
            "  \"ae_version\": " + quote(app.version) + ",\n" +
            "  \"bits_per_channel\": " + app.project.bitsPerChannel + ",\n" +
            "  \"templates\": [" + templateRows.join(", ") + "],\n" +
            "  \"template_settings\": [" + templateSettingsRows.join(", ") + "],\n" +
            "  \"format_attempts\": [" + formatAttemptRows.join(", ") + "],\n" +
            "  \"default_settings_source\": " + quote(settingsText) + "\n" +
            "}\n";
        writeText(outputPath, body);
    } catch (error) {
        writeText(outputPath, "{\n  \"error\": " + quote(error.toString()) + "\n}\n");
        throw error;
    } finally {
        try {
            if (item) {
                item.remove();
            }
        } catch (_) {}
        try {
            if (comp) {
                comp.remove();
            }
        } catch (_) {}
        app.endSuppressDialogs(false);
    }
}());
