# P00 plugin-only AE host-shape audit

`P00-host-realism.cpp` is an independently buildable derivative of
`F47d-native-bridge.cpp` (the suites used by F51). It loads actual Mach-O bundles,
not copied plugin sources, and never invokes an AEX or a pixel oracle. Run:

```sh
python3 tools/fuzz/build_F47_bundles.py --scratch "$HOME/.cache/olm-emu/P00"
python3 tools/fuzz/ae_realism_audit.py --build-host
python3 tools/fuzz/ae_realism_audit.py --phase baseline --jobs 1
python3 tools/fuzz/ae_realism_audit.py --phase matrix --jobs 1
python3 tools/fuzz/ae_realism_audit.py --summarize
```

Run commands from the worktree. Logs and compiler temporaries belong in
`orchestra/state/P00-ae-realism-refusal-audit/`. Builds are sequential, arm64 for
the host and Universal Release for the bundles. The audit does not install into
AE. Reproducing is a several-minute or longer operation, depending on CPU/load.

## Changes from F51/F47d

* `in_data.width/height` are full-resolution layer dimensions. Input and initial
  output worlds are `ceil(full/downsample_denominator)`, including asymmetric
  downsample. `PF_CheckoutResult.ref_width/ref_height` retain full dimensions,
  per the comments in `Headers/AE_Effect.h`.
* PARAMS_SETUP populates native defaults and supplies the actual parameter
  count (512-slot capacity). Arbitrary default handles are retained. Point
  defaults are converted from fixed-point percentages to full layer coordinates.
  Corpus scalar values override defaults **after** PARAMS_SETUP. The established
  F47d Kira raw-angle to float-slider mapping is retained by the Python driver.
* Strides can be padded independently of packed width (both worlds use the same
  padding in this campaign). The alignment case rounds odd-width rows to 64
  bytes. All buffers retain F47d outer canaries and input-mutation checking.
* The extent case has a centered content extent and transparent black pixels
  outside it. The ROI case supplies a centered subregion request with a full
  input checkout. The large-layer case uses a 2560x1440 layer and centered
  1920x1080 request: a comp-sized viewport, not a simulated compositor.
* The cropped-expand case supplies a half-width/half-height origin-zero input
  checkout (transparent content outside that checkout is assumed), retaining
  full-resolution reference dimensions. It uses the same expansion policy.
* The expanded case allocates a larger output **only if** PreRender's result
  rectangle asks for it, and sets output origins from that rectangle. It does
  not force unrequested expansion. The result and maximum rectangles are logged.
* The host emits a compact JSON render time, error, active-byte nonzero check,
  and output dimensions. Timing covers the render selector only, excludes setup,
  PreRender and output scanning. The driver also records complete-process wall
  time, final errors, refusal tags and unsupported callback diagnostics.
* Input is a deterministic opaque ARGB pattern, RGB `(17*x+29*y+53*c)%256`,
  normalized to PF16 0..32768 or PF32 0..1. Extent probes zero outside the hint.

## Scope and limits

This is host-shape evidence, not native AE testing, output correctness evidence,
or an assertion that the original Windows plugin accepts a case. The user-supplied
native AE observation is independent supporting evidence for Blur/ColorKey.
No disassembly or oracle comparison is performed by the driver.

The matrix is one-factor-at-a-time, not every Cartesian combination. All 19
situations use all three depths and defaults plus ten sampled corpus entries
where available. ColorKeep has no retained JSON corpus records, so its matrix
contains defaults only and the ticket must report that missing coverage.
The baseline's first 90 rows are ten plugins x three downsample settings x three
depths. Smoother v1 uses Classic (its shipped path); ROI request rectangles do
not reach its Classic selector, and expansion does not apply to that plugin.
Its GLOBAL_SETUP flags do not advertise FLOAT_COLOR_AWARE; directly supplying
PF32 is an unsupported-host-input probe, not proof of a black 32bpc AE comp.
AE may supply a converted supported-depth world.

Corpus samples are selected deterministically from records whose current saved
route says `exact`. This is provenance, not newly verified exactness on HEAD or
at large sizes. Parameters remain unchanged, including absolute point values.
For fewer than ten eligible records, all available records are used and the
remaining entries are sampled **with replacement**; manifests expose duplicates.
They are not ten independent tuples. No new exactness claim is made.

The inherited suite implementation only supports a subset of AE callbacks.
Unsupported callback results are separately classified `host_error`, never
silently counted as plugin refusals. Auxiliary layer parameters are empty/None;
no separate layer pixels, threading, GPU, color management, tile-origin input
checkout, or actual compositor is simulated. ROI keeps the full input/output
world; this cannot prove correctness for cropped input worlds. The output
expansion path cannot be considered exercised unless dimensions actually grow.

Empty output is a sanity datum, not automatically a failure: a valid key/matte
can be transparent. `render_seconds` on a PreRender refusal measures a skipped
render and must not be interpreted as successful frame performance. A timeout
is a lower bound on process time, not a measured rendering time.

## P00b rerun changes

P00b uses cache `~/.cache/olm-emu/P00b`, a 60-second process timeout, and
first runs 8bpc defaults for all ten plugins at 1080p/4K with 1/1, 1/2 and
1/4 downsample (60 rows). The full matrix adds 4K half/quarter probes (21
situations). If a plugin has no top-level corpus JSON, the driver also searches
nested retained cases; this supplies three ColorKeep T15b anchors, sampled with
replacement and labelled by their original geometry provenance.

Current ColorKeep supplies an explicit area to ordinary iterate. P00's callback
rejected every non-null area, yielding six baseline host errors. P00b clips the
requested rectangle to the source/destination world intersection, preserving
independent rowbytes and leaving other destination pixels untouched. The SDK
`AE_EffectCBSuites.h` documents NULL as all pixels; current ColorKeep's
`ColorKeepRenderSmart` passes output extent explicitly. `test_P00b_iterate.cpp`
checks explicit-area clipping, unequal world sizes, NULL/full intersection,
and untouched destination bytes. The original host-error rows are retained
separately, and the baseline was rerun after this host-only correction.

This callback has no compositor/transform semantics beyond ordinary coordinate
intersection. It does not establish native AE numerical conformance.
