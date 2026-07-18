# OLMRadialBlur row-slice independence proof

- Status: `pass_row_slice_independence_with_two_phase_barrier`
- Production source changed: `no`
- Parallel runner started: `no`
- Protected PID stopped: `no`

## FACT

- FUN_1800056f0 caps omp_get_max_threads() at 32 but executes B150 slices in a serial loop.
- The caller starts A9D0 only after the complete B150 loop, creating a required phase barrier.
- B150 reads source rows and immutable kernel tables and writes only current-row output ranges.
- A9D0 reads current-row source/valid/accumulation values and updates only current-row accumulation/max ranges.
- Neither worker contains a CALL instruction, atomic, lock, or shared reduction in the audited function body.
- Existing bounded natural-AEX replay evidence covers 196 words and span families 2/3/inner1.

## Required Schedule

1. Partition `[0,H)` into contiguous half-open row ranges.
2. Run `FUN_18000b150` for all ranges concurrently, then join.
3. Run `FUN_18000a9d0` for all ranges concurrently, then join.
4. Keep the existing normalization and final sampler after the second join.

## INFERENCE

- Row slices are safe to run concurrently within each worker phase when pointer-range guards pass.
- The output of B150 is an input to A9D0, so a two-phase join is mandatory.
- The artifact does not authorize changing the production plug-in or claim AE exactness.

## Fail-Closed Conditions

- do not parallelize B150 and A9D0 as one mixed phase
- do not omit the join between B150 and A9D0
- do not omit the join before normalization or sampler
- do not run when any input/output pointer range aliases unexpectedly
- do not claim AE exactness from this artifact

## Bounded Evidence

- Natural B150 replay: 196 actual-AEX RGBA/scalar words matched an independent float32 oracle.
- Natural span matrix: Outer spans 2 and 3 plus Inner span 1 matched the bounded oracle.
- These are bounded emulator facts, not Windows or Mac AE exactness.

Report JSON: `refs/conformance/olmradialblur_row_slice_independence_20260718.json`
