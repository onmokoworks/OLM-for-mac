# OLMToonDilate 16/32bpc Expansion Readiness Audit

Date: 2026-07-18
Scope: `OLMToonDilate` only.
Policy: Windows AE `SOFTWARE` is the reference; `AE exact` requires the declared cases to compare with `max_diff=0`.

## Decision

`OLMToonDilate` is ready for a focused 32bpc Mac AE capture, but it is not yet
32bpc `AE exact`.

- **16bpc:** `AE exact` for the declared three-case slice (`3/3`). This is a
  narrow covered slice, not a whole-plugin claim.
- **32bpc Windows evidence:** usable. The 2026-07-10 AE 26.3 recap contains
  three ToonDilate effect EXRs and three before-effects EXRs. Its manifest says
  `bits_per_channel=32`, renderer `SOFTWARE`, `output_format=exr`, and
  `float_preserving=true`.
- **32bpc Mac evidence:** not available in the repository as a ToonDilate EXR
  candidate. Therefore no cross-host 32bpc comparison and no exact claim can
  be made.
- **Package state:** the Mac 32bpc package smoke now passes. The packaging
  script records the current candidate binary SHA at generation time, so a
  deliberate rebuild no longer trips a stale fixed-hash check. This changes
  package provenance only; it is not evidence of an algorithm match.

## Verified Local Semantics

The current Mac source contains distinct PF8, PF16, and PF32 dispatch paths;
typed opaque-seed predicates; `ceil(search_radius * width / comp_width)`;
pre-render composition-width capture; RGB preservation for zero-alpha input;
and two directional neighbor-relaxation passes. These facts are recorded by
the machine-readable audit and are not promoted to AE exactness by themselves.

The existing bounded binary evidence also passes:

- PF16 actual-AEX worker-stage boundary, including the `32768` seed boundary.
- PF16/PF32 worker copy boundary and row-padding ownership.
- PF32 48-case seed/propagation matrix.
- Mac SmartRender adapter contract for PF16 and PF32, including zero-alpha RGB
  preservation.

These are binary/host-contract evidence, not Windows AE output equivalence.

## Highest-Value Mac-Only Action

Build the current plugin, refresh the isolated Mac 32bpc validation package so
its provenance matches that binary, then run the fixture with:

- AE 26.3;
- project `32bpc`;
- renderer `SOFTWARE`;
- working space `None`;
- linear blending off;
- `OLM EXR 32 Float`;
- identical no-effect and effect-on output-module settings;
- captured output-module settings and SHA-256 for both EXRs.

The next acceptance step is not source tuning. It is to produce a Mac
no-effect/effect FLOAT EXR pair that can be compared with the Windows
Software EXR contract. A no-effect-only render, PNG, CLI output, or synthetic
worker fixture is insufficient.

## Reproduction

The bounded audit is read-only with respect to the plugin and ledger:

`python3 tools/emulation/audit_olmtoondilate_16_32bpc_readiness_20260718.py`

The audit output is:

`refs/conformance/olmtoondilate_16_32bpc_readiness_20260718.json`

The audit runs the existing bit-depth, PF16, PF32, SmartRender, and isolated
package checks. On 2026-07-18 they passed. A Mac candidate EXR and a
cross-host comparison are still required before any 32bpc exact claim.
