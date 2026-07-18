# OLMSmoother2 force-input-premultiply safety audit - 2026-07-18

## Scope

Audit the current production-source diagnostic gate
`OLMSMOOTHER2_FORCE_INPUT_PREMULTIPLY` in
`mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`, prove the default path is
unchanged, and identify accidental production exposure.

## FACT

- The gate is only read from process environment inside
  `OLMSmoother2ConfigureTracePixelFromEnvironment()`.
- `rg` found no mention of `OLMSMOOTHER2_FORCE_INPUT_PREMULTIPLY` in
  `OLMSmoother2PiPL.r`, `OLMSmoother2_Strings.h`,
  `OLMSmoother2_Strings.cpp`, `OLMSmoother2.cpp`, or
  `Mac/OLMSmoother2.plugin-Info.plist`.
- The only production callsite is inside `RenderBits()` before scratch-buffer
  population; the helper specializes PF8/PF16 integer premultiply rounding and
  uses plain `rgb *= a` for float input.
- Before this audit, the boolean only updated when the environment variable was
  present. Therefore a process that had rendered once with
  `OLMSMOOTHER2_FORCE_INPUT_PREMULTIPLY=1` could keep the diagnostic path
  enabled even after the variable was removed in-process.
- The source now resets the gate every render with:

  `g_olmsmoother2_force_input_premultiply = force_input_premultiply && std::strcmp(force_input_premultiply, "1") == 0;`

- Focused builds succeeded:
  - `refs/scripts/build_olmsmoother2_cli.sh`
  - `xcodebuild -project mac/OLMSmoother2/Mac/OLMSmoother2.xcodeproj -configuration Debug -target OLMSmoother2 build`
- Focused smokes succeeded:
  - `python3 refs/scripts/smoke_olmsmoother2_case0012_unpremul_gate.py`
  - `python3 refs/scripts/smoke_olmsmoother2_pf8_host_adapter_chain_20260718.py`
  - `python3 refs/scripts/smoke_olmsmoother2_force_input_premultiply_safety_20260718.py`
- The new safety smoke proves:
  - env unset output SHA-256:
    `085b14fb9403f9cc7bce536293e24929656b35974436777f36e5f08e9f8c93c5`
  - env `"0"` output SHA-256:
    `085b14fb9403f9cc7bce536293e24929656b35974436777f36e5f08e9f8c93c5`
  - env `"1"` output SHA-256:
    `5c861e453263697830ea90c9936560c9e55f7f0b85ec14d68229c1979a52f214`

## INFERENCE

- Default production behavior is unchanged for normal launches where the
  environment variable is absent.
- The accidental exposure surface is process-environment only; there is no UI,
  PiPL, or plist surface for ordinary AE users to toggle this path.
- Leaving the old latch behavior in place would have made the diagnostic gate
  fail-open under in-process env mutation. The narrow reset is an appropriate
  production safety fix.

## Not Claimed

- No claim of AE exactness from this audit.
- No claim that other diagnostic env toggles are fail-closed; this audit is
  scoped to `OLMSMOOTHER2_FORCE_INPUT_PREMULTIPLY`.
