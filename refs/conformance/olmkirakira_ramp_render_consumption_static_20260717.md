# OLMKiraKira Ramp Render Consumption Static Audit

Date: 2026-07-17
Scope: read-only static analysis after `FUN_18114e860` in
`plugins_2025/OLMKiraKira.aex`
Evidence: `decomp/OLMKiraKira.aex.c.txt` and
`disasm/OLMKiraKira.aex.asm.txt`

This artifact records whether the five confirmed `0x144`-byte ramp blocks are
consumed by the recovered render path. It does not modify production code,
the ledger, or the current Mac implementation.

## FACT

### Confirmed ramp ranges

`FUN_18114e860` checks out and copies five blocks into these state ranges:

| Ramp | State range | Use byte | Checkout call |
| --- | --- | --- | --- |
| Vertical | `state+0x1E8 .. +0x32B` | `state+0x83C` | `0x18114E95A` |
| Horizontal | `state+0x32C .. +0x46F` | `state+0x83D` | `0x18114E9C0` |
| Diagonal | `state+0x470 .. +0x5B3` | `state+0x83E` | `0x18114EA26` |
| Diagonal 2 | `state+0x5B4 .. +0x6F7` | `state+0x83F` | `0x18114EA8C` |
| Highlight | `state+0x6F8 .. +0x83B` | `state+0x840` | `0x18114EAF2` |

Decomp: `decomp/OLMKiraKira.aex.c.txt:3523493-3523522`. Assembly:
`disasm/OLMKiraKira.aex.asm.txt:3567790-3567920`.

### Pointer threading after checkout

All three bit-depth render entries pass `state+0x1E8` as an additional stack
argument to the shared ray driver:

| Entry | Call instruction | Ramp pointer setup |
| --- | --- | --- |
| `FUN_18114cc50` @ `0x18114CC50` | `CALL 0x18114F4A0` at `0x18114D05C` | `LEA RAX,[RDI+0x1E8]` at `0x18114CFE7`, then store at `[RSP+0x40]` |
| `FUN_18114d220` @ `0x18114D220` | `CALL 0x18114F4A0` at `0x18114D62C` | `LEA RAX,[RDI+0x1E8]` at `0x18114D5B7`, then store at `[RSP+0x40]` |
| `FUN_18114d7f0` @ `0x18114D7F0` | `CALL 0x18114F4A0` at `0x18114DBFC` | `LEA RAX,[RDI+0x1E8]` at `0x18114DB87`, then store at `[RSP+0x40]` |

Assembly references:

- `disasm/OLMKiraKira.aex.asm.txt:3566296-3566317`
- `disasm/OLMKiraKira.aex.asm.txt:3566638-3566659`
- `disasm/OLMKiraKira.aex.asm.txt:3566980-3567001`

The corresponding decompilation shows the same call shape through the local
argument setup at `decomp/OLMKiraKira.aex.c.txt:3522621-3522633`, repeated in
the 8-bit, 16-bit, and 32-bit entries.

### No dereference in the recovered ray driver

`FUN_18114f4a0` @ `0x18114F4A0` receives the threaded pointer as an extra
argument. Its recovered body saves incoming arguments, constructs five image
descriptors, reads per-ray state-derived values, and calls
`FUN_181150790`; it does not load from `state+0x1E8`, add the `0x144` stride,
or dereference any of the five ramp ranges.

The relevant decompilation is:

- argument save and setup: `decomp/OLMKiraKira.aex.c.txt:3523954-3523991`
- five-ray loop: `decomp/OLMKiraKira.aex.c.txt:3524003-3524114`
- aggregation dispatch: `decomp/OLMKiraKira.aex.c.txt:3524115-3524119`

The assembly loop at `0x18114F6E0-0x18114F9A1` reads ray descriptors and state
values, then calls `FUN_181150790` at `0x18114F929`. No load uses a ramp-block
base or a `0x144`-spaced offset.

Therefore the binary-grounded FACT is: **the ramp pointer is threaded through
the recovered render call chain, but no recovered function dereferences the
confirmed ramp ranges after checkout.**

### Proven state fields used by the render entries

| State offset | Proven role in recovered path |
| --- | --- |
| `+0x10` | Vertical ray length |
| `+0x18` | Horizontal ray length |
| `+0x20` | Diagonal ray length |
| `+0x28` | Diagonal-2 ray length |
| `+0x30` | Highlight ray length |
| `+0x40` | Channel/seed handler selector; branches for `1`, `2`, and `4` |
| `+0x48` | Merge-mode selector; driver dispatches mode `1` or `2` |
| `+0x4C` | Blur-mode selector; driver dispatches modes `1..4` |
| `+0x50` | Boolean gating the resized/approximated-input path |
| `+0x198` | Vertical color payload/source passed into render setup |
| `+0x1A8` | Horizontal color payload/source |
| `+0x1B8` | Diagonal color payload/source |
| `+0x1C8` | Diagonal-2 color payload/source |
| `+0x1D8` | Highlight color payload/source |
| `+0x83C..+0x840` | Corresponding five `Use Ramp` bytes |

The checkout writes for the non-ramp fields are visible at
`decomp/OLMKiraKira.aex.c.txt:3523486-3523531`. Ray-length reads and scaling
are visible at `decomp/OLMKiraKira.aex.c.txt:3522523-3522552`.

## INFERENCE

- The extra pointer argument appears reserved for, or intended to support,
  ramp processing, but the recovered `FUN_18114f4a0` implementation does not
  use it.
- The five `0x144`-byte blocks remain opaque. Their stop positions, colors,
  interpolation, encoding, and premultiplication are not recoverable from
  these accesses.

## NON-CLAIM

This negative result is limited to the recovered static call chain and
decompilation/assembly body described above. It does **not** prove that all
possible hidden indirect calls, unrecognized vtable implementations, alternate
dispatch paths, compiler artifacts, or future binary revisions cannot consume
the ramp blocks. It also does not authorize changes to production or the Mac
ramp/UI path.
