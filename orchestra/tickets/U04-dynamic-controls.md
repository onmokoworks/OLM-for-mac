depends: U03-aexcompat-ui-oracle
# U04: dynamic controls (hide / disable) matching the original for all plugins

## Do
- Using U03's UI oracle and witnesses, make every plugin's UPDATE_PARAMS_UI / USER_CHANGED behaviour match the original, following U01's "UPDATE_PARAMS_UI rules" exactly:
  - **hidden** (DynamicStream HIDDEN) versus **disabled** (`PF_PUI_DISABLED` via `PF_UpdateParamUI`), per row;
  - the same slots and the same conditions;
  - no renaming;
  - ColorKeep: hide slots above the count. The Mac port currently disables them, which is wrong.
  - Blur: always hide Blur Smoothness.
  - ColorKey: the P/C/N/R rules.
  - Smoother2: add the missing dispatch.
  - DirectionalBlur, RadialBlur, DistanceGradation: audit the existing handlers.
  - KiraKira: Use Ramp enable/disable.
  - Smoother v1 and ToonDilate: negative tests (nothing happens).
- Compare Mac against the original on the full U01 test matrix. The Mac side runs the same handler logic through a test host that records ParamUtils/DynamicStream calls.
- Check that saved-project reload restores the same UI state.

## Acceptance
- The whole matrix is equal to the original.
- Render unchanged: default fuzz seed 1 n300 per touched plugin with no exact→non-exact, and all corpora replay true.

## Rules
- Use 1-2 processes. Do not change pixel kernels. Do not touch the release gate or ledger. Commit partial results at least every 30 minutes. The stop rule applies.
