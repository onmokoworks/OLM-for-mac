# OLMToonDilate 32bpc Typed-Procedural AE Exact — 2026-07-28

The declared `olmtoondilate_typed_procedural_64x64` profile is Windows/Mac
AE exact at both required raw FLOAT32 gates.

## Contract

- AE: `26.3x87`
- Project: `32bpc`, Software renderer, working space None, linear blending off
- Fixture: `scripts/ae_generate_32bpc_typed_procedural_fixture.jsx`
- Fixture commit: `7db4aa313fe319c26465ac1c78e1d042dce82fed`
- Fixture SHA-256:
  `665fa9f05fe652895cb7c7f94064f2471ef992c74751cd11a4254aeb00529d82`
- Input: one AE-generated `64x64` source comp with a transparent background
  and four integer-position semi-alpha/opaque rectangles
- Effect: `OLM Toon Dilate`
- Search Radius: requested `13`, read back `13` on both hosts
- Output: uncompressed `A/B/G/R` FLOAT OpenEXR, `64x64`

The former fixture used an opaque full-frame black background. That made every
input alpha opaque and therefore made ToonDilate correctly no-op. Commit
`7db4aa31` repairs the fixture without changing the plug-in core: ToonDilate
uses a transparent background, the Search Radius property identity/value is
fail-closed, and ColorKey retains its opaque-background profile.

## Runtime binding

- Mac AE PID `75663` loaded
  `/Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMToonDilate.plugin/Contents/MacOS/OLMToonDilate`
  according to `vmmap`. Mach-O SHA-256:
  `731798e1386f04afd181523e3fd55fbf5824a89b7ea97493281217ed5882c36e`.
- Windows AE PID `40764`, Session `1`, started
  `2026-07-28T01:15:58.0015191+09:00`, loaded
  `C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMToonDilate.aex`
  at `0x2d005ef0000` according to `System.Diagnostics.Process.Modules`.
  AEX SHA-256:
  `c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3`.

## Raw FLOAT32 result

| Gate | Compared words | Mismatched words | Max raw-u32 delta |
| --- | ---: | ---: | ---: |
| Windows no-effect vs Mac no-effect | 16,384 | 0 | 0 |
| Windows effect-on vs Mac effect-on | 16,384 | 0 | 0 |

The Mac effect-on output differs from its no-effect control at `6,448` words,
so this is not a pass-through/no-op coincidence. All four retained EXRs contain
exactly `16,384` finite FLOAT samples, no NaN or infinity, channel order
`A/B/G/R`, and compression code `0`.

## Decision

Promote this declared 32bpc typed-procedural Search Radius `13` profile to
`AE exact`. Both the no-effect attribution gate and the effect-on gate are raw
exact under one hash-bound cross-host contract.

This is deliberately narrow. It does not promote every possible 32bpc
ToonDilate input or Search Radius value.

Machine-readable evidence and the four source EXRs are retained in
`refs/conformance/olmtoondilate_32bpc_typed_procedural_ae_exact_20260728.json`
and
`refs/conformance/olmtoondilate_32bpc_typed_procedural_ae_exact_20260728/`.
