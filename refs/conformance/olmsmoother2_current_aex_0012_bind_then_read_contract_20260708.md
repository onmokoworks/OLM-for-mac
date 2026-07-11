# OLMSmoother2 Current-AEX 0012 Bind-Then-Read Contract

Date: 2026-07-08

## Why this note exists

The latest producer-byte return was `failed_partial`:

- `refs/conformance/olmsmoother2_current_aex_producer_bytes_return_intake_20260708.md`

That return preserved local Mac/Unicorn sweeps, but it did not preserve a fresh
same-run Windows stop with typed producer bytes. The next Windows request should
therefore optimize for "can the debugger hold one witness-local stop?" rather
than "can it cover both unresolved lanes in one package?"

## Decision

Yes: the next Windows runtime request should narrow to `legacy_case_0012_gamma5_red_blue_current_aex`
at `(91,841)` first, not `0012 + 0004` together.

Reasons:

1. `0012` has the smaller discriminant. The local unresolved branch is already
   narrowed to three class/producer bytes plus the `FUN_18000e170` bitsum `c`.
2. `0012` does not need the wider `0004` scanner-span and class-prev-byte3
   state space to become informative.
3. The latest failure mode was "no retained same-run Windows stop," not "wrong
   interpretation of returned Windows values." Reducing to one lane lowers hit
   storm risk.
4. `0004` remains valid follow-up work, but it is the broader lane: it may need
   scanner spans, `class_prev_b3`, emit/no-emit, polygon count, and possibly
   `cce0` output state before it becomes decisive.

## Local witness to test on Windows

Target:

- case: `legacy_case_0012_gamma5_red_blue_current_aex`
- pixel: `(91,841)`

Local Mac/Unicorn witness:

- `center_b0 = 0`
- `prev_b0 = 1`
- `left_b1 = 0`
- `FUN_18000e170` bitsum `c = 2`
- `FUN_18000f270`: append
- `FUN_18000e3a0`: append

The only local three-byte `f270` no-append pattern in the current sweep is:

- `center_b0 = 0`
- `prev_b0 = 0`
- `left_b1 = 1`
- `c = 4`

This makes `0012` the cleanest next Windows stop: one retained same-run byte
read can decide whether Windows agrees with the current Mac producer input or is
already on the suppressing `c=4` family.

## Required request shape: two-stage bind-then-read

Do not ask Windows to "capture bytes and downstream append state" as one broad
step. Ask for two explicit stages in the same run:

### Stage A: bind the live producer/class buffer

Goal:

- prove the callback stop can bind the exact `0012 (91,841)` witness in the
  current AE Software run
- identify the concrete Windows buffer/address that backs:
  - center pixel class byte 0
  - previous pixel class byte 0
  - left pixel byte 1

Minimum return for Stage A:

- module base
- exact hook address / breakpoint site used
- exact case id and pixel xy held at that stop
- the concrete base/pointer/address arithmetic used to recover the three bytes
- the exact failed bind reason if the witness-local stop still cannot be held

### Stage B: read typed bytes and immediate branch value from that bound stop

From the Stage A-bound stop, read in the same run:

- `center_b0`
- `prev_b0`
- `left_b1`
- observed `FUN_18000e170` bitsum `c`

Nice-to-have only after the four fields above are captured:

- whether `FUN_18000f270` appends or suppresses
- whether `FUN_18000e3a0` appends or suppresses
- `cce0` output floats before final u8 packing

## Stop condition

The request should stop successfully at the first same-run Windows `0012` stop
that returns:

- exact witness xy binding, and
- the three typed producer bytes plus `e170 c`

That is enough to classify whether the active Windows divergence is already
present at the compact producer-byte stage.

## Acceptance

`answered`:

- Stage A binds the exact `0012 (91,841)` witness in a live Windows run, and
- Stage B returns `center_b0`, `prev_b0`, `left_b1`, and observed `e170 c`

`answered_partial`:

- Stage A succeeds and the return includes the exact address/pointer recovery
  route for the witness bytes, but Stage B cannot yet read all four typed
  fields; or
- the run fails to hold the witness-local stop, but returns the exact failed
  breakpoint/watchpoint condition plus the nearest bound pointer context needed
  for the retry

`failed`:

- broad breakpoint hit counts only
- local Mac/Unicorn facts restated as if they were Windows facts
- final writer bytes/floats only
- a combined `0012 + 0004` package that again returns no retained same-run
  Windows witness stop

## Deferred lane

Do not drop `0004`; just do not spend the next request on it.

`0004 (1903,519)` should return only after `0012` either:

1. proves a concrete Windows producer-byte difference, or
2. proves that this narrower bind-then-read method works and can be reused for
   the wider scanner/class-prev lane.

## Boundaries

- Do not change `mac/OLMSmoother2` from this contract alone.
- Do not promote local Unicorn-only producer facts to Windows truth.
- Do not ask for final writer bytes again; that stage is already grounded.

## Inputs

- `notes/CONFORMANCE_LEDGER.md`
- `refs/conformance/olmsmoother2_current_aex_producer_bytes_contract_20260708.md`
- `refs/conformance/olmsmoother2_current_aex_producer_bytes_return_intake_20260708.md`
- `refs/conformance/olmsmoother2_producer_branch_sweep_20260708.md`
- `refs/conformance/olmsmoother2_producer_branch_sweep_20260708.json`
- `tools/emulation/SMOOTHER2_PRODUCER_EMU_REPORT.md`
