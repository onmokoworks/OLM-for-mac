# OLMSmoother2 host class-neighborhood trace (2026-07-12)

## Purpose

The current-AEX `case_0012` residual is localized to the producer/cardinal
decision, but the earlier Mac AE trace contained only the target class bytes.
The bounded env-gated host trace recorded the complete 5x5 class-plane and setup
RGBA neighborhood around the requested pixel.

## Scope

- Diagnostic only; inactive unless `OLM_SMOOTHER2_HOST_TRACE` and target
  coordinates are set.
- The instrumentation was removed from the production render path after this
  evidence was captured; reproduction belongs in a dedicated harness.
- No class generation, polygon, compositing, or writeback behavior changed.
- The additional evidence can validate the local cardinal descriptor before
  comparing it with the pending same-run Windows class/config witness.

## Verification

- `python3 refs/scripts/smoke_olmsmoother2_host_class_neighborhood.py`: PASS.
- Universal arm64/x86_64 Debug plug-in build: `BUILD SUCCEEDED`.
- Mac AE `26.3x87`, 8bpc, working space `None`, linear blending off, Software
  render completed for `legacy_case_0012_gamma5_red_blue_current_aex`.
- Captured log:
  `refs/conformance/olmsmoother2_case0012_class_neighborhood_20260712.log`
  (`sha256 fa447e6f7e76d9accc5422aff868a602da93744ee6e95eb8c5dbf3e2bd1fe527`).
- The 5x5 capture contains 25 `class_neighbor` records. The target remains
  `class=0,255,0,255`, `polygon count=1`, orchestrator alpha `0.3549245`, and
  Mac AE output `[32,32,32,91]`; this reproduces the prior residual while
  adding the missing local descriptor inputs.

This is not an AE-exact promotion and does not justify a production fallback.
