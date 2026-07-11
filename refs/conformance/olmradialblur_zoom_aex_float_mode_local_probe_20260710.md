# OLMRadialBlur Zoom AEX-Float Mode Local Probe

Date: 2026-07-10  
Case: `case_0009`, 8bpc Zoom  
Reference: current packaged Windows Software `refs/win_references/20260604_olm/OLMRadialBlur/case_0009.png`

## Scope

Mac/local diagnostic evidence only. This is not Windows truth and does not
authorize a source edit. The worktree was already dirty; no existing file was
reverted or edited for this probe.

The reference top-row alpha-254 target set is `{6, 7, 12}`. Controls used in
the row classification were `x=8` and `x=24`; the reference values there are
alpha 255.

## FACT

- The Zoom CLI default is double precision for polar-grid coordinate
  generation and for inverse `dx/dy -> sqrt/atan2` coordinate generation.
- The existing Zoom option `--zoom-grid-mode aex-float` makes the forward grid
  arithmetic scalar-float-like, but still uses separate `std::sin` and
  `std::cos` calls rather than the AEX paired-trig helper.
- The existing `--rgba-sampler-alpha-mode repeat-raw-f32` and
  `--outer-caller-collapse-mode polar-alpha` options are also available. The
  existing `--rotation-grid-mode aex-float` inverse path is for Rotation, not
  this Zoom case; Zoom has no implemented inverse-float CLI switch.
- The AEX-oriented audit identifies scalar-float forward coordinates and
  scalar-float inverse coordinates as the narrow parity hypothesis. A reduced
  32x32/q90 AEX prefill check is not a full-size final-plane proof.

## Fresh Full-Frame Renders

All four runs used the existing CLI and the existing `run_reference_test.py`
against the Software reference. `max` is the maximum absolute byte-channel
delta, `mean` is mean absolute channel delta, and `nonzero_px` counts pixels
with any nonzero RGBA difference.

| Variant | Target hits / 3 | Row FP | Row FN | Max | Mean | Nonzero pixels | Nonzero % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| default double | 0 | 0 | 3 | 1 | 0.004613474 | 31,119 | 1.500723 |
| `--zoom-grid-mode aex-float` | 0 | 0 | 3 | 1 | 0.004609134 | 31,097 | 1.499662 |
| grid AEX-float + `repeat-raw-f32` | 0 | 0 | 3 | 1 | 0.004609134 | 31,097 | 1.499662 |
| grid AEX-float + `repeat-raw-f32` + `polar-alpha` | 0 | 0 | 3 | 1 | 0.004609134 | 31,097 | 1.499662 |

The grid AEX-float change therefore removes 22 differing pixels and lowers
mean channel error by `0.000004340`; it does not change the primary target
classification. Fresh candidate pixels at `(6,0)`, `(7,0)`, `(12,0)` remain
alpha 255 instead of reference alpha 254. The controls `(8,0)` and `(24,0)`
remain alpha 255, as required. No tested full-frame variant emitted a row
false-positive alpha 254.

The earlier local quantize-locus run additionally tested the existing
`polar-alpha` plus global truncate path. It emitted the `(6,0)` target, but
the full-frame `nonzero_px` count rose to `567,071`; this is an overbroad
quantizer effect, not evidence for a bounded parity change.

## Existing Final-Sample Float Replay

Command-level replay of the existing `analyze_olmradialblur_zoom_final_sample_float_sequence.py`
uses the captured local cell/coordinate locus and does not render or modify
the implementation. Results for the target set `{6,7,12}`:

| Sequence | Quantizer | Hits | FP | FN |
| --- | --- | --- | --- | --- |
| current double sum | epsilon | 0/3 | 0 | 3 |
| f32 products, double sum | epsilon | 0/3 | 0 | 3 |
| f32 products, sequential f32 sum | epsilon | 0/3 | 0 | 3 |
| f32 products, grouped f32 sum | epsilon | 0/3 | 0 | 3 |
| f32 products, sequential f32 sum | truncate | 1/3 (`x=12`) | 3 (`x=1,15,16`) | 2 |
| f32 products, double sum | truncate | 3/3 | 11 | 0 |

The last row is the best arithmetic-only target hit, but its 11 false
positives reject final weight/sum precision as a sufficient rule. The prior
cell-set search likewise found a target-complete offset only with 11 false
positives (`x=3,4,8,10,11,13,24,25,26,27,28`).

## Commands Run

```bash
python3 scripts/analyze_olmradialblur_zoom_quantize_locus.py \
  --output-json /tmp/olmradialblur_case0009_float_probe_20260710/locus.json \
  --output-md /tmp/olmradialblur_case0009_float_probe_20260710/locus.md
python3 scripts/analyze_olmradialblur_zoom_final_sample_float_sequence.py \
  --locus-json /tmp/olmradialblur_case0009_float_probe_20260710/locus.json \
  --output-json /tmp/olmradialblur_case0009_float_probe_20260710/final-sequence.json \
  --output-md /tmp/olmradialblur_case0009_float_probe_20260710/final-sequence.md
python3 scripts/analyze_olmradialblur_zoom_cellset_candidate.py \
  --locus-json /tmp/olmradialblur_case0009_float_probe_20260710/locus.json \
  --output-json /tmp/olmradialblur_case0009_float_probe_20260710/cellset.json \
  --output-md /tmp/olmradialblur_case0009_float_probe_20260710/cellset.md
python3 refs/scripts/run_reference_test.py refs/win_references/20260604_olm/OLMRadialBlur \
  --run-dir /tmp/olmradialblur_case0009_float_probe_20260710/<variant> \
  --expected-effect "OLM RadialBlur" --case-id case_0009
```

The four `<variant>` commands were the default, `--zoom-grid-mode aex-float`,
that option plus `--rgba-sampler-alpha-mode repeat-raw-f32`, and the latter
plus `--outer-caller-collapse-mode polar-alpha`. The actual command lines and
outputs are retained under `/tmp/olmradialblur_case0009_float_probe_20260710`.

## INFERENCE

The existing forward AEX-float grid mode is directionally plausible but too
weak to explain the Software target: it improves the residual by only 22
pixels and misses all three alpha-254 hits. Final sampler arithmetic alone is
also rejected by the false-positive counts.

A future bounded experiment is justified for the **coordinate sequence**:
implement, behind a temporary/local diagnostic gate, the exact scalar-float
operation order including the paired-trig helper for Zoom prefill, then the
float `sqrtf`/`atan2f` inverse path. It should be tested first on the five
top-row witnesses and then on the full frame. This is a candidate experiment,
not a patch recommendation: do not promote it without a full-size Windows
witness containing final-plane cell IDs, pre-byte alpha, and the same controls.

The **final-sample float-sequence-only** candidate does not deserve a bounded
implementation patch on this evidence; it either misses targets or creates
broad false positives.

