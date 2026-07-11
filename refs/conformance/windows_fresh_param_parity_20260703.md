# Windows Fresh Parameter Parity Audit - 2026-07-03

This note freezes the current Windows cold-start defaults/ranges parity state
into `refs/conformance` so later host/debug work does not depend on ignored
`refs/reports` artifacts.

Inputs:
- Defaults manifest: `refs/win_references/olm_fresh_instance_defaults_20260629/OLMmulti-effectdefaultcapture/reference_manifest.json`
- Ranges manifest: `refs/win_references/olm_fresh_instance_ranges_20260629/OLMmulti-effectrangecapture/reference_manifest.json`
- Mac schema snapshot: `refs/reports/mac_plugin_param_schema_20260629.json`

Status meaning:
- `fixed`: no actionable parity gap in the current cold-start defaults/ranges lane.
- `mostly-fixed`: narrow remaining drift, typically aliases, symbolic defaults, or grouped placeholder rows.
- `needs-followup`: there is still a real Windows-visible default/range mismatch worth fixing.

| Plug-in | Defaults | Ranges | Overall | Next gap |
| --- | --- | --- | --- | --- |
| `OLMBlur` | `fixed` | `mostly-fixed` | `mostly-fixed` | OLMBlur: no immediate fresh-instance schema blocker |
| `OLMColorKey` | `mostly-fixed` | `mostly-fixed` | `mostly-fixed` | Use Color 1: symbolic_examples |
| `OLMDirectionalBlur` | `mostly-fixed` | `mostly-fixed` | `mostly-fixed` | OLMDirectionalBlur: no immediate fresh-instance schema blocker |
| `OLMDistanceGradation` | `mostly-fixed` | `mostly-fixed` | `mostly-fixed` | Blur Mode: symbolic_examples |
| `OLMKiraKira` | `fixed` | `mostly-fixed` | `mostly-fixed` | OLMKiraKira: no immediate fresh-instance schema blocker |
| `OLMRadialBlur` | `mostly-fixed` | `mostly-fixed` | `mostly-fixed` | OLMRadialBlur: no immediate fresh-instance schema blocker |
| `OLMSmoother` | `fixed` | `mostly-fixed` | `mostly-fixed` | Smooth Length Tolerance: source_only_examples |
| `OLMSmoother2` | `mostly-fixed` | `mostly-fixed` | `mostly-fixed` | Gamma Color 2: source_only_examples |
| `OLMToonDilate` | `fixed` | `fixed` | `fixed` | OLMToonDilate: no immediate fresh-instance schema blocker |

## Operational read

- This lane is about AE-visible defaults and slider/range metadata, not algorithm exactness.
- A `fixed` or `mostly-fixed` row does not promote the plug-in to `AE exact`.
- `needs-followup` means Mac host/UI work can still remove ambiguity before image-path debugging.

## Per plug-in notes

### OLMBlur

- Defaults: `fixed` (all compared Windows defaults matched current Mac schema)
- Ranges: `mostly-fixed` (source-no-range 1)
- Next gap: OLMBlur: no immediate fresh-instance schema blocker

### OLMColorKey

- Defaults: `mostly-fixed` (source-empty 2, symbolic defaults 25)
- Ranges: `mostly-fixed` (symbolic range 1, source-no-range 105, windows-no-range 2)
- Next gap: Use Color 1: symbolic_examples

### OLMDirectionalBlur

- Defaults: `mostly-fixed` (source-empty 2)
- Ranges: `mostly-fixed` (windows-no-range 5)
- Next gap: OLMDirectionalBlur: no immediate fresh-instance schema blocker

### OLMDistanceGradation

- Defaults: `mostly-fixed` (symbolic defaults 4)
- Ranges: `mostly-fixed` (source-no-range 4)
- Next gap: Blur Mode: symbolic_examples

### OLMKiraKira

- Defaults: `fixed` (all compared Windows defaults matched current Mac schema)
- Ranges: `mostly-fixed` (source-no-range 11, windows-no-range 1)
- Next gap: OLMKiraKira: no immediate fresh-instance schema blocker

### OLMRadialBlur

- Defaults: `mostly-fixed` (source-empty 5)
- Ranges: `mostly-fixed` (source-no-range 1, windows-no-range 8)
- Next gap: OLMRadialBlur: no immediate fresh-instance schema blocker

### OLMSmoother

- Defaults: `fixed` (all compared Windows defaults matched current Mac schema)
- Ranges: `mostly-fixed` (source-no-range 2)
- Next gap: Smooth Length Tolerance: source_only_examples

### OLMSmoother2

- Defaults: `mostly-fixed` (symbolic defaults 2)
- Ranges: `mostly-fixed` (symbolic range 1, source-no-range 8)
- Next gap: Gamma Color 2: source_only_examples

### OLMToonDilate

- Defaults: `fixed` (all compared Windows defaults matched current Mac schema)
- Ranges: `fixed` (all Windows-exposed ranges matched current Mac hard min/max)
- Next gap: OLMToonDilate: no immediate fresh-instance schema blocker
