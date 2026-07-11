# OLMRadialBlur Zoom Staging Loop Probe - 2026-07-08

## Verdict

`0x180007811` is a full-frame pre-Zoom staging loop. The current local emulator
does not reach the Zoom worker because it is spending the instruction budget in
this 1920x1080 staging pass.

## Command

```bash
python3 tools/emulation/test_zoom_case0009.py \
  --trace-staging-loop \
  --max-instructions 1000000 \
  --output-json /tmp/zoom_case0009_staging_probe.json \
  --output-md /tmp/zoom_case0009_staging_probe.md
```

The runner exits `2` by design when the Zoom entry is not reached, but it writes
the JSON/Markdown witness.

## FACTS

- `classification`: `zoom-entry-not-reached-within-instruction-cap`
- `render_instructions`: `1000000`
- `render_stop_rip`: `0x18001726c`
- `zoom_branch_hits`: `0`
- `zoom_callsite_hits`: `0`
- `zoom_setup_a7e0_calls`: `0`
- `zoom_setup_a810_calls`: `0`
- `staging_loop_hits`: `16380`

First sampled loop state:

```json
{
  "bound_x_r15_0x24": 1920,
  "bound_y_r15_0x28": 1080,
  "hit": 1,
  "r12_row": 0,
  "r14_col": 0,
  "r15": 1073742528,
  "rdi": 553459712,
  "rgba_being_written": [0.0, 0.0, 0.0, 0.0],
  "rsi": 586637312
}
```

The next samples increment `r14_col` and advance both `rdi` and `rsi` by
16 bytes per pixel, matching the objdump loop at `0x180007803..0x18000784c`.

## Reading

This strengthens the emulator-entry bottleneck classification. The next
Mac-only RadialBlur action should not be algorithm tuning; it should be one of:

1. synthesize or prefill the staging planes and start closer to `0x1800072d3`;
2. build a direct `FUN_1800056f0` harness once the work-buffer contract is
   pinned;
3. add a safe fast-forward/detour for this staging loop only if its writes are
   proven equivalent.

Do not change Mac RadialBlur output code from this witness.
