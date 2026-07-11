# OLMRadialBlur Zoom case_0009 AEX witness

Date: 2026-07-08

## Purpose

Check whether the Mac-side AEX/Unicorn runner can reach the Zoom `case_0009`
caller-collapse / denominator path before requesting more Windows evidence or
changing the Mac implementation.

## Inputs

- AEX: `aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex`
- Case: `case_0009`
- Witness pixel: `(6, 0)`
- Runner: `tools/emulation/test_zoom_case0009.py`
- Full run report: `refs/reports/olmradialblur_zoom_case0009_aex_witness.md`
  (ignored generated report; facts below are copied here for tracked evidence)

## Result

Classification: `zoom-entry-not-reached-within-instruction-cap`

The runner completes parameter setup with `param_ctx.blur_type = 1`, but the
known Zoom path is not reached within the instruction cap:

- `FUN_1800056f0`: not observed
- `0x1800072d3` Blur Type branch hook: `0` hits
- `0x1800072fd` Zoom callsite hook: `0` hits
- `FUN_18000a7e0`: `0` calls
- `FUN_18000a810`: `0` calls
- `FUN_180009d80` direct sampler: not reached through this path

Full run values:

- `render_instructions`: `50000000`
- `max_instructions`: `50000000`
- `elapsed_seconds`: `31.84765911102295`
- `render_stop_rip`: `0x180007811`

Quick smoke run:

- `render_instructions`: `1000000`
- `max_instructions`: `1000000`
- `render_stop_rip`: `0x18001726c`

## Reading

This is a partial local emulation fact, not a semantic proof. It supports the
interpretation that the current emulator is spending time upstream of the known
Zoom dispatch sequence inside `FUN_180007520`, rather than failing because the
case has the wrong Blur Type parameter.

Do not change RadialBlur output code from this result. The next local move is
to shrink or short-circuit the pre-Zoom full-frame staging in the emulator, or
to prefer a Windows same-run stage witness if one becomes available.

## Commands

```sh
tools/emulation/.venv/bin/python tools/emulation/test_zoom_case0009.py
```

Output summary:

```text
wrote_json=/Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/olmradialblur_zoom_case0009_aex_witness.json
wrote_md=/Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/olmradialblur_zoom_case0009_aex_witness.md
classification=zoom-entry-not-reached-within-instruction-cap
render_instructions=50000000 max_instructions=50000000
```

```sh
tools/emulation/.venv/bin/python tools/emulation/test_zoom_case0009.py --max-instructions 1000000 --output-json /tmp/zoom_case0009_quick.json --output-md /tmp/zoom_case0009_quick.md
```

Output summary:

```text
wrote_json=/tmp/zoom_case0009_quick.json
wrote_md=/tmp/zoom_case0009_quick.md
classification=zoom-entry-not-reached-within-instruction-cap
render_instructions=1000000 max_instructions=1000000
```
