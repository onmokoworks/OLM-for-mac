# ColorKey / ToonDilate 32bpc Typed Procedural Fixture Design - 2026-07-13

## Triggering evidence

The 2026-07-12 paired Mac runs for OLMColorKey and OLMToonDilate were raw
float-bit no-ops inside Mac AE, while each Windows-before vs Mac-no-effect
comparison differed at all `6,220,800` samples. The accepted classification is
`blocked-by-host-input-conversion`; the imported EXR source is not a proven
cross-host-identical input world. The existing evidence must remain unchanged.

## Fixture boundary

`scripts/ae_generate_32bpc_typed_procedural_fixture.jsx` creates the source
pixels in After Effects itself. It imports no PNG, EXR, footage, or sidecar
data. The source comp is 64x64 and contains one full-frame black solid plus
four solids whose bounds are integer `(x, y, width, height)` values:

| layer | bounds | RGB | opacity |
| --- | --- | --- | --- |
| `rect_integer_a25` | `(4,4,20,16)` | `(1,0,0)` | `0.25` |
| `rect_integer_a50` | `(28,4,20,16)` | `(0,1,0)` | `0.50` |
| `rect_integer_a75` | `(4,28,20,16)` | `(0,0,1)` | `0.75` |
| `rect_integer_a100` | `(28,28,20,16)` | `(1,1,1)` | `1.00` |

The fixture is explicitly set to 32bpc, no working space, and linear blending
off. This is an AE typed procedural source, not a claim that two hosts have
identical renderer internals.

## A/B package

One render comp contains two instances of the generated source precomp:

- `generated_source_only`: no effect, enabled for the control render.
- `generated_source_effect_on`: the selected OLMColorKey or OLMToonDilate
  effect, enabled for the effect render.

The generator renders both branches from this same comp at frame 0, changing
only layer enabled state. It writes both uncompressed FLOAT EXR targets using
the caller-provided AE output template and saves the generated `.aep`. The
manifest binds the source recipe, effect, project settings, output names, and
fail-closed requirements without embedding machine-specific absolute paths.

## Fail-closed rules

The generator refuses unsupported effect names, non-empty target artifacts,
non-32bpc/project-color drift, a missing effect, a missing output, or a missing
manifest/project package. The companion smoke rejects any later addition of
footage import/read paths and checks both effect names, all four integer/alpha
stages, same-comp A/B rendering, and the required failure guards.

This package is evidence for isolating imported-input conversion. It does not
promote either plug-in to `AE exact`, does not replace the Windows no-effect
control, and must not be used to tune ColorKey or ToonDilate pixel math until
the typed source is rendered and compared on both hosts under the same host
contract.
