status: done
summary:
- Restored ColorKey's denominator-weighted distance scans for downsampled Thin/Blur; amounts remain unchanged.
- Admitted positive downsample fractions in the production PreRender/SmartRender geometry check.
- Fixed ColorKey-specific harness forwarding; F52 seed 1 and seed 20261024 each pass Smart 100/100.
- Added 810 exact downsample witnesses; 4,000 default route outputs equal the ticket-base outputs, and corpus replay is 9/9.
- ColorKey tests: 6 passed; fuzz framework: 34 run, OK, 2 skipped. Native AE rendering was not run.

facts:

Static evidence was read from MAIN's `disasm/OLMColorKey.aex.asm.txt`, without changing MAIN or the emulator. Original AEX SHA-256 is `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`. F52 worker SHA-256 is `1be0cb14f6e68ab9276ef37be3a381aae9fb0306914987eb91e1a9d23dd94f4b`.

- FACT: Thin orchestration at `0x180009181..0x1800091d1` dispatches distance types 3/2/1 to `0x7ca0/0x58a0/0x66f0`. Corresponding PF32/PF8 workers use `0x7ec0/0x5d60/0x6e20` and `0x80f0/0x6210/0x7550`.
- FACT: `0x58ae/0x58d8`, `0x6703/0x6734` and `0x7cc4/0x7cce` read PF_InData X/Y **denominators** at `+0x120/+0x128`. City-block and chessboard convert these to float32 horizontal/vertical increments. Diagonal chessboard neighbors use the vertical increment. The cap stays 4000 and the first nonseed stays 3999; neither is scaled.
- FACT: The reverse scan is not interchangeable with a separable mathematical distance transform under unequal steps. At `0x5ca1..0x5cfe`, the cached output pointer still denotes x+1 when read; XMM6 retains the candidate before the final minimum with the current pixel. Chessboard has the analogous carry/read order at `0x6c8a..0x6dad`. The implementation now follows these scans rather than adding output corrections.
- FACT: Euclidean `0x7ca0` passes the denominators to `0xa980`; the one-dimensional worker `0xa770` multiplies squared distances by the step twice, computes envelope intersections with the step and its float reciprocal (`0xa7d9..0xa85b`), then emits squared distances (`0xa930..0xa951`). The port propagates both steps through its existing squared-distance/envelope calculation and square root.
- FACT: Thin compares the original amount converted to float (`0x91df..`); Blur uses its existing float-materialized slider amount. There is no new integer radius rounding or radius multiplication. The `0x13a30` inverse-double helper has a caller at `0xd978`, but is not the distance-step source above.
- FACT: `ColorTriage.candidate()` overrides `PublicAdapter.candidate()`, so F52's common downsample environment setup was previously bypassed for ColorKey. This explains why the old F52 report could show numeric mismatches without the production PreRender refusal. The ColorKey adapter now supplies geometry to its existing real-SDK host, using a per-invocation environment copy. That host invokes production `EffectMain` for both SMART_PRE_RENDER and SMART_RENDER, with no hostless geometry bypass.

Commands actually run (all scratch under `orchestra/state/P01c-colorkey-downsample`, at most two active processes):

1. `python3 tools/fuzz/verify_colorkey_downsample_P01c.py --seed 1 --n 100`
   and `--seed 20261024 --n 100`: **Smart 100 E / 0 M / 0 R / 0 U each**.
   This wrapper runs `measure_F52.main()` with `--plugin olmcolorkey --n 100`, relocates its hardcoded scratch directory, and supplies/corrects the requested seed without editing the shared F52 driver. Classic remains 100 M for each seed, as in F52; its zero-output route is outside this ticket.
2. `python3 tools/fuzz/witness_colorkey_downsample_P01c.py`: **810/810 exact**, no refusal. Independent patterned input, PF8/PF16/PF32, 7x5/1x7/7x1 sampled worlds, all three metrics, Thin +/-3 and zero, Blur 0/2.5/4/5/4000 with directions 1/2/3. Fractions include 1/2, 1/4, asymmetric 1/2 x 1/3 and its transpose, and 2/3 x 2/3. These go through PreRender and SmartRender with full layer dimensions separate from sampled dimensions.
3. `python3 tools/fuzz/run.py --plugin olmcolorkey --n 2000 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$s/default-final" --report "$s/default-final.json" --corpus "$s/default-final-corpus"`: **Smart 1999 E, 0 M, 0 R, 1 U**. Index 1996 has an original-AEX invalid read at `0x180006d56`; the candidate renders, but no oracle output exists. Classic is 5 E / 1995 M. No tolerance was used.
4. `python3 tools/fuzz/regression_colorkey_downsample_P01c.py`: built ticket base `22f8f802` and final source; **all 4,000 route outputs/statuses identical**, zero changed outputs and zero exact-to-non-exact transitions. Thus the default campaign's oracle failure is not a changed candidate output. The script would consult the original oracle for any changed output.
5. `python3 tools/fuzz/run.py --plugin olmcolorkey --replay tests/fuzz_corpus/olmcolorkey --jobs 1 --scratch "$s/replay" --report "$s/replay.json"`: **9/9 match saved results**, using the two corpus-bound workers. No saved expectations changed.
6. `python3 tools/fuzz/verify_colorkey_downsample_P01c.py --unit-tests`: **6 passed**, including generic pixel/edge matrices and ASan/UBSan Thin coverage. This invokes the existing F20 worktree-aware ColorKey tests with ticket-local scratch.
7. `OLM_FUZZ_TEST_SCRATCH="$s/framework-tests" python3 -m unittest discover -s tools/fuzz -p 'test_*.py'`: **34 run, OK, 2 skipped**.
8. `git diff --check`: passed.

Intermediate observations, not final results:

- The first weighted-neighbor candidate gave seed 1 **99 E / 1 M**. Index 87, 11x2 PF16, asymmetric 1/2 x 1/3: one word differed at word 32, original `7513`, candidate `7713`. The disassembled chessboard carry resolved this boundary.
- The first independent 810-case campaign had **5 mismatches**, all Manhattan/asymmetric 1/2 x 1/3 on 7x5. The first was PF8, Blur=5/Around: five bytes differed, first byte 16, original `74`, candidate `66`. Following the cached pointer and carry in the Manhattan reverse scan resolved all five. The original failing rows are retained in `P01c-evidence/intermediate-witness-failures.json`.
- An intermediate candidate had 23 default Smart mismatches. The final full scan restoration eliminated them; the base-versus-final comparison proves this is **not** an improvement over the ticket base, but removal of an intermediate regression.
- Two baseline build attempts failed because a scratch directory occupied the output executable path `base/mac`; moving baseline source and build directories apart fixed this tooling error. No permission rejection occurred.

Final source SHA-256: `0b3309f0d66d395ff9fb8901c01bb41ed96915d1d0683a5cf186e3697eb0d7da`.
Final candidate SHA-256: `b76f54cd9fba5ff64f9304161b0ec8e8152127c87697c290968deae783974079`.
Summaries, per-witness hashes, compact F52 rows, corpus results, source hashes and test logs are committed in [P01c-evidence](P01c-evidence/). Inputs/parameters regenerate from the committed drivers; no copied AEX, reference-worker build, or candidate oracle is required. Regenerable build trees were removed.

inference:

- The seven F52 numeric mismatches came from comparing downsample-aware original distances with an unforwarded candidate geometry, not from a Blur-like truncated radius rule. Denominator-aware scans plus real geometry forwarding resolve all seven and both independent campaigns.
- The retained scan carry is observable under asymmetric steps, so scaling an already-computed isotropic distance plane is insufficient.
- These are CPU-AEX versus production-source public-entry results in a fake SDK host. They do not claim native AE preview validation, arbitrary ROI/expanded-world negotiation, or all-input numerical closure.

changed_files:

- `mac/OLMColorKey/OLMColorKey.cpp`
- `mac/OLMColorKey/OLMColorKey.h`
- `tools/fuzz/adapters/olmcolorkey.py`
- `tools/fuzz/verify_colorkey_downsample_P01c.py`
- `tools/fuzz/verify_colorkey_downsample_P01c.sh`
- `tools/fuzz/witness_colorkey_downsample_P01c.py`
- `tools/fuzz/regression_colorkey_downsample_P01c.py`
- This report and `orchestra/reports/P01c-evidence/*`.

verify:

From the worktree, run serially:

```sh
bash tools/fuzz/verify_colorkey_downsample_P01c.sh
```

Expected: both F52 seeds Smart 100/100; witnesses 810/810; default Smart 1999 exact plus the recorded unavailable oracle; 4000 base/final route comparisons with zero changes; corpus 9/9; ColorKey tests 6 passed; framework 34 run with 2 skips. Commands and complete logs remain under the ticket scratch directory. The individual commands above can be run separately with `s="$PWD/orchestra/state/P01c-colorkey-downsample"` and TMPDIR/TMP/TEMP pointing there.

next:

- Orchestrator review/merge; native AE 1/2 and 1/4 preview smoke on the rebuilt bundle.
- Separate ticket for the original oracle invalid read at seed 1/index 1996 and for ColorKey Classic route semantics. Neither is hidden by a tolerance, expected-value update, or release-gate change here.
