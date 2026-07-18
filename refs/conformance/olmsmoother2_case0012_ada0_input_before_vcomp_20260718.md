# OLMSmoother2 case0012 ADA0 input witness, 2026-07-18

## Verdict

`PASS_BOUNDED_ACTUAL_AEX_ADA0_INPUT_BEFORE_VCOMP`

The checked-in Windows AEX was executed locally through `FUN_18000ada0`; a code hook captured its four entry pointers and the descriptor-resolved input before the ADA0 call to `VCOMP140!_vcomp_fork`.

## Captured Boundary

- Source descriptor: `{'address': '0x20001600', 'base': '0x20000000', 'width': 16, 'height': 16, 'stride_bytes': 256}`.
- Class descriptor: `{'address': '0x20001620', 'base': '0x20001000', 'width': 16, 'height': 16, 'stride_bytes': 64}`.
- Rectangle: `[0, 0, 16, 16]`.
- Config `+0x1c`: `88`; `+0x70`: `0`; `+0x74`: `0.0`.
- Captured source window: `25` RGBA float pixels, offsets `-2..2` around translated origin `[8, 8]`.

## Execution

- Bounded run counted `54625` guest instructions, one serial worker, and `256` classifier calls.
- The generated class window matched the retained translated tuple exactly; this validates the capture did not alter the natural caller path.

## Boundary

This is an actual-AEX Mac-local witness over retained fixture inputs. It is not a replacement for same-run Windows capture: no live Windows source bytes, config bytes, descriptor strides, or rectangle are asserted.

## Reproduce

```sh
python3 tools/emulation/probe_olmsmoother2_case0012_ada0_input_before_vcomp_20260718.py \
  --output-json refs/conformance/olmsmoother2_case0012_ada0_input_before_vcomp_20260718.json \
  --output-md refs/conformance/olmsmoother2_case0012_ada0_input_before_vcomp_20260718.md
```
