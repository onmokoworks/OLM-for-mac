# OLMToonDilate Semialpha Actual-AEX Worker Fixture - 2026-07-16

## Result

- Status: **PASS_NO_COPY_HELPER_PREMULTIPLY_OBSERVED**
- Execution: checked-in Windows PE AEX under local Unicorn on macOS.
- Scope: PF8/PF16/PF32 worker entries through their actual-AEX copy-helper boundary.
- Input: ARGB pixels with partial alpha; both premultiplied-looking and straight-looking variants per depth.
- Arrangement: PF8/PF32 selected pixel in helper source slot 3; PF16 selected pixel in helper source slot 0; the opposite end is opaque.
- Output: raw four-channel bytes captured at the helper boundary.
- No AE, Windows, production, or unsupported host-convention claim is made.

## PF8 / premult-looking

- Worker: `0x1801a6150`; helper: `0x1801ac880`
- Worker returned: `RETURN`; helper reached: `True`
- Helper source slot: `3`; explicit selected raw match: `True`
- Raw four-channel preservation: `True`
- Input raw: `[255, 31, 127, 223, 0, 0, 0, 0]`
- Source/output raw after worker: `[128, 64, 32, 16, 128, 64, 32, 16]`
- Captures: `[{"source": "0x20000040", "destination": "0x20000044", "before_source": [128, 64, 32, 16], "before_destination": [128, 64, 32, 16], "return_address": "0x1801a64e2", "after_source": [128, 64, 32, 16], "after_destination": [128, 64, 32, 16], "raw_four_channel_preserved": true}]`

## PF8 / straight-looking

- Worker: `0x1801a6150`; helper: `0x1801ac880`
- Worker returned: `RETURN`; helper reached: `True`
- Helper source slot: `3`; explicit selected raw match: `True`
- Raw four-channel preservation: `True`
- Input raw: `[255, 31, 127, 223, 0, 0, 0, 0]`
- Source/output raw after worker: `[128, 200, 100, 50, 128, 200, 100, 50]`
- Captures: `[{"source": "0x20000040", "destination": "0x20000044", "before_source": [128, 200, 100, 50], "before_destination": [128, 200, 100, 50], "return_address": "0x1801a64e2", "after_source": [128, 200, 100, 50], "after_destination": [128, 200, 100, 50], "raw_four_channel_preserved": true}]`

## PF16 / premult-looking

- Worker: `0x1801a5a90`; helper: `0x1801ac8b0`
- Worker returned: `RETURN`; helper reached: `True`
- Helper source slot: `0`; explicit selected raw match: `True`
- Raw four-channel preservation: `True`
- Input raw: `[0, 128, 0, 64, 0, 32, 0, 16, 0, 0, 0, 0, 0, 0, 0, 0]`
- Source/output raw after worker: `[0, 128, 0, 64, 0, 32, 0, 16, 0, 128, 0, 64, 0, 32, 0, 16]`
- Captures: `[{"source": "0x20000080", "destination": "0x20000088", "before_source": [0, 128, 0, 64, 0, 32, 0, 16], "before_destination": [0, 128, 0, 64, 0, 32, 0, 16], "return_address": "0x1801a5e22", "after_source": [0, 128, 0, 64, 0, 32, 0, 16], "after_destination": [0, 128, 0, 64, 0, 32, 0, 16], "raw_four_channel_preserved": true}]`

## PF16 / straight-looking

- Worker: `0x1801a5a90`; helper: `0x1801ac8b0`
- Worker returned: `RETURN`; helper reached: `True`
- Helper source slot: `0`; explicit selected raw match: `True`
- Raw four-channel preservation: `True`
- Input raw: `[0, 128, 80, 195, 48, 117, 32, 78, 0, 0, 0, 0, 0, 0, 0, 0]`
- Source/output raw after worker: `[0, 128, 80, 195, 48, 117, 32, 78, 0, 128, 80, 195, 48, 117, 32, 78]`
- Captures: `[{"source": "0x20000080", "destination": "0x20000088", "before_source": [0, 128, 80, 195, 48, 117, 32, 78], "before_destination": [0, 128, 80, 195, 48, 117, 32, 78], "return_address": "0x1801a5e22", "after_source": [0, 128, 80, 195, 48, 117, 32, 78], "after_destination": [0, 128, 80, 195, 48, 117, 32, 78], "raw_four_channel_preserved": true}]`

## PF32 / premult-looking

- Worker: `0x1801a6800`; helper: `0x1801ac8e0`
- Worker returned: `RETURN`; helper reached: `True`
- Helper source slot: `3`; explicit selected raw match: `True`
- Raw four-channel preservation: `True`
- Input raw: `[0, 0, 128, 63, 0, 0, 0, 62, 0, 0, 128, 62, 0, 0, 0, 63, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`
- Source/output raw after worker: `[0, 0, 0, 63, 0, 0, 128, 62, 0, 0, 0, 62, 0, 0, 128, 61, 0, 0, 0, 63, 0, 0, 128, 62, 0, 0, 0, 62, 0, 0, 128, 61]`
- Captures: `[{"source": "0x20000080", "destination": "0x20000090", "before_source": [0, 0, 0, 63, 0, 0, 128, 62, 0, 0, 0, 62, 0, 0, 128, 61], "before_destination": [0, 0, 0, 63, 0, 0, 128, 62, 0, 0, 0, 62, 0, 0, 128, 61], "return_address": "0x1801a6b9f", "after_source": [0, 0, 0, 63, 0, 0, 128, 62, 0, 0, 0, 62, 0, 0, 128, 61], "after_destination": [0, 0, 0, 63, 0, 0, 128, 62, 0, 0, 0, 62, 0, 0, 128, 61], "raw_four_channel_preserved": true}]`

## PF32 / straight-looking

- Worker: `0x1801a6800`; helper: `0x1801ac8e0`
- Worker returned: `RETURN`; helper reached: `True`
- Helper source slot: `3`; explicit selected raw match: `True`
- Raw four-channel preservation: `True`
- Input raw: `[0, 0, 128, 63, 0, 0, 0, 62, 0, 0, 128, 62, 0, 0, 0, 63, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`
- Source/output raw after worker: `[0, 0, 0, 63, 205, 204, 76, 63, 154, 153, 25, 63, 205, 204, 204, 62, 0, 0, 0, 63, 205, 204, 76, 63, 154, 153, 25, 63, 205, 204, 204, 62]`
- Captures: `[{"source": "0x20000080", "destination": "0x20000090", "before_source": [0, 0, 0, 63, 205, 204, 76, 63, 154, 153, 25, 63, 205, 204, 204, 62], "before_destination": [0, 0, 0, 63, 205, 204, 76, 63, 154, 153, 25, 63, 205, 204, 204, 62], "return_address": "0x1801a6b9f", "after_source": [0, 0, 0, 63, 205, 204, 76, 63, 154, 153, 25, 63, 205, 204, 204, 62], "after_destination": [0, 0, 0, 63, 205, 204, 76, 63, 154, 153, 25, 63, 205, 204, 204, 62], "raw_four_channel_preserved": true}]`

## Exact Checks

```json
{
  "all_six_runs_return": true,
  "both_input_orientations_per_depth": true,
  "all_helpers_reached": true,
  "all_helper_sources_match_explicit_selected_raw": true,
  "all_raw_four_channels_preserved": true
}
```

## Interpretation

The actual-AEX typed copy helpers preserve injected semialpha ARGB bytes exactly after the PF_COPY resume intervention. This does not prove the full worker has no earlier premultiply stage and does not establish AE host conventions.

## Reproduce

```sh
tools/emulation/.venv/bin/python tools/emulation/olmtoondilate_semialpha_actual_aex_20260716_fixture.py
```
