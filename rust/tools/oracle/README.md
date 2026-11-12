# AEXCompat bit-exact oracle

`olm_oracle.py` compares any two inspectable effect `.aex` files through the
Windows AEXCompat CPU harness. It never modifies or copies the plug-ins, installs
into AE, or launches AE. This is **AEXCompat evidence, not native AE conformance**.

This directory is Python-only: there is deliberately **no Cargo.toml**. If the
parent Cargo workspace uses `members = ["tools/*"]`, its owner must exclude
`tools/oracle` or narrow that glob. Job F-oracle does not edit the workspace.

## Requirements and usage

Python 3.11+, NumPy and Pillow. Tested with Python 3.11, NumPy 1.26.4 and Pillow
10.3.0. `unittest` is sufficient; pytest is optional. The default harness is
`D:\Projects\01_Project\04_Tools\AEXCompat-wt-main\broker\target\release\aexcompat-harness.exe`.
Pass `--harness` to select another build. All paths passed to the harness are
absolute, and every invocation includes `--headless`.

From the repository root, in PowerShell:

```powershell
$original = 'D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex\OLMBlur.aex'
$candidate = 'D:\build\OLMBlur.aex'
python rust/tools/oracle/olm_oracle.py inventory --reference $original --candidate $candidate --out rust/tools/oracle/runs/inventory
python rust/tools/oracle/olm_oracle.py render --reference $original --candidate $candidate --cases 20 --seed 20261112 --jobs 4 --downsample 1,1/2,1/4 --out rust/tools/oracle/runs/comparison
python rust/tools/oracle/olm_oracle.py replay rust/tools/oracle/runs/comparison/case-0003-smart32
```

Output directories must be new, preventing old artifacts from being mistaken
for current results. Render's default destination is a timestamp under `runs/`.
Inventory prints a field-by-field diff; `--out` additionally retains its JSON.
Render and replay always write `summary.json` and a short route table.

Additional render options:

| Option | Meaning |
| --- | --- |
| `--routes smart8,smart16,smart32,classic8,classic16,classic32` | Default route list; undeclared routes are `not_applicable` |
| `--sizes 1x1,3x7,97x61,256x144` | Default cyclic size list, including odd dimensions |
| `--downsample 1,1/2,1/4` | Cycle these exact rational preview scales; default `1` |
| `--extent 0,0,3,7` | SmartFX output demand rectangle `[left,top,right,bottom]`; use SmartFX routes only |
| `--timeout 120` | Default seconds per render/replay process; inventory defaults to 60. Self-test also defaults to 120; use an explicit override for shorter probes |
| `--force-classic` | Non-AE debug only: allow classic8/16 probes of a SmartFX effect; labelled `non_ae_debug` in JSON and the table |
| `--jobs N` | Concurrent route-cases; default half the logical CPU count, minimum one |
| `--perturb-candidate 1=0.5` | Debug negative control: add 0.5 to candidate numeric slot 1; repeatable option |

Perturbations are never clamped. New case plans record numeric bounds and reject
out-of-range perturbations before dispatch; older replay plans without bounds
still rely on harness validation. Neither rejection proves a pixel mismatch.
An explicit perturbation can materialize an otherwise untouched numeric default.
Use a small in-range offset and a
nontrivial size; the self-test uses OLMBlur's default amount 5, offset +0.5,
97x61 input and all three SmartFX depths.

Exit codes: **0** means all attempted comparisons exact; **1** means inventory
differences, pixel mismatches, or a candidate failure when the reference rendered;
**2** means an incomplete comparison (reference unrenderable, reference timeout, tool/setup error).
Mismatch status takes precedence over incomplete status. When both sides fail,
the case is `reference_unrenderable`; side-specific harness failure counts still
include both failures. An unsupported route is never counted as an exact case.
`reference_timeout` is separate from `reference_unrenderable`: reaching a time
budget does not establish that the reference cannot render. `timeout_seconds`
is recorded in render/replay summaries. No extrema are dropped or clamped to
make the comparison finish faster.
The child environment also sets `AEXCOMPAT_FRAME_DEADLINE_MS` to the timeout in
milliseconds (within the harness's supported 1000..600000 ms range). Without
this override the installed harness has an independent **30000 ms** frame
deadline, even if its parent allows 120 seconds. Overrides are recorded in each
process log and the summary and do not modify the calling shell's environment.
Both outer-process timeouts and reported internal `frame_deadline` expirations
are classified as `reference_timeout`. The outer bound includes process startup.
Ctrl+C cancels queued work, stops owned running jobs and returns **130**; a render
already underway retains an incomplete summary with `cancelled: true`.

## Comparison and generation contract

Inventory runs both `--inspect-experimental` and
`--inspect-experimental-with-deps <aex> <aex-parent>`. Every field of every
parameter record is compared, including hidden/disabled parameters, controls,
components, choices and arbitrary-data summaries. Host comparison additionally
covers reported parameter count, parameter metadata (including UI vs host
ranges), advertised `out_flags`/`out_flags2`, SmartFX/audio flags, plug-in kind,
plug-in data, and any exposed PiPL diagnostic fields. Raw diagnostics are saved.
Binary identity, dependency lists, elapsed times, PIDs, memory addresses and
callback traces are retained evidence, not compatibility fields. This harness
does **not** expose a complete PiPL descriptor through these inspection commands;
the oracle does not claim to verify unexposed match names/category/version data.

The first three cases select defaults, minima and maxima. Remaining numeric
assignments sample their complete declared host ranges with additional min/max/
default choices. Popups use the declared integer range; colors cover byte
endpoints/defaults and random ARGB bytes. Angle/point inventories do not expose
component ranges: the tool uses defaults, zero, point components interpreted by
the harness as **percent of layer extent**, +/-360 degree
angles and bounded random point components. The generator derives some numeric
point values from the image dimensions, but does not convert pixels to percent:
(97,61) therefore means (97%,61%), not pixel (97,61). To target a full-resolution
pixel explicitly, use `[100*x/full_width, 100*y/full_height]` for both sides. Secondary layer parameters receive their
own deterministic PNGs. UI-only, arbitrary-data and path parameters keep their
declared defaults; `cases.json` lists all unassigned slots and reasons. There is
no guessed serialization for custom data or authored masks.

**Untouched-default semantics:** after selecting a typed value, if it equals the
reference's declared default, the generator omits that slot from the request.
`cases.json` retains it in `untouched_defaults`, with its slot, kind, exact typed
value and `reason: "untouched default"`. This includes colors and components,
and min/max/random picks that happen to equal the default. An untouched
parameter is not an AE edit: even an out-of-range declared default (OLMKiraKira
slot 5: approximately 0.1, valid range [1,100]) must not be resubmitted as an edit.
Other explicit numeric values are checked against the declared range/type and
rejected rather than clamped if invalid. Numeric bounds are recorded in
`numeric_ranges`; request JSON still contains only actual typed assignments.

**Plans changed for default picks.** The selection algorithm and RNG consumption
are unchanged: with the same seed and inventory, chosen values, input seeds,
sizes, layers and downsample factors remain the same. Only default-equal entries
move from explicit assignments to untouched-default records (plus bounds metadata).
Historical saved requests remain unchanged and replay their original edits.
The generator uses the reference inventory for both sides; inventory differences
are still reported independently, rather than forcing a reference default onto
the candidate. This relies on the rebuilt shared harness's untouched-default
handling introduced by AEXCompat PR #1824.

Python's seeded generator creates the complete case plan before scheduling.
NumPy PCG64 creates noise from each recorded input seed. Thus `--jobs` cannot
change parameters or input bytes. Sizes and downsample ratios cycle independently
of scheduling. Inputs combine gradients, a hard color edge, noise, nonblack RGB
under zero alpha and alpha bytes **0, 1, 32, 128, 255**. Images with at least five
pixels contain all five alpha values. A 1x1 image cannot contain five values; its
single alpha is zero. PNG inputs are straight RGBA8, promoted by the harness for
deep routes; this does not cover arbitrary HDR/negative-alpha source data.

* 8 bpc: Pillow decodes RGBA PNG samples; no ICC/gamma transform is applied and
  encoded PNG compression/metadata differences are irrelevant.
* 16 bpc: compare little-endian native words from `output.rgba16le`, not PNG.
* 32 bpc: compare `output.rgba32f-le` as **u32 words**, so signed zero and NaN
  payload differences fail. Float subtraction is used only for explanatory max
  absolute difference, never for equality.

Dimensions and raw byte lengths are checked. Summary fields contain mismatching
pixel/sample counts, first `(x,y)` coordinates, maximum absolute difference and
nonfinite difference counts. `Infinity` is a string to keep JSON standards
compliant. A signed-zero or NaN-only mismatch can have max absolute difference
zero; its bit mismatch count remains authoritative.

All cases are retained (including successful cases) for auditability. Each has
`input.png`, secondary PNGs, `requests/{reference,candidate}.json`, `case.json`,
both available outputs/sidecars, `*.process.json`, and `diff.json`. Summary binds
tool/harness/reference/candidate SHA-256s, seed, cases, options and per-route
counts. `case.json` also hashes the inputs and requests. Replay checks those
hashes and the executable identities, writes into a fresh directory, and leaves
the original evidence intact. Plug-ins remain at their original external paths.

## Harness routes, downsample, layers and extents

Implementation was checked against the installed harness's `--help`,
`--print-cli-contract`, `docs/RENDER_FIXTURE.md`, and its request parser. These
are the mappings, without probing undeclared routes as if they were supported:

| Route | CLI suffix after `--render-experimental-` | Required declaration |
| --- | --- | --- |
| smart8 | `smart-request` | `out_flags2` bit 10 (`SUPPORTS_SMART_RENDER`) |
| smart16 | `smart-request-16` | SmartFX plus `out_flags` bit 25 (`DEEP_COLOR_AWARE`) |
| smart32 | `smart-request-32-cpu` | SmartFX plus `out_flags2` bit 12 (`FLOAT_COLOR_AWARE`) |
| classic8 | `request` | Image effect **without** `SUPPORTS_SMART_RENDER` |
| classic16 | `request-16` | Image effect **without** SmartFX, plus `DEEP_COLOR_AWARE` |
| classic32 | `request-32` exists in harness | Not applicable: AE declares float support through SmartFX, not classic |

AE never sends `PF_Cmd_RENDER` to an effect declaring
`PF_OutFlag2_SUPPORTS_SMART_RENDER`; it dispatches SmartPreRender/SmartRender.
Consequently classic8/16 are `not_applicable` for all nine SmartFX originals,
even when explicitly included in `--routes`. OLMSmoother does not declare
SmartFX, so its classic8/16 routes remain applicable. `--force-classic` bypasses
only this SmartFX exclusion for classic8/16, not depth or audio restrictions.
For example, `--routes classic8 --force-classic` is a **non-AE host/debug probe**.

Request `host_context.spatial.downsample_x/downsample_y` holds rational scales;
full-resolution dimensions are `ceil(input_dimension / scale)`. The supplied
PNG already has the preview dimensions; the tool does not secretly resample it.
Request host context also contains the required empty `mask_scene`. Render
settings explicitly request straight pixels, software renderer, disabled color
management and no linear-light conversion.

Typed request assignments use `layer` for a layer image. The harness resolves
relative paths against the **parent of the requests directory**, which is why
requests and assets have this layout. Components use `components`, colors use
`color`, and scalars use `value`.

For SmartFX, `host_context.smart_output_request_rect` sets output demand; it is
not a primary-world extent hint. For actual primary/secondary world extents,
origins and padded strides, AEXCompat's **fixture v2** has
`worlds.primary/secondary[].extent`, `origin`, `rowbytes` and `row_padding`.
Fixture v1/v2 take complete parameter records with `layer_path`, relative to the
fixture itself, and support both classic and SmartFX checkpoints in packed ARGB.
The fixture schema does **not** expose spatial/downsample context. This oracle
uses request routes for downsample and layer coverage; it does not yet generate
fixture-v2 padded worlds or classic extent variations. Unsupported combinations
are rejected explicitly rather than silently dropping a requested extent.

## Self-test and measured results

```powershell
python -m unittest discover -s rust/tools/oracle -p test_oracle.py -v
# Or, if installed:
python -m pytest rust/tools/oracle -q
python rust/tools/oracle/self_test.py --out rust/tools/oracle/runs/all-ten-new --jobs 4
```

Unit coverage includes deterministic generation across scheduling, alpha inputs,
all-field inventory diffs, 8/16/32-bit loading, signed zero/NaN payload comparison,
shape/length rejection, summary classification, downsample/perturbation and
owned-process timeout cleanup.

The original **2026-11-12** all-ten run used seed **20261112**, **20 cases per probed
route**, jobs **4**, an explicitly chosen timeout of **30 seconds**, sizes **1x1, 3x7, 97x61, 256x144**,
and downsample **1, 1/2, 1/4** (7, 7, 6 cases respectively per route). Inventory
was identical for **all ten**. These are real reference-vs-itself measurements,
not Rust-port validation. Its raw evidence is preserved unchanged. Its classic
probes of SmartFX effects were **non-AE debug observations**, not AE routes;
the initial route classification was incorrect and is superseded here.

The current route table combines the original 30-second observations with the
120-second review reruns for DistanceGradation and OLMRadialBlur. Cells are
**exact / mismatched / reference_unrenderable / reference_timeout / candidate_failure**.
All applicable cells contain 20 attempts. `N/A` means excluded under the
route contract above; all ten have `classic32 = N/A`.

| Original plug-in | Timeout | smart8 | smart16 | smart32 | classic8 | classic16 |
| --- | --- | --- | --- | --- | --- | --- |
| ColorKeep | 30s historical | 20/0/0/0/0 | 20/0/0/0/0 | 20/0/0/0/0 | N/A | N/A |
| DistanceGradation | 120s rerun | 20/0/0/0/0 | 20/0/0/0/0 | 19/0/0/1/0 | N/A | N/A |
| OLMBlur | 30s historical | 20/0/0/0/0 | 20/0/0/0/0 | 20/0/0/0/0 | N/A | N/A |
| OLMColorKey | 30s historical | 20/0/0/0/0 | 20/0/0/0/0 | 20/0/0/0/0 | N/A | N/A |
| OLMDirectionalBlur | 30s historical | 20/0/0/0/0 | 20/0/0/0/0 | 20/0/0/0/0 | N/A | N/A |
| OLMKiraKira | 30s historical | 0/0/20/0/0 | 0/0/20/0/0 | 0/0/20/0/0 | N/A | N/A |
| OLMRadialBlur | 120s rerun | 15/0/5/0/0 | 15/0/5/0/0 | 15/0/5/0/0 | N/A | N/A |
| OLMSmoother | 30s historical | N/A | N/A | N/A | 20/0/0/0/0 | 20/0/0/0/0 |
| OLMSmoother2 | 30s historical | 20/0/0/0/0 | 20/0/0/0/0 | 20/0/0/0/0 | N/A | N/A |
| OLMToonDilate | 30s historical | 20/0/0/0/0 | 20/0/0/0/0 | 20/0/0/0/0 | N/A | N/A |

Historical raw total, **including non-AE classic probes**: **940 route-cases, 605 exact, 10 pixel mismatches, 322 reference
unrenderable, 3 candidate-only failures, 0 tool errors**. The three
candidate-only failures are also DistanceGradation classic8 self-comparisons:
the same binary rendered on the first invocation and failed on the second.

Observed limitations and reproducibility findings:

* **DistanceGradation classic8 is nondeterministic in this non-AE host/debug corpus.** Ten
  successful pairs differed, with max absolute sample difference 255. Case 0000
  also mismatched in a sequential `replay`, so concurrent case scheduling is
  not required to reproduce it. The root cause (plug-in memory, host behavior,
  internal thread counts, etc.) was not established. Do not use this route as
  a deterministic comparison oracle, and do not treat it as an AE-dispatched
  route or an AE conformance failure. Its historical debug counts were
  classic8 **3 exact / 10 mismatched / 4 reference failures / 3 candidate-only
  failures**, classic16 **20 exact**. The three historical SmartFX failures were
  case 0002 (all numeric maxima), with both sides exceeding 30 seconds; that
  old `reference_unrenderable` classification represented a timeout, not proof
  of inability to render, and is superseded by the longer run below.
* **Historically, OLMKiraKira could not reach rendering** through the original harness interface.
  Slot 5's observed default is 0.10000000149011612 but its declared minimum is
  1.0: 20 route-cases were rejected as out-of-range. The other 80 were rejected
  with `arbitrary parameter has no printable text` for default ramp data.
  This is a host serialization/validation limitation, not measured pixel
  inequality. No fabricated ramp payload or clamped default was substituted.
  This historical result predates PR #1824 and the untouched-default generator
  correction; see the newer original-vs-Rust run below.
* Non-AE debug probes of OLMColorKey, OLMDirectionalBlur, OLMSmoother2 and OLMToonDilate classic8/16
  failed all attempts with `session frame reported error -6 past a clean final
  report` (`classic_finalize`/output validation). OLMRadialBlur classic routes
  showed the same failure; its 15 SmartFX failures across depths were resident
  worker/session failures. Inspect individual logs for the actual diagnostic.
* No same-binary pixel mismatches were observed on the other tested routes.
  This is bounded evidence, not proof of determinism for untested parameters.

The negative control (OLMBlur slot 1 +0.5, 97x61) mismatched on all three
SmartFX depths and returned **1**. Max differences were **4** (8 bpc), **459**
(16 bpc), **0.014009296894073486** (32 bpc). Float replay reproduced the mismatch
and exit code 1. An additional 3x7, downsample 1/2, explicit output-rectangle
smoke was exact on all three SmartFX depths; the harness report echoed the
requested rational scale and 6x14 full-resolution dimensions.

Evidence:

* [Compact campaign record](evidence/all-ten-20261112.json): executable hashes,
  inventories, per-route results, failure witnesses and hashes of full logs.
* [Exact campaign tool source](evidence/olm_oracle.campaign.py.txt), SHA-256
  `c638d9e6d043f835f919f99b5608c4003f36330c815124b0709ba1e73a7b5414`.
  After this campaign, only cancellation/cleanup handling, atomic JSON writing,
  setup-failure reporting and replay provenance were hardened. Case generation,
  and sample comparison were unchanged. That revision's smoke:
  three SmartFX and two non-AE classic OLMBlur probes exact at 3x7/downsample 1/2;
  negative float replay still mismatched. That revision passed **13/13** tests.
  The review revision changes route selection and timeout reporting as described
  above; its test and rerun results are recorded below.
* [Validation record](evidence/validation.json) binds those follow-up checks.
* Full local artifacts: `runs/all-ten-20261112/`; serial mismatch replay:
  `runs/dg-serial-mismatch/`; extent smoke: `runs/extent-smoke/`.
  `runs/` is ignored by Git but retained locally, including failing inputs,
  requests and every available raw output. No original binaries are copied.

Harness SHA-256 for the campaign:
`81676eae08b30ee60ad95c29dcf227324755bc0dec7a436ac77f4686e72b3d27`.
To rebuild the compact evidence from a new completed campaign:

```powershell
python rust/tools/oracle/collect_results.py rust/tools/oracle/runs/all-ten-new --out rust/tools/oracle/evidence/new-results.json
```


## Review reruns: AE route selection and longer deadlines

Review tests: **18/18 passed** with
`python -m unittest discover -s rust/tools/oracle -p test_oracle.py -v`.
Coverage now includes SmartFX classic exclusion, OLMSmoother-style classic
admission, explicit non-AE classic labels, the 120-second CLI default, local
child environment overrides and separate outer/internal timeout classification.
An actual OLMBlur `--routes classic8 --force-classic --cases 1` smoke was exact,
and both its human table and JSON labelled it **non-AE debug**.

Both originals were rerun with seed **20261112**, 20 cases, four jobs per run,
the same cyclic sizes and downsample ratios as the original campaign. The two
campaigns ran concurrently, up to eight owned harness processes overall. The
case-plan JSONs were compared to the original campaign and were identical.
Plug-in and harness hashes were unchanged. The outer timeout was **120 seconds**
and the child-only frame deadline override was **120000 ms**. Both inventories
again compared identical, and all classic routes were `not_applicable`.

| Plug-in | Route | Cases | Exact | Mismatched | Reference unrenderable | Reference timeout | Candidate-only failure |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DistanceGradation | smart8 | 20 | 20 | 0 | 0 | 0 | 0 |
| DistanceGradation | smart16 | 20 | 20 | 0 | 0 | 0 | 0 |
| DistanceGradation | smart32 | 20 | 19 | 0 | 0 | 1 | 0 |
| OLMRadialBlur | smart8 | 20 | 15 | 0 | 5 | 0 | 0 |
| OLMRadialBlur | smart16 | 20 | 15 | 0 | 5 | 0 | 0 |
| OLMRadialBlur | smart32 | 20 | 15 | 0 | 5 | 0 | 0 |

Both render summaries returned **2** (incomplete comparison). This table does
not count a time budget as proof of an unrenderable reference. In particular,
DistanceGradation case **0002**, all numeric maxima at **97x61 / downsample 1/4**,
completed exactly at smart8 (reference **59.453s**, candidate **67.687s**) and
smart16 (**56.437s / 63.047s**). Its smart32 pair hit the outer bound
(**120.047s / 120.032s**), with exit 124 and no stdout/stderr; it is a
`reference_timeout`, not `reference_unrenderable`. No extrema were removed.

The first review attempt only lengthened the parent process deadline, exposing
the harness's still-active 30000 ms internal `frame_deadline`. Those intermediate
artifacts remain under `runs/review-120-{DistanceGradation,OLMRadialBlur}/` and are
superseded by `runs/review-frame120-{DistanceGradation,OLMRadialBlur}/`. Internal
deadline configuration was confirmed in AEXCompat's `windows/cli.rs` and
`image_render/diagnostics.rs`; no harness sources or binaries were modified.

[Review results](evidence/review-120-results.json) retain the full summaries,
case-plan hashes, exact maxima process logs, tool identity and test result.
To reproduce the final 20-case runs (use new output directories):

```powershell
$originals = 'D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex'
foreach ($name in @('DistanceGradation', 'OLMRadialBlur')) {
    $aex = Join-Path $originals ($name + '.aex')
    python rust/tools/oracle/olm_oracle.py render --reference $aex --candidate $aex --cases 20 --seed 20261112 --jobs 4 --downsample 1,1/2,1/4 --timeout 120 --out "rust/tools/oracle/runs/review-new-$name"
}
```

The loop is sequential across plug-ins; within each run, `--jobs 4` controls
case parallelism. No native AE or GUI was used.


### Additional bounded maxima replay

DistanceGradation case **0002 smart32** was then replayed alone, after both 20-case campaigns exited, with **300 seconds** and `AEXCOMPAT_FRAME_DEADLINE_MS=300000`. Both sides completed normally (reference **116.875s**, candidate **107.844s**) and the raw float output was **bit-exact**, including all u32 words. Replay exit code: **0**. No parameters, inputs, or executable hashes were changed.

| Check | Exact | Mismatched | Reference unrenderable | Reference timeout | Exit |
| --- | ---: | ---: | ---: | ---: | ---: |
| Case 0002 smart32, 300s, sequential | 1 | 0 | 0 | 0 | 0 |

This resolves the remaining maxima witness: all **20 distinct DistanceGradation cases at each SmartFX depth** have now produced exact self-comparisons, with the smart32 maxima established by the separate 300-second replay. The 120-second campaign table remains unchanged at 19 exact + 1 timeout for smart32. The sequential replay timings and the parallel campaign timing limits are different observations; no causal performance claim is inferred.

[Exact replay evidence](evidence/review-max32-300.json) includes both process logs and the summary.

```powershell
python rust/tools/oracle/olm_oracle.py replay rust/tools/oracle/runs/review-frame120-DistanceGradation/case-0002-smart32 --timeout 300 --out rust/tools/oracle/runs/max32-new
```

## OLMRadialBlur 120-second failure diagnostics

This rerun used both an outer 120-second limit and `AEXCOMPAT_FRAME_DEADLINE_MS=120000`. Exactly cases **0002, 0004, 0008, 0015, 0017** failed on smart8/16/32, on both sides. All 30 failing processes returned **1** with `timeout=false` and `harness_frame_timeout=false`; there were no timeout cases. All five cases assigned slot 25 (`Noise Type`) = **3**. This correlation is observed data, not a diagnosis of the underlying fault.

Each row maps the exact stderr/report error fields to a diagnostic block below. The full stdout including every `parameter_metadata` field, exact stderr, arguments, environment, PID, elapsed time, case manifest and log hashes are retained in [review-radial-diagnostics.json](evidence/review-radial-diagnostics.json). Raw images/requests/logs remain in `runs/review-frame120-OLMRadialBlur/case-NNNN-ROUTE/`. The emitted failure reports contain no SEH code, fault address or backtrace; none is inferred here.

| Case | Route | Reference diagnostic | Candidate diagnostic | Seconds reference / candidate |
| --- | --- | --- | --- | --- |
| 0002 | smart8 | D1 | D1 | 9.766 / 9.906 |
| 0002 | smart16 | D1 | D1 | 10.188 / 9.906 |
| 0002 | smart32 | D1 | D1 | 10.437 / 10.968 |
| 0004 | smart8 | D2 | D2 | 5.266 / 5.453 |
| 0004 | smart16 | D2 | D2 | 5.688 / 6.218 |
| 0004 | smart32 | D2 | D2 | 6.266 / 6.406 |
| 0008 | smart8 | D3 | D3 | 5.406 / 6.078 |
| 0008 | smart16 | D3 | D3 | 5.172 / 5.579 |
| 0008 | smart32 | D3 | D3 | 5.500 / 5.547 |
| 0015 | smart8 | D4 | D5 | 6.719 / 6.546 |
| 0015 | smart16 | D6 | D7 | 6.703 / 6.609 |
| 0015 | smart32 | D8 | D9 | 6.687 / 7.047 |
| 0017 | smart8 | D10 | D10 | 6.766 / 6.343 |
| 0017 | smart16 | D10 | D10 | 6.407 / 6.765 |
| 0017 | smart32 | D10 | D10 | 6.328 / 6.578 |

### D1

Exact stderr (including any capture warning):

```text
the resident render session could not carry this render (render session close rejected invariant=worker_not_ok invalidated=false worker_ok=false suite_acquires=4964 suite_releases=4964 live_suite_lease_count=0 live_suite_reference_count=0). Diagnose the session failure; there is no alternate transport. Any world-dump snapshots from the failed session are preserved for diagnosis; clear the dump directory before re-running, since it must start empty.
```

Exact report error fields (the remaining stdout field is `parameter_metadata`):

```json
{"classification": "nonzero_exit", "failure_stage": "render"}
```

### D2

Exact stderr (including any capture warning):

```text
the resident render session could not carry this render (render session close rejected invariant=worker_not_ok invalidated=false worker_ok=false suite_acquires=68 suite_releases=68 live_suite_lease_count=0 live_suite_reference_count=0). Diagnose the session failure; there is no alternate transport. Any world-dump snapshots from the failed session are preserved for diagnosis; clear the dump directory before re-running, since it must start empty.
```

Exact report error fields (the remaining stdout field is `parameter_metadata`):

```json
{"classification": "nonzero_exit", "failure_stage": "render"}
```

### D3

Exact stderr (including any capture warning):

```text
the resident render session could not carry this render (render session close rejected invariant=worker_not_ok invalidated=false worker_ok=false suite_acquires=84 suite_releases=84 live_suite_lease_count=0 live_suite_reference_count=0). Diagnose the session failure; there is no alternate transport. Any world-dump snapshots from the failed session are preserved for diagnosis; clear the dump directory before re-running, since it must start empty.
```

Exact report error fields (the remaining stdout field is `parameter_metadata`):

```json
{"classification": "nonzero_exit", "failure_stage": "render"}
```

### D4

Exact stderr (including any capture warning):

```text
2026-11-12T04:13:29.861135Z  WARN aexcompat_broker::windows_process: worker output truncated at capture limit stdout_truncated=false stderr_truncated=true
the resident render session could not carry this render (render session close rejected invariant=worker_not_ok invalidated=false worker_ok=false suite_acquires=29916 suite_releases=29916 live_suite_lease_count=0 live_suite_reference_count=0). Diagnose the session failure; there is no alternate transport. Any world-dump snapshots from the failed session are preserved for diagnosis; clear the dump directory before re-running, since it must start empty.
```

Exact report error fields (the remaining stdout field is `parameter_metadata`):

```json
{"classification": "nonzero_exit", "failure_stage": "render"}
```

### D5

Exact stderr (including any capture warning):

```text
2026-11-12T04:13:36.364204Z  WARN aexcompat_broker::windows_process: worker output truncated at capture limit stdout_truncated=false stderr_truncated=true
the resident render session could not carry this render (render session close rejected invariant=worker_not_ok invalidated=false worker_ok=false suite_acquires=29916 suite_releases=29916 live_suite_lease_count=0 live_suite_reference_count=0). Diagnose the session failure; there is no alternate transport. Any world-dump snapshots from the failed session are preserved for diagnosis; clear the dump directory before re-running, since it must start empty.
```

Exact report error fields (the remaining stdout field is `parameter_metadata`):

```json
{"classification": "nonzero_exit", "failure_stage": "render"}
```

### D6

Exact stderr (including any capture warning):

```text
2026-11-12T04:13:34.239558Z  WARN aexcompat_broker::windows_process: worker output truncated at capture limit stdout_truncated=false stderr_truncated=true
the resident render session could not carry this render (render session close rejected invariant=worker_not_ok invalidated=false worker_ok=false suite_acquires=29916 suite_releases=29916 live_suite_lease_count=0 live_suite_reference_count=0). Diagnose the session failure; there is no alternate transport. Any world-dump snapshots from the failed session are preserved for diagnosis; clear the dump directory before re-running, since it must start empty.
```

Exact report error fields (the remaining stdout field is `parameter_metadata`):

```json
{"classification": "nonzero_exit", "failure_stage": "render"}
```

### D7

Exact stderr (including any capture warning):

```text
2026-11-12T04:13:41.109347Z  WARN aexcompat_broker::windows_process: worker output truncated at capture limit stdout_truncated=false stderr_truncated=true
the resident render session could not carry this render (render session close rejected invariant=worker_not_ok invalidated=false worker_ok=false suite_acquires=29916 suite_releases=29916 live_suite_lease_count=0 live_suite_reference_count=0). Diagnose the session failure; there is no alternate transport. Any world-dump snapshots from the failed session are preserved for diagnosis; clear the dump directory before re-running, since it must start empty.
```

Exact report error fields (the remaining stdout field is `parameter_metadata`):

```json
{"classification": "nonzero_exit", "failure_stage": "render"}
```

### D8

Exact stderr (including any capture warning):

```text
2026-11-12T04:13:34.976397Z  WARN aexcompat_broker::windows_process: worker output truncated at capture limit stdout_truncated=false stderr_truncated=true
the resident render session could not carry this render (render session close rejected invariant=worker_not_ok invalidated=false worker_ok=false suite_acquires=29916 suite_releases=29916 live_suite_lease_count=0 live_suite_reference_count=0). Diagnose the session failure; there is no alternate transport. Any world-dump snapshots from the failed session are preserved for diagnosis; clear the dump directory before re-running, since it must start empty.
```

Exact report error fields (the remaining stdout field is `parameter_metadata`):

```json
{"classification": "nonzero_exit", "failure_stage": "render"}
```

### D9

Exact stderr (including any capture warning):

```text
2026-11-12T04:13:41.853560Z  WARN aexcompat_broker::windows_process: worker output truncated at capture limit stdout_truncated=false stderr_truncated=true
the resident render session could not carry this render (render session close rejected invariant=worker_not_ok invalidated=false worker_ok=false suite_acquires=29916 suite_releases=29916 live_suite_lease_count=0 live_suite_reference_count=0). Diagnose the session failure; there is no alternate transport. Any world-dump snapshots from the failed session are preserved for diagnosis; clear the dump directory before re-running, since it must start empty.
```

Exact report error fields (the remaining stdout field is `parameter_metadata`):

```json
{"classification": "nonzero_exit", "failure_stage": "render"}
```

### D10

Exact stderr (including any capture warning):

```text
the resident render session could not carry this render (render session close rejected invariant=worker_not_ok invalidated=false worker_ok=false suite_acquires=72 suite_releases=72 live_suite_lease_count=0 live_suite_reference_count=0). Diagnose the session failure; there is no alternate transport. Any world-dump snapshots from the failed session are preserved for diagnosis; clear the dump directory before re-running, since it must start empty.
```

Exact report error fields (the remaining stdout field is `parameter_metadata`):

```json
{"classification": "nonzero_exit", "failure_stage": "render"}
```

## OLMKiraKira original vs Rust: untouched defaults, seed 777123

With the rebuilt shared default harness and the untouched-default generator,
inventory compared **identical**, and render returned **0**:

| Route | Cases | Exact | Mismatched | Reference failures/timeouts | Candidate failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| smart8 | 15 | 15 | 0 | 0 | 0 |
| smart16 | 15 | 15 | 0 | 0 | 0 |
| smart32 | 15 | 15 | 0 | 0 | 0 |
| classic8/16/32 | 0 | N/A | N/A | N/A | N/A |

Settings: `--cases 15 --seed 777123 --jobs 4 --sizes 5x5,11x7,31x19,97x61
--downsample 1,1/2,1/4`, default 120-second timeout, no forced classic routes.
Reference: `D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex\OLMKiraKira.aex`.
Candidate: `C:\Users\optim\AppData\Local\Temp\claude\d399b726667e509a\f4e88ce9-5b8e-4d58-b1e2-473311555016\scratchpad\olmv\OLMKiraKira.aex`.
Slot 5 is recorded as untouched in cases **0, 8, 11**; every other explicit slot-5
value lies in [1,100]. All 90 side/route request documents were checked against
the generated plans, and all selected values/input seeds were checked against
the previous generator. Defaults are omitted, not clamped or replaced.

Unit tests: **21/21 passed**, including out-of-range defaults, typed default
omission, numeric range/type rejection, default-based perturbations, and preserved
random draws versus the historical generator for multiple seeds.
[Hash-bound result](evidence/kirakira-777123-untouched.json) records both binaries,
the rebuilt harness, tool hash, route counts and plan verification. Full artifacts:
`runs/kirakira-777123-untouched-inventory/` and
`runs/kirakira-777123-untouched-render/`. Earlier KiraKira failures above used the
old harness/generator and remain historical observations, not this run's result.

## Process ownership and limitations

On Windows each harness starts suspended, is assigned to a new private Job
Object, and is resumed only after ownership is established. Timeout/normal
cleanup terminates only that job, polls its active-process count to zero, closes
the handle and waits for the owned child. No executable-name kill or global
process enumeration is used. The harness can retain its own nested worker jobs.
POSIX uses an owned process group, but this Windows-AEX workflow is only tested
on Windows; no macOS/native AE/GPU qualification is implied.

The installed worker can report `worker_freshness_warning=source_newer_than_worker`.
This is preserved in the inspection diagnostics. The executable used is hashed;
this job does not rebuild the harness or change its workers. Timing, callbacks,
arbitrary/custom UI payloads, dynamic parameter UI behavior, masks, GPU routes,
temporal sequences, HDR input and exhaustive combinations remain outside this
bounded corpus. Harness failures are observations, not proof of candidate bugs.
