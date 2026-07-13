(function () {
    function env(name) { try { return $.getenv(name) || ""; } catch (e) { return ""; } }
    var root = File($.fileName).parent.parent.fsName;
    var requestDir = env("OLM_DG_LIVE_REQUEST_DIR");
    var workRoot = env("OLM_DG_LIVE_WORK_ROOT");
    if (!requestDir || !workRoot) { throw new Error("liveness request/work root is required"); }
    $.setenv("OLM_AE_REQUEST_DIR", requestDir);
    $.setenv("OLM_AE_CASE_ID", "case_0001");
    $.setenv("OLM_AE_OUTPUT_DIR", workRoot + "/single_case_output");
    $.setenv("OLM_AE_LOG_PATH", workRoot + "/AE_SINGLE_CASE.log");
    $.setenv("OLM_AE_RESULT_JSON", workRoot + "/AE_SINGLE_CASE_RESULT.json");
    $.setenv("OLM_AE_KEEP_OPEN", "0");
    $.setenv("OLM_AE_FORCE_NEW_PROJECT", "1");
    $.evalFile(new File(root + "/scripts/ae_render_single_case.jsx"));
})();
