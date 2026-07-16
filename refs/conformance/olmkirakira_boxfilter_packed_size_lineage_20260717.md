# OLMKiraKira boxFilter packed-size lineage

Date: 2026-07-17

## Result

The new runner observes the natural actual-AEX call from `FUN_181281260` at
`0x181281326` and the entry to `FUN_181280fa0` at `0x181280fa0`. It records
the packed `param_4` in `R9`, the fifth argument from the caller's
`[RSP+0x20]`, and the sixth argument from `[RSP+0x28]`, then verifies that the
callee sees the same values under the Win64 entry offsets.

Static asm identifies the construction:

```text
0x1812812c3 -> 0x1812812cb: qword load into param_5 stack slot
0x181281304 -> 0x18128130c: byte load into param_6 stack slot
0x181281326: CALL FUN_181280fa0 with R9/R8/RDX/RCX already selected
0x181280fc9..0xfd4: param_4/param_3/param_2/param_1 retained
0x181281079: FUN_181281e90 receives param_4 low dword as its fourth argument
```

The JSON report is the authoritative runtime record. Classification is
fail-closed: only a complete callsite-to-entry trace, the unchanged
FilterEngine invalid-geometry assertion, and matching raw argument continuity
can classify the observed words as actual AEX/object algorithm values. Missing
fixture or host state remains `UNRESOLVED_FIXTURE_OR_HOST_STATE_FAIL_CLOSED`.

Host parameter checkout is a negative control. No checkout value is written
into the packed argument slots, and no value patch or assertion suppression is
performed.

## Limits

This is Mac-only Unicorn execution of the checked-in Windows PE AEX. It makes
no Windows, After Effects host, final-pixel, writer, or AE-exactness claim.
