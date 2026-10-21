/* Batch5 deferred v1 aggregate payload.

   This is an execution dependency only. The paired Python contract exposes no
   live AE path. If a separately reviewed live adapter is later authorized,
   only Blur and DirectionalBlur remain enabled for the generic frame; every
   bounded/fail-closed effect, including ToonDilate, is disabled after load/add.
   This payload makes no numerical claim. */
(function () {
    var source = new File(
        File($.fileName).parent.fsName +
        "/ae_host_all10_current_install_fresh_validation_20260812.jsx"
    );
    if (!source.open("r")) throw new Error("FAIL_CLOSED: base payload unavailable");
    var text = source.read(); source.close();
    var oldSpec = '{ plugin: "OLMToonDilate", matchNames: ["ADBE OLMToonDilate", "OLM Toon Dilate"], width: 64, height: 36, depth: 32, enabledHostFrame: true }';
    var newSpec = '{ plugin: "OLMToonDilate", matchNames: ["ADBE OLMToonDilate", "OLM Toon Dilate"], width: 64, height: 36, depth: 32 }';
    var oldClaim = "Fresh installed host load/add and exact mapping for all ten; effect-enabled host frame render only for OLMBlur, OLMDirectionalBlur, and OLMToonDilate; effect-disabled host frame render for the other seven. No pixel-exact, Windows-equivalence, typed-plane, padding, or public-owner numerical-exact claim.";
    var newClaim = "Batch5 installed host load/add/enable-state and exact mapping for all ten; effect-enabled generic host-frame render only for OLMBlur and OLMDirectionalBlur; OLMToonDilate and the other seven bounded effects are disabled before generic saveFrameToPng. Numerical behavior is not assessed by this AE smoke. No pixel-exact, Windows-equivalence, typed-plane, padding, admission, or public-owner numerical-exact claim.";
    if (text.split(oldSpec).length !== 2 || text.split(oldClaim).length !== 2 ||
        text.split("numerical_render_supported: false,").length !== 2)
        throw new Error("FAIL_CLOSED: base payload contract drifted");
    text = text.replace(oldSpec, newSpec).split(oldClaim).join(newClaim);
    text = text.split("numerical_render_supported: false,").join(
        "numerical_render_supported: null, numerical_render_assessment: \"not_assessed\","
    );
    eval(text);
}());
