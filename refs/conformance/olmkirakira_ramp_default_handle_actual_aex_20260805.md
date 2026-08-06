# OLMKiraKira ramp default handle

Status: **derived default producer executed**

The constructor first installs base vtable `0x1814d66c8` at `effect+0x200`,
then overwrites it with derived RampDataHandler vtable `0x18148d818`.
Registration therefore calls derived slot `+0x18`, target `0x18123abf0`, not
the base `_purecall` slot.

The actual target requests a `0x260`-byte PF handle. With the checked-in
zero-filled host scaffold, the callback sequence is Acquire PF Handle Suite
v2, NewHandle(608), Lock, initialize, Unlock, and Release Suite. The complete
bytes and SHA-256 are stored in the companion JSON.

Dispose is not part of this producer because ownership transfers to the AE
host. Mac arbitrary rows remain withheld until callback selector dispatch and
copy/dispose ownership are grounded; no AEX pointer-bearing default bytes are
reused on Mac.
