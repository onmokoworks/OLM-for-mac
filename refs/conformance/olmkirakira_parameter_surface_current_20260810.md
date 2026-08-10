# OLMKiraKira current parameter surface — 2026-08-10

Status: **registration exact; native-host interaction bounded**

The pinned 2025 Windows AEX and current Mac production both expose 41 total
parameters including the input row. All 40 owned rows match in registration
order, disk ID, normalized type, name, defaults/ranges, flags, UI flags and
declared UI dimensions. This includes five group rows, five `Use Ramp`
checkboxes, five arbitrary-data `Ramp` rows and five group-end rows.

The five arbitrary rows use a 608-byte in-memory payload. Through the actual
Windows AEX exported entrypoint, all 11 arbitrary callback selectors were
executed: dispose, new, copy, flatten, unflatten, flat-size, compare,
interpolate, print-size, print and scan. The serialized form is 0x145 bytes;
the Mac implementation canonicalizes the unused tail instead of depending on
the Windows allocator pattern.

Revalidated commands:

```sh
python3 tools/emulation/test_olmkirakira_ui_setup_actual_aex_20260806.py
python3 tools/emulation/test_olmkirakira_ramp_arbitrary_entrypoint_20260805.py
python3 tools/emulation/test_olmkirakira_ramp_event_contract_20260805.py
python3 tools/emulation/test_olmkirakira_mode2_ramp_typed_completion_20260805.py
```

Results:

- `PASS_OLMKIRAKIRA_UI_SETUP_ACTUAL_AEX_20260806 rows=40 ramps=5 global=exact`
- `PASS_OLMKIRAKIRA_RAMP_ARBITRARY_ENTRYPOINT_20260805 selectors=11 flat=0x145 compare=0 canonical=accepted`
- `PASS_OLMKIRAKIRA_RAMP_EVENT_CONTRACT_20260805 color_returns=actual_and_synthetic host=gate`
- `PASS_OLMKIRAKIRA_MODE2_RAMP_TYPED_COMPLETION_20260805 depths=3 exact=1`

## Remaining boundary

This evidence proves registration and arbitrary-data lifecycle behavior without
claiming native AE visual equivalence. The custom ramp editor's Drawbot
appearance, mouse interaction and invalidation behavior still need a current
Mac AE visual/interaction check. A non-default ramp's live Windows
`ParamCheckout` object payload has not been captured, so the Mac handle layout
is not promoted to live Windows-host checkout equivalence. The render-side
bounded Mode 2/4 ramp arithmetic has separate actual-AEX production evidence.
