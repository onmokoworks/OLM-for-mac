# OLMDirectionalBlur Iterate8 Natural Pre-Render Follow-up

Status: `pass` for the bounded natural 8bpc continuation. No production source
or ledger file was edited, no Windows value was fabricated, and no pixel output
was modeled or copied into the fixture's host byte array.

The first natural PF_Iterate8 callback frame was preserved byte-for-byte while
the real AEX callback `0x180006980` ran on a separate emulated stack. At callback
entry, the observed frame was:

| slot | value | meaning |
|---|---:|---|
| `RSP` | `0x0f0f5928` | PF_Iterate8 callback frame |
| `[RSP+0x28]` | `0x4000041c` | rectangle |
| `[RSP+0x30]` | `0x0f0f6e60` | refcon/params |
| `[RSP+0x38]` | `0x180006980` | populate callback |
| `[RSP+0x40]` | `0x400003f0` | destination world |

The populate callback returned naturally after 35 AEX instructions to the
private sentinel `0x820ffff0`. Unlike the loader's global `0x90000000`
trampoline, this sentinel does not call `emu_stop()` and does not overwrite the
outer PF_Iterate8 frame.

Unicorn pauses a parent `emu_start` after a nested emulation run even without an
explicit stop. The parent machine remained live immediately after the sampled
instruction at `0x180002064`, at `RIP=0x180002068`. The harness captured the
full GPR set, low float/raw values for XMM2/XMM3/XMM5/XMM6, and readable qwords
for candidate pointer registers at `0x180002064`, then resumed that exact live
state rather than reconstructing the frame or any pixel data.

The explicit continuation reached every requested downstream checkpoint in
natural order:

1. Rotateback call `0x180005628`.
2. Real `FUN_180001ec0` return at `0x18000562d`.
3. Second PF_Iterate8 call at `0x180005665`.
4. Real output callback `0x180006b30` with refcon `0x0f0f6e60`.
5. Render return trampoline `0x90000000`.

The output callback also returned after 35 real AEX instructions. Its guest
write was allowed to occur, but the harness deliberately did not read it into,
or otherwise populate, the fixture's host-side output model. The first observed
actual downstream write overlapping the selected `params+0x8090` cell occurred
at `0x180002196`; the report makes no pixel-value or AE-exact output claim.

The embedded fixture JSON is written before this follow-up's explicit live
resume and therefore retains its generic `pre-render-return` diagnosis ending
at `0x180002064`. The ordered `target.required_checkpoint_order` and
`target.natural_continuation_checkpoints` fields in the owned JSON sidecar are
the authoritative post-resume result. If a future run loses state, the harness
returns exit code 0 with `status: blocked` and names the first missing natural
ABI/state checkpoint.

Reproduction:

```sh
python3 tools/emulation/test_olmdirectionalblur_iterate8_natural_prerender_followup_20260717.py
```
