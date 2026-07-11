# PF Iterate8 Area Audit

Verdict: **PASS**. The corrected host loop walks the `PF_EffectWorld` area
`[left, top, right, bottom]` in host-world coordinates. It does not walk the
parameter work dimensions (`params+0x80a0/+0x80a4`, observed as `2206x2206` in
the requested full-world scenario). The callback at `0x180006980` applies the
padded work offsets itself.

## Scope

- Audited file: `tools/emulation/dblur_fullrender_host_fixture_20260711.py`
- Binary: `plugins_2025/OLMDirectionalBlur.aex`
- Primary binary evidence: `disasm/OLMDirectionalBlur.aex.asm.txt`,
  `decomp/OLMDirectionalBlur.aex.c.txt`
- Wrapper ABI evidence: `FUN_180006700` / `0x180006700..0x1800067ee`
- Callback evidence: populate `0x180006980`, output `0x180006b30`

## Findings

1. **Wrapper ABI is correctly decoded.** The AEX call sites load the world
   extent pointer (`world + 0x2c`) as the `rect` argument, pass `0` as start,
   pass the host/world height as end, and pass the world as the source/dest
   world. `FUN_180006700` forwards arguments 1-4 in registers and arguments
   5-8 from its call area to the PF Iterate8 suite. At the suite callback entry
   the fixture correctly reads `rect`, `refcon`, `pixel_fn`, and `dst` from
   `RSP+0x28`, `+0x30`, `+0x38`, and `+0x40`.

2. **The area source is correct.** The loop reads exactly four signed 32-bit
   words from `rect` and iterates `x in range(left, right)` and
   `y in range(top, bottom)`. It validates those coordinates against the
   source and destination world dimensions, not against the padded work
   dimensions.

3. **The padded dimensions remain callback-local.** The fixture records
   `params+0x80a0/+0x80a4` as diagnostic `param_stride/param_height`; it does
   not use them as the host iteration bounds. This matches the AEX callback
   index in `notes/IR_OLMDirectionalBlur.md`: `((params+0x8098+y) *
   params+0x80a0 + (params+0x809c+x)) * 16` for the float work plane. The
   populate model uses the same formula.

4. **World metadata and rowbytes are inspected.** `build_world()` stores data
   at `+0x18`, rowbytes at `+0x20`, width at `+0x24`, height at `+0x28`, and
   extent `[0,0,width,height]` at `+0x2c`. The loop reads source and
   destination rowbytes from `+0x20` and addresses host pixels as
   `data + y*rowbytes + x*4`. The observed 960x540 run recorded area
   `[0,0,960,540]`, work dimensions `1104x1104`, and successful populate and
   output callbacks.

5. **No concrete correctness bug found.** In particular, there is no remaining
   use of parameter work dimensions as PF Iterate8 area bounds in the audited
   loop. The current implementation therefore supports the critical claim for
   a 1920x1080 host world with a larger padded work plane.

## Requested smoke

Exact command:

```text
python3 tools/emulation/smoke_dblur_fullrender_detour_equivalence_20260711.py
```

Exact stdout:

```json
{"status": "pass", "dimensions": [16, 16], "argb_sha256": "8b8a28887908f089024bc38f69221148b612adfdcf44afc63d282216a0d7d3ae", "actual_aex_instructions": 326427, "detoured_instructions": 124347, "rowdriver_detour_calls": 26}
```

The smoke also asserted both real and detoured reports contained Iterate8
areas `[0,0,16,16]`, matching the host world rather than padded dimensions,
and that their final output hashes were equal.

## Defensive validation

After this audit, the loop was tightened to reject `rowbytes < width*4` and to
verify that the declared final source and destination rows are readable. These
checks do not alter the valid worlds exercised by the passing smoke.

## Files changed

Only this report and its JSON companion were added. No existing file was
modified.
