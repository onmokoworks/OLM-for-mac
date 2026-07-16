# OLMBlur case_0004 staged-helper replay

## FACT

- Pinned actual AEX: `plugins_2025/OLMBlur.aex` / `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.
- Exact manifest parameters: amount `125.599998474121`, smoothness `100`, repeat `4`, bias `1`, Legacy `0`.
- The actual worker staging boundary `0x1800028db` captured the complete `6220800`-byte RGB float plane and `518400`-byte active mask; both match the retained PF16 decode.
- During schedule capture, both helper bodies are detoured to an immediate return. All `48` caller calls retain their exact radius, dimensions, pass range, weight pointer, and weight bytes in the JSON.
- The captured and H/V-agreed radius sequence is `[125, 36, 10, 2]`. Only captured coefficient bytes drive the direct bounded helper calls.
- Layer A: all `8` actual-AEX one-strip helper fixtures match the portable C++ helper byte-for-byte. Every actual run uses a `3,000,000` instruction cap.
- Layer B: two independent `347x347` dependency cones are composed through the portable helper only, using the exact caller-captured radii and weight bytes.

## Witnesses

- `(411,258)` portable full-cone float32 bits: `['0x46ac2b00', '0x00000000', '0x00000000']`.
- `(458,314)` portable full-cone float32 bits: `['0x46ce0b00', '0x00000000', '0x00000000']`.

## INFERENCE

- Classification: `actual_helper_micro_exact_and_portable_full_cone_result`.
- `actual_helper_micro_exact` establishes function-level compatibility only on the eight deterministic strips.
- `portable_full_cone_result` is a complete portable composition for the two witnesses. No actual-AEX full chain is executed or implied.
- Neither layer is AE exact or Windows/export evidence.
- The known capped full-image run was not repeated.

## Test

```text
python3 tools/emulation/test_olmblur_case0004_staged_helper_replay_20260716.py
```

## Changed files

- `tools/emulation/probe_olmblur_case0004_staged_helper_replay.py` (new)
- `tools/emulation/probe_olmblur_case0004_portable_helper.cpp` (new)
- `tools/emulation/test_olmblur_case0004_staged_helper_replay_20260716.py` (new)
- `refs/conformance/olmblur_case0004_staged_helper_replay_20260716.json` (new)
- `refs/conformance/olmblur_case0004_staged_helper_replay_20260716.md` (new)
