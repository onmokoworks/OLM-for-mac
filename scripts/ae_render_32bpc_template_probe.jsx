/* Render a tiny 32bpc comp through a named Output Module template. */
(function () {
    function getenv(name) { try { return $.getenv(name); } catch (_) { return ""; } }
    function quote(value) { return '"' + String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r/g, "\\r").replace(/\n/g, "\\n") + '"'; }
    function writeText(path, text) {
        var file = new File(path); file.encoding = "UTF-8";
        if (!file.open("w")) throw new Error("Cannot write " + path);
        file.write(text); file.close();
    }
    var outputPath = getenv("OLM_AE_EXR_PROBE_OUTPUT");
    var resultPath = getenv("OLM_AE_EXR_PROBE_RESULT");
    var template = getenv("OLM_AE_EXR_TEMPLATE");
    if (!outputPath || !resultPath || !template) throw new Error("OLM_AE_EXR_PROBE_OUTPUT, RESULT, and TEMPLATE are required");
    var oldBpc = null, comp = null, item = null;
    var result = {kind: "olm_ae_32bpc_template_probe", ae_version: app.version, template: template, output: outputPath, status: "unknown", error: ""};
    var previousSuppress = app.beginSuppressDialogs();
    try {
        if (!app.project) app.newProject();
        oldBpc = app.project.bitsPerChannel;
        app.project.bitsPerChannel = 32;
        // AE rejects comp dimensions below 4 pixels; this remains intentionally tiny.
        comp = app.project.items.addComp("OLM_EXR_32BPC_TemplateProbe", 4, 4, 1, 1 / 24, 24);
        comp.layers.addSolid([0.25, 0.5, 0.75], "probe", 4, 4, 1, 1 / 24);
        item = app.project.renderQueue.items.add(comp);
        item.timeSpanStart = 0;
        item.timeSpanDuration = 1 / 24;
        var module = item.outputModule(1);
        module.applyTemplate(template);
        // Sequence-capable Output Modules append frame digits after a literal
        // extension. Put AE's frame token before `.exr` instead.
        var sequencePath = outputPath.replace(/\.exr$/i, "_[#####].exr");
        var out = new File(sequencePath);
        if (out.exists) out.remove();
        module.file = out;
        app.project.renderQueue.render();
        // This probe renders exactly its first frame at time zero, so the
        // sequence token resolves deterministically to 00000.
        var rendered = new File(sequencePath.replace("[#####]", "00000"));
        if (!rendered.exists) {
            throw new Error("Render Queue did not write one EXR sequence frame: " + sequencePath);
        }
        result.output = rendered.fsName;
        result.status = "ok";
    } catch (error) {
        result.status = "error";
        result.error = error.toString();
    } finally {
        try { if (item) item.remove(); } catch (_) {}
        try { if (comp) comp.remove(); } catch (_) {}
        try { if (oldBpc !== null) app.project.bitsPerChannel = oldBpc; } catch (_) {}
        app.endSuppressDialogs(false);
    }
    writeText(resultPath, "{\n" +
        "  \"kind\": " + quote(result.kind) + ",\n" +
        "  \"ae_version\": " + quote(result.ae_version) + ",\n" +
        "  \"template\": " + quote(result.template) + ",\n" +
        "  \"output\": " + quote(result.output) + ",\n" +
        "  \"status\": " + quote(result.status) + ",\n" +
        "  \"error\": " + quote(result.error) + "\n}\n");
    if (result.status !== "ok") throw new Error(result.error);
}());
