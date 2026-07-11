# OLMBlur Legacy center-copy correction

## Binary fact

In actual AEX `FUN_1800014f0` and `FUN_180001ea0`, the persistent RGB values
are comparison state only. When the decompiled `all_same` predicate remains
true, the helper copies the current center source RGB into the destination.
The portable helper incorrectly copied the comparison carry RGB instead.

The difference is visible in `decomp/OLMBlur.aex.c.txt`:

- horizontal `FUN_1800014f0`: the `bVar2` branch reads the current source
  address derived from `param_2` and writes it through `param_3`;
- vertical `FUN_180001ea0`: the `bVar2` branch copies `puVar10[-2..0]`, the
  current source center, through the `param_3 - param_2` destination delta.

## Reproduction

Before the correction, both 8bpc and 16bpc Legacy case 0007 differed only at
`y=0, x=1..18`. Mac wrote zero RGB while Windows retained the horizontal-pass
ramp. The identical coordinates at both depths ruled out quantization.

After changing `core/olmblur_fullworker_helper.cpp` to copy `center`:

- all six helper fixtures remain byte-exact;
- all three 8bpc Legacy complete-worker fixtures remain byte-exact;
- all three 16bpc Legacy complete-worker fixtures remain byte-exact;
- all three 32bpc Legacy complete-worker fixtures become byte-exact;
- Mac AE 8bpc case 0007 becomes `max_diff=0`;
- Mac AE 16bpc cases 0001 through 0007 are all `max_diff=0`.

This is an asm-grounded semantic correction, not PNG tuning.
