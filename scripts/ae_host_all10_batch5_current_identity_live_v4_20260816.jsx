/* Batch5 host-plumbing payload after bounded OLMBlur admission.

   Only DirectionalBlur remains enabled for the generic 64x36 frame.  The
   other nine effects are loaded/applied and then disabled; numerical behavior
   is not assessed here. */
(function () {
    var source = new File(
        File($.fileName).parent.fsName +
        "/ae_host_all10_current_install_fresh_validation_20260812.jsx"
    );
    if (!source.open("r")) throw new Error("FAIL_CLOSED: base payload unavailable");
    var text = source.read(); source.close();
    var oldBlur = '{ plugin: "OLMBlur", matchNames: ["OLM OLM Blur", "OLM Blur"], width: 64, height: 36, depth: 32, enabledHostFrame: true }';
    var newBlur = '{ plugin: "OLMBlur", matchNames: ["OLM OLM Blur", "OLM Blur"], width: 64, height: 36, depth: 32 }';
    var oldToon = '{ plugin: "OLMToonDilate", matchNames: ["ADBE OLMToonDilate", "OLM Toon Dilate"], width: 64, height: 36, depth: 32, enabledHostFrame: true }';
    var newToon = '{ plugin: "OLMToonDilate", matchNames: ["ADBE OLMToonDilate", "OLM Toon Dilate"], width: 64, height: 36, depth: 32 }';
    var oldClaim = "Fresh installed host load/add and exact mapping for all ten; effect-enabled host frame render only for OLMBlur, OLMDirectionalBlur, and OLMToonDilate; effect-disabled host frame render for the other seven. No pixel-exact, Windows-equivalence, typed-plane, padding, or public-owner numerical-exact claim.";
    var newClaim = "Batch5 installed host load/add/enable-state for all ten; effect-enabled generic host-frame render only for OLMDirectionalBlur. OLMBlur and the other eight bounded effects are disabled before generic saveFrameToPng. Numerical behavior is not assessed by this AE smoke. No pixel-exact, Windows-equivalence, typed-plane, padding, admission, or public-owner numerical-exact claim.";
    if (text.split(oldBlur).length !== 2 || text.split(oldToon).length !== 2 ||
        text.split(oldClaim).length !== 2 ||
        text.split("numerical_render_supported: false,").length !== 2)
        throw new Error("FAIL_CLOSED: base payload contract drifted");
    text = text.replace(oldBlur, newBlur).replace(oldToon, newToon).replace(oldClaim, newClaim);
    text = text.replace(
        "numerical_render_supported: false,",
        "numerical_render_supported: false, numerical_render_assessment: \"not_assessed\","
    );
    eval(text);
}());
