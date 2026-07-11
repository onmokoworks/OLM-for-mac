# OLMSmoother2 Producer Branch Table - 2026-07-07

- Status: `local-aex-cpu-emulation-branch-table`
- Source: `tools/emulation/test_smoother2_producer.py`
- AEX: `aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex`
- Leaf check: `PASS`

## case_0004

- Witness: `(1903, 519)`
- Reference RGBA8: `[103, 103, 103, 113]`
- Local problem: Mac-side path can fall through to count=0 passthrough; Windows writer is already known semitransparent gray.

| Scenario | Entry | iVar6 | iVar5 | class_prev | Emit | vcount |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `empty-around-cur` | `True` | `1` | `1` | `0` | `True` | `3` |
| `isolated-class-at-cur` | `True` | `1` | `1` | `0` | `True` | `3` |
| `edge-cur-x0` | `False` | `1` | `1` | `None` | `None` | `0` |
| `edge-cur-ybottom` | `False` | `1` | `1` | `None` | `None` | `0` |
| `dense-nw-block` | `True` | `1` | `4` | `0` | `True` | `3` |
| `force-passthrough` | `True` | `7` | `8` | `1` | `False` | `0` |

### case_0004 Reading

- FUN_180013140 append/no-append is controlled by entry_guard, scanner spans, class_prev_byte, and emit_guard.
- The force-passthrough synthetic class-plane reaches vcount=0 without changing global fallback logic.
- This is local AEX branch grounding, not Windows-vs-Mac AE exact proof.

## case_0012

- Witness: `(91, 841)`
- Reference RGBA8: `[0, 0, 0, 0]`
- Local candidate RGBA8: `[90, 90, 90, 91]`
- Desc: `[5, 6, 1, 5, 8, 5]`
- e170 bitsum c: `2`
- f270 scale input: `0.5800000023841858`
- f270 append count: `1`
- e3a0 with-source append count: `1`

### case_0012 Reading

- Local e170/f270/e3a0 direct calls show c=2 keeps append alive.
- The remaining evidence needed is Windows-side class-plane/bitsum or cce0 producer state, not final writer bytes.

## Next Allowed Actions

- Use this table to choose a narrower producer witness before requesting more Windows debugger work.
- If continuing locally, sweep 0012 e170 bitsum c values and 0004 class-plane scanner patterns in the same harness.

## Forbidden

- Do not request final writer bytes again for these witnesses.
- Do not add global transparent-center fallback or global f270 suppression from this local table alone.
- Do not promote this local emulation evidence to AE exact.
