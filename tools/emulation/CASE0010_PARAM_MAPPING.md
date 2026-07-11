# case_0010 -> param_2 field mapping

`FUN_180008690` reads each AE parameter into a byte offset of the context struct (the same struct FUN_180004640 sees as `param_2` / FUN_180007520 sees as `param_5`). Reader functions:

- `FUN_18000e5f0` -> int/menu (OneD popup)
- `FUN_18000de60` -> TwoD spatial (two doubles: X @+0x28, Y @+0x30)
- `FUN_18000e270` -> int (checkbox/slider int)
- `FUN_18000e430` -> float (FpLong/percent)
- `FUN_18000e190` -> byte/bool
- `FUN_18000e6d0` -> int angle (degrees)
- `FUN_18000e7b0` -> float

| reader | ctx byte off | AE param (case_0010 value) | post-read transform |
|--------|--------------|----------------------------|---------------------|
| e5f0 idx1  | +0x20 | Blur Type (=2 Rotation) | - |
| de60 idx2  | +0x28/+0x30 (double) | Center (=960,540) | later: minus world origin, * downsample |
| e270 idx4  | +0x64 | Outer Blur enable/int | - |
| e5f0 idx1c | +0x54 | (outer) | -> param_1[9] |
| e270 idx1d | +0x58 | (outer) | -> param_1[10] |
| e270 idx5  | +0x6c | (outer strength/size) | -> param_1[0xf24c] kernel size |
| e270 idx8  | +0x68 | | -> param_1[0xea7b] |
| e5f0 idx1e | +0x5c | | -> param_1[0xb] |
| e270 idx1f | +0x60 | | -> param_1[0xc] |
| e270 idx9  | +0x70 | | -> param_1[0xf24d] kernel size |
| e190 idx1a | +0x74 (byte) | Repeat Border (=1) | selects sampler pair |
| e430 idxc  | +0x78 (float) | | -> param_1[5] (divisor) |
| e6d0 idxd  | +0x7c (int) | Angle (=0 deg) | `+0x7c = (int)(deg * pi/180)` = 0 |
| e430 idxf  | +0x80 (float) | strength feeding param_5[0x10] | `if v>0: +0x80 = 1/v else 0.2` -> FUN_180001ac0 -> param_1[0] |
| e430 idx10 | +0x38 | | -> param_1[?] |
| e430 idx11 | +0x40 | | `*= DAT_1800215f8`; +0x44 bool = (DAT_180021600 < v) |
| e430 idx13 | +0x3c | | `*= DAT_1800215f8` |
| e5f0 idx14 | +0x50 | | if ==3: checkout layer param 0x15 |
| e270 idx16 | +0xfc | | quality/threads-ish |
| e7b0 idx17 | +0x100 | | float |
| e430 idx18 | +0x104 | | * downsample |

## Key derivation for case_0010

- Angle = 0 deg  => ctx +0x7c = 0  => `cos=1, sin=0` in FUN_180004640.
- Witness geometry forces **iVar29 = 1800**, i.e. param_1[0] ~= 0.2, i.e. the strength value feeding `param_5[0x10]` reached FUN_180001ac0's `<= 0` default branch. (case_0010 has Inner Strength = 0 and Outer Strength = 4; the field that lands in +0x80/param_5[0x10] is the one that evaluates to <=0 here -- to be confirmed by running the reader.)
- Center (960,540) is transformed in FUN_180007520 (lines ~3455-3463): `param_5[5/6] = downsample * (center - world_origin)`.

## To build param_2 by real code (next step)

Mock each `FUN_18000eXXX(ctx, indata, reader_idx, out_ptr)` call to write the case_0010 manifest value at `out_ptr` (respecting int vs float vs double per the reader), then emulate `FUN_180008690 -> FUN_180007520 -> FUN_180004640` with the real input world. That yields a `param_2` the plugin's own code produced, ready for the bit-exact typed-cell compare against the Windows CDB values.
