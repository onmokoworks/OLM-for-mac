status: blocked

summary:
- Reproduced F28 double-pow's 275 / 267 mismatches on 100,000,000 pairs, in both UCRT FMA modes.
- Retained four complete diagnostic campaigns and two single-witness hypothesis tests; no candidate qualifies.
- Two distinct hypotheses on the remaining normal-result witness were refuted without a new boundary; stopped under worker rule 8.
- Added reproducible diagnostic tooling/evidence only; no library API, Microsoft-derived implementation, plugin, or worker integration.
- Required billion-input/native-arm64/dense-boundary qualification and sin/cos/exp implementation remain unperformed.

facts:
- Worktree branch: `orch/F43-ucrtmath-double`. Read AGENT_GUIDE.md, GOTCHAS.md, compatibility plan, F42 policy/how-to-derive, F28/F27c reports, and the relevant ledger matrix rows. Initial git status was clean.
- `memory_pressure` reported 51% system-wide memory free before building. Compiler: Apple clang 17.0.0 (clang-1700.6.4.2). At most two mathematical processes ran concurrently; builds were sequential. No worker, AEXCompat, plugin, MAIN, ledger, or gate edits.
- AMD source was cloned to F43 scratch and checked out at `29fd054f383e6c5e2dec2fce781d5220059f1836`. Each build asserts the exact commit and clean checkout. No AMD source modification is made in that checkout; variants are generated in sibling scratch build directories.
- DLL used in place: `/Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll`, SHA256 `385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3`. The existing F27c loader and F28 comparator are unchanged: two relocated DLLs, asserted FMA masks 0/3, MXCSR 0x1f80. These are Rosetta measurements, not new Unicorn or native-Windows observations.
- The input producer is native arm64; candidates are x86_64 AMD builds, contraction-off / contraction-fast with `-mfma`. Explicit upstream FMA remains in the off build. No native arm64 candidate exists yet.
- Ran `python3 ucrtmath/tests/double/diagnose.py VARIANT` for `baseline`, `top20`, `scaled`, `combined`, each with 100,000,000 F28 random pairs and both modes. All commands exited 0 (successful measurement, not equivalence). Streams were bounded and not retained as large arrays.

| Variant | UCRT0 vs AMD-off | finite inputs | UCRT1 vs AMD-fma | finite inputs | first witness |
| --- | ---: | ---: | ---: | ---: | --- |
| baseline | 275 | 263 | 267 | 255 | W1 |
| top20 | 271 | 259 | 266 | 254 | W1 |
| scaled | 311 | 299 | 303 | 291 | W2 |
| combined | 307 | 295 | 302 | 290 | W3 |

Raw bits (same first witness/results for both paired modes in each listed campaign):

| ID | x | y | UCRT | mismatching candidate |
| --- | --- | --- | --- | --- |
| W1 | `4af491eedc5e5b0a` | `c0173ef560c4bc83` | `00021a62ea4eeb21` | `00021a62ea4eeb20` |
| W2 | `17db023316630462` | `3f89997eeda3c17f` | `3f6fa8d8ddaac688` | `3f6fa8d8ddaac689` |
| W3 | `300422d9a042d15f` | `3efb46f239a9a9c7` | `3fefda7803f095f0` | `3fefda7803f095f1` |

- `top20` changes AMD's `abs_ylogx` extraction from `>>32` to `>>44` before comparison with `TOP20_EXP_MAX`. `scaled` replaces `result * dn` by `fma(w, dn, (z + temp) * dn)` in the subnormal path. `combined` applies both. These are algorithmic experiments, not expected-bit patches.
- Direct one-row replay of W1/W2 established: baseline fails both; top20 fixes W2 but not W1; scaled fixes W1 but not W2, in both modes. These six observations are retained under `isolated` in results.json. An intermediate commentary called W2 a newly introduced normal failure; this was corrected after replay: W2 already fails baseline. No source change was based on that mistaken interpretation.
- For W3, `python3 ucrtmath/tests/double/diagnose.py tail-fma --witness 3` tested fused accumulation of the high-product residual with `y * log_lo`. It exited 0 and retained 1/1 mismatch in each mode, with W3's unchanged bits above.
- For the same W3, `python3 ucrtmath/tests/double/diagnose.py horner --witness 3` tested Horner exp-polynomial evaluation instead of Estrin, with unchanged coefficients. It exited 0 and retained 1/1 mismatch in each mode, with unchanged bits. These are two distinct, unsuccessful local causal hypotheses with no new boundary. Numerical investigation stopped here.
- Read-only Capstone inspection identified pow export RVA `0x78440`, selecting `0x65160` or `0xa5310` according to the active mode mask; sin/cos/exp exports are `0xbb6e0` / `0xb7370` / `0xb7de0`. Scratch disassembly was not committed. This inspection does not establish equivalent algorithms or constants for a port.
- `PYTHONDONTWRITEBYTECODE=1 python3 ucrtmath/tests/double/check_results.py` exited 0: six campaigns' counts, first witnesses, candidate source hashes and AMD/DLL pins matched retained evidence. Both final Python files parsed successfully. The final runner reuses the original comparator directly; measurements used a byte-for-byte copy of that comparator with only the relative include path adjusted. No comparator semantics changed.
- Actual generated candidate and dylib SHA256 values are retained per campaign in `ucrtmath/tests/double/results.json`; binary hashes are provenance, not portable rebuild acceptance criteria.
- Peak observed scratch size was 42 MiB, below 5 GiB. All started processes exited. Regenerable AMD checkout and build directories were removed after packaging; logs and numerical evidence remain.

inference:
- The input-range check and subnormal reconstruction each affect real failures, but neither their individual nor combined variants establishes UCRT equivalence. The scaled variant's larger count specifically prevents adopting it as a general fix.
- W3 is a normal result near one. Its unchanged response to tail accumulation and polynomial evaluation changes does not identify the root cause, and does not prove those operations irrelevant for other inputs. The next investigation needs an intermediate-value boundary, rather than further blind arithmetic variants.
- F28's closeness does not justify assuming float fixes alone close double pow. No claims are made about the missing native-arm64 implementation, billion-input campaign, plugin-range coverage, sin/cos/exp, or AE exactness.

changed_files:
- `ucrtmath/tests/double/diagnose.py`: pinned-source, bounded-process diagnostic build/run harness; rejected variants remain test-only.
- `ucrtmath/tests/double/check_results.py`: compare reproduced numerical outcomes and identities.
- `ucrtmath/tests/double/results.json`: measured counts, first witnesses, isolated observations, candidate hashes.
- `ucrtmath/tests/double/README.md`: scope, hypotheses, limitations and OLM-internal oracle policy.
- `orchestra/reports/F43-ucrtmath-double.md`: this report.

verify:
Run from this worktree (sequentially; no jobs pool). After cleanup, clone is required:
```sh
state="$PWD/orchestra/state/F43-ucrtmath-double"
mkdir -p "$state"
export TMPDIR="$state"
export PYTHONDONTWRITEBYTECODE=1
git clone https://github.com/amd/aocl-libm-ose "$state/amd-source" > "$state/recheck-clone.log" 2>&1
git -C "$state/amd-source" checkout 29fd054f383e6c5e2dec2fce781d5220059f1836 >> "$state/recheck-clone.log" 2>&1
for variant in baseline top20 scaled combined; do
  python3 ucrtmath/tests/double/diagnose.py "$variant" > "$state/recheck-$variant.log" 2>&1 || exit 1
done
for variant in tail-fma horner; do
  python3 ucrtmath/tests/double/diagnose.py "$variant" --witness 3 > "$state/recheck-$variant.log" 2>&1 || exit 1
done
python3 ucrtmath/tests/double/check_results.py
```
Expected: commands exit 0; checker prints `6 campaigns: numerical results, candidate source hashes, AMD/DLL pins match`. Mismatches must reproduce the nonzero table above; this is a blocked-result reproduction, not a library acceptance test. Individual W1/W2 observations can be rerun with `--witness 1` / `--witness 2` for baseline/top20/scaled.

next:
- Assign a focused double-pow intermediate trace: W3 through log high/low, y-product high/low, exp reduction/table selection and reconstruction in both actual UCRT paths versus AMD. Preserve W1/W2 and reject variants that merely move the first mismatch. Establish the first differing operation before another general fix.
- Then implement and qualify publishable AMD-derived pow natively on arm64. The requested 10^9 random pairs per mode plus dense boundaries are still outstanding.
- Implement sin/cos/exp separately under `ucrtmath/ms/` using F42's interoperability policy and constant provenance, then perform all required billion-input and dense-boundary campaigns. No such implementation was attempted after the stop condition.
- Only after qualification, a separate integration ticket should update worker imports and Mac call sites, following F30/F31. No integration is authorized by these diagnostic results.
