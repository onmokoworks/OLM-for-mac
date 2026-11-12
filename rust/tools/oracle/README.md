# AEXCompat bit-exact oracle

`render --resident` opts into AEXCompat's finite fresh-instance batches.
Per-process rendering remains the default. Every resident mismatch or failed
case is rerun per-process with identical saved inputs and requests; both
observations remain in the report. See [resident rendering](#resident-rendering).
The earlier [feasibility proposal](../fastrender/AEXCOMPAT_PROPOSAL.md) is a
historical record from before AEXCompat PR #1828 supplied the missing API.

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
python rust/tools/oracle/olm_oracle.py render --reference $original --candidate $candidate --cases 20 --seed 20261112 --jobs 3 --downsample 1,1/2,1/4 --out rust/tools/oracle/runs/comparison
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
| `--jobs N` | Concurrent route-cases; 1..3, default half the logical CPU count capped at three |
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
python -m unittest discover -s rust/tools/oracle -p "test_*.py" -v
# Or, if installed:
python -m pytest rust/tools/oracle -q
python rust/tools/oracle/self_test.py --out rust/tools/oracle/runs/all-ten-new --jobs 3
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
    python rust/tools/oracle/olm_oracle.py render --reference $aex --candidate $aex --cases 20 --seed 20261112 --jobs 3 --downsample 1,1/2,1/4 --timeout 120 --out "rust/tools/oracle/runs/review-new-$name"
}
```

The loop is sequential across plug-ins; within each run, `--jobs 3` controls
case parallelism under the current limit. Historical measurements above used
four jobs; their recorded counts/options are not rewritten. No native AE or GUI was used.


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

## Porting workflows: check, minimize and sweep

Existing public oracle functions remain available with their prior arguments and
result shapes. `run_process` additionally accepts optional `cwd=None`; existing
calls are unchanged. Workflows live in `oracle_workflows.py`, loaded lazily by
the CLI. `generate_sweep_cases` is exported directly from `olm_oracle` for triage.
The current CLI and self-test limit `--jobs` to **1..3**. Historical four-job
measurements above remain historical facts.

### Build and check one crate

```powershell
python rust/tools/oracle/olm_oracle.py check olm-blur --jobs 3
python rust/tools/oracle/olm_oracle.py check olm-blur --full --jobs 3
python rust/tools/oracle/olm_oracle.py check new-effect --reference D:\originals\NewEffect.aex --jobs 3
```

`check` runs `cargo build --release -p <crate> --locked --jobs N
--message-format=json-render-diagnostics` with `rust/` as its working directory.
`--rust-root` overrides that workspace. Build output goes only to ignored
`rust/tools/oracle/runs/cargo-target/`; `--locked` prevents edits to Cargo.lock.
Workspace/lockfile corrections must be handled by the workspace owner. The tool
does not rewrite workspace manifests or other kits' directories.

The emitted `cdylib` DLL is taken from Cargo's artifact JSON, not from a guessed
or possibly stale target path. `--lib-name` supports custom library target names.
It stages only the candidate DLL under the **original .aex filename**, inside the
run's `stage/` directory with its own ignore-all `.gitignore`. The original is
read only and never copied. Plug-ins needing separate runtime dependencies may
require a separately prepared candidate; this command only stages the DLL.

Next it records inventory and runs the applicable routes. Quick mode uses **6
cases/route**; `--full` uses the standard **20 cases/route**. Both use seed
20261112 by default, sizes 1x1/3x7/97x61/256x144 and downsample 1,1/2,1/4.
`--seed`, `--timeout` (120s), `--build-timeout` (900s), `--harness` and `--out`
are configurable. Build logs, inventory, staged identity and render summaries
remain beneath the run directory. One final line reads
`ORACLE PASS|FAIL|INCOMPLETE|ERROR crate=... mode=... summary=...`.
No applicable renders is incomplete, not PASS. Exit codes retain 0/1/2 semantics.

The built-in mapping is:

| Crate | Original basename |
| --- | --- |
| color-keep | ColorKeep.aex |
| olm-blur | OLMBlur.aex |
| olm-color-key | OLMColorKey.aex |
| olm-directional-blur | OLMDirectionalBlur.aex |
| olm-distance-gradation | DistanceGradation.aex |
| olm-kirakira | OLMKiraKira.aex |
| olm-radial-blur | OLMRadialBlur.aex |
| olm-smoother | OLMSmoother.aex |
| olm-smoother2 | OLMSmoother2.aex |
| olm-toon-dilate | OLMToonDilate.aex |

`--originals` overrides the default original-binary directory; an explicit
`--reference` takes precedence and also supports new crates.

### Minimize a saved mismatch

```powershell
python rust/tools/oracle/olm_oracle.py minimize rust/tools/oracle/runs/comparison/case-0003-smart8 --out rust/tools/oracle/runs/minimized --max-attempts 80
```

The source case, request/input asset hashes and executable hashes are verified
before any trial. The source is never changed. Each candidate reduction is saved
as a replayable `step-NNNN-operation/` with both requests, inputs, outputs, logs
and `diff.json`. Rejected trials remain evidence too. Default **two confirmations**
must both report a pixel mismatch; harness failures, exact outputs and timeouts
are rejected. `--confirmations` can explicitly change this count. Trials are
sequential (no extra worker pool). `--timeout` defaults to 120 seconds per process.

The deterministic greedy reduction tries:

1. Reset one assigned slot on **both sides** by omitting it, returning each side
   to its own untouched default (including a debug perturbation, if removable).
2. Normalize both downsample ratios to 1 and update full-resolution dimensions.
3. Reduce image dimensions by halves, then one pixel, using top-left cropping
   and nearest-neighbor downscaling. Secondary PNG layers shrink proportionally;
   full-resolution dimensions and explicit SmartFX request rectangles are updated.

After an accepted reduction the search restarts. A complete unsuccessful pass
reports `local_minimum_under_documented_moves`; this is **not** a proof of a
global minimum over all images, crop origins, values or parameter subsets.
At the attempt budget it reports `attempt_budget_exhausted` and returns the best
confirmed reproducer without claiming minimality. A non-reproducing baseline
returns 2. Successful minimization returns 0 even though the saved case is
intentionally mismatching; ordinary `replay` of it returns 1.

`summary.json` identifies `minimal_case_dir`, original/final dimensions, every
attempt and the first differing pixel/channel with the value pair. Deep native
request sidecars and PNG use RGBA indices (fixture checkpoint buffers are
separately packed ARGB). Float differences include raw
u32 hexadecimal words and textual float values, retaining signed zeros/NaNs.
The saved requests are authoritative (`requests_authoritative: true`); the old
input seed remains provenance, not a recipe for regenerating the cropped image.
Only self-contained PNG-input bundles are supported; external secondary layers
are rejected. Two confirmations reduce, but cannot prove absence of, nondeterminism.

### Importable one-parameter sweep

```python
from olm_oracle import generate_sweep_cases, make_request

plans = generate_sweep_cases(inventory["parameters"], seed=42,
                             size=(31, 19), downsample="1/2")
requests = [make_request(plan) for plan in plans]
```

This pure helper returns an untouched baseline, followed by unique typed
min/max/random assignments with **one slot varied per plan**. All plans share
the same input seed/geometry so parameter effects can be compared to defaults.
Values equal to defaults stay untouched, unsupported custom/path payloads stay
at defaults, and layer probes use the normal deterministic layer input convention.
Plans carry `sweep.slot`/`sweep.selection` metadata and work with existing
`make_request`/`run_case`; neither inventory nor global RNG state is mutated.

### Measured demonstration and tests

**28/28 unit tests passed** using
`python -m unittest discover -s rust/tools/oracle -p "test_*.py" -q`.
New coverage includes quick/full build orchestration and DLL selection, build
failure short-circuiting, baseline repeatability, retained rejected trials,
Windows-native bundle paths, budget accounting, exact float word reporting and
one-parameter sweeps. Cargo success paths use controlled artifacts in unit tests.

Real AEXCompat demonstration: OLMBlur vs itself, smart8, 97x61, downsample 1/2,
candidate slot 1 offset +0.5. All other parameters start untouched.

| Measurement | Result |
| --- | --- |
| Source image | 97x61 (5917 pixels) |
| Final image | **2x2 (4 pixels)** |
| Downsample | 1/2 → **1** |
| Saved attempts | **38**, including baseline and rejected trials |
| Confirmation policy | Two mismatching pairs for every accepted step |
| Minimality | Local minimum under documented moves |
| First difference | **(x=0,y=1), B (RGBA index 2), reference 73 / candidate 72** |
| Independent replay | Mismatch reproduced, exit **1**, max absolute difference 1 |

The minimal case is
`runs/kit-minimized-blur/step-0030-crop-2x2/`; the source is in
`runs/kit-minimize-source/`, the independent replay in `runs/kit-minimal-replay/`.
[Workflow evidence](evidence/kit-workflows.json) binds the measured summaries.

The actual `check olm-blur --jobs 3` attempt stopped before compilation because
Cargo reported `multiple workspace roots found in the same workspace`, naming
`rust/tools/witness` and `rust`. Its verdict was **ERROR**, exit 2, and the full
build diagnostic is in `runs/kit-check-blur/build.process.json`. This is an
external workspace blocker; no other kit's files or Cargo workspace files were
changed. An end-to-end native Cargo build/check success is therefore **not
verified** in this run; the orchestration's success/failure paths are unit-tested.

## Resident rendering

Requires AEXCompat's independent-case batch command and a matching native worker
(PR #1828, merged at `7418be04e400c5020ea5b088e904db3fdf82b052`). The shared
detached checkout was updated to that revision and **both** Release binaries
rebuilt in their existing locations. Native compilation used the existing Ninja
Release/MSVC 14.50 configuration; header dependencies verified for 217 translation
units. The ordinary-session and independent-case APIs are different: this option
uses `--render-request-batch`, not persistent animation frames.

```powershell
python rust/tools/oracle/olm_oracle.py render --reference D:\originals\OLMBlur.aex --candidate D:\staged\OLMBlur.aex --resident --cases 60 --seed 20261112 --jobs 3 --downsample 1,1/2,1/4 --out rust/tools/oracle/runs/resident-new
```

Omit `--resident` for the unchanged per-process path. Existing `run_case`,
`evaluate_case`, case generation, comparison and replay arguments remain intact.
`prepare_case` is the extracted artifact-preparation helper. `check` continues
using per-process rendering. `replay` of a resident case runs per-process and
does not reconstruct its preceding resident history; use the saved batch
manifest to investigate ordering. Batch manifests point at existing outputs,
so rerunning one requires fresh output destinations.

Partitioning uses side/plug-in identity, route/depth, input dimensions, complete
static host context (including spatial scale/extent), timing step/scale/duration,
render settings, dependencies and secondary-layer slots/dimensions/decoded RGBA
content. Primary pixels, frame time and non-layer parameter edits may change.
Reference and candidate always get different workers, even for self-comparisons.
The key is conservative: equivalent differently written context documents may
split unnecessarily. Groups preserve generation order and split at both 128
cases and the 1 MiB manifest limit. The full typed requests are passed unchanged;
the harness remains the final preflight authority. Unique secondary layers can
force single-case groups and reduce acceleration.

The module/global data, PARAMS_SETUP declarations and owned default source
handles remain loaded. Each case gets fresh parameter/instance definitions,
owned arbitrary-value copies and sequence setup/setdown. Frame and SmartFX
cleanup follows the selected route. DLL statics, TLS, global caches and allocator
history remain shared: **fresh instance/sequence isolation is not process
isolation or native AE conformance**. See the upstream
[batch contract](https://github.com/onmokoworks/AEXCompat/blob/7418be04e400c5020ea5b088e904db3fdf82b052/docs/INDEPENDENT_CASE_BATCH.md).
This models independent effect instances in one loaded host, where module/global
state can legitimately persist. It does not model successive frames of one AE
effect instance, which may retain sequence state; process-local hidden state can
still make a plug-in differ from the per-process authority.

Memory-fill diagnostics from PR #1827 are supported by ordinary typed requests
but explicitly unsupported in resident batches; the adapter rejects them rather
than dropping them. Forced Classic probes of SmartFX effects are also rejected.
GPU, audio, custom UI and auxiliary-channel manifests are outside this batch
interface. The oracle does not expand its existing input-generation coverage.

The global `--jobs` cap (1..3) covers both reference and candidate batches.
Each batch runs under the existing private Windows Job; descendants are collected
on success, cancellation or failure. The internal watchdog remains per-case.
The outer finite batch budget is `(case_count + 1) * --timeout`, allowing one
extra case budget for discovery/startup/close. It is not an unlimited discovery
wait or a single-case timeout applied to an entire campaign.

### Reports and per-process authority

Each original `case-NNNN-route/` retains the same requests, inputs, outputs,
`case.json`, side process records and `diff.json`. `batches/batch-NNNNN/` adds the
exact manifest and raw batch process report. Side records reference their batch
and stable case ID, and separate case timing from batch wall time. The module
source identity is recorded as `resident_tool` alongside the ordinary tool hash.

Mapping checks the complete result population, unique IDs, indices, route,
loaded identity and final close evidence. A batch may exit 1 for a recoverable
failed case while other cases remain valid. A failed final close, missing report,
protocol failure or process timeout cannot produce an accepted exact result,
even if an output file exists. Native 16/32-bit sidecars remain authoritative.

**Every non-exact resident result is rerun per-process**, after resident workers
have exited, using hash-checked copies of the saved inputs/requests. These
artifacts live in `case-NNNN-route/per-process-authority/` and never overwrite
resident outputs. `diff.json.per_process_authority` and
`summary.json.per_process_reruns` contain the second verdict. The top-level
`results` and `routes` retain resident verdicts; `per_process_rerun_routes`
summarizes only the reruns, not an independently rerun whole campaign.

The CLI prints both verdicts for each rerun. An exact per-process rerun does not
turn a resident failure/mismatch into a pass. Exit 1 applies if either transport
shows a mismatch or candidate failure; otherwise incomplete/error observations
return 2. Success remains 0 only when the attempted resident comparisons are
exact and inventory comparison passes. Input preparation errors return 2 with
an incomplete summary; no render verdict is invented when dispatch never began.

### Qualification commands and corpus

```powershell
python -m unittest discover -s rust/tools/oracle -p 'test_*.py' -q
python rust/tools/oracle/qualify_resident.py --out rust/tools/oracle/runs/resident-qualification-new --cases 60 --seed 20261112 --jobs 3
```

The driver accepts `--originals`, `--candidates`, `--harness`, and `--only` for a
named configuration. It never builds or copies a plug-in. Candidate defaults
are the already-staged Rust artifacts in `rust/local/integration/staged-final`.

All-ten self-comparisons use 60 cases per advertised route: ten six-case
A/B/A/edited-C/B/A blocks, with seeded image triplets and alpha coverage from
the normal oracle, 97×61 pixels, preview scales 1, 1/2 and 1/4. A single numeric
slot is edited by a bounded one-unit step; all other parameters remain untouched.
This is a declared lifecycle/reset corpus, not a full-range parameter campaign.
Rust OLMBlur and ColorKeep use the ordinary full-range generator, 60 cases per
route, sizes 11×7/31×19 and the same three scales and seed. No post-result
exclusion or pass substitution is performed.

Both transports get identical saved plans and asset hashes. The driver compares
every verdict, both side PNG file bytes, and both native deep sidecars; absence
is recorded separately from successful equality. Wall times include input and
request preparation, dispatch, I/O, report processing, comparison and owned
cleanup, with the common inventory acquisition outside both clocks. Transport
order alternates across configurations. These are single campaign samples on a
shared machine with warm filesystem caches, not benchmark medians.

### Measured resident qualification (2026-11-12)

[Recorded evidence](evidence/resident-20261112.json) binds the binaries, source,
full comparison reports, tests and retained local artifacts by SHA256. The shared
detached checkout was updated to `7418be04e400c5020ea5b088e904db3fdf82b052`.
Both `cargo build --release -p aexcompat-harness` in `broker/` and
`tools/build-native.ps1 -BuildDir target/minihost-build` succeeded. The existing
Ninja/MSVC Release configuration and output locations were retained. The build
needed the existing VS Installer and Ninja directories on PATH; the initial
verification failure and successful repeat are both saved. No upstream source
was edited. Full old/new harness and worker hashes are in the evidence file.

The rebuilt per-process harness reproduced the saved OLMBlur Smart8 and
OLMSmoother Classic8 baseline: three seeded inputs each, **12/12 PNG files
byte-identical**, with all six reference/candidate comparisons exact.

The qualified complete campaigns below cover **2,100 route-cases**, with
**4,200/4,200 side outputs** and **6,960/6,960 PNG/native artifact comparisons**
identical between transports. All verdicts also match. Each advertised route
has 60 cases; Smoother has two routes and the other configurations have three.

| Configuration | Per-process seconds | Resident seconds | Speed-up |
|---|---:|---:|---:|
| Original ColorKeep | 60.10 | 11.74 | 5.12x |
| Original DistanceGradation | 92.67 | 17.08 | 5.43x |
| Original OLMBlur | 59.71 | 13.15 | 4.54x |
| Original OLMColorKey (full repeat) | 60.06 | 13.51 | 4.45x |
| Original OLMDirectionalBlur | 59.02 | 9.98 | 5.91x |
| Original OLMKiraKira | 120.63 | 35.89 | 3.36x |
| Original OLMRadialBlur | 59.39 | 12.92 | 4.60x |
| Original OLMSmoother | 38.54 | 6.98 | 5.52x |
| Original OLMSmoother2 | 60.25 | 12.09 | 4.98x |
| Original OLMToonDilate | 67.36 | 12.35 | 5.46x |
| Rust OLMBlur vs original | 64.00 | 12.38 | 5.17x |
| Rust ColorKeep vs original | 59.70 | 17.92 | 3.33x |
| Sum / ratio of summed times | **801.44** | **176.00** | **4.55x** |

The first ColorKey campaign is **not** marked equivalent: per-process case 22
Smart8 reference failed at session open with `file already exists (os error 80)`
before rendering. Its candidate and both resident outputs agree. The initial
report remains under `runs/resident-qualification-60/` and records 179/180 matching
verdicts and 359/360 matching side outputs for ColorKey. Three unchanged
per-process replays then matched both resident outputs, followed by the separate
complete campaign in `runs/resident-colorkey-requalification-60/`. The table uses
that complete repeat for ColorKey; it does not splice passing cases into the
initial run. The startup error's root cause is unproven.

The timed sources are preserved under `runs/resident-qualification-60/source/`.
Final review corrected manifest byte accounting (pretty JSON and Windows
newlines), replay transport metadata and the qualification check for missing
outputs (matching failures alone cannot prove byte equivalence). An offline check confirmed that all
246 timed batch manifests remain exactly identical under the final partitioner;
the complete ColorKey repeat exercised the final code. Final validation passed
**45 Python tests**, **12 upstream native batch tests**, **5 upstream CLI tests**
and **4 native self-test executables**.

Live controls also preserved both observations: three deliberately perturbed
OLMBlur routes mismatched in both transports; RadialBlur's full-range case 2
failed in both transports and retained both failure reports. Replaying the
resident Smart32 negative control through the default per-process authority
still mismatched and correctly recorded its transport. These controls are not
counted in the successful equivalence totals. The scoped cleanup audit found
no remaining task process; recycled Windows PIDs were left alone.

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
the resident follow-up rebuilt the shared harness and worker at the merge named
above, in their existing output locations. Timing, callbacks,
arbitrary/custom UI payloads, dynamic parameter UI behavior, masks, GPU routes,
temporal sequences, HDR input and exhaustive combinations remain outside this
bounded corpus. Harness failures are observations, not proof of candidate bugs.

## Secondary-layer sizes (N-uvmap)

`render --layer-sizes 17x9,1x1,2x1,1x5,33x17,8x16` cycles independently sized
secondary PNGs through the case plans. Omitting the option preserves the old
same-size behavior. Importable cases optionally contain
`"layer_sizes": {"1": [17, 9]}` for slot 1; dimensions must be positive integers.
`prepare_case` still emits the existing request schema and asset hashes. Saved
and minimized bundles record the actual secondary asset dimensions, including
a resized/cropped layer, so replay metadata remains accurate.

These are PNG preview dimensions. The harness promotes channel values to each
depth and obtains checkout layers through `PF_CHECKOUT_PARAM`. A downsample
request supplies the rational scale to the effect; it does not authorize an
oracle-side resize of the supplied secondary PNG. Output `--extent` is a
SmartFX demand rectangle. It is distinct from setting a texture world's own
origin, extent, or row padding. Current fixture-v2 Smart sessions reject custom
world layouts before rendering, so such probes are not native AE acceptance.
N-uvmap validated distinct sizes and 1, 1/2, 1/4 requests on Smart 8/16/32.

The additive size option, legacy behavior, invalid-size rejection, replay
assets, deep request-sidecar RGBA channel labels, and resized-bundle metadata
are covered by the 47 passing oracle tests (2026-11-13).
