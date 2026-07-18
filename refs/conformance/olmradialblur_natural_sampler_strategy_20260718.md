# OLMRadialBlur natural sampler strategy

- Status: `pass_read_only_strategy_gate`
- Checkpoint RIP: `0x18000af9a`
- Instructions executed: `10974651817`
- Estimated remaining worker cells: `1786739`
- Final sampler: `0x180005e68`
- Progress sidecar: `/tmp/olm_radialblur_natural_progress_long2_row_20260718.json`
- Bounded progress observation: `14 hook hits`, monotonic=`True`

## FACT

- The checkpoint uses the natural full render path.
- The current RIP is inside the scatter worker, not the final sampler.
- The worker increments R14D at 0x18000b0b4; the runner observes at 0x18000b0b7 after that increment and before DEC R15D.
- The worker stores the next outer row at 0x18000b0f1; the low-overhead row mode observes at 0x18000b0f9 after that store and before the next row-loop compare.
- The final sampler callsite is downstream of worker completion and is present in the disassembly.
- The checkpoint header does not contain the outer worker row; the row used for the estimate is an external witness supplied to this audit.
- The checkpoint callback list contains no progress code-hook address; AexLoader validates host callbacks, while the cell/row observation hook is installed by the fresh runner.

## INFERENCE

- A single uninterrupted resume is the only direct route to an unmodified final sampler call.
- Checkpoint frequency alone cannot reduce CPU work; it only improves restartability.
- A safe acceleration candidate is row-slice parallelism, but it requires a new proof that worker slices write disjoint planes and have no shared reduction or synchronization.
- The natural runner can reduce its own callback overhead with --hook-mode row, which observes 0x18000b0f9 once per outer-row transition; this changes observability only and does not accelerate the AEX algorithm itself.
- Because the observation code hook is not serialized in the checkpoint callback list, switching from cell to row mode on a compatible checkpoint is a loader-topology-neutral observation change; the AEX memory/register state remains the checkpoint source of truth.
- Until row-slice independence is proven, no worker detour, state rewrite, or parallel fresh process is safe.

## Safe Sequence

A [completed_in_runner]. Use the Radial-only runner's read-only hook at 0x18000b0b7 for cell witnesses, or --hook-mode row at 0x18000b0f9 for low-overhead progress; both use the existing checkpoint mechanism for any stop.
B [completed]. Run a short continuation from this checkpoint to confirm the post-increment hook sees monotonically increasing row/cell state and does not change memory or registers.
C [blocked_on_B]. Use disassembly plus two bounded differential runs to prove whether row slices are disjoint. Only then consider parallel fresh processes from the same natural pre-worker checkpoint.
D [blocked_on_B_C]. Resume the natural path to 0x180005e68 only after A-C pass; record the sampler call arguments and final writer separately.

Row estimate source: external checkpoint-stack witness supplied via `--worker-row`; it is not present in the checkpoint header.

Boundary: Natural checkpoint state and worker boundary are verified; this is not sampler reachability, Windows equivalence, or AE exactness.
