# Native reference/fast differential

`OLM_REFERENCE_BUILD=1` selects the readable scalar/sequential reconstruction.
Without that compile definition, builds retain the fast path. The reference does
not require `OLM_PARALLEL_MAX=1`. DirectionalBlur also disables Clang optimization
in its rotation translation unit to preserve the pre-P05a `-O0` policy.

Run one plugin, with one host process at a time:

```sh
python3 tools/perf/ref_vs_fast.py --plugin olmdirectionalblur
```

The default requests 200 small cases, 20 full 1920×1080 frames and five full
3840×2160 frames. Small cases cycle default, realistic-v1, realistic-v2 and
odd-even-v1 fuzz samplers. Depths and exceptional floating-point inputs come from
the seeded fuzz generator. Fixed large frames tile its pixel payload and resize
point parameters; they are not independent random pixels at every coordinate.
Use `--max-size 3840 --max-height 2160` to extend odd/even sampling to 4K;
`--large-corpus` substitutes the ten P00b retained parameter sets in large cases,
including corpus09. These additional stress options can take substantially longer.

Hosts are built twice from the existing fuzz adapters, with the definition added
only to the reference compiler command. No oracle, emulator build, installed
bundle or release gate is used. Raw output streams go to disk; byte comparisons
are chunked and output rectangles are compared independently. Fast runs use
`OLM_PARALLEL_MAX=1,2,8`. Matching refusals are counted separately and **are not
successful image comparisons**. A timeout or host failure fails the command.
The first mismatch preserves the exact input, outputs and case metadata.

Results and summary JSON live under
`orchestra/state/R10-reference-fast-split/<plugin>/`. Choose a separate
`--scratch` for independent runs. A quick build/smoke check is:

```sh
python3 tools/perf/ref_vs_fast.py --plugin olmdirectionalblur --small 8 --hd 0 --uhd 0
```

For original-AEX validation, the existing runner accepts `--reference-build`:

```sh
python3 tools/fuzz/run.py --plugin olmdirectionalblur --reference-build \
  --seed 1 --n 100 --jobs 1 --shrink-attempts 0
```

Interpret Smart results for these plugins and Classic for Smoother v1. Native
reference/fast equality does not replace the independent AEX validation. Timing
and full acceptance coverage are recorded in the R10 worker report; no runtime
bound is claimed until measured on the particular parameter set.
