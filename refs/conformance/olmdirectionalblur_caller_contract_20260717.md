# OLMDirectionalBlur Caller Contract Audit

Status: `pass`; Mac-only actual-AEX/Unicorn witness. Production and ledger unchanged.

## Scope

This bounded fixture makes one real call to `FUN_180006700` (`0x180006700`),
using a synthetic PF Iterate8 suite callback, then enters the checked-in actual
AEX output callback at `0x180006b30` for one pixel. It does not invoke the AE
host, full render entry, PNG code, or Windows live writer-entry.

## FACT

- Decomp and `objdump` show `FUN_180006700` forwarding eight arguments to
  `PF Iterate8 Suite`; its callback call area places `rect` at `[RSP+0x28]`,
  `refcon` at `[RSP+0x30]`, callback at `[RSP+0x38]`, and destination pixel at
  `[RSP+0x40]`.
- The actual callback at `0x180006b30` observed `RCX=params`, `RDX=x`, and
  `R8=y`. It reads the destination `PF_Pixel8*` from `[RSP+0x28]`.
- It reads `params+0x8090` as a float RGBA base, `+0x8098` as `row0`,
  `+0x809c` as `col0`, and `+0x80a0` as a float-element stride. The selected
  source cell is `((row0+y)*stride+col0+x)*16` bytes.
- The one-cell fixture selected index `23` and the actual writer packed the
  four output bytes as `[alpha, red, green, blue]` with truncating float-to-int
  conversion. The exact captured values are in the JSON fixture.

## INFERENCE

- This reconstructs the immediate Mac-side caller contract as far as a real
  AEX wrapper and callback can be driven without AE. It does not promote any
  Windows live writer-entry fact, and it cannot identify whether the pending
  Windows residual is in the pre-writer float state or the store.
- `R9` is not treated as the output-pointer contract at `0x180006b30`; the
  callback ABI uses the stack slot documented above.

## Commands

```sh
python3 tools/emulation/test_olmdirectionalblur_caller_contract_20260717.py
python3 -m json.tool refs/conformance/olmdirectionalblur_caller_contract_20260717.json >/dev/null
git diff --check -- tools/emulation/test_olmdirectionalblur_caller_contract_20260717.py refs/conformance/olmdirectionalblur_caller_contract_20260717.md
```
