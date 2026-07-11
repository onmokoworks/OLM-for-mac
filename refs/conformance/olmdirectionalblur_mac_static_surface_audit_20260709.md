# OLMDirectionalBlur Mac Static Surface Audit

This is a local static/CLI audit only. It does not promote DirectionalBlur out
of the parked lane and does not justify PNG-only tuning.

## Findings

- The Mac plug-in still builds DirectionalBlur weights with the old broad
  divisor:
  `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:191` computes
  `2.0f * (length / 0.5f)^2 + 1e-5f`.
- The CLI and IR use the binary-grounded AEX divisor:
  `cli/OLMDirectionalBlur/main.cpp:525` documents
  `length / 3.0f`, matching `notes/IR_OLMDirectionalBlur.md`.
- The Mac plug-in currently copy-throughs unsupported lanes:
  `noise_variation`, back strength, alpha fades, and 16/32bpc.
- The local witness smoke now targets `rotated-aex-full-choreo`, not the older
  broad `rotated` mode, and asserts the richer July 8 witness schema including
  `aex_two_stage_output`, padded coordinates, denominators, pre-rotateback
  RGBA, output-canvas RGBA, pre-quant sample, and final byte output.

## Commands

```bash
nl -ba mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp | sed -n '188,200p;226,238p;328,338p'
nl -ba cli/OLMDirectionalBlur/main.cpp | sed -n '522,536p'
nl -ba notes/IR_OLMDirectionalBlur.md | sed -n '206,218p'
python3 refs/scripts/smoke_olmdirectionalblur_cli_witness.py
```

## Interpretation

This closes a local smoke-coverage gap. The next allowed DirectionalBlur work
is still witness-level proof or a narrowly justified Mac implementation patch,
not broad visual tuning.
