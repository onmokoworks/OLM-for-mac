# OLMBlur `case_0006` Reference Provenance - 2026-07-01

> **Evidence correction (2026-07-10):** the claimed Windows helper/pre-store
> values in this historical note are not runtime-grounded. The CDB target bind
> failed, no `TARGET_OLMBLUR_CASE0006_*` block was captured, and the later
> `windows_*` values merely duplicate the Mac values. Do not use the sections
> below that say Windows and Mac agree internally. The current authority is
> `refs/conformance/olmblur_case0006_unverified_windows_value_audit_20260710.md`.

This note historically narrowed `case_0006` to a provenance/export question.
That narrowing is retracted by the correction above; the typed Windows
helper/pre-store boundary remains open.

## Scope

- Plug-in: `OLMBlur`
- Lane: `olmblur__case_0006` non-Legacy 16bpc
- Active question:
  after the 2026-07-01 answered witness proved Windows and Mac agree on
  pre-store float and stored internal word at the tracked points, what
  comparison artifact is still disagreeing?

## Canonical 16bpc reference chain

The canonical Windows Software 16bpc reference file and the handoff expected
file are byte-identical:

| Role | Path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| canonical Windows Software 16bpc ref | `refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `2485242` | `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f` |
| handoff expected mirror | `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `2485242` | `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f` |

So there is no ambiguity about which canonical PNG the current 16bpc Mac AE
lane is comparing against.

## Current Mac-side exports in this lane

Known Mac-side exported candidates are different files:

| Role | Path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| single-case Mac AE witness export | `refs/reports/ae_single_case_olmblur_16bpc_witness_latest/olmblur__case_0006/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `2485331` | `8990ef5b4cbf82b2d86e4a6014e4d8944eff24397aa97c1fb8ceafcc310a8787` |
| 2026-06-26 23:35 endian-fix batch candidate | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_2335_endian_fix/bitdepth16_olmblur_exact/candidate/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `2485333` | `d99b462a4f273578c616a556cf844db515694706ae3e7fad2bc2b9c4de152974` |

This is expected: these are Mac exports, not the Windows canonical file.

All three files are genuine 16-bit RGBA PNGs (`file` reports
`PNG image data, 1920 x 1080, 16-bit/color RGBA, non-interlaced`). Read
pixel values with ImageMagick or another 16-bit-aware reader; simple 8-bit
RGBA decoders will collapse these values and hide the one-word families.

## Proven internal witness boundary

The answered Windows witness and the live Mac witness now agree at the two
tracked non-Legacy points:

| XY | Windows pre-store float | Windows stored word | Mac live raw | Mac stored word | Canonical ref PNG | Mac export PNG |
| --- | --- | --- | --- | --- | --- | --- |
| `(314,14)` | `1100.5` | `1100` | `1100.5` | `1100` | `[2201,2201,2201,65535]` | `[2199,2199,2199,65535]` |
| `(29,71)` | `363.5` | `364` | `363.5` | `364` | `[725,725,725,65535]` | `[727,727,727,65535]` |

Primary sources:

- `refs/reports/runtime_trace_comparisons/olmblur_case0006_helper_prestore_witness.md`
- `refs/conformance/olmblur_case0006_nonlegacy_helper_witness_20260630.md`
- `refs/conformance/olmblur_current_word_baseline_20260629.md`

That retires the old primary suspicions for this lane:

- not a current live Mac helper-local mismatch at the tracked points
- not a current live Mac writer/store mismatch at the tracked points

## Export artifact split matrix

Using 16-bit reads (`magick <png> -depth 16 txt:-`) on representative
coordinates:

| XY | canonical Windows ref | single-case Mac export | 2026-06-26 batch candidate | Reading |
| --- | --- | --- | --- | --- |
| `(314,14)` | `[2201,2201,2201,65535]` | `[2199,2199,2199,65535]` | `[2201,2201,2201,65535]` | batch matches canonical; single-case stays on local stored-word model |
| `(29,71)` | `[725,725,725,65535]` | `[727,727,727,65535]` | `[727,727,727,65535]` | both Mac exports disagree with canonical in the same direction |
| `(601,598)` | `[4609,4609,4637,65535]` | `[4607,4607,4637,65535]` | `[4609,4609,4637,65535]` | batch matches canonical; single-case differs by one word on R/G |
| `(378,487)` | `[64767,35,35,65535]` | `[64767,35,35,65535]` | `[64769,35,35,65535]` | single-case matches canonical; batch differs by one word on R |

This matters because the residual no longer behaves like one coherent
"Mac implementation is always one word low/high" story.

- The single-case export agrees with the local `store16 -> export16(word)` model
  at the two lane-defining witnesses:
  - `1100 -> 2199`
  - `364 -> 727`
- The batch export matches canonical on one of those witnesses and misses on
  the other.
- Away from the original pair, the match direction flips again:
  batch matches canonical at `(601,598)`, but single-case matches canonical at
  `(378,487)`.

So even inside the current repo artifact set, no single one-line implementation
story explains all observed `case_0006` file deltas.

## Missing artifact

What is still **not** present as durable repo evidence is a same-run Windows
current-AEX 16bpc exported PNG that can be compared directly against the
canonical 2026-06-25 reference file.

The answered runtime return only records an AE-side `output_png` note:

- `logs/case_0006_effect.png`

but that note explicitly says the PNG readback is ordinary exported RGBA and is
not itself proof of PF_Pixel16 internal words. In the current repo state, that
same-run Windows export is not available here as a durable imported artifact.

## Current reading

The canonical 16bpc reference path is fixed and unambiguous.

The current Mac implementation is not the active suspect for `case_0006`,
because Windows and Mac agree on the traced pre-store float and stored word at
the two lane-defining witnesses.

The broader artifact matrix now makes that safer to say: the disagreement is
not one stable implementation-side sign pattern. It already depends on which
export artifact is compared.

The remaining open question is therefore provenance/export-side:

1. does a same-run Windows current-AEX export agree with the canonical
   2026-06-25 reference file?
2. if not, is `case_0006` effectively a reference-generation split rather than
   a live Mac port bug?

## Decision boundary

Do not change `mac/OLMBlur/OLMBlur.cpp` from this lane alone.

Required stronger evidence to reopen implementation:

- a Windows current-AEX capture that disagrees with Mac on pre-store float, or
- a Windows current-AEX capture that disagrees on the stored internal word

Otherwise, treat `case_0006` as provenance/export audit work, not source
surgery.
