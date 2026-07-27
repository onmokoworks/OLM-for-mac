/*
  Generate a cross-host-identical 32bpc source fixture entirely in AE.

  Required environment:
    OLM_AE_TYPED_FIXTURE_OUTPUT_DIR
    OLM_AE_TYPED_FIXTURE_TEMPLATE       (for example: OLM EXR 32 Float)
    OLM_AE_TYPED_FIXTURE_PROJECT_PATH   (new .aep path)

  Optional:
    OLM_AE_TYPED_FIXTURE_EFFECT         (OLM Color Key or OLM Toon Dilate)
    OLM_AE_TYPED_FIXTURE_OVERWRITE=1

  The same render comp is rendered twice by toggling only the no-effect and
  effect-on layers. No footage is imported and no external pixel source is
  consulted.
*/
(function () {
    function getenv(name) {
        try { return $.getenv(name) || ""; } catch (_) { return ""; }
    }

    function fail(message) { throw new Error("typed procedural fixture: " + message); }

    function writeText(path, text) {
        var file = new File(path);
        file.encoding = "UTF-8";
        if (!file.open("w")) fail("cannot write " + path);
        file.write(text);
        file.close();
    }

    function quote(value) {
        return '"' + String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"')
            .replace(/\r/g, "\\r").replace(/\n/g, "\\n") + '"';
    }

    function ensureFolder(path) {
        var folder = new Folder(path);
        if (!folder.exists && !folder.create()) fail("cannot create output directory " + path);
        return folder;
    }

    function requireEmpty(path, overwrite) {
        var file = new File(path);
        if (file.exists && !overwrite) fail("refusing to overwrite " + path);
        if (file.exists && !file.remove()) fail("cannot remove stale output " + path);
    }

    function addIntegerRect(comp, spec) {
        if (spec.x !== Math.floor(spec.x) || spec.y !== Math.floor(spec.y) ||
            spec.width !== Math.floor(spec.width) || spec.height !== Math.floor(spec.height)) {
            fail("non-integer rectangle " + spec.name);
        }
        var layer = comp.layers.addSolid(spec.color, spec.name, spec.width, spec.height, 1.0, 1.0 / 24.0);
        layer.position.setValue([spec.x + spec.width / 2, spec.y + spec.height / 2]);
        layer.opacity.setValue(spec.alpha * 100.0);
        return layer;
    }

    function renderOne(comp, outputDir, filename, template) {
        var sequenceName = filename.replace(/\.exr$/i, "_[#####].exr");
        var sequenceFile = new File(outputDir + "/" + sequenceName);
        var renderedFile = new File(outputDir + "/" + filename.replace(/\.exr$/i, "_00000.exr"));
        requireEmpty(renderedFile.fsName, overwrite);
        var item = app.project.renderQueue.items.add(comp);
        item.timeSpanStart = 0;
        item.timeSpanDuration = 1.0 / 24.0;
        var module = item.outputModule(1);
        module.applyTemplate(template);
        module.file = sequenceFile;
        app.project.renderQueue.render();
        if (!renderedFile.exists) fail("render did not produce " + renderedFile.fsName);
        item.remove();
        return renderedFile;
    }

    var outputDir = getenv("OLM_AE_TYPED_FIXTURE_OUTPUT_DIR");
    var template = getenv("OLM_AE_TYPED_FIXTURE_TEMPLATE");
    var projectPath = getenv("OLM_AE_TYPED_FIXTURE_PROJECT_PATH");
    var effectName = getenv("OLM_AE_TYPED_FIXTURE_EFFECT") || "OLM Color Key";
    var overwrite = getenv("OLM_AE_TYPED_FIXTURE_OVERWRITE") === "1";
    var resultPath = outputDir ? outputDir + "/fixture_result.json" : "";
    var project = null;
    var sourceComp = null;
    var renderComp = null;
    var suppressStarted = false;
    var result = {
        kind: "olm_32bpc_typed_procedural_fixture_result",
        status: "error",
        ae_version: "",
        effect: effectName,
        output_dir: outputDir,
        project: projectPath,
        manifest: "fixture_manifest.json",
        parameters: [],
        outputs: [],
        error: ""
    };

    try {
        if (!outputDir || !template || !projectPath) {
            fail("OLM_AE_TYPED_FIXTURE_OUTPUT_DIR, TEMPLATE, and PROJECT_PATH are required");
        }
        ensureFolder(outputDir);
        ensureFolder(new File(projectPath).parent.fsName);
        if (effectName !== "OLM Color Key" && effectName !== "OLM Toon Dilate") {
            fail("unsupported effect " + effectName);
        }
        requireEmpty(projectPath, overwrite);
        requireEmpty(resultPath, overwrite);
        var manifestPath = outputDir + "/fixture_manifest.json";
        requireEmpty(manifestPath, overwrite);
        result.ae_version = String(app.version);

        app.beginSuppressDialogs();
        suppressStarted = true;
        if (app.project) app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
        app.newProject();
        project = app.project;
        if (project.numItems !== 0) fail("fixture requires an empty AE project");
        if (project.renderQueue.numItems !== 0) fail("fixture requires an empty render queue");
        project.bitsPerChannel = 32;
        project.workingSpace = "";
        project.linearBlending = false;
        try {
            project.gpuAccelType = GpuAccelType.SOFTWARE;
        } catch (gpuSetError) {
            fail("cannot set SOFTWARE renderer: " + gpuSetError.toString());
        }
        if (Number(project.bitsPerChannel) !== 32) fail("AE did not accept 32bpc");
        if (Number(project.gpuAccelType) !== Number(GpuAccelType.SOFTWARE)) {
            fail("renderer is not SOFTWARE: " + project.gpuAccelType);
        }
        var workingSpaceText = String(project.workingSpace);
        if (workingSpaceText !== "" && workingSpaceText !== "None") {
            fail("working space is not None: " + workingSpaceText);
        }
        if (project.linearBlending) fail("linear blending is enabled");

        var width = 64;
        var height = 64;
        sourceComp = project.items.addComp("OLM_TYPED_SOURCE_64x64", width, height, 1.0, 1.0 / 24.0, 24.0);
        var backgroundAlpha = effectName === "OLM Toon Dilate" ? 0.0 : 1.0;
        var backgroundLayer = sourceComp.layers.addSolid(
            [0.0, 0.0, 0.0], "solid_background", width, height, 1.0, 1.0 / 24.0);
        backgroundLayer.opacity.setValue(backgroundAlpha * 100.0);
        var rects = [
            {name: "rect_integer_a25", x: 4, y: 4, width: 20, height: 16, color: [1.0, 0.0, 0.0], alpha: 0.25},
            {name: "rect_integer_a50", x: 28, y: 4, width: 20, height: 16, color: [0.0, 1.0, 0.0], alpha: 0.50},
            {name: "rect_integer_a75", x: 4, y: 28, width: 20, height: 16, color: [0.0, 0.0, 1.0], alpha: 0.75},
            {name: "rect_integer_a100", x: 28, y: 28, width: 20, height: 16, color: [1.0, 1.0, 1.0], alpha: 1.00}
        ];
        for (var i = rects.length - 1; i >= 0; i--) addIntegerRect(sourceComp, rects[i]);

        renderComp = project.items.addComp("OLM_TYPED_EFFECT_AB_64x64", width, height, 1.0, 1.0 / 24.0, 24.0);
        var sourceLayer = renderComp.layers.add(sourceComp);
        sourceLayer.name = "generated_source_only";
        var effectLayer = renderComp.layers.add(sourceComp);
        effectLayer.name = "generated_source_effect_on";
        if (sourceLayer.source !== effectLayer.source) fail("A/B layers do not share source comp");
        var effect = effectLayer.property("ADBE Effect Parade").addProperty(effectName);
        if (!effect) fail("AE could not add " + effectName);
        if (effectName === "OLM Toon Dilate") {
            var searchRadius = effect.property(1);
            if (!searchRadius || String(searchRadius.matchName) !== "ADBE OLMToonDilate-0001") {
                fail("Search Radius identity mismatch");
            }
            searchRadius.setValue(13.0);
            var searchRadiusReadback = Number(searchRadius.value);
            if (Math.abs(searchRadiusReadback - 13.0) > 0.0001) {
                fail("Search Radius readback mismatch " + searchRadiusReadback);
            }
            result.parameters = [{
                property_index: 1,
                match_name: String(searchRadius.matchName),
                requested: 13.0,
                actual: searchRadiusReadback
            }];
        }
        sourceLayer.enabled = true;
        effectLayer.enabled = false;
        var noEffect = renderOne(renderComp, outputDir, "effect_no_effect.exr", template);
        sourceLayer.enabled = false;
        effectLayer.enabled = true;
        var effectOn = renderOne(renderComp, outputDir, "effect_effect_on.exr", template);

        var manifest = "{\n" +
            "  \"kind\": " + quote("olm_32bpc_typed_procedural_fixture") + ",\n" +
            "  \"schema_version\": 1,\n" +
            "  \"ae_version\": " + quote(String(app.version)) + ",\n" +
            "  \"project_bits_per_channel\": 32,\n" +
            "  \"working_space\": \"None\",\n" +
            "  \"linear_blending\": false,\n" +
            "  \"dimensions\": [64, 64],\n" +
            "  \"frame\": 0,\n" +
            "  \"effect\": " + quote(effectName) + ",\n" +
            "  \"source_policy\": \"AE-generated solids only; no footage imported\",\n" +
            "  \"render_policy\": \"same comp, only branch enabled state changes\",\n" +
            "  \"outputs\": {\n" +
            "    \"no_effect\": \"effect_no_effect_00000.exr\",\n" +
            "    \"effect_on\": \"effect_effect_on_00000.exr\"\n" +
            "  },\n" +
            "  \"source_layers\": [\n" +
            "    {\"name\": \"solid_background\", \"kind\": \"solid\", \"bounds\": [0, 0, 64, 64], \"rgb\": [0, 0, 0], \"alpha\": " + backgroundAlpha + "},\n" +
            "    {\"name\": \"rect_integer_a25\", \"kind\": \"solid\", \"bounds\": [4, 4, 20, 16], \"rgb\": [1, 0, 0], \"alpha\": 0.25},\n" +
            "    {\"name\": \"rect_integer_a50\", \"kind\": \"solid\", \"bounds\": [28, 4, 20, 16], \"rgb\": [0, 1, 0], \"alpha\": 0.5},\n" +
            "    {\"name\": \"rect_integer_a75\", \"kind\": \"solid\", \"bounds\": [4, 28, 20, 16], \"rgb\": [0, 0, 1], \"alpha\": 0.75},\n" +
            "    {\"name\": \"rect_integer_a100\", \"kind\": \"solid\", \"bounds\": [28, 28, 20, 16], \"rgb\": [1, 1, 1], \"alpha\": 1.0}\n" +
            "  ],\n" +
            "  \"fail_closed\": [\n" +
            "    \"reject imported footage or missing source recipe\",\n" +
            "    \"reject non-32bpc, working-space, or linear-blending drift\",\n" +
            "    \"reject missing no-effect or effect-on EXR\",\n" +
            "    \"reject comparison unless both outputs came from this same comp\"\n" +
            "  ]\n" +
            "}\n";
        writeText(manifestPath, manifest);
        project.save(new File(projectPath));
        result.outputs = [noEffect.fsName, effectOn.fsName];
        result.status = "ok";
    } catch (error) {
        result.error = error.toString();
    } finally {
        try { if (suppressStarted) app.endSuppressDialogs(false); } catch (_) {}
    }

    if (resultPath) {
        writeText(resultPath, "{\n" +
            "  \"kind\": " + quote(result.kind) + ",\n" +
            "  \"status\": " + quote(result.status) + ",\n" +
            "  \"ae_version\": " + quote(result.ae_version) + ",\n" +
            "  \"effect\": " + quote(result.effect) + ",\n" +
            "  \"manifest\": " + quote(result.manifest) + ",\n" +
            "  \"parameters\": [" + (result.parameters.length ?
                "{\"property_index\":1,\"match_name\":" + quote(result.parameters[0].match_name) +
                ",\"requested\":13,\"actual\":" + result.parameters[0].actual + "}" : "") + "],\n" +
            "  \"outputs\": [" + (result.outputs.length ? quote(result.outputs[0]) + "," + quote(result.outputs[1]) : "") + "],\n" +
            "  \"error\": " + quote(result.error) + "\n}\n");
    }
    if (result.status !== "ok") fail(result.error || "unknown failure");
}());
