# OLM Kira Kira Ramp custom UI — Mac AE 2026-08-10

## Result

`PASS`: After Effects 26.3.0.87 on Apple Silicon loaded the Universal
`OLMKiraKira.plugin`, expanded `Vertical Color Ramp > Ramp`, drew the gradient
and three default stops, and accepted a click that inserted a fourth stop.

## Failure and cause

Before the fix, expanding `Ramp` terminated AE before `PF_Event_DRAW` reached
the plug-in. The arm64 minidump stopped at
`CECCustomControl::GetContext(dvaui::drawbot::Drawbot*) + 52`; its
`CECCustomTitle::GetContext` result in `x21` was null.

Fresh execution of the Windows AEX established two setup contracts that the
Mac port had omitted:

- `GLOBAL_SETUP` calls `AEGP_RegisterWithAEGP(nullptr, "OLM Kira Kira", ...)`.
- `PARAMS_SETUP` calls `PF_REGISTER_UI` with the exact ten-word
  `PF_CustomUIInfo` value `[0,4,0,0,0,0,0,0,0,0]`, i.e.
  `PF_CustomEFlag_EFFECT` and zero dimensions/alignment.

The same probe also established that all five arbitrary Ramp rows use one
stable non-null owner-side `refcon` (`effect + 0x200`). The Mac callback needs
no state from it, but now preserves the same opaque identity and lifetime.

Adding the AEGP registration alone did not fix the crash. Adding the exact
`PF_REGISTER_UI` contract did: AE created the ECW context and dispatched the
existing native Drawbot/event implementation.

## Evidence boundary

- Host: macOS, Apple Silicon, After Effects 26.3.0.87.
- Plug-in binary SHA-256:
  `21e89157d769d824cea0f177663812e89ca48a60d9a5d747adaed433d0e0dbe5`.
- Original crash dump SHA-256:
  `75cf8d1937f44fdd88a3c1f11788f9cc710c9c7a66d2be2c59292b593ffc2768`.
- Reproduction: new 1920x1080 comp, black solid, apply OLM Kira Kira, expand
  `Vertical Color Ramp`, expand `Ramp`.
- Proved here: ECW context creation, default draw, and single-click stop
  insertion. Continuous dragging, deletion, and color-picker interaction remain
  covered by focused synthetic event regression, not claimed as live AE input.
- This is a UI/event-host result; it does not widen renderer pixel-equivalence
  claims.
