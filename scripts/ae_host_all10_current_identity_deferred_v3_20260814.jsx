/* Deferred v3 aggregate payload.

   This file is an execution dependency only.  The paired Python contract
   refuses every live execution path until a separate explicit approval
   changes that contract.  If later authorized, the generic 64x36 frame keeps
   Toon and the other bounded-only effects disabled; it adds no numerical
   claim. */
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
    var newClaim = "Fresh installed host load/add/enable-state and exact mapping for all ten; effect-enabled generic host-frame render only for OLMBlur and OLMDirectionalBlur; OLMToonDilate and the other seven are disabled before generic saveFrameToPng. Numerical behavior is not assessed by this AE smoke. No pixel-exact, Windows-equivalence, typed-plane, padding, admission, or public-owner numerical-exact claim.";
    if (text.split(oldSpec).length !== 2 || text.split(oldClaim).length !== 2 ||
        text.split("numerical_render_supported: false,").length !== 2)
        throw new Error("FAIL_CLOSED: base payload contract drifted");
    text = text.replace(oldSpec, newSpec).split(oldClaim).join(newClaim);
    text = text.split("numerical_render_supported: false,").join(
        "numerical_render_supported: null, numerical_render_assessment: \"not_assessed\","
    );
    eval(text);
}());
