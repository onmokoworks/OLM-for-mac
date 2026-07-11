# OLMDirectionalBlur angle-0 static helper/writeback audit

- Date: 2026-07-10
- Scope: static audit only; Windows return is not required for this pass
- Ownership: this report only
- Decision: `keep-angle0-blocked; no-code-change; single-shot-Windows-witness-is-minimal`
- PNG tuning: forbidden and not used

## Executive summary

The angle-0 residual remains a typed helper/validity/writeback question, not a
PNG-tuning question. The static AEX facts establish the front helper's source
and destination direction, its effective-span gate, its separate validity input,
and its denominator accumulation. They also establish the two-stage A/B
writeback order. They do not identify which local source/range or validity path
produces the Windows pixels `(494,169)` and `(579,169)`.

No Mac-only probe is currently sufficient to answer that missing question
without changing the implementation or adding instrumentation. The smallest
actionable next probe is therefore the already-materialized single-shot Windows
request, gated on the two angle-0 pixels in one Software execution.

## FACT: source and static evidence

### Angle-0 witness boundary

- The active case is `directionalblur_context_scale_20260606` /
  `db_existing_case_0001_software_pair`, with `Angle=0`, front strength `1690`,
  front alpha fade `0`, sharp tail `45`, and size variation `92`.
  Reference: `refs/conformance/olmdirectionalblur_angle0_local_readiness_audit_20260710.md:19-21`.
- The local row is `y=169`, with the full/scatter segment `x=380..579`.
  Interior witness `(494,169)` is Windows `[164,0,0,255]` versus local
  `[0,0,0,255]`; alpha already matches. Endpoint witness is `(579,169)`.
  References: `refs/conformance/olmdirectionalblur_angle0_local_static_review_20260707.md:13-17`,
  `refs/conformance/olmdirectionalblur_lane_state_20260703.md:10-15`.
- The endpoint cannot be explained by a same-row front-helper source wholly
  inside that visible segment if the static front direction is applied: the
  source x must be strictly greater than the destination x, hence at least
  `580` for destination `579`. This is a constraint, not proof of an alternate
  path. Reference: `refs/conformance/olmdirectionalblur_angle0_endpoint_constraint_20260630.md`.

### Helper validity and denominator

- `FUN_1800013e0` reads source RGB from `param_4` and a separate
  source-alpha/validity value from `param_7` (`decomp/OLMDirectionalBlur.aex.c.txt:171-176`).
- It truncates `param_9 * param_11` to the effective span, starts at offset `1`,
  and does no work when the resulting span is not greater than `1`
  (`decomp/OLMDirectionalBlur.aex.c.txt:177-201`). The front direction
  (`param_3=1`) steps with `iVar11=-1` and clamps at the left boundary
  (`decomp/OLMDirectionalBlur.aex.c.txt:184-200`).
- Each accepted contribution is `source_validity * weight`; RGB is added to
  `param_5`, the same contribution is added to `param_6` (denominator), and
  output alpha is updated by a max operation. The helper-local stores are
  visible at `decomp/OLMDirectionalBlur.aex.c.txt:207-220`, `222-270`, and
  `276-285`. Address-level interpretation is also recorded at
  `notes/OLMDirectionalBlur_ASM_FACTS.md:219-281`.
- `FUN_1800038d0` first runs `FUN_180001000` with source A, destination B,
  `alpha_or_valid = params+0x8088`, and denominator `params+0x8080`; it then
  skips scatter when source A alpha is exactly zero
  (`decomp/OLMDirectionalBlur.aex.c.txt:1538-1550`). The front call passes
  `param_3=1`, source A, destination B, denominator, and `alpha_or_valid`
  (`decomp/OLMDirectionalBlur.aex.c.txt:1578-1580`).
- The rowdriver's validity gate, component coefficient, sharp-tail coefficient,
  and front helper call are distinct operations. Therefore a final RGB miss
  does not by itself distinguish row membership, `alpha_or_valid`, helper span,
  or denominator ownership (`decomp/OLMDirectionalBlur.aex.c.txt:1550-1592`).

### Writeback ownership

- AEX work buffers are A=`params+0x8078`, B=`params+0x8090`; denominator is
  `params+0x8080`; validity side-channel is `params+0x8088`.
  Reference: `notes/IR_OLMDirectionalBlur.md:162-189`.
- The first rotate is A -> B, followed by a copy B -> A before component-map
  and rowdriver processing. After rowdriver, B RGB is divided by the per-pixel
  denominator and A is cleared. The normalized B is then rotated back into A,
  and `params+0x8090` is repointed to A for output.
  Address references: `notes/OLMDirectionalBlur_ASM_FACTS.md:378-466`.
- Final normalization is guarded by denominator `> 0`; a zero denominator does
  not establish a nonzero output contribution. Reference:
  `notes/IR_OLMDirectionalBlur.md:308-311` and
  `decomp/OLMDirectionalBlur.aex.c.txt:2110-2205`.
- The Gaussian table divisor is statically fixed at `length/3.0` with `1e-5`
  epsilon, and the Mac source now matches it at
  `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:191-199`. This is confirmed
  static parity only; it does not close the angle-0 helper gate.

## FACT: current Windows evidence state

- The 2026-07-07 helper-gate return is `answered_partial`: Windows reached the
  real plugin and broad offsets `+0x13e0`, `+0x38d0`, `+0x4a20`, `+0x6b30`, and
  `+0x4880`, but broad auto-continue caused a hit storm and retained no typed
  values for `(494,169)` or `(579,169)`.
  Reference: `refs/conformance/olmdirectionalblur_angle0_helper_gate_return_acceptance_20260707.md:9-35`.
- The focused request package now exists and verifies as a 23-entry ZIP:
  `refs/runtime_trace_packages/olm_runtime_trace_directionalblur_angle0_single_shot_20260710.zip`.
  Its materialization record says it contains the exact one-request profile and
  claims no Windows return or typed witness values
  (`refs/conformance/olmdirectionalblur_angle0_single_shot_package_materialized_20260710.md:1-24`).
- The single-shot contract requires two independent same-run records, not a
  case-level value: A/B mapping, helper source/range, touched destination range,
  group membership, denominator, validity side-channel, numerator,
  pre-writeback RGBA, and final bytes
  (`refs/conformance/olmdirectionalblur_angle0_single_shot_witness_contract_20260708.md:17-43`).
- Current runtime summary contains no DirectionalBlur result. The package is
  prepared, but no typed Windows return is present locally.

## FACT: Mac-only probe feasibility

- The Mac implementation reads `downsample_x/y` and scales the front strength;
  at angle zero the directional scale reduces to `scale_x`
  (`mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:253-265`, `365-375`).
- For the supported 8bpc slice it uses one direct same-row bilinear gather with
  `accum_sum`, max-like alpha, and a fixed `strength` denominator
  (`mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:270-321`). It copy-throughs
  nonzero alpha-fade/noise/back lanes and 16/32bpc paths
  (`mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:226-233`, `327-339`).
- This Mac path does not expose the AEX A/B buffers, `alpha_or_valid` side
  channel, component-map row membership, helper-local source range, or the
  AEX final rotate-back ownership. A final Mac pixel or existing CLI witness
  can therefore vary output, but cannot identify which of the AEX validity,
  denominator, helper coverage, or writeback hypotheses is true.
- Ghidra MCP was attempted read-only for `0x1800013e0`, `0x1800038d0`, and
  `0x180004a20`. The connected database resolved those addresses to a
  RadialBlur program/function namespace, not the checked-in DirectionalBlur
  AEX. Its result is not used as DirectionalBlur evidence; the checked-in
  `decomp/` and `disasm/` remain the authoritative local sources.

## INFERENCE and decision

- There is no Mac-only executable probe in the current workspace that can close
  the requested helper validity/denominator/writeback question without source
  instrumentation or an implementation change. Such a change is outside this
  audit's ownership and would risk converting a structural unknown into PNG
  tuning.
- The minimum useful probe is the existing single-shot Windows witness because
  it runs the actual AEX helper and captures the two pixels that separate the
  interior accumulation question from the endpoint coverage question. A broad
  helper breakpoint is not minimal in information terms: the prior return
  demonstrated reachability but lost the typed fields to hit volume.
- Keep the Mac and CLI algorithm behavior unchanged. Do not change Gaussian
  width, rowdriver direction, validity handling, denominator, or output
  writeback based on PNGs or the partial Windows return.

## Executable next-probe specification

Use exactly one Software render from the materialized package, with conditional
or single-shot gating at the two output witnesses `(494,169)` and `(579,169)`.
Do not include diagonal witnesses and do not use broad auto-continue at
`+0x13e0`.

For each witness, return independently:

1. normalized consumed parameters;
2. output-to-A/B mapping and buffer identity;
3. helper-local source x/y and source x range;
4. actual touched destination x range on row `169`;
5. rowdriver/component membership;
6. denominator and `alpha_or_valid` (or equivalent validity value);
7. accumulation numerator RGBA;
8. pre-writeback RGBA float/hex;
9. final stored RGBA bytes.

Accept only when both records are complete in the same run. A module-load hit,
broad stage reachability, PNG, final-byte-only result, or collapsed case-level
record remains `answered_partial`/`failed_partial` and does not authorize a Mac
or CLI source change.

## Commands run

```bash
git status --short
python3 refs/scripts/smoke_compare_directionalblur_trace.py
python3 refs/scripts/smoke_olmdirectionalblur_cli_witness.py
python3 refs/scripts/smoke_analyze_directionalblur_angle0_endpoint_constraint.py
test -f refs/runtime_trace_packages/olm_runtime_trace_directionalblur_angle0_single_shot_20260710.zip
unzip -l refs/runtime_trace_packages/olm_runtime_trace_directionalblur_angle0_single_shot_20260710.zip
python3 -m json.tool refs/reference_requests/directionalblur_context_scale_20260606.json
```

Results: all three local smokes passed; the package exists and lists 23 entries;
the runtime summary has no DirectionalBlur result. No source, package, PNG, or
shared-worktree change was made by this audit.
