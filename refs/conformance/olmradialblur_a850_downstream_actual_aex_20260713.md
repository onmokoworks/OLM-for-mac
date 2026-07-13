# OLMRadialBlur A850 downstream actual-AEX probe (2026-07-13)

## Scope

- Actual Windows AEX executed locally through the existing Unicorn harness.
- `FUN_18000A850` output, downstream index formation, and direct `FUN_180009D80` call are recorded.
- Prefill is an opaque prerequisite; this probe performs no new prefill reconstruction or comparison.

## Results

- Input crop: `None` from `refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png`.
- The actual D80 output agrees with the existing mirror in RGB at all four points.
- Alpha agrees exactly at three points; `(6,0)` differs by one float32 ULP.

### (6,0)

- entry_reached: `True`
- A850: `{"angle_raw_f32": 3.656665325164795, "function": "FUN_18000A850", "input_xy_f32": [6.0, 0.0], "radius_raw_f32": 1096.22802734375, "work": 553500672}`
- downstream indices: `{"angle_index": 3.557459233642021, "angle_int": 3, "radius_index": 41.22802734375, "radius_int": 41}`
- actual D80: `{"angle_count": 4, "derived_rgba_stride_bytes": 784, "function": "FUN_180009D80", "output": 553527664, "plane": 553521792, "r8_radial_count": 49, "r9_angle_count": 4, "radial_count": 49, "rgba_f32": [0.0, 0.0, 0.0, 0.9999999403953552], "stack_angle_f32_bits": 1080274281, "stack_radius_f32_bits": 1109715328, "stack_stride_float_words": 196}`
- actual vs mirror: `{"exact_f32": true, "rgba_abs_delta": [0.0, 0.0, 0.0, 0.0]}`

### (7,0)

- entry_reached: `True`
- A850: `{"angle_raw_f32": 3.6571152210235596, "function": "FUN_18000A850", "input_xy_f32": [7.0, 0.0], "radius_raw_f32": 1095.35791015625, "work": 553500672}`
- downstream indices: `{"angle_index": 3.6863449042787124, "angle_int": 3, "radius_index": 40.35791015625, "radius_int": 40}`
- actual D80: `{"angle_count": 4, "derived_rgba_stride_bytes": 784, "function": "FUN_180009D80", "output": 553527664, "plane": 553521792, "r8_radial_count": 49, "r9_angle_count": 4, "radial_count": 49, "rgba_f32": [0.0, 0.0, 0.0, 1.0], "stack_angle_f32_bits": 1080814867, "stack_radius_f32_bits": 1109487232, "stack_stride_float_words": 196}`
- actual vs mirror: `{"exact_f32": true, "rgba_abs_delta": [0.0, 0.0, 0.0, 0.0]}`

### (8,0)

- entry_reached: `True`
- A850: `{"angle_raw_f32": 3.6575655937194824, "function": "FUN_18000A850", "input_xy_f32": [8.0, 0.0], "radius_raw_f32": 1094.488037109375, "work": 553500672}`
- downstream indices: `{"angle_index": 3.8153671786997165, "angle_int": 3, "radius_index": 39.488037109375, "radius_int": 39}`
- actual D80: `{"angle_count": 4, "derived_rgba_stride_bytes": 784, "function": "FUN_180009D80", "output": 553527664, "plane": 553521792, "r8_radial_count": 49, "r9_angle_count": 4, "radial_count": 49, "rgba_f32": [0.0, 0.0, 0.0, 1.0], "stack_angle_f32_bits": 1081356026, "stack_radius_f32_bits": 1109259200, "stack_stride_float_words": 196}`
- actual vs mirror: `{"exact_f32": true, "rgba_abs_delta": [0.0, 0.0, 0.0, 0.0]}`

### (24,0)

- entry_reached: `True`
- A850: `{"angle_raw_f32": 3.6648709774017334, "function": "FUN_18000A850", "input_xy_f32": [24.0, 0.0], "radius_raw_f32": 1080.599853515625, "work": 553500672}`
- downstream indices: `{"angle_index": 1.9082054584951038, "angle_int": 1, "radius_index": 25.599853515625, "radius_int": 25}`
- actual D80: `{"angle_count": 4, "derived_rgba_stride_bytes": 784, "function": "FUN_180009D80", "output": 553527664, "plane": 553521792, "r8_radial_count": 49, "r9_angle_count": 4, "radial_count": 49, "rgba_f32": [0.0, 0.0, 0.0, 1.0], "stack_angle_f32_bits": 1072971796, "stack_radius_f32_bits": 1103940736, "stack_stride_float_words": 196}`
- actual vs mirror: `{"exact_f32": true, "rgba_abs_delta": [0.0, 0.0, 0.0, 0.0]}`

## Interpretation

The direct D80 result is the local actual-AEX inverse-sampling observation. A mismatch against the existing mirror localizes the remaining difference to the sampler ABI/operation order or coordinate handoff; an exact match moves the residual beyond this local AEX sampler path.
