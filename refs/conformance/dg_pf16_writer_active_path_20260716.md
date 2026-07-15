# DG PF16 writer active-path census

- Status: `inactive_for_fixture`
- Scope: one same-loader actual-AEX run using the existing case_0023 compose fixture.
- Hooks: `0x181458030`, `0x1814581a0`, and compose `0x181170480`.
- No AE-exact claim and no production edits.

## Path proof

- Compose reached: `True`.
- Final output reached: `True`.
- Compose calls: `3`.
- Writer hits: `0`.

## Writer census

Each hit would retain RCX float32 values/raw bytes, RDX, R8D, the stack return address, and final destination words.

- No writer hit was observed. The leaves are `inactive_for_fixture`; this does not claim they are globally dead.

## Final words

- `(414, 393)`: AGRB16 `[32768, 0, 3598, 30583]`.
- `(415, 393)`: AGRB16 `[32768, 0, 32768, 0]`.
- `(416, 393)`: AGRB16 `[32768, 0, 32768, 0]`.

## Commands

```sh
python3 -m py_compile tools/emulation/test_dg_pf16_writer_active_path_20260716.py
python3 tools/emulation/test_dg_pf16_writer_active_path_20260716.py
```
