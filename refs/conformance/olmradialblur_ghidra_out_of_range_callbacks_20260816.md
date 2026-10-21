# OLMRadialBlur Ghidra inventory — r16 out-of-range callback closure

- Target: live Ghidra MCP `default`, unchanged throughout the audit.
- Binary: `plugins_2025/OLMRadialBlur.aex`, pinned 2025 target used by r01–r15.
- Purpose: close address-taken plug-in callbacks registered by the in-range Compute Cache setup even when their entry lies outside the frozen `[0x180001000,0x18001ce70)` 362-function range.
- Production/source edits: none.

## Registration site

`0x18000f7c0`, now named `RadialBlur_RegisterComputeCacheCallbacks`, acquires `AEGP Compute Cache` v1, builds the key `OLM RadialBlur.cache.v<instance/version>`, and passes one four-pointer callback table to the suite registration method.

The complete table is materialized by four consecutive `LEA` instructions at `0x18000fa4b`, `0x18000fa56`, `0x18000fa61`, and `0x18000fa6c`:

| Table entry | Address | Ghidra representation | Operational meaning | Frozen-set status | Confidence |
|---:|---:|---|---|---|---|
| 0 | `0x18001cdb0` | local label `LAB_18001cdb0`, not a Ghidra function start | Tail-forwards the two qwords at input offsets `+0/+8` plus the caller-supplied output/context argument to suite-object virtual slot `+0x00`. Exact SDK callback typedef spelling is not asserted. | Bytes lie inside the frozen range, but it is not one of the 362 function starts. | High operation / Medium canonical callback name |
| 1 | `0x18001cde0` | `RadialBlur_ComputeCache_CopyValue` | Allocates a 16-byte destination value, copies the scalar field, retains/duplicates the stored suite handle through virtual slot `+0x08`, and returns the new record. | Included in r15 and the frozen 362. | High |
| 2 | `0x18001ce50` | local label `LAB_18001ce50`, not a Ghidra function start | Tail-forwards the record's first qword to suite-object virtual slot `+0x10`. Exact SDK callback typedef spelling is not asserted. | Bytes lie below the frozen end, but it is not one of the 362 function starts. | High operation / Medium canonical callback name |
| 3 | `0x18001ce70` | `RadialBlur_ComputeCache_DestroyValue` | Calls suite-object virtual slot `+0x18` on the retained handle at record offset `+0`, then frees the value record. This is the ownership inverse paired with the copy callback. | First function start outside the frozen range; added by this appendix. | High |

## Live rename

`0x18001ce70` was renamed through Ghidra MCP from `FUN_18001ce70` to:

`RadialBlur_ComputeCache_DestroyValue`

The name is operation-only. It does not claim an unrecovered Adobe SDK typedef or source method spelling.

## Evidence for the destroy classification

- `RadialBlur_RegisterComputeCacheCallbacks` writes `0x18001ce70` into the same contiguous callback table as `RadialBlur_ComputeCache_CopyValue`.
- Live xrefs to `0x18001ce70` are the two instruction/data references at `0x18000fa6c` and `0x18000fa73`, plus unwind metadata at `0x18002e0ec`.
- The complete decompile loads the retained qword from `*record`, invokes the suite object stored at global effect offset `+0x1f0` through virtual slot `+0x18`, and calls `free(record)`.
- The callback immediately follows the slot-`+0x10` forwarding label and is terminated before the CRT `_Xlength_error` entry at `0x18001ce9f`.

## Outside-range callback scan result

The complete registration function was decompiled and disassembled, and all four address-taken callback values passed to the Compute Cache registration call were enumerated. **Exactly one function start is outside the frozen range: `0x18001ce70`.** The other two non-function targets are the in-range local labels described above; the copy callback is already in r15.

No second out-of-range plug-in callback target is materialized by this registration function. Entries beginning at `0x18001ce9f` are CRT/runtime support and are not members of the registered callback table.

## Scope decision

The canonical 362-function ledger remains a stable frozen function-start set. This r16 appendix is its explicit indirect-root closure: it records the one directly registered plug-in function just beyond the end boundary and the two address-taken local callback labels that cannot appear as Ghidra function starts. Therefore “362/362 frozen function starts” and “all directly registered Compute Cache callbacks bounded” are both true without silently changing the original denominator.
