# F29: SSE NaN operand order

The patch changes x86 SSE's two-input NaN selection to the first NaN operand,
quieted by the existing softfloat caller. A separate status flag keeps x87's
significand-based rule. CPU initialization, reset, and MXCSR updates establish
that flag. MIN/MAX, conversions, invalid-operation default NaNs, and FMA's
separate three-input selector are untouched.

Reference: [Intel SDM volume 1, revision 090](https://cdrdv2-public.intel.com/874241/253665-090-sdm-vol-1.pdf),
section 4.8.3.5 / Table 4-8. Rosetta agrees on all 2,368 tested NaN arithmetic
lanes. This is masked-exception output-bit evidence, not native Windows or AE
validation. Rosetta reports FMA=0 and AVX=0, so those instructions were not run.

The reference worker is
`~/.cache/olm-emu/worker-F29-ssenan/aex-guest-worker`, SHA-256
`1c8fb695596e5cf9be21b7c644a3680011ea5b88f4be6e092d93383e3ed4f369`.
The cache index has a new entry; the fuzzer default is unchanged.

## Recheck the final worker

Run from the worktree. Commands write only scratch reports/corpora:

```sh
bash tools/emulation/aexcompat_patches/replay_F29.sh baseline
bash tools/emulation/aexcompat_patches/replay_F29.sh patched
python3 tools/emulation/aexcompat_patches/verify_replays_F29.py \
  --scratch orchestra/state/F29-unicorn-sse-nan-propagation \
  --output orchestra/state/F29-unicorn-sse-nan-propagation/replays.json
```

Expected: 708 corpus cases, 707 unchanged; all 687 cases without input NaNs
unchanged. Only saved OLMBlur case 99 changes. Seed 1 n300 changes reference
outputs for 99, 116, 290, 299, exclusively NaN-to-NaN words; Smart remains
281 exact / 2 mismatch / 17 refusal. Exit 1 for the patched OLMBlur corpus is
expected because saved oracle hashes are unchanged. Both workers also disagree
with 16 historical gate-off KiraKira and 29 RadialBlur expectations; their results
are identical to each other, and those saved expectations are not modified.

## Independent rebuild and instruction characterization

The original AEXCompat snapshot is copied to `src-F29`; the actual build input
is its `reference-guest` subdirectory, copied from the actual fuzzer default worker's source lineage at
`/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest`
(parent worker SHA `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`). This deliberately preserves that worker's host and math patches
instead of introducing unrelated differences from current upstream AEXCompat.
Only the six files in the committed patch differ from the parent source.

A fresh, space-free destination is required. The build uses one job, offline
locked dependencies, and refuses to start below 30% free memory. Existing source
and binary destinations are never overwritten.

```sh
python3 tools/emulation/aexcompat_patches/build_F29.py \
  --cache-root "$HOME/.cache/olm-emu/F29-independent-check" \
  --scratch orchestra/state/F29-unicorn-sse-nan-propagation/rebuild
bash tools/emulation/aexcompat_patches/characterize_F29.sh \
  "$HOME/.cache/olm-emu/F29-independent-check"
```

Expected: 3,200 instruction conditions, old disagreement count 188, patched 0;
2,368 NaN lanes agree with SDM; 144 x87 conditions unchanged and equal to
Rosetta; default-initialized ADDSS returns `7fc12345`. Scalar SS/SD, packed
PS/PD, ADD/SUB/MUL/DIV/MIN/MAX/SQRT and SS↔SD/PS↔PD conversions are covered.
Registers are loaded from integer bytes, with distinct signs/payloads and
rotated packed lanes. The same instruction bytes run in both environments.
The library path and hash are checked, preventing silent Python-library fallback.
Unicorn's `uc_version()` reports the same value in these libraries despite the
worker crate being 2.1.5; library hashes and Cargo.lock establish identity.

After characterization, delete the independent cache's
`worker-F29-ssenan/build` directory and the generated `probe*` / `controls-*`
subdirectories in scratch. Keep reports/logs and the final worker binary.
Rebuild hashes can vary with absolute paths; output equality is the check.

`F29-evidence/instructions.json` contains the complete disagreement table.
`replays.json` contains every changed case's before/after result, raw hashes,
and every changed NaN word. Other evidence files bind the build sources and
instruction libraries. No plugin, saved corpus expectation, or release gate
was changed.

`F29-evidence/parent-selection.json` records why C24's cached worker was not
used as the final parent: it already differs from the actual fuzzer default in
29 RadialBlur corpus results. The final F29 build preserves the actual default.
