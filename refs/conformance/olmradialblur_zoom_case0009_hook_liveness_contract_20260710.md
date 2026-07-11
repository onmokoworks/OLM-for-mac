# OLMRadialBlur Zoom case_0009 Hook-Liveness Contract

## Purpose

The prior typed-witness run rendered `case_0009` successfully, but none of the
coordinate-conditioned hooks at `+0x5e5b`, `+0x5e6d`, `+0x7404`, or `+0x7409`
hit. This request does **not** ask for inferred cells or PNG tuning. It decides
whether those offsets execute in the same current-AEX run at all.

## Required Same Run

Run the package-local `case_0009` request once under CDB. Arm unconditional,
one-shot breakpoints at all four offsets. For every hit, record the module base,
absolute address, registers, and the first stack words. Let the render finish
and return the AE log/result plus CDB console/log.

## Acceptance

`answered` requires a complete same-run AE result with at least one raw offset
hit. `answered_partial` requires an AE render result and a CDB log proving all
four raw breakpoints were armed but none hit. Do not call an offset dead solely
because a coordinate predicate was false in an earlier run.

## Decision

- raw hit: use its captured registers to rebuild the typed-coordinate gate;
- no raw hit after a completed render: audit the loaded AEX identity and select
  a new callsite from the current binary, rather than retuning the Mac port.
