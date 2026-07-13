# OLM Porting Roadmap

## Scope and authority

This roadmap covers the compatibility target set: `OLMBlur`, `OLMColorKey`,
`OLMToonDilate`, `OLMDistanceGradation`, `OLMSmoother v1`, `OLMSmoother2`
(no-key and legacy/key/gamma), `OLMDirectionalBlur`, `OLMRadialBlur`, and
`OLMKiraKira`. `ColorKeep` is excluded from the compatibility target: retain it
only as a support/helper utility unless a real Windows AE Software reference
slice is explicitly commissioned. The governing definitions are in
`notes/AE_EXACT_CONFORMANCE.md`, the current state and forbidden actions are in
`notes/CONFORMANCE_LEDGER.md`, and the repository workflow is in
`AGENT_GUIDE.md`.

`OLMSmoother v1` is an endgame decision, not an early expansion lane. Preserve
its exact packaged 8bpc behavior. After the higher-priority plug-ins have
stronger 16/32bpc coverage, make one explicit decision: keep v1 as an
independent supported compatibility path and add its own references, or declare
it mapped to the supported Smoother2 behavior. Do not mix v1/v2 behavior or
spend early 32bpc budget on v1.

## Completion model

Track every feature, execution path, and bit-depth slice independently. Use one
row per `(plugin, feature, path, depth, case_set)` in the conformance ledger.
The minimum matrix schema is:

| plugin | feature/case_set | path | depth | reference_kind | runner_kind | correctness_status | host_status | work_lane | evidence/manifest | next action | owner | updated | stale_after |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

`path` must identify materially different behavior, such as CPU Software,
Zoom/Rotation/Inner, no-key versus legacy/key/gamma, or a Layer/background
mode. `depth` is `8bpc`, `16bpc`, or `32bpc`; the reference format must obey the
bit-depth policy in `notes/AE_EXACT_CONFORMANCE.md`. `reference_kind` and
`runner_kind` are never collapsed into `correctness_status`.

`AE exact` means zero-diff Mac AE output against the declared Windows AE
Software reference for that exact row. `CLI exact`, `binary-grounded`,
`guarded`, `known-red`, and `blocked` are evidence/work states, not completion.
A slice can be `AE exact` while the plug-in is not plugin-complete: plugin
completion additionally requires all declared features/paths, supported
bit-depths, host usability, manifests, binary-grounded IR, and release tests.
Conversely, a host-stable plug-in is not correct unless every declared slice is
`AE exact`.

Do not use percentages, “green,” or “complete-ish.” Report both the exact slice
count and the unclosed plugin-level rows. A plugin-level `complete` claim is
allowed only at the release gate below.

## Critical path and parallel work

The critical correctness lane is 8bpc hard-path closure and regression
preservation. The former DistanceGradation 16bpc exact-address exception is
closed locally by the 2026-07-11 OpenCV/PF16 boundary proof; do not keep a
superseded Windows request alive after its decision has been answered.

1. Preserve the `OLMDistanceGradation` OpenCV/PF16 boundary proven in
   `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.md`.
   The current 16bpc extended batch is `7/16 AE exact`, with `0010/0011`
   closed. Split its remaining 16bpc work into Layer/no-bg
   `0012/0013/0014/0016`, max-2 `0024..0027`, and outlier `0028`. Separately,
   the depth-correct current 8bpc batch is known-red `0/29`; reconstruct that
   lane from current binary-grounded field/compose rules rather than the
   historical unbound `29/29` candidate images.
2. Close `OLMDirectionalBlur` with separate angle-0 and diagonal witnesses;
   do not combine their proof or tune from broad PNGs.
3. Keep `OLMRadialBlur` Zoom, tiny Rotation, and Inner as separate lanes;
   require sampler/prepass/writeback proof before visual tuning.
4. Complete the bounded upstream producer proof for `OLMSmoother2` legacy;
   preserve exact no-key behavior and the Smooth Range fix.
5. Preserve the now-exact `OLMBlur` 16bpc cell, then expand the already strong
   `OLMColorKey` and `OLMToonDilate` slices.
6. Keep `OLMKiraKira` parked after the narrow Mode 1/2 dispatch fix until
   provenance/witness placement or the independently scoped Mode 3, Mode 4,
   Merge 2, and other endgame controls become the highest-value work.

When the 8bpc critical lane is waiting on a Windows return, a missing binary
fact, or an accepted host artifact, use the wait only for independent
16/32bpc reference acquisition, comparator work, or exact-slice regression on
`OLMColorKey`, `OLMToonDilate`, and other already-grounded paths. Do not start
new broad 16/32bpc algorithm tuning, and do not let parallel work alter the
8bpc contract or consume the active runtime-trace slot. Once the blocker
returns, the 8bpc lane resumes priority.

## Release completion gate

Release is complete only when all rows in the declared target set are `AE
exact` for every declared feature/path/depth, using canonical Windows AE
Software references and the required typed 8/16/32bpc formats; every supported
row has a reproducible manifest and comparator; binary-grounded IR records the
algorithm and writeback rules; Mac AE host load, parameter application, and
render are stable; and the release report has no unresolved `blocked`,
`guarded`, `known-red`, probe-only, stale-reference, or unverified-depth rows.
Support-only `ColorKeep` is not part of this gate, but must not be advertised as
OLM compatibility. A passing CLI, smoke, or packaged subset never satisfies
the gate.

## Evidence and stale-document policy

The latest accepted ledger row and its linked acceptance note control. A
runtime return is usable only when it delivers the exact witness requested by
its contract; otherwise record `failed_partial`, `answered_partial`, or
`superseded` and do not change source from it. The pending queue is currently
authoritative in `refs/reports/pending_runtime_trace_packages.md`.

Every status-changing result updates the ledger row, evidence link, and date in
the same change. Older reports remain historical, but must be marked or treated
as stale when a later canonical reference, verifier, intake, or acceptance
note supersedes them. An exact image set without the loaded Mac plug-in hash is
not current-binary conformance. Never revive an old count, reference,
case-number mapping, or runtime package by citation alone. If documents
disagree, use the newest accepted evidence and add a short supersession note;
do not silently rewrite history.

## Ownership and orchestration

The orchestrator owns target scope, priority, matrix schema, release claims,
stale-doc resolution, and final acceptance. A subagent owns only the explicitly
assigned plugin/path/depth lane and may edit only its declared files. A
subagent must report commands, real outputs, evidence classification, and
remaining blocker; a plan without verification is not a result.

Only the orchestrator may promote a row to `AE exact`, close a plugin, change
the target set, supersede a canonical reference, or schedule a new shared
Windows runtime slot. Subagents must not broaden a witness, resend a rejected
package unchanged, tune from PNG appearance, change a frozen lane, or edit
another worker's files. Parallel workers may prepare independent artifacts,
but the orchestrator serializes shared-folder sends, source merges, and ledger
updates. All handoffs cite repository paths and leave the worktree changes
visible for review.

Use `gpt-5.6-luna` at medium reasoning for difficult decompilation, AEX CPU
simulation, and algorithm reconstruction. Use `gpt-5.4` at high reasoning for
bounded packaging, schema checks, comparator plumbing, documentation audits,
and other lighter integration work. Model choice does not lower the evidence
bar; the orchestrator re-runs focused verification before accepting either.
