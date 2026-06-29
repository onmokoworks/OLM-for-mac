# OLMBlur 16bpc Live Probe Audit - 2026-06-29

## Scope

- Plug-in: `OLMBlur`
- Host: Mac AE `26.3x87`
- Goal: tie the 2026-06-29 live `store16` debug witnesses to the exported
  16bpc PNG deltas for the two remaining proof families:
  - non-Legacy `case_0006`
  - Legacy `case_0007`

Primary artifacts:

- `refs/reports/ae_single_case_olmblur_16bpc_witness_latest/probe_report.md`
- `refs/reports/ae_single_case_olmblur_16bpc_witness_case0007_retry_20260629/probe_report.md`
- `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625/expected/*.png`

## What was measured

For each witness point we compared:

1. Mac AE live debug dump from `store16`
2. Mac AE exported 16bpc PNG value
3. Windows Software reference PNG value

The debug dump logs internal channel words before/through the final writer.
ImageMagick `-depth 16 txt:-` was used to read the exported/reference PNG
channels at the same coordinates.

## Witness table

### `olmblur__case_0006` non-Legacy

| Point | Mac raw | Mac stored word | Mac exported PNG | Windows ref PNG | Export delta | Internal interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `(314,14)` | `1100.5` | `1100` | `2199` | `2201` | `-2` | ref is one internal word higher (`1101`) |
| `(29,71)` | `363.5` | `364` | `727` | `725` | `+2` | ref is one internal word lower (`363`) |
| `(0,0)` | `0.489586234` | `0` | `0` | `0` | `0` | exact |
| `(951,7)` | `3.2578516` | `3` | `5` | `5` | `0` | exact |

### `olmblur__case_0007` Legacy

| Point | Mac raw | Mac stored word | Mac exported PNG | Windows ref PNG | Export delta | Internal interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `(314,14)` | `1203.05823` | `1203` | `2405` | `2405` | `0` | exact |
| `(29,71)` | `226.505157` | `227` | `453` | `453` | `0` | exact |
| `(0,0)` | `191.976715` | `192` | `383` | `0` | `+383` | anomaly already exists before final writer |
| `(951,7)` | `51.5` | `52` | `103` | `101` | `+2` | shared one-word family, not the main Legacy anomaly |

## Direct findings

### 1. Positive exported 16bpc values match the internal-word model

At all positive witness points here, the exported PNG channel equals:

- `2 * stored_word - 1`

Examples:

- `1100 -> 2199`
- `364 -> 727`
- `192 -> 383`
- `52 -> 103`
- `3 -> 5`

This directly explains why the known non-Legacy one-word family appears in the
PNG diffs as `+/-2`, and why the Legacy `(0,0)` witness appears as `383`.

### 2. `case_0006` remains sign-mixed one-word, not a single global rounding-direction bug

The two half-step non-Legacy witnesses land on opposite sides:

- `(314,14)` stores one word below reference
- `(29,71)` stores one word above reference

So even with live host evidence, the family is still sign-mixed. This does not
justify a blind global `nearbyintf -> floorf(v + 0.5f)` swap.

### 3. `case_0007 (0,0)` is not a final-writer problem

Legacy `case_0007` now has a live Mac AE witness at the problematic pixel:

- raw `191.976715`
- stored word `192`
- exported PNG `383`
- Windows reference PNG `0`

Therefore the surviving `case_0007` anomaly is already present before the final
16bpc word store. It is not created by the `floorf(v + 0.5f)` Legacy writer.

### 4. `case_0007 (951,7)` belongs to the shared one-word family

The Legacy retry also captured a non-anomalous point:

- Mac stored `52`
- Mac exported `103`
- Windows ref `101`

This is exactly the same `+1 internal word => +2 exported PNG` family as the
non-Legacy cases. So `case_0007` should stay split into:

- the general one-word family
- the separate Legacy border/seed/all-same anomaly at `(0,0)`

## Decision

- Keep the current OLMBlur 8bpc AE-exact behavior untouched.
- Do not perform a blind global non-Legacy writer swap from this evidence.
- Treat `case_0006` as a pre-writeback/helper-order proof target.
- Treat `case_0007 (0,0)` as a Legacy border/seed/all-same proof target.

## Commands used

```bash
python3 scripts/probe_olmblur_16bpc_store16.py \
  --output-dir refs/reports/ae_single_case_olmblur_16bpc_witness_latest

python3 scripts/probe_olmblur_16bpc_store16.py \
  --case-id olmblur__case_0007 \
  --output-dir refs/reports/ae_single_case_olmblur_16bpc_witness_case0007_retry_20260629

magick <candidate-or-reference>.png -depth 16 txt:- | egrep '^(314,14|29,71|0,0|951,7):'
```
