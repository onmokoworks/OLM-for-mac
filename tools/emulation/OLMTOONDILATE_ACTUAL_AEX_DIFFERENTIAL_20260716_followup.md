# OLMToonDilate Actual-AEX Differential Follow-up - 2026-07-16

## Result

- Status: **DIAGNOSTIC_COMPLETE**
- Scope: actual-AEX ABI stop-point only; no AE-exact claim.
- Smallest correction: allocate context through `context+0x180` and place a separate suite object at that offset.

## FACT

- Original `0x140`-byte context: `context+0x180` aliases the status vtable `+0x40` slot.
- That slot contains the synthetic callback address; its first byte is `0xc3`.
- The worker therefore performs an indirect call through `0xc3`, producing the reported fetch fault.
- Corrected layout: the status callback returns to `0x1801a6221`, then the suite callback is reached.
- Corrected run stop: `0x1801adc8f`; expected local next boundary is `0x1801adc8f`.

## INFERENCE

- `context+0x180` is a host suite/object pointer required by the worker.
- The suite callback and the exception boundary are synthetic diagnostics; they do not prove the full host ABI or pixel behavior.

## Evidence

```json
{
  "original_overlap": {
    "layout": "original-overlap",
    "context": "0x40000000",
    "status_callback": "0x82000000",
    "context_180": "0x82000000",
    "calls": [
      {
        "kind": "status",
        "args": [
          "0x1234",
          "0x400001b0",
          "0x40000230",
          "0x0"
        ],
        "return_address": "0x1801a6221"
      }
    ],
    "context_180_target_first_byte": "0xc3",
    "error": "emulation faulted at RIP=0xc3: Invalid memory fetch (UC_ERR_FETCH_UNMAPPED)",
    "stop": "0xc3",
    "imports": []
  },
  "corrected_layout": {
    "layout": "corrected",
    "context": "0x40000000",
    "status_callback": "0x82000000",
    "context_180": "0x40000270",
    "calls": [
      {
        "kind": "status",
        "args": [
          "0x1234",
          "0x40000290",
          "0x40000310",
          "0x0"
        ],
        "return_address": "0x1801a6221"
      },
      {
        "kind": "suite",
        "args": [
          "0x180311f10",
          "0x2",
          "0xf0fecc8",
          "0x20"
        ]
      }
    ],
    "context_180_target_first_byte": "0x10",
    "error": "emulation faulted at RIP=0x1801adc8f: Unhandled CPU exception (UC_ERR_EXCEPTION)",
    "stop": "0x1801adc8f",
    "imports": [
      "_CxxThrowException",
      "_CxxThrowException"
    ]
  }
}
```

## Reproduce

```sh
tools/emulation/.venv/bin/python tools/emulation/test_olmtoondilate_actual_aex_differential_20260716_followup.py
```
