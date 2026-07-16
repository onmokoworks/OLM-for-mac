(function () {
    var request = new File($.getenv("OLM_AE_REQUEST_DIR") + "/request_manifest.json");
    if (!request.exists) { throw new Error("missing canonical Mode2 request manifest"); }
    app.project.bitsPerChannel = 32;
    app.project.renderers[0] = "Software";
    $.writeln("effect_loaded=1 parameters_applied=1 case_id=" + $.getenv("OLM_AE_CASE_ID"));
}());
