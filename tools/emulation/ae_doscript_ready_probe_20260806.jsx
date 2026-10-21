(function () {
    var output = new File("/tmp/olm_ae_doscript_ready_20260806.txt");
    output.encoding = "UTF-8";
    if (output.open("w")) {
        output.write("ae=" + String(app.version) + "\n");
        output.close();
    }
}());
