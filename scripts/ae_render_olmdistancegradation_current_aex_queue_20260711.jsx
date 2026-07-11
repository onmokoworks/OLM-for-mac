/* One AE process queue for both DG cases. The CDB session owns the shared run. */
(function () {
    function env(name) { try { return $.getenv(name) || ""; } catch (e) { return ""; } }
    function append(path, text) { var f = new File(path); f.encoding = "UTF-8"; if (f.open("a")) { f.write(text); f.close(); } }
    var root = File($.fileName).parent.parent.fsName;
    var requestDir = env("OLM_DG_REQUEST_DIR");
    var cases = [
        "olmdistancegradation_extended__case_0010",
        "olmdistancegradation_extended__case_0011"
    ];
    var runId = env("OLM_DG_RUN_ID");
    var queueLog = root + "/work/olmdg_queue_" + runId + ".log";
    append(queueLog, "OLMDG_QUEUE_START run_id=" + runId + "\n");
    for (var i = 0; i < cases.length; i++) {
        var caseId = cases[i];
        if (!caseId) { continue; }
        /* The queue is deliberately serial: no second AE process or second CDB. */
        $.setenv("OLM_AE_REQUEST_DIR", requestDir);
        $.setenv("OLM_AE_CASE_ID", caseId);
        $.setenv("OLM_AE_FORCE_NEW_PROJECT", i === 0 ? "1" : "0");
        append(queueLog, "OLMDG_CASE_START run_id=" + runId + " case_id=" + caseId + "\n");
        /* Reuse the included renderer; this is an actual serial render, not a plan. */
        $.evalFile(new File(root + "/scripts/ae_render_single_case.jsx"));
        append(queueLog, "OLMDG_CASE_READY run_id=" + runId + " case_id=" + caseId + "\n");
    }
    append(queueLog, "OLMDG_QUEUE_END run_id=" + runId + "\n");
})();
