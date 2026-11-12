# Independent-case resident rendering: proposal and patch draft

Status: **AEXCompat changes are required; no resident oracle mode was added.**
This is Job B-fast-oracle's stop-point under requirement 3. Neither AEXCompat
checkout was edited or rebuilt, and no issue, PR, commit or push was made.
The oracle's implementation, public functions, CLI and tests remain unchanged.

## Finding and source scope

Read-only investigation covered `D:/Projects/01_Project/04_Tools/AEXCompat`
and, to reconcile the newer installed CLI, the corresponding source files in
`D:/Projects/01_Project/04_Tools/AEXCompat-wt-main`. The measured executable is
the oracle's existing shared harness in the latter checkout. These trees are
not interchangeable: the first checkout's CLI does not contain the installed
performance/differential commands. File hashes are recorded in
[`evidence/measurement.json`](evidence/measurement.json); source line numbers
below describe the files examined, not an assertion that all source was built.

The installed `--help` and `--print-cli-contract` were executed with
`--headless`. Raw results are in `runs/discovery/`. No GUI or AE was launched.

| Existing interface | Actual behavior | Why it cannot implement independent oracle cases unchanged |
| --- | --- | --- |
| Harness typed request routes | Inspect, open render session, render one frame, close | Repeats discovery and worker startup per side/case |
| `--render-experimental-session[-param]` | Length-one session wrapper; optional single scalar assignment | Name does not imply a persistent external protocol |
| `--render-differential` | Fixed geometry/stride/origin/extent/tile experiments; `render_variant` opens and closes its own session | No arbitrary request list, no worker reuse across variants |
| `--render-performance-diagnostics` | Four fixed sizes, four repeated time-zero frames per session, untouched defaults or one scalar override | Useful timing instrumentation; no case inputs, full typed requests, independent sequence reset or saved image artifacts |
| Broker `render-video-batch` | One session, same-size PNG list, advancing time, fixed parameters or animation | No typed per-case requests; no oracle spatial/downsample/mask/render-setting/layer context; sequence persists |
| Multifilter `render_sweep --frames N` | One continuous sequence per effect, advances time, generated input | Corpus investigation interface, not independent request replay |
| `InteractiveRenderSession` / raw `RenderSession` | Rust API supports primary pixels, per-frame parameters, UI actions and some dynamic layers | No fresh-case boundary; static dimensions/context and persistent sequence; GUI caller is out of scope |
| Closure session `swap_plugin` | Set down sequence/global state, unload effect, load/bootstrap another manifest member | Same current index is rejected; not reuse of one loaded instance; not a reset API |

Source anchors (relative to AEXCompat-wt-main unless labelled otherwise):

- `broker/crates/harness/src/windows/cli.rs`: contract at 330/336,
  performance dispatch at 1102, differential at 1206, length-one session at
  1265, typed-request discovery and dispatch at 1636–1698.
- `broker/crates/broker/src/image_render/session.rs`: wrapper opens at
  829–853 and closes at 894; final-report gate at 1254;
  `InteractiveRenderSession` begins near 1308.
- `broker/crates/broker/src/render_differential.rs`: `render_variant` at 321.
- `broker/crates/broker/src/performance_diagnostics.rs`: input pattern at 407,
  open at 432, frame loop at 484, close validation at 572.
- `broker/crates/broker/src/render_session.rs`: `swap_plugin` at 2399,
  same-index rejection at 2414, reported elapsed clock at 3640.
- `minihost/src/worker_render_session.cpp`: frame parameter override at 928,
  `if (!sequence_started)` at 1182, setdown after the entire loop at 1442.
- Original checkout `broker/crates/broker/src/render_session.rs`:
  `VideoBatchRequest` at 3420, `run_video_batch` at 3482; context trailers are
  `None`, layers empty, frame time advances and sizes must match.
- Original checkout `bridges/aviutl2-multifilter/examples/render_sweep.rs`:
  `--frames` contract at 49/260, session open at 898 and frame loop at 946.
- Read `docs/RENDER_SESSION_PROTOCOL_2026-07-19.md`,
  `docs/CLOSURE_SESSION_SWEEP_MEASUREMENT_2026-07-23.md`,
  `docs/SWEEP_INVESTIGATION_WORKFLOW_2026-08-17.md` and
  `docs/RENDER_FIXTURE.md`. Old one-shot argv references in the protocol are
  explicitly historical. Closure-sweep timings concern discovery, not this task.

## Isolation contract that is missing

Independent oracle cases represent fresh effect sequence/instance contexts,
not successive frames of an authored animation. Existing resident sessions are
appropriate for the latter, but keeping their `sequence_data` across random
oracle cases can make one case depend on another. Replaying time zero is not a
sequence reset. Re-submitting every discovered default is also wrong: KiraKira's
declared Gain 0.1 is outside its accepted edit range and differs from the
effective untouched value. Arbitrary defaults may own handles rather than plain
copyable values.

The proposed mode retains the loaded module, dependencies, `global_data`, and
global setup across cases, as an AE host can for separate effect instances.
It must freshly initialize instance parameters and sequence state per case;
classic frame setup/render/setdown or SmartFX pre-render/render and their
cleanup run according to the existing route. It must never send Classic render
to an effect declaring SmartFX merely to obtain a faster path.

DLL statics, TLS, plug-in internal caches, global suite leases and allocator
history remain shared. They cannot be reset generically without unloading or
restarting. Consequently **fresh sequence is not process isolation**, and even
correct AE-like lifetimes do not promise per-process byte identity for a
stateful or undefined-memory plug-in. Qualification must demonstrate equivalence
for the admitted corpus; native AE conformance is not claimed here. Keep the
per-process oracle as default and diagnostic authority when investigating a
resident mismatch. Never silently replace mismatching resident evidence with a
successful per-process retry.

Host-owned frame worlds, checkout receipts, pre-render data, instance handles,
parameter edits, UI return messages and diagnostics must not carry between
cases. Reinitialize them through existing ownership-aware constructors and
destructors. A `memcpy` of parameter definitions containing arbitrary handles,
or zeroing counters while leaving resources alive, is not an implementation.
Global-owned resources may persist; validate case-local resources against an
ownership-scoped baseline, not a blanket zero suite-reference count.

## Minimal external API

Add a finite headless command rather than a daemon:

```text
aexcompat-harness --headless --render-request-batch <manifest.json>
```

Example proposed manifest (paths are absolute; existing request JSON is reused):

```json
{
  "schema": "aexcompat.independent_case_batch",
  "schema_version": 1,
  "plugin": "D:/originals/OLMBlur.aex",
  "route": "smart8",
  "isolation": "fresh_sequence",
  "frame_deadline_ms": 120000,
  "cases": [
    {
      "id": "case-0000-smart8/reference",
      "input": "D:/run/case-0000-smart8/input.png",
      "request": "D:/run/case-0000-smart8/requests/reference.json",
      "output": "D:/run/case-0000-smart8/reference.png"
    }
  ]
}
```

The first implementation accepts a bounded, homogeneous list: one plug-in,
route/depth, dimensions, static host context, timing scale/step/total time,
secondary-layer bindings and render settings. Primary pixels, explicit typed
assignments and current time may differ. Every request's omitted parameters
mean that case's untouched defaults. Resolve layers by the existing request's
parent-directory convention, not the batch manifest's location. Reject duplicate
case IDs/output paths, malformed/oversized manifests, unavailable routes and
incompatible static context before starting the affected session. Reuse the
existing parser and validation, including out-of-range edit rejection.

This restriction is deliberate minimal scope: an oracle adapter can partition
by the exact static key and preserve original case IDs. Layer content identity
belongs in that key; a change at the same filename is a change. Cases with
unique secondary layers may get no reuse initially. Never coerce dimensions,
drop an extent/downsample or promote a depth to keep a worker alive. Static-key
changes require explicit close/reopen with a new session generation. Hashes
record observations/cache identity; they must not introduce AEXCompat launch
approval or enforced pre-selection gates.

Use a new advertised worker capability and a versioned `render_case` message,
not an unrecognized flag on `render_frame`. The worker performs exactly one
fresh instance/sequence lifecycle, sends case-local diagnostics and a result
only after sequence cleanup, then is ready for another case. Old workers must
be detected and rejected as unsupported before dispatch. No fallback on an
old worker, unknown message or failed invariant.

Final JSON contains each stable ID, outcome/error classification, requested
and actual route, dimensions/origin, artifact paths and hashes, loaded plug-in
and worker identities, session generation/PID, case index, per-stage timings,
case cleanup and final session-close status. Deep output uses the existing
`.rgba16le` / `.rgba32f-le` writers and ordering, not preview PNGs. Per-case
successes remain provisional until final global/session close validates. On a
failed close retain artifacts, invalidate the batch evidence, and label it
incomplete. Preserve legal empty results explicitly.

## Patch draft (not applied or compiled)

This is an implementation sketch against the examined sources, not a patch
claimed to compile. New helper names below denote work to implement. Leave
existing video/interactive/frame APIs and their lifetime defaults unchanged.

```diff
--- broker/crates/harness/src/windows/cli.rs
+++ broker/crates/harness/src/windows/cli.rs
+ // Advertise --render-request-batch in --print-cli-contract.
+ // Parse strict bounded manifest; inspect once per plugin identity.
+ // Resolve each existing typed request with its own base directory.
+ // Clone metadata, NOT previous case values; preserve untouched defaults.
+ // Preflight compatible static contexts and unique output destinations.
+ // Dispatch to independent_case_batch::run; print structured final result.

--- broker/crates/broker/src/lib.rs
+++ broker/crates/broker/src/lib.rs
+ pub mod independent_case_batch;

+++ broker/crates/broker/src/independent_case_batch.rs
+ // New CaseBatchRequest / CaseEntry / CaseResult, strict serde schemas.
+ // Reuse typed-request validation extracted from the harness, and existing
+ // image conversion, output writers and close validators. No alternate host.
+ // One inspect + one RenderSession open; process cases serially; close once.
+ // Retain sidecars and only finalize evidence after validated session close.

--- broker/crates/broker/src/render_session.rs
+++ broker/crates/broker/src/render_session.rs
+ pub fn render_case(&mut self, case_id: &str, current_time: i32,
+                    rgba: &[u8], parameters: &[InteractiveParameter])
+                    -> io::Result<CaseOutcome> {
+     // Require advertised fresh-sequence capability; validate before send.
+     // Share existing slot generation, deadline, bounds and process watching.
+     // New versioned message includes case_id + complete explicit edits.
+     // Verify case_done belongs to this case/generation and cleanup succeeded.
+ }

--- minihost/src/worker_render_session.hpp
+++ minihost/src/worker_render_session.hpp
+ // Versioned render_case/case_done schema and FreshCaseLifecycle owner.
+ // Additive capability: default render_frame behavior remains persistent.

--- minihost/src/worker_render_session.cpp
+++ minihost/src/worker_render_session.cpp
+ // In control loop, strictly distinguish render_case from render_frame.
+ // FreshCaseLifecycle starts from pristine instance parameter ownership,
+ // preserving global_data. Apply THIS case's explicit edits only.
+ // Use the same first-frame ordering as the length-one wrapper:
+ // SEQUENCE_SETUP, existing frame dispatch, frame cleanup, SEQUENCE_SETDOWN.
+ // Route every error/early-return through one cleanup epilogue.
+ // Do not publish output generation or case_done success before that epilogue.
+ // Retire instance state; clear both in/out sequence pointers; validate
+ // case-local ownership deltas; snapshot diagnostics before resetting them.
+ // Setup/setdown error or invariant violation poisons the session; no next case.
+ // A frame error is reusable only after proven clean instance/sequence teardown.
```

Extract the typed-request parser from `windows/cli.rs` into a shared module
without changing its existing call sites' behavior; do not duplicate its
untouched-default, relative layer or conformance-setting logic. Factor instance
parameter initialization/retirement from the existing worker parameter/runtime
and render wrappers. Extend worker protocol parsing and native self-tests with
the same schema. The existing close report checks expect one sequence setup/
setdown: add explicit per-case totals/errors for this capability; retain the old
checks for normal sessions. Do not overwrite an earlier nonzero error with a
later success.

Required new measurements: inspect, dependency preparation, worker launch and
ready, plug-in bootstrap, instance initialization, sequence setup/setdown,
frame setup/render/finalize, artifact I/O and final close. Current timings do
not isolate DLL load from global setup. Keep these clocks explicitly nested.

Proposed oracle adapter, only after AEXCompat implements the capability:

1. Add opt-in `render --resident`; retain existing API signatures, case plans,
   request bytes, `run_case`/`evaluate_case`, replay and default process mode.
2. Prepare all artifacts exactly as today, partition homogeneous cases by side
   and static key; reference and candidate never share a worker, even when their
   paths/hashes match. Preserve order within each group; record grouping/order.
3. One global semaphore caps active render workers at `--jobs` (1..3), including
   both sides. Bound group length to limit retained memory; record every recycle.
4. Run each finite batch under the existing private Windows Job ownership.
   Keep per-case watchdogs and a separately stated batch deadline; a 120-second
   *case* timeout must not accidentally become a 120-second whole-campaign cap.
5. Adapt structured side outcomes into the existing exact/mismatch/reference
   timeout/reference unrenderable/candidate failure/tool error summaries.
   Report interrupted and unattempted cases, retain completed artifacts, and
   verify owned descendants exited on success, error, timeout and Ctrl+C.

## Required behavioral tests before integration

- A synthetic stateful Classic/Smart fixture increments sequence state and
  retains global state. Two `render_case` calls must each see fresh sequence
  state while one load/global setup/PID persists. `render_frame` must continue
  seeing persistent sequence state. Assert selector order and balanced teardown.
- A/B/A case order and explicit-edit → untouched-default transitions for scalar,
  popup, checkbox, color, point/angle, layer and arbitrary-owned defaults;
  include KiraKira's invalid declared default without serializing it as an edit.
  Mutating earlier parameter arrays must not change later defaults.
- Reject incompatible size/downsample/extent/settings/layer data before sending
  a frame; prove correct new generations for deliberate close/reopen groups.
- Verify exact 8-bit samples and native 16/32-bit words, including NaN payloads
  and signed zero, cropped/origin/empty-output dimensions and artifact ordering.
- Inject setup, render, setdown, serialization, worker-exit, deadline, stale-slot,
  ownership and final-global-close failures. No stale pixels or missing cases
  become success; no poisoned worker receives another case. Verify Job cleanup.
- Keep existing session, fixture, interactive and oracle tests intact.
- Qualification gate: fixed seed 20261112, saved identical requests/inputs,
  all ten originals on declared CPU routes/depths and downsample 1, 1/2, 1/4.
  Compare process-reference vs resident-reference **and** process-candidate vs
  resident-candidate for the same actual staged Rust binaries, as well as normal
  reference/candidate comparisons. Report every failure and timeout. Add reversed
  and A/B/A order checks. Known original nondeterminism requires retained repeated
  witnesses and exclusions under existing policy, never blanket case removal.
  Record exact successful bytes and failure-class equivalence separately.
- Measure campaign wall time and side/case medians with identical artifacts,
  concurrency and requests, including startup, parsing, I/O and close. Repeated
  frame diagnostics alone do not pass either the equivalence or speed gate.

## Measurements and expected gain

See [`README.md`](README.md) for the real run and complete limits. All values
below are medians, serial jobs=1, no outlier removal. The 33 case pairs are
original-vs-itself defaults, seed 20261112 input seeds, **not Rust equivalence**.

At 97×61, most originals take 422–430 ms per side; DistanceGradation 492.5 ms,
KiraKira 796 ms. OLMBlur at 320×180 takes 422 ms. In that last case the report's
`worker_diagnostics.elapsed_ms` is 101 ms and the outside residual is 321 ms.
The elapsed field is a **broker session clock** (`opened` is set when the
session object is constructed; clock ends after close/exit collection), not
plug-in CPU time or a full DLL-loading stopwatch. The benchmark field named
`render_worker_lifetime_ms` retains that raw reported clock with this definition.
The residual includes harness startup, discovery, open preparation and I/O; it
must not all be attributed to process creation. Separate controls measured
78 ms for help and 250 ms for OLMBlur inspection (including harness startup).
The oracle's preparation/comparison/cleanup overhead outside the two recorded
process clocks was 15.85 ms median per pair over the 33 pairs. These control
medians overlap other intervals and must not be summed as independent phases.

Existing OLMBlur Smart8 performance diagnostics, three invocations, 12 sessions,
48 frames, have these measured internal timings:

| Size | Session open ms | Cold frame ms | Warm frame ms | (open + cold) / warm |
| --- | ---: | ---: | ---: | ---: |
| 320×180 | 63.570 | 43.191 | 9.855 | 10.83× |
| 640×360 | 65.456 | 55.221 | 22.604 | 5.34× |
| 1280×720 | 63.500 | 110.979 | 75.762 | 2.30× |
| 1920×1080 | 64.237 | 207.330 | 164.129 | 1.65× |

At 320×180 the warm frame includes 0.0186 ms input write, 0.0131 ms worker
setup, 9.6092 ms worker render (including 4.6159 ms render selector),
0.1142 ms finalize and 0.0532 ms output verification. The remaining approximately
0.0466 ms is the residual of these independently aggregated medians, not a
direct scheduling measurement. The selector is nested in worker render.
Sequence initialization, output PNG encoding and fresh-case teardown are not
included in this warm cost. The diagnostic uses opaque normalized XY/XOR
pixels and no explicit oracle conformance context; baseline inputs include
noise and transparent pixels. Timing differences are not an equivalence proof.

An illustrative large homogeneous batch model uses 422 ms for its first side
render and `9.8549 + D` ms for each subsequent side render, where **D is the
unmeasured** fresh-instance/sequence/reset, request/artifact I/O and context
difference cost. For 1,000 pairs, one group per side:

| Assumed D | Estimated batch time | Estimated speed-up over 844 s process time |
| --- | ---: | ---: |
| 5 ms | 30.52 s | 27.65× |
| 20 ms | 60.49 s | 13.95× |
| 50 ms | 120.43 s | 7.01× |

Formula: `2 * (422 + 999 * (9.8549 + D)) / 1000` seconds. These are sensitivity
estimates, **not measured independent-case throughput or guaranteed bounds**;
final close and oracle orchestration still need measurement. More static groups,
unique layer inputs, expensive parameters and memory-triggered recycling reduce
the gain. Existing diagnostics flag memory growth for this short run; do not
assume thousands of frames fit in one process. The observed 10.83× internal
ratio demonstrates a worthwhile opportunity, while the isolated-case speed-up
and all-ten resident/reference/candidate equivalence remain unverified until
the proposed upstream capability exists.
