# OLMColorKey Replace + Edge Orchestration 20260716

- Status: **pass_static_runtime_blocked**
- Scope: static AEX control flow plus Mac source/build guard; no AE-exact claim.

## Evidence

- Source guards removed: Thin=True, Blur=True.
- Static AEX branch proof: **pass**; Replace flag reads are absent from the Edge orchestrator.
- Static event order: `['0x1800095ff', '0x180009625', '0x18000983c', '0x1800098cc']` (keyer, Thin boundary, Blur boundary, Blur apply).
- Isolated arm64 build: **pass**.
- Actual AEX orchestrator runtime: **blocked**.
- Controls Replace=1/Thin=0/Blur=0, Replace=0/Thin=0/Blur=0, and Replace=1/Thin=1/Blur=1: **blocked/unexecuted** because the entry faulted before stage hooks.
- Fixture: opaque green 5x5 background, opaque red keyed center, blue replacement; Thin +1 distance 2 and Blur 2 distance 2 Around.
- Combined-on required order: replacement write `0x18000291a`, Thin `0x180009625`, Blur boundary `0x18000983c`, Blur apply `0x1800098cc`.

## Fail-Closed Boundary

The static lane proves that Replace cannot skip the Edge orchestrator and that the calls are ordered keyer -> Thin -> Blur. The runtime lane remains blocked until the real entry returns with all control/order conditions; no pixel output is promoted as proof.
