# OLMDistanceGradation case_0023 Return Acceptance - 2026-07-01

This note explains how to judge the currently pending Windows runtime package
for `case_0023`.

## Current package scope

The live shared package is:

- `refs/runtime_trace_packages/olm_runtime_trace_requests_20260630_182750.zip`
- request id:
  `olmdistancegradation_16bpc_constant_case0023_outside0_witness_20260630`

Its README asks most explicitly for the top-edge representatives:

- `(1699,7)`
- `(985,26)`

That is useful, but it does **not** cover the full current 2026-07-01 witness
contract by itself.

## Why that matters

The active Mac-side contract is now split into two residual families:

1. edge family
   - `65px`
   - `inside=1.0`, `outside=0.0`
   - representatives around `(1698..1700,7)`
2. threshold family
   - `8px`
   - `raw_inside` crossing `35.014 -> 36.013 -> 37.013`
   - representatives around `(414..416,393)`

The current package directly names the first family, but not the second.

## Acceptance rule for the pending return

### `answered`

Classify the current pending package as `answered` only if it returns typed
helper-staging / ownership / compose facts that truly close the active lane for
the edge family and also make the threshold family unnecessary or explained by
the same rule.

That means more than final red-endpoint bytes. It needs the missing upstream
ownership facts.

### `answered_partial`

Classify the return as `answered_partial` if it does either of these:

- re-confirms only the edge-family boundary facts (`inside=1.0`,
  `outside=0.0`, red endpoint) without isolating the typed ownership/compose
  values, or
- isolates the edge-family typed witness but says nothing decisive about the
  threshold family around `(414..416,393)`

This is the most likely acceptable outcome for the current package, because the
package itself is still edge-family-centric.

### `trace-too-sparse` or `not isolated`

Use these if the return hits the right case but still cannot isolate:

- helper-stage field value before compose
- equality / plateau ownership rule
- whether the Constant-only binary fork sees the pixel before or after that
  ownership decision

## What a follow-up would need if the return is only partial

If the current package answers only the edge family, the next narrower request
should target the threshold-family triplet directly:

- `(414,393)`
- `(415,393)`
- `(416,393)`

with the same typed ownership/helper-staging fields.

## Practical implication

Do not promote a code change from a return that merely re-states the
edge-family final endpoint. That is useful evidence, but not yet the full
`case_0023` contract.
