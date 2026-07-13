# DirectionalBlur Alpha Fade residual stage audit

Status: `stage-not-yet-localized`; production unchanged.

## Scope

This audit is limited to the current 2025-AEX Alpha Fade case
`db_angle0_alpha_fade_hard_edges`, `front_strength=240`,
`front_alpha_fade=96`, PREMULTIPLIED 8bpc input. The accepted comparison is
the current raw PF-world return, not the superseded June 19 PNG.

## FACT

- The Windows raw PF worlds are present and size-valid at `1920x1080x4` bytes:
  `refs/win_references/20260711_directionalblur_front_alpha_current_2025_aex/raw/input_argb8_tight.bin`
  and `output_argb8_tight.bin`.
- The validated Windows UCRT return contains exactly `96 + 240 = 336`
  Gaussian result words. Every word matches the current double-exp/f32 model
  used by `core/dblur_gaussian.h`.
- The bounded actual-AEX leaf gate remains byte-exact for the Alpha Fade
  front-only full-entry core, and the bounded full rowdriver gate remains
  byte-exact for its declared fixtures.
- The residual after the accepted UCRT update is `226` pixels, all at
  `x=1308`, `y=184..517`, with maximum channel delta `3`.

## FACT: current stage boundary

The available Windows return contains only input/output PF worlds. It does not
contain prepass destination/denominator/alpha planes, scatter destination or
denominator planes, normalized work-buffer bytes, or rotate-back output. The
existing full-entry Unicorn runner was attempted with the same source and
parameters, but the unmodified AEX worker reached its 2206x2206 internal pass
and exhausted the 200,000,000 instruction budget before PF Iterate8. It produced
no intermediate buffer and is not evidence for a stage mismatch.

## INFERENCE

The Gaussian table stage is not the remaining explanation: the returned UCRT
words and the portable model are equal for both live table sizes. The first
live differing stage is therefore still unobserved among prepass, scatter
buffer ordering/accumulation, normalization, rotate-back, and host output.
The final-column shape alone cannot distinguish those operations.

## Commands

```sh
python3 refs/scripts/smoke_dblur_alpha_fade_stage_residual_20260712.py
python3 tools/emulation/dblur_fullrender_host_fixture_20260711.py \
  --source refs/win_references/20260711_directionalblur_front_alpha_current_2025_aex/input/directionalblur_context_scale_20260606__software__fr24__db_angle0_alpha_fade_hard_edges_before_effects.png \
  --angle 0 --size-variation 0 --front-strength 240 --front-alpha-fade 96 \
  --front-sharp-tail 0 --back-strength 0 --back-alpha-fade 0 \
  --back-sharp-tail 0 --noise-variation 0 --no-detour-rotate --no-detour-rowdriver \
  --downsample-num 1 --downsample-den 1 --max-instructions 200000000 \
  --output <scratch-output.json>
```

The next binary-grounded step is a focused actual-AEX capture of one affected
prepass/scatter call, retaining destination, denominator, and alpha buffers
before and after that call. No PNG tuning or production change is authorized
by this audit.
