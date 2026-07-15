# OLMColorKey Edge Blur Apply AEX Harness

This follow-up is the smallest actual-AEX attempt for `FUN_1800085b0` at
`0x1800085b0`. It drives typed byte and float worlds under local Unicorn and
installs only the PF Handle Suite surface reached by the apply helper. It is
not AE-host execution and makes no AE-exact claim.

Direction 1 is the first lane. The target selects the independently proven
`FUN_1800049a0` weight helper at `0x1800049a0`; the report retains source,
boundary, distance, destination bytes, normal `RAX`, callback order, and
cleanup evidence. Directions 2 and 3 remain intentionally gated on direction
1 stability.

Run:

```text
python3 tools/emulation/probe_olmcolorkey_edge_blur_apply_aex_20260716.py \
  --direction 1 \
  --json refs/conformance/olmcolorkey_edge_blur_apply_aex_20260716.json
python3 -m pytest tools/emulation/test_olmcolorkey_edge_blur_apply_aex_20260716.py
```

The machine-readable result is the authority for whether the shim reached the
normal return. If the host ABI blocks, `deepest_rip` is the exact deepest RIP
reported by Unicorn and callback history identifies the last host boundary.

## 2026-07-16 result

Direction 1 reached the normal return in 1,021 instructions with `RAX=0`.
The destination payload begins:

```text
[184,204,204,204, 27,204,204,204, 0,204,204,204, ...]
```

The shim observed acquire, new-handle, lock, unlock, dispose, and suite
release callbacks. This is a normal AEX return under the shim, not proof that
the real AE host uses the same suite object layout. The direction-1 call uses
the independent `FUN_1800049a0` weight selection and therefore provides the
requested apply-vs-weight boundary comparison: the apply helper writes the
first byte of each destination pixel while preserving the sentinel bytes in
the remaining three bytes.

After direction 1 was stable, directions 2 and 3 were exercised. Both also
returned `RAX=0` under the same typed worlds and shim. Their first destination
bytes were direction 2: `[127,177,27,234,77,27,234,0]`, and direction 3:
`[255,255,127,27,227,127,27,0]`. These are raw AEX/shim observations; no
AE-exact classification is made for any direction.
