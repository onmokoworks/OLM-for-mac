# OLMSmoother2 legacy key producer actual AEX - 2026-07-16

- Verdict: `ANSWERED_WINDOWS_ACTUAL_AEX_LEGACY_KEY_PRODUCER`
- Corrected summary JSON:
  `refs/reports/runtime_trace_summary_windows_witness_olmsmoother2_legacy_key_producer_common_core_20260716_20260716_150855.json`
- Accepted return:
  `refs/windows_returns/20260716/20260716_142500__RETURN__OLMSMOOTHER2_LEGACY_KEY_PRODUCER_INPROCESS/RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.zip`
- Corrected descriptor return:
  `refs/windows_returns/20260716/20260716_150500__RETURN__OLMSMOOTHER2_RDX_DESCRIPTOR_CORRECTED/RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.zip`
- Corrected return SHA-256:
  `8c031837ac6a2e95fec657cd444ca303ba3c8fb66bf2235f3c038b37e207efcf`
- Witness: `legacy_case_0012_gamma5_red_blue_current_aex`, corrected sample
  `x=92`, `y=841`, `idx=105`, renderer `Software`, `project_bpc=8`
- Live `RDX p2[0..5]` descriptor:
  `92,841,1,92,842,2`
- AEX SHA-256:
  `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`

## FACT

- The corrected in-process Windows run answered
  `olmsmoother2_legacy_key_producer_inprocess_20260716` with same-run identity
  fields: `ae_pid=59192`, `module_base=0x7ffa99cd0000`, and
  `run_id=smoother2-legacy-producer-inprocess-fcefd3f4d8b9410b93ede5dff562675b`.
- The live bind expression is
  `writer_xy_anchor_then_producer_return_address` at writer hook
  `+0x350b`, using `rsp+0x34_x_rsp+0x38_y` as the pointer context.
- The exact observed call/event order is:
  1. `bind`
  2. `f270_entry` (`hook_rva=f270`, `return_address=0x7ffa99cdff5b`)
  3. `e170_entry` (`hook_rva=e170`, `return_address=0x7ffa99cdf284`)
  4. `e170_return` (`return_site=f284`, `return_rax=0x7`, `e170_c=7`)
  5. `e3a0_entry` (`hook_rva=e3a0`, `return_address=0x7ffa99cdff5b`)
  6. `e3a0_return` (`return_site=e420`, `return_low=1`)
  7. `f270_return` (`return_site=ff5b`, `return_low=1`)
- The live class-plane addressing is
  `class_base=[RCX+0x18]=0x1c09a160100` and
  `class_stride=[RCX+0x28]=0x1e00`.
- The corrected rerun proves the live descriptor and predicate bytes feeding
  the observed `e170` call:
  - live `RDX p2[0..5]`: `92,841,1,92,842,2`
  - corrected sample `x=92`, `y=841`
  - center bytes: `255,255,0,255` with `center_b0=255`
  - previous-row bytes: `255,0,0,0` with `prev_b0=255`
  - left-neighbor bytes: `0,255,0,255` with `left_b1=255`
- The accepted live result is `e170_c=7`. This supersedes the older local-only
  `c=2` witness as the actual Windows return value for this target.
- These corrected bytes prove that the live Windows `e170` predicate matches
  the observed `c=7` return.
- `e3a0_return` and `f270_return` both report the same typed vertex payload:
  `vertex_count=1`, `vertex_storage=0x908f6ff8a0`,
  `first_vertex_rgba_words=3e3ce706,3e3ce706,3e3ce706,3f2eaeaf`,
  `weight_word=3e91a7b9`.

## Superseded Collector Error

- The collector hardcoded `x=91`, `y=841` for the class-byte address
  calculation and hardcoded the descriptor emitted by `bind`; it did not read
  the live `param_2` / `RDX p2[0..5]` tuple for those fields.
- That older collector output is superseded by the corrected rerun above and
  must not be used as the live input proof.

## INFERENCE

- Interpreting the returned words as big-endian IEEE-754 float32 gives a first
  vertex of approximately
  `[0.18447503, 0.18447503, 0.18447503, 0.68235296]` with weight
  `0.28448275`.
- With the corrected `RDX` tuple and predicate bytes in hand, the remaining
  divergence moves upstream to descriptor/dispatch selection versus the current
  Mac local descriptor `91,841,1,91,843,5`.

## Next Action

1. Capture the `d3b0` and `da50` stop-predicate bytes around `x=91..93`,
   `y=840..844` in the same Windows run. The local `92,841` probe produces
   descriptor `92,840,1,92,843,2`, so origin selection alone does not explain
   the Windows `92,841,1,92,842,2` descriptor.
2. Compare those bytes against the local class plane and patch the first
   proven class-plane or scan-input mismatch.
3. Rerun the bounded legacy witness and keep `0004` separate.

## Claims Not Made

- No claim that OLMSmoother2 legacy is `AE exact`
- No claim that `0004` is solved
- No claim that raw word decoding alone proves semantic source-coordinate
  ownership
- No claim that the older local `c=2` witness was useless; it remains a local
  predecessor, not the live Windows truth
