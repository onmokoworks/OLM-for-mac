# OLMRadialBlur case_0010 PF8 writeback static boundary - 2026-07-28

## Scope and decision

This is a Mac-only static read of the checked-in Windows AEX, plus an audit of
the existing Mac Unicorn harness. No Windows, AE, NAS, production source, or
ledger state was changed.

The final-writeback boundary can be advanced beyond the direct inverse sampler:
`OLMRadialBlur+0x4ec8` is not a PF8 store. It is the `RDI += 16` advance of the
internal float32 RGBA destination used by `FUN_180004640`. For the 8bpc path,
that internal frame is consumed after `FUN_180004640` returns at
`OLMRadialBlur+0x7b4a`; the concrete PF8 pack/store call is
`OLMRadialBlur+0x7c14 -> FUN_180017400`.

This resolves the CPU writeback locus and makes a bounded Mac actual-AEX
witness possible. It does not establish that the retained Windows PNG used
this CPU path, nor does it establish an export handoff after the checked-out
PF world.

## Proven static call chain

The render dispatcher selects the 8bpc owner:

```text
+0x41cc  compare bits-per-channel with 8
+0x41f3  call FUN_180007520 (8bpc owner)
```

For Rotation (`[RBX+0x20] == 2`), the 8bpc owner executes:

```text
+0x7b45  call FUN_180004640
+0x7b4a  return from Rotation worker
+0x7b54  begin internal-frame -> PF8 loop
+0x7c14  call FUN_180017400 (PF8 pack/store)
```

Inside `FUN_180004640`, the final inverse-sample loop is:

```text
+0x4eb9  R8D = R13D                         ; polar/sample extent argument
+0x4ebc  RDX = RDI                          ; destination float32 RGBA cell
+0x4ebf  RCX = [RSI+0x38]                   ; collapsed +0xe plane pointer
+0x4ec3  call FUN_180001000                 ; direct inverse sampler
+0x4ec8  RDI += 0x10                        ; next internal RGBA float cell
```

At the start of each output row, `RDI` is derived from `[R14+0xa0]`:

```text
RDI = [R14+0xa0] + ((y * width * 4) * 4)
```

Thus the direct sampler destination relation is:

```text
internal_cell(x,y) = [work+0xa0] + 16 * (y * width + x)
```

The later PF8 loop independently derives the same internal cell relation from
`[RBX+0xa0]` (`+0x7b70..+0x7bb0`) and loads:

```text
XMM10 = cell[0]
XMM9  = cell[1]
XMM8  = cell[2]
XMM7  = cell[3]
```

RGB only is multiplied by `[RBX+0x38]` and upper-clamped with `MINSS(...,1.0)`
at `+0x7bdd..+0x7bf6`. Alpha remains `cell[3]`.

`FUN_180017260` at `+0x7bd8` resolves the PF8 destination:

```text
dst = [R13+0x18] + y * [R13+0x20] + x * 4
```

where the observed structure fields are PF-world data pointer (`+0x18`),
rowbytes (`+0x20`), width (`+0x24`), and height (`+0x28`).

At `+0x7c14`, the Windows x64 float arguments are:

```text
XMM0 = min(cell[0] * [RBX+0x38], 1.0)
XMM1 = min(cell[1] * [RBX+0x38], 1.0)
XMM2 = min(cell[2] * [RBX+0x38], 1.0)
XMM3 = cell[3]
[RSP+0x20] = dst
```

`FUN_180017400` multiplies all four channels by the PF8 scale constant, uses
`CVTTSS2SI`, and stores:

```text
dst[0] = trunc(XMM3 * scale)  ; A
dst[1] = trunc(XMM0 * scale)  ; R
dst[2] = trunc(XMM1 * scale)  ; G
dst[3] = trunc(XMM2 * scale)  ; B
```

Therefore `[RBX+0xa0]` is the shared pointer relation connecting the sampler
destination at `+0x4ec3` to the PF8 packer input at `+0x7bb5`, and the PF8
output world is ARGB byte order.

## Proven versus hypothesis

### Proven

- `+0x4ec8` advances an internal 16-byte float32 RGBA cell; it is not a host
  output or export store.
- `+0x7c14` is the 8bpc CPU pack/store boundary.
- The internal source address and PF8 destination address can be calculated
  exactly from `(x,y)`, `[RBX+0xa0]`, and the PF-world fields above.
- RGB brightness gain and upper clamp occur between the internal cell load and
  PF8 packing; alpha bypasses both.
- PF8 conversion is truncating float-to-int and stores ARGB.
- The 16bpc and float sibling owners use the analogous later boundaries
  `+0x7404 -> FUN_180017440` and `+0x8424 -> FUN_180017490`; they are not the
  `case_0010` 8bpc store.

### Not proven / hypothesis

- The retained bright Windows PNG was produced by this exact 8bpc CPU owner.
- Any host-side premultiplication, color management, output-module conversion,
  GPU substitution, or stale-AEX path after the PF world.
- That the PF8 scale constant alone explains a pixel difference. The direct
  helper implementation and its use with normalized floats are consistent
  with 255, but the decisive witness should record the raw constant word.
- Exported PNG causality. Static control flow ends at the checked-out PF world;
  no AEX-local PNG exporter is present in this chain.

## Mac actual-AEX harness reachability

`tools/emulation/test_m4_case0010.py` already invokes
`FUN_180008690 -> FUN_180007520 -> FUN_180004640` at the real `1920x1080`
geometry. Its retained report records both the direct `+0xe` sample and the
output-world bytes at `(1614,6)`. Because it enters the 8bpc owner rather than
calling only the sampler leaf, it can exercise `+0x7b4a..+0x7c19`.

The existing M4 artifact reports direct sampled alpha `1.0` but output-world
ARGB `(0,0,0,0)`. That observation is useful as a reason to add exact hooks,
not as proof of an AEX rule: the run used `fast=True`, substitutes host
services, and did not retain the `+0x7c14` argument tuple or immediate
post-store bytes. A bounded rerun can classify whether the zero-alpha byte is
created by the native PF8 packer or by harness/world binding.

## Exact next witness specification

Run only `case_0010`, pixel `(1614,6)`, in the existing Mac Unicorn 8bpc owner
harness. Fail closed unless all addresses and pointer relations agree.

1. At `+0x7b45`, record `RBX`, `[RBX+0x20]`, `[RBX+0xa0]`, `[RBX+0x38]`,
   `R13`, and PF-world fields `[R13+0x18/+0x20/+0x24/+0x28]`.
2. At `+0x4ebf/+0x4ec3`, gate on the owner loop indices for `(1614,6)` and
   record `RCX`, `RDX`, `R8D`, sampler coordinates on the stack, and the
   16-byte cell at `RDX` immediately after return.
3. Assert:
   `RDX == [RBX+0xa0] + 16*(6*width+1614)`.
4. At `+0x7bb0`, record `RDI` and the four raw float32 words; assert
   `RDI == RDX` from step 2.
5. At `+0x7c14`, record raw `XMM0..XMM3`, `[RBX+0x38]`,
   `[RSP+0x20]`, the PF8 scale word at `0x1800252a0`, and four destination
   bytes before the call.
6. Assert:
   `[RSP+0x20] == [R13+0x18] + 6*[R13+0x20] + 1614*4`.
7. At `+0x7c19`, record the four destination bytes after the native helper.
8. Also record the same tuple for one nearby control, preferably `(1612,6)`.

Acceptance:

- `answered`: native `+0x7c14` is reached, both pointer equalities hold, and
  immediate before/after PF8 bytes plus raw float inputs are retained.
- `answered_partial`: the owner reaches `+0x7b4a` but a precise harness/service
  failure prevents the gated PF8 call.
- `failed`: only the old direct sampler or final PNG/output artifact is
  reported without the `+0x7c14` tuple.

This witness closes the AEX CPU sampler-to-PF8 boundary locally. It still
cannot close PF-world-to-export provenance; that requires a real AE host
capture or a same-run Windows Software output/export witness.
