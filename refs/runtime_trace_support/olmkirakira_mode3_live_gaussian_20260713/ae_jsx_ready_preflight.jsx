(function () {
    var markerPath = "";
    try {
        markerPath = $.getenv("OLM_AE_PREFLIGHT_READY_MARKER") || "";
        if (!markerPath || !/^(?:[A-Za-z]:[\\\/]|\\\\)/.test(markerPath)) {
            throw new Error("OLM_AE_PREFLIGHT_READY_MARKER must be absolute");
        }
        var marker = new File(markerPath);
        marker.encoding = "UTF-8";
        if (!marker.open("w")) {
            throw new Error("could not open preflight marker");
        }
        marker.write("AE_JSX_PREFLIGHT_READY ae_version=" + app.version + " jsx=" + File($.fileName).fsName + "\n");
        marker.close();
    } catch (error) {
        try {
            if (markerPath) {
                var failure = new File(markerPath + ".error.txt");
                failure.encoding = "UTF-8";
                if (failure.open("w")) {
                    failure.write(error.toString() + "\n");
                    failure.close();
                }
            }
        } catch (_) {}
    }
    try { app.quit(); } catch (_) {}
}());
