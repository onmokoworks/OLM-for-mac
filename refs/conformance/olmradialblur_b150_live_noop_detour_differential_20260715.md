# OLMRadialBlur B150 live versus no-op-detour differential

Date: 2026-07-15

## Scope

Bounded 32x32 direct-core emulator run for `case_0009`, using the actual AEX
`FUN_18000B150` worker once and a paired run with only that function replaced by
the existing no-op detour. The capture is limited to the worker-owned B150
RGBA/scalar row slice and the surrounding typed input contract.

## Result

The live run reached and returned from B150 once. The paired no-op run reached
the B150 detour once. Both runs used `width=49`, `row_start=0`, `row_end=5`,
the same source/scalar input words, the same context spans, and the same
denominator pointer (`work+0x843`, also the scalar output pointer).

| Capture | Live AEX | B150 no-op detour |
|---|---:|---:|
| B150 entry hits | 1 | 1 detour hit |
| B150 returns | 1 | 1 |
| worker RGBA/scalar nonzero cells before return | 9 | 9 |
| worker RGBA/scalar nonzero cells after return | 245 | 9 |
| RGBA slice SHA-256 before | `68759c7aeaec08736341a86049846fad33738a8fe44bda6057f5f5d4a9730901` | same |
| RGBA slice SHA-256 after | `4d1f45c56e7e0d1e1794ac9a927811c75fa395f9f3bcfd70678f4a12ca012b24` | `68759c7aeaec08736341a86049846fad33738a8fe44bda6057f5f5d4a9730901` |
| scalar slice SHA-256 before | `d548a9abe35efd163fa84c2863cbb389691bd7c2cd4d1b2333d4a2b8c8bd831a` | same |
| scalar slice SHA-256 after | `d1c6282c9ea986a7cc0ca35811bd8dd2380cf052d83864007b787bb371cd1561` | `d548a9abe35efd163fa84c2863cbb389691bd7c2cd4d1b2333d4a2b8c8bd831a` |

The capture retains raw float32 words for every nonzero cell in each before and
after slice. The analyzer verifies those words round-trip to the recorded
float32 values and fails closed on missing or inconsistent fields.

## Verification

```sh
python3 tools/emulation/run_radialblur_case0009_b150_differential.py \
  --combined-json /tmp/radial_combined_final.json \
  --output-json /tmp/radial_analysis_final.json \
  --output-md /tmp/radial_analysis_final.md
```

The runner retains the two probe reports as
`/tmp/radial_combined_final.live.json` and
`/tmp/radial_combined_final.noop.json`, combines them into
`/tmp/radial_combined_final.json`, invokes the analyzer, and fails closed if
the differential does not pass. The focused test suite and this runner smoke
passed. This is local actual-AEX/emulator evidence only. It does not compare
Windows and Mac outputs, claim AE exactness, tune PNG values, or authorize
production-code changes.
