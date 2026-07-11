# OLM Parameter Source of Truth

Updated: 2026-07-03

## Purpose

OLM plug-in parameter values must not depend on memory or manual re-entry.
This note fixes the source-of-truth order for:

- default values when an effect is newly added in AE
- min/max and UI ranges
- the exact values used by a Windows reference case

## Source-of-truth order

### 1. Windows fresh-instance defaults

For a newly added plug-in instance, treat the returned Windows fresh-instance
capture as the source of truth for:

- cold-start default value
- popup default index as AE actually shows it
- checkbox default on/off
- property ordering and group shape as AE actually exposes it

Primary anchor:

- [refs/win_references/20260629_202911__olm_fresh_instance_defaults_20260629_windows_return/OLMmulti-effectdefaultcapture/reference_manifest.json:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/win_references/20260629_202911__olm_fresh_instance_defaults_20260629_windows_return/OLMmulti-effectdefaultcapture/reference_manifest.json:1)
- Committed parity note:
  [refs/conformance/windows_fresh_param_parity_20260703.md:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/windows_fresh_param_parity_20260703.md:1)
- Audit summary:
  [refs/reports/windows_fresh_defaults_audit_20260629.md:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/windows_fresh_defaults_audit_20260629.md:1)

This is the correct place to answer questions like:

- "What should this plug-in default to when added to a layer in Windows AE?"
- "What enum index is actually selected at cold start?"
- "Did we port the same initial state or just what the Mac source happened to declare?"

### 1.5. Windows fresh-instance ranges

For a newly added plug-in instance, treat the returned Windows fresh-instance
range capture as the source of truth for:

- AE scripting `minValue` / `maxValue` where Windows exposes them
- popup/count shape as AE reports it at cold start
- which parameters have no readable AE-side range metadata at all

Primary anchor:

- [refs/win_references/olm_fresh_instance_ranges_20260629/OLMmulti-effectrangecapture/reference_manifest.json:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/win_references/olm_fresh_instance_ranges_20260629/OLMmulti-effectrangecapture/reference_manifest.json:1)
- Committed parity note:
  [refs/conformance/windows_fresh_param_parity_20260703.md:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/windows_fresh_param_parity_20260703.md:1)
- Audit summary:
  [refs/reports/windows_fresh_ranges_audit_20260629.md:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/windows_fresh_ranges_audit_20260629.md:1)

This is the correct place to answer questions like:

- "What slider bounds does Windows AE actually expose for this plug-in?"
- "Is the Mac port's hard min/max just a placeholder?"
- "Which controls have no Windows-readable range and therefore need code/SDK inspection instead?"

### 2. Slider ranges and code-declared UI bounds

Treat each Mac port's `ParamsSetup(...)` as the source of truth for:

- hard min/max currently compiled into the Mac port
- UI min/max currently compiled into the Mac port
- symbolic enum constants and code-side naming

This is the correct place to answer questions like:

- "What range is the current Mac port exposing?"
- "Which symbolic enum name maps to this popup value?"
- "Which defaults still need to be changed to match Windows?"

### 3. Per-case validation values

For any validation case, treat the Windows `reference_manifest.json` as the
source of truth for:

- exact parameter values
- exact popup selections
- exact checkbox states
- color values
- AE-built-in effect metadata captured alongside the OLM effect

This is the correct place to answer questions like:

- "What did Windows AE actually render for `case_0009`?"
- "Was this case using Legacy on or off?"
- "Which Color Space / Gamma / Merge Mode was selected?"

### 4. Conflict rule

If Windows fresh-instance defaults and `ParamsSetup(...)` disagree, Windows wins
for cold-start behavior and `ParamsSetup(...)` is treated as a port bug or stale
placeholder until proven otherwise.

If Windows fresh-instance range metadata and `ParamsSetup(...)` disagree, Windows
wins for user-visible AE range behavior and `ParamsSetup(...)` is treated as a
UI-schema mismatch until proven otherwise.

If a per-case manifest disagrees with both, the per-case manifest wins for that
case's validation and reproduction.

Reason: Windows fresh-instance capture records the original AEX behavior on a
newly added effect instance; case manifests record the exact Windows AE state
used to produce a reference PNG.

## Operating rule

When we build a new probe, fixture, or AE-host validation case:

1. Start from Windows fresh-instance capture if the question is about "what is
   the default when the user first adds the effect?"
2. Start from Windows fresh-instance range capture if the question is about
   "what bounds does Windows AE expose for this control?"
3. Use `ParamsSetup(...)` for current code ranges and symbolic labels, not as
   final proof of Windows defaults/ranges.
4. As soon as a per-case Windows manifest exists, stop using guessed defaults
   for that case and use the manifest literally.
5. Do not infer execution path from `GPU Rendering` / `ADBE Force CPU GPU`.
   Use `project_gpu_accel_type` as reference metadata for the render set.

## Fresh-instance mismatch status

The 2026-06-29 audit exposed several real Windows-vs-Mac cold-start default
disagreements. Those defaults have now been patched in the Mac source for:

- `OLMBlur`
- `OLMRadialBlur`
- `OLMKiraKira`
- `OLMSmoother2`
- `OLMToonDilate`
- `OLMDistanceGradation`

Current audit truth should be checked in:

- [refs/conformance/windows_fresh_param_parity_20260703.md:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/windows_fresh_param_parity_20260703.md:1)
- [refs/reports/windows_fresh_defaults_audit_20260629.md:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/windows_fresh_defaults_audit_20260629.md:1)
- [refs/reports/windows_fresh_ranges_audit_20260629.md:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/windows_fresh_ranges_audit_20260629.md:1)
- [refs/reports/windows_fresh_param_parity_summary_20260630.md:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/windows_fresh_param_parity_summary_20260630.md:1)

Any newly reported mismatch after that point should be treated as a fresh host
bug, schema-extraction bug, or normalization bug rather than a memory issue.

The range audit exposed real Windows-vs-Mac UI bound mismatches that are
tracked as schema work rather than algorithm drift.

For a quick per-plug-in host-parity snapshot, use the generated summary:

- [refs/conformance/windows_fresh_param_parity_20260703.md:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/windows_fresh_param_parity_20260703.md:1)
- [refs/reports/windows_fresh_param_parity_summary_20260630.md:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/windows_fresh_param_parity_summary_20260630.md:1)

This report compresses the defaults audit plus range audit into:

- `fixed`
- `mostly-fixed`
- `needs-followup`

for each plug-in, and lists the next schema/UI gap that still blocks a clean
Windows-fresh host-parity claim.

To regenerate the committed snapshot from the imported Windows manifests:

```sh
python3 scripts/materialize_windows_fresh_param_parity.py --stamp 20260703
```

2026-06-29 first-pass host-range alignment has already landed for:

- `OLMBlur`
  - `Blur Amount`: Mac hard min `0.05 -> 1.0` to match Windows `1..1000`
- `OLMDirectionalBlur`
  - `Front/Back Blur Strength`: `0..3000 -> 0..4000`
  - `Front/Back Alpha Fade`: `0..3000 -> 0..100`
  - `Seed`: `1..32767 -> 1..1000`
- `OLMDistanceGradation`
  - `Inside/Outside Threshold`: `0..4096 -> 0..1000`
- `OLMRadialBlur`
  - `Outer/Inner Strength`: `0..3000 -> 0..2000`
  - `Ratio`: `0.01..10.0 -> 1.0..5.0`
  - `Seed`: `1..32767 -> 1..1000`
- `OLMSmoother2`
  - `Smoothness`: `0..1000 -> 0..100`
  - `Extra Smooth`: `0..1000 -> 0..100`
  - `Smooth Range`: `1..32 -> 0..100`
  - `Gamma Value`: `0.1..10.0 -> 1.0..2.4`
- `OLMToonDilate`
  - `Search Radius`: `0..1000 -> 0..100`

After that pass, the highest-signal remaining host-range/schema gaps are:

- `OLMKiraKira`
  - host surface alignment landed for:
    - `Channel` choices: `Alpha|Luminance|RGB|Brightness`
    - `Blur Mode` choices/range: Windows `1..4`
    - `Strength Multiplier`: Windows `0..1000`, slider `0..200`
    - `Glow Opacity`: Windows `0..10000`, slider `0..100`
    - `Fade Out`: Windows fresh range `0..1`
  - still unresolved:
    - `Brightness Gain` range semantics
      - Windows fresh range metadata says `1..100`
      - returned reference manifests also contain real applied float values like
        `9.39999961853027`, so the host control is not safely modeled as a
        plain integer `1..100` slider yet
    - `Highlight Radius` hard max (`500` Windows fresh capture vs `1000` manual/source)
- `OLMRadialBlur`
  - `Offset` still reads as mismatched in the current audit, but this is mixed
    with duplicate label normalization (`Outer Offset`, `Inner Offset`,
    `Noise Offset`) and should be treated as an audit-target, not immediately as
    an algorithm bug

These are UI-schema mismatches. They do not automatically prove algorithm
drift, but they do mean the current Mac port should not claim Windows-equivalent
host behavior for those controls yet.

## Current parameter-definition anchors

| Plug-in | Primary `ParamsSetup(...)` anchor | Notes |
| --- | --- | --- |
| OLMBlur | [mac/OLMBlur/OLMBlur.cpp:31](/Users/onmk/Documents/Projects/Personal/OLM%20as/mac/OLMBlur/OLMBlur.cpp:31) | Blur Amount, Smoothness, Repeat, Bias Direction, Legacy |
| OLMColorKey | [mac/OLMColorKey/OLMColorKey.cpp:54](/Users/onmk/Documents/Projects/Personal/OLM%20as/mac/OLMColorKey/OLMColorKey.cpp:54) | Thresholds, per-color slots, replace colors, edge params |
| OLMSmoother v1 | [mac/OLMSmoother/Mac/OLMSmoother_port.cpp:95](/Users/onmk/Documents/Projects/Personal/OLM%20as/mac/OLMSmoother/Mac/OLMSmoother_port.cpp:95) | Use Key, Key Color, Tolerance |
| OLMSmoother v2 | [mac/OLMSmoother2/OLMSmoother2.cpp:733](/Users/onmk/Documents/Projects/Personal/OLM%20as/mac/OLMSmoother2/OLMSmoother2.cpp:733) | Keying, Smoothness, Extra Smooth, Version, Gamma |
| OLMDirectionalBlur | [mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:45](/Users/onmk/Documents/Projects/Personal/OLM%20as/mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:45) | Angle, front/back blur groups, noise block |
| OLMRadialBlur | [mac/OLMRadialBlur/OLMRadialBlur.cpp:47](/Users/onmk/Documents/Projects/Personal/OLM%20as/mac/OLMRadialBlur/OLMRadialBlur.cpp:47) | Outer/Inner groups, ellipse, noise, repeat border |
| OLMKiraKira | [mac/OLMKiraKira/OLMKiraKira.cpp:470](/Users/onmk/Documents/Projects/Personal/OLM%20as/mac/OLMKiraKira/OLMKiraKira.cpp:470) | Glow lengths, merge/channel mode, colors, ramps |
| OLMDistanceGradation | [mac/OLMDistanceGradation/OLMDistanceGradation.cpp:33](/Users/onmk/Documents/Projects/Personal/OLM%20as/mac/OLMDistanceGradation/OLMDistanceGradation.cpp:33) | Thresholds, render mode, colors, power, blur mode |
| OLMToonDilate | [mac/OLMToonDilate/OLMToonDilate.cpp:45](/Users/onmk/Documents/Projects/Personal/OLM%20as/mac/OLMToonDilate/OLMToonDilate.cpp:45) | Search Radius only |

## Default/range snapshot

This is a convenience summary for the most common "what is the default?" checks.
When in doubt, the code link above is the canonical source.

### OLMBlur

- Blur Amount: default `5.0`, range `1.0..1000.0`, UI `1.0..50.0`
- Blur Smoothness: default `100`, range `1..100`
- Repeat: default `2`, range `1..10`
- Bias Direction: popup default `1`
- Legacy: default `off`

### OLMColorKey

- Color Keep: default `off`
- Threshold: default `0.0`, range `0.0..1.0`
- Premultiplied Color: default `off`
- Color Space: popup default `1`
- Force Lower Precision: popup default `1`
- Per Color: default `off`
- Per Component: default `off`
- Edge Thin Amount: default `0.0`, range `-100.0..100.0`
- Edge Blur Amount: default `0.0`, range `0.0..100.0`
- Number of Colors: default `1`, range `1..OLMCOLORKEY_MAX_COLORS`
- Enable Replace: default `off`
- Use Color 1: default `on`

### OLMSmoother v1

- Use Color Key: default `off`
- Color Key: default white
- Smooth Length Tolerance: default `6`, range `0..255`, UI `0..6`

### OLMSmoother v2

- Enable Color Key: default `off`
- Color Key: default white
- Invert Color Key: default `off`
- Smoothness: default `100`, range `0..100`, UI `0..100`
- Extra Smooth: default `0`, range `0..100`, UI `0..100`
- Smooth Range: default `2`, range `0..100`, UI `0..100`
- Smoother Version: popup default `SMOOTHER_V2`
- Gamma Correction: popup default `GAMMA_NONE`
- Gamma Value: default `2.4`, range `1.0..2.4`, UI `1.0..2.4`
- Number of Gamma Colors: default `1`

### OLMDirectionalBlur

- Angle: default `0.0`
- Brightness Gain: default `1.0`
- Size Variation: default `0.0`
- Front Strength / Back Strength: default `0`
- Front Alpha Fade / Back Alpha Fade: default `0`
- Front Sharp Tail / Back Sharp Tail: default `0.0`
- Noise Variation: default `0.0`
- Noise Type: popup default `1`
- Seed: default `1`
- Noise Offset: default `0`
- Thickness: default `10.0`

### OLMRadialBlur

- Blur Type: popup default `1`
- Center: default `(960, 540)`
- Outer Strength: default `0`, range `0..2000`
- Outer Offset Mode: popup default `1`
- Outer Offset: default `153`
- Outer Edge Fade: default `0.0`
- Inner Strength: default `0`, range `0..2000`
- Inner Offset Mode: popup default `1`
- Inner Offset: default `0`
- Inner Edge Fade: default `0.0`
- Repeat Border: default `on`
- Ratio: default `1.0`, range `1.0..5.0`
- Angle: default `0.0`
- Quality: default `5.0`
- Brightness Gain: default `1.0`
- Size Variation: default `0.0`
- Noise Variation: default `0.0`
- Noise Type: popup default `1`
- Seed: default `1`
- Noise Offset: default `0`
- Thickness: default `10.0`

### OLMKiraKira

- Glow Rotation: default `0.0`
- Brightness Gain: default `1.0`
- Vertical / Horizontal / Diagonal Length: default `50`
- Highlight Radius: default `0`
- Glow Opacity: default `100`
- Channel: popup default `1`
- Blur Mode: popup default `2`
- Approximated Input: default `off`
- Strength Multiplier: default `100`
- Source Opacity: default `100`
- Vertical / Horizontal / Diagonal / Highlight Color: default white
- Merge Mode: popup default `1`
- Ramp toggles: default `off`
- Diagonal2 Length: default `50`
- Fade Out: default `0`
- Diagonal2 Color: default white
- Diagonal2 Use Ramp: default `off`
- UI/schema caution:
  Windows fresh-instance captures expose per-direction topic labels such as
  `Vertical Color Ramp` and `Highlight Color Ramp`, but the actual child
  checkbox inside each topic still appears as `Use Ramp`. Treat those topic
  labels and child labels as separate schema facts; do not "fix" the child
  checkbox by renaming it to the topic title unless a fresh Windows capture
  also changes the child label itself.

### OLMDistanceGradation

- Invert: default `off`
- In/Out: popup default `IN_OUT_BOTH`
- Inside Threshold: default `128`, range `0..4096`, UI `0..512`
- Outside Threshold: default `128`, range `0..4096`, UI `0..512`
- Render Mode: popup default `RENDER_MODE_RGB`
- Use BG Color: default `off`
- Grad Color: default literal RGB (`255,0,0`)
- BG Color: default black
- Interp Mode: popup default `INTERP_LINEAR`
- Power: default `1.0`, range `0.01..5.0`
- Blur Mode: popup default `BLUR_MODE_NONE`
- Blur Size: default `0`

### OLMToonDilate

- Search Radius: default `2.0`, range `0.0..1000.0`, UI `0.0..100.0`

## Manifest anchors

Representative manifest roots that already capture real Windows case values:

- OLMColorKey:
  [refs/win_references/olm_reference_return_windows_20260614/OLMColorKey/reference_manifest.json:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/win_references/olm_reference_return_windows_20260614/OLMColorKey/reference_manifest.json:1)
- OLM bit-depth normalized suite:
  [refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json:1)
- Current Smoother2 residual audit:
  [refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/reference_manifest.json:1](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/reference_manifest.json:1)

## Practical implication

If we need to reproduce a case and a manifest exists, we should not ask the user
to restate the values manually. We should ingest the manifest and use that.

Manual user input should only be needed for:

- entirely new cases not yet captured on Windows
- AE project/setup choices not yet encoded in the request package
- genuinely missing host-side metadata

## Fresh default return audit

Once the Windows return for
`refs/reference_requests/olm_fresh_instance_defaults_20260629.json` is imported,
audit it with:

```sh
python3 scripts/audit_windows_fresh_defaults.py \
  path/to/imported/reference_manifest.json
```

This writes:

- `refs/reports/windows_fresh_defaults_audit_latest.json`
- `refs/reports/windows_fresh_defaults_audit_latest.md`

Use that audit to separate:

- source-backed current Mac UI defaults
- original Windows AEX cold-start defaults
- controls that are source-only, Windows-only, symbolic, or structurally aliased

If the return is imported through:

```sh
python3 scripts/intake_olm_return.py path/to/returned_reference.zip --quick
```

then the fresh-default audit now runs automatically when the imported manifest
contains request id `olm_fresh_instance_defaults_20260629`, and dated reports
are written under `refs/reports/`.
