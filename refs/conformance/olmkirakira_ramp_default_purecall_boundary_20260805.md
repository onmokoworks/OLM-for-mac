# OLMKiraKira ramp default-handle boundary

Status: **base vtable only; not the actual registration caller**

The base `ArbitraryDataHandler` vtable slot `+0x18` resolves through thunk `0x18132d5e8`
and IAT `0x181485518` to `VCRUNTIME140.dll!_purecall`. Executing the actual
AEX thunk under the checked-in loader records only `_purecall`; there are no
PF Handle Suite NewHandle, Lock, Unlock, or Dispose callbacks. Consequently
there is no requested size, payload byte capture, or handle hash.

This vtable is installed transiently by the base constructor. `FUN_1811513a0`
then overwrites `effect+0x200` with derived RampDataHandler vtable
`0x18148d818`. Actual registration calls derived slot `+0x18` at
`0x18123abf0`; therefore the purecall is not reached and is not an AEXCompat
gap. This artifact is retained as a negative control.

Mac remains at 36 parameters and does not register the five arbitrary rows.
No default handle or `0x144`-byte payload is synthesized.
