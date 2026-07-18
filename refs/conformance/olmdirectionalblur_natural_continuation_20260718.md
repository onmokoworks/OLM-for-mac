# OLMDirectionalBlur Natural Continuation 20260718

- Status: `pass`.
- Scope: natural 8bpc AEX path, accepted actual populate callback through downstream continuation.
- Production source changed: `False`.
- Windows values fabricated: `False`.
- AE exact claim: `False`.

## Checkpoint State

- Accepted populate evidence: `refs/conformance/olmdirectionalblur_actual_populate_checkpoint_20260717.json` (sha256 `99c3ef367f9763120d6bdce9062a5e1d9345f81f8e4de9ceaa17540fa0fa2111`).
- Observed in this bounded replay: `real_populate_return_0x180006980, rotate_sample_0x180002064, rotateback_call_0x180005628, rotateback_return_0x18000562d, output_iterate_call_0x180005665, real_output_callback_0x180006b30`.
- First missing checkpoint: `None`.
- Last observed checkpoint: `real_output_callback_0x180006b30`.
- Downstream target-cell write: `True`.
- Real output callback: `True`.
- Initial fixture blocker before explicit continuation: `pre-render-return` at `0x180002064`.
- Final blocker: `None`.

## FACT

- The accepted populate witness is a real AEX callback at `0x180006980` in the natural 26-wide fixture.
- The kernel preserves the outer Iterate8 frame while invoking the callback through a private return sentinel.
- This run returned kernel status `pass` with subprocess return code `0`.
- A downstream write is counted only when a real AEX memory write overlaps the natural `params+0x8090` target cell after populate.

## INFERENCE

- A `pass` here is a bounded natural-path continuation witness, not Mac AE exactness.
- A `blocked` result identifies the first missing callback/state and is the only safe conclusion when the natural path stops early.
- `--resume` replays the same bounded kernel after validating the saved token; it does not restore serialized AEX CPU memory.

## Reproduction

`python3 tools/emulation/run_olmdirectionalblur_natural_continuation_20260718.py`
`python3 tools/emulation/run_olmdirectionalblur_natural_continuation_20260718.py --resume`
