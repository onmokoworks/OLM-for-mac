# OLMDirectionalBlur Natural Writer-Owner Checkpoint

- Status: `pass`.
- Scope: Mac-local Unicorn, requested angle `0`, natural 8bpc render caller into `FUN_180006700` and the real writer at `0x180006b30`.
- The bounded owner is the output Iterate8 callback refcon at `[RSP+0x30]`; its `+0x8090` field points at the writer-entry float buffer.
- The checkpoint observed the natural Iterate8 callbacks `0x180006980` then `0x180006b30`, with the real writer invoked for each output pixel.
- This is bounded local ownership evidence. It contains no fabricated Windows values and makes no AE-exact claim.
- The producer upstream of that refcon remains unresolved; the internal post-rotateback context is a distinct object and is not conflated with the writer refcon.

The JSON records the hash-pinned AEX, fixture, source, natural checkpoints, and captured writer-entry samples.

Reproduction:

```sh
python3 tools/emulation/test_olmdirectionalblur_natural_writer_owner_20260717.py
```
