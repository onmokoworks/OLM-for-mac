/* Fresh-process Mac AE smoke. The config literal below is replaced by the runner. */
(function () {
    var CONFIG_PATH = __CONFIG_PATH_JSON__;
    function fail(message) { throw new Error("FAIL_CLOSED: " + message); }
    function readJson(path) {
        var file = new File(path); file.encoding = "UTF-8";
        if (!file.open("r")) fail("open config");
        var value = eval("(" + file.read() + ")"); file.close(); return value;
    }
    function quote(value) {
        return '"' + String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"')
            .replace(/\r/g, "\\r").replace(/\n/g, "\\n") + '"';
    }
    function encode(value) {
        if (value === null || value === undefined) return "null";
        if (typeof value === "number" || typeof value === "boolean") return String(value);
        if (typeof value === "string") return quote(value);
        if (value instanceof Array) {
            var array = []; for (var i = 0; i < value.length; i++) array.push(encode(value[i]));
            return "[" + array.join(",") + "]";
        }
        var parts = []; for (var key in value) if (value.hasOwnProperty(key))
            parts.push(quote(key) + ":" + encode(value[key]));
        return "{" + parts.join(",") + "}";
    }
    function writeJson(path, value) {
        var file = new File(path); file.encoding = "UTF-8";
        if (!file.open("w")) fail("write " + path);
        file.write(encode(value) + "\n"); file.close();
    }
    function findOne(group, matchName) {
        var found = [];
        function walk(node) {
            if (!node || !node.numProperties) return;
            for (var i = 1; i <= node.numProperties; i++) {
                var property = node.property(i);
                if (property.matchName === matchName) found.push(property);
                if (property.numProperties) walk(property);
            }
        }
        walk(group);
        if (found.length !== 1) fail("property cardinality " + matchName + "=" + found.length);
        return found[0];
    }
    function renderPng(comp, path) {
        var file = new File(path); if (file.exists && !file.remove()) fail("stale output");
        comp.saveFrameToPng(0, file);
        for (var i = 0; i < 1800 && !file.exists; i++) { $.sleep(100); file = new File(path); }
        if (!file.exists) fail("render missing " + path);
        return file.fsName;
    }
    var cfg = readJson(CONFIG_PATH), summary = {status: "error"};
    try {
        if (app.project) try { app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES); } catch (_) {}
        var project = app.newProject(); if (!project) project = app.project;
        project.bitsPerChannel = 32; project.linearBlending = false;
        try { project.gpuAccelType = GpuAccelType.SOFTWARE; } catch (rendererError) { fail("SOFTWARE " + rendererError); }
        if (Number(project.bitsPerChannel) !== 32 || Number(project.gpuAccelType) !== 1816) fail("project contract");

        var plumbingComp = project.items.addComp("radial_plumbing", 16, 16, 1, 1, 24);
        var plumbingLayer = plumbingComp.layers.addSolid([0.25, 0.5, 0.75], "primary", 16, 16, 1);
        var plumbingEffect = plumbingLayer.property("ADBE Effect Parade").addProperty("OLM RadialBlur");
        if (!plumbingEffect || plumbingEffect.matchName !== "OLM RadialBlur") fail("effect identity");
        writeJson(cfg.ready_path, {status: "ready", ae_version: String(app.version), bits: 32,
            renderer_raw: Number(project.gpuAccelType), effect_match_name: String(plumbingEffect.matchName)});
        var marker = new File(cfg.continue_path), until = (new Date()).getTime() + 600000;
        while (!marker.exists && (new Date()).getTime() < until) $.sleep(100);
        if (!marker.exists) fail("continue timeout");
        var plumbingOutput = renderPng(plumbingComp, cfg.plumbing_output);

        var type3 = {status: "live_type3_skipped_after_retained_timeout", pixel_exact: false};
        if (cfg.attempt_type3) {
        try {
            var comp = project.items.addComp("radial_type3_layer", 9, 7, 1, 1, 24);
            var noiseLayer = comp.layers.addSolid([0.8, 0.2, 0.4], "noise_layer", 9, 7, 1);
            var primaryLayer = comp.layers.addSolid([0.2, 0.7, 0.3], "type3_primary", 9, 7, 1);
            noiseLayer.enabled = false;
            var effect = primaryLayer.property("ADBE Effect Parade").addProperty("OLM RadialBlur");
            if (!effect || effect.matchName !== "OLM RadialBlur") fail("Type3 effect identity");
            var parameters = cfg.type3_parameters, readback = [];
            for (var matchName in parameters) if (parameters.hasOwnProperty(matchName)) {
                var property = findOne(effect, matchName), wanted = parameters[matchName];
                property.setValue(wanted); readback.push({match_name: matchName, value: property.value});
            }
            var layerProperty = findOne(effect, cfg.noise_layer_match_name);
            layerProperty.setValue(noiseLayer.index);
            if (Number(layerProperty.value) !== Number(noiseLayer.index)) fail("Noise Layer readback");
            var type3Output = renderPng(comp, cfg.type3_output);
            type3 = {status: "live_render_plumbing_pass", pixel_exact: false,
                noise_layer_written: Number(noiseLayer.index), noise_layer_readback: Number(layerProperty.value),
                parameter_readback: readback, output_path: type3Output};
        } catch (type3Error) {
            type3 = {status: "live_type3_unavailable_fail_closed", pixel_exact: false,
                error: type3Error.toString(), line: Number(type3Error.line || 0)};
        }
        }
        summary = {status: "ok", ae_version: String(app.version), bits: Number(project.bitsPerChannel),
            renderer_raw: Number(project.gpuAccelType), effect_match_name: String(plumbingEffect.matchName),
            plumbing_output_path: plumbingOutput, type3: type3,
            scope: "fresh AE load/add/default PF32 SOFTWARE render plumbing; Type3 live render, if present, is non-exact plumbing only"};
    } catch (error) {
        summary = {status: "error", error: error.toString(), line: Number(error.line || 0)};
    }
    writeJson(cfg.result_path, summary);
    try { if (app.project) app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES); } catch (_) {}
    try { app.quit(); } catch (_) {}
}());
