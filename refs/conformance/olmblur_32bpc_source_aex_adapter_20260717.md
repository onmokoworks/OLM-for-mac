# OLMBlur 32bpc Mac source/AEX adapter differential

Date: 2026-07-17 (Mac)

## Result

The production Mac `BlurRender` 32bpc dispatch matches all checked-in actual
AEX float worker fixtures byte-for-byte: 12/12 cases, covering both
Non-Legacy `FUN_180004b80` and Legacy `FUN_1800086d0`, both bias directions,
large-radius/repeat boundaries, and mixed zero/negative alpha inputs.

The harness also verifies that source alpha is copied unchanged and that 32
bytes of output row padding remain untouched for every row.

## Evidence

Run:

```text
python3 tools/emulation/test_olmblur_32bpc_source_aex_adapter_20260717.py
```

The harness source-includes `mac/OLMBlur/OLMBlur.cpp`, compiles the production
32bpc worker sources, calls the production `BlurRender(..., 32, ...)` dispatch,
and compares each padded-row active byte against the corresponding actual-AEX
fixture. Fixture AEX SHA-256 is pinned to
`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.

## Claim boundary

This is Mac-only production-source versus actual-AEX CPU-fixture evidence. It
closes no Windows comparison, Adobe After Effects host render, EXR conversion,
or `AE exact` claim. It does not establish the Windows CRT math backend.
