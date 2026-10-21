/* v2 launch payload: numerical/host semantics remain owned by the frozen
   corrected v1 payload.  The v2 Python launcher adds a stronger readiness
   handshake before this file can be invoked. */
(function () {
    var payload = new File(
        File($.fileName).parent.fsName +
        "/ae_host_all10_post_toondilate_ded9_corrected_20260813.jsx"
    );
    if (!payload.exists) throw new Error("FAIL_CLOSED: corrected v1 payload unavailable");
    $.evalFile(payload);
}());
