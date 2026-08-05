(function () {
    if (app.project) {
        try { app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES); } catch (ignored) {}
    }
    app.newProject();
    var project = app.project;
    if (!project) { throw new Error("FAIL_CLOSED: cannot create prewarm project"); }
    var comp = project.items.addComp("OLMRadialBlur_PREWARM", 16, 16, 1, 1, 24);
    var layer = comp.layers.addSolid([0, 0, 0], "PREWARM", 16, 16, 1);
    var effect = layer.property("ADBE Effect Parade").addProperty("OLM RadialBlur");
    if (!effect || effect.matchName !== "OLM RadialBlur") {
        throw new Error("FAIL_CLOSED: OLM RadialBlur prewarm identity");
    }
}());
