# OLMDirectionalBlur Iterate8 Continuation Transform Checkpoint

- Status: `blocked` at the next natural boundary.
- Actual `0x180006980` runs on a private stack with `context_save/context_restore`, then returns to the emulated Iterate8 handler without using `call_function` continuation recovery.
- The target source cell is captured from `params+0x8078` before downstream processing, and the writer cell from `params+0x8090` is captured before the transform.
- No subsequent write overlapping the writer target cell was observed. The fixture stopped at `pre-render-return`, so no downstream function/address is claimed.
- The isolated natural event showed distinct source and writer pointers. The earlier `0x20000980`/`0x20000980` alias came from the fixture's synthetic `callback_model_check`, not true natural state.
- The harness stops at the next fixture-reported ABI boundary and makes no Windows or AE-exact claim.

Reproduction:

```sh
python3 tools/emulation/test_olmdirectionalblur_iterate8_continuation_transform_20260717.py
```
