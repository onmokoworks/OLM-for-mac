# OLMRadialBlur Strength 290 exported math boundary

Status: `PASS_LOCALIZED_HOST_MATH_BOUNDARY_STRENGTH290_REMAINS_FAIL_CLOSED`.

The exact PF32 32x18 fixture gives byte-identical output from the pinned AEX internal owner and the current Mac typed owner (`940c1e7e…`). The exported Smart route through an AE-free AEXCompat worker using Rust f32 `atan2f`/`log2f` produces `f8be3360…` instead: 84 float words differ, with ULP histogram `{"1":54,"10":1,"2":25,"3":3,"4":1}`. A double-to-float counterfactual produces a third hash, so neither host substitute is promoted as a Windows oracle. The exported call census is 149 `log2f` calls over one input plus 576 `atan2f` calls over a complete 18×32 argument grid (577 unique native request vectors). Native Windows UCRT output has not been captured. Strength 290 therefore remains fail-closed before iteration; production, the installed bundle, network state, and After Effects were unchanged.
