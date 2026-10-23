status: blocked

summary:
- Numerical implementation and all requested qualification completed: zero mismatches in both modes.
- Independently implemented UCRT double pow, minimal tables, provenance, and native-arm64/Rosetta harness.
- A closeout command containing `rm -rf` was rejected by tool policy; worker brief explicitly requires blocked status after any tool rejection.
- Cleanup was subsequently completed by a path-checked Python operation. This status records the mandated tool-rejection disposition, not a numerical failure.
- No plugin/worker integration, ledger, or release-gate changes.

facts:
- Branch `orch/F43c-ucrtmath-ms-pow`, initially clean. Read shared guide, emulation gotchas, compatibility plan, F42 policy, F43 evidence, and relevant plugin ledger rows. No ancestor AGENTS.md was present.
- `memory_pressure` reported 46% system-wide memory free. Compiler: Apple clang 17.0.0 (clang-1700.6.4.2), native target arm64-apple-darwin24.6.0. At most two mathematical processes ran concurrently with fixed 4096-row buffers. No subagents, AMD patches, or AEXCompat rebuilds.
- Local read-only Capstone inspection: pow export RVA `78440`, FMA path `65160`, non-FMA path `a5310`. Both use 128 log intervals and 256 exp intervals; log/product compensation differs by mode, while exp reconstruction is unfused. Dedicated subnormal reconstruction recovers addition residuals before rounding on the subnormal grid. `pow.md` records each constant/decision RVA; instruction listings remain scratch-only.
- DLL used in place: `/Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll`, SHA256 `385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3`. No Microsoft binary committed. `pow_extract.py` asserts the pin and extracts only 128 x 3 used log fields and 256 x 2 exp fields; unused fields/padding omitted.
- `python3 ucrtmath/ms/pow_check.py random --count 1000000` initially measured one mismatch per mode: x=`ffff603a66bc749d`, y=`c31b287de1f952ec`, oracle=`7fff603a66bc749d`, candidate=`ffff603a66bc749d`. Disassembly showed a finite-exponent NaN base is squared, then the odd-integer sign is applied. Implemented that general rule, not a per-witness patch. Initial result/source hash retained in `results/pow/initial-nan-diagnostic.json`.
- After correction, `python3 ucrtmath/ms/pow_check.py random --count 100000000` returned 0: zero mismatches both modes, 9.719 seconds. No further numerical revisions were needed.
- Final campaigns below returned 0. Native arm64 builds use `-O2 -ffp-contract=off -fno-fast-math`, with explicit FMA where observed. The unchanged F27c PE loader relocates two images, asserts FMA masks 0/3, sets MXCSR 0x1f80. All comparisons use complete raw 64-bit words, including NaN payload/sign. These are Rosetta observations, not new Unicorn, native-Windows, or AE observations.

| Command after `python3 ucrtmath/ms/pow_check.py` | Pairs | NOFMA mismatches | FMA mismatches | Seconds |
| --- | ---: | ---: | ---: | ---: |
| `random --count 1000000000` | 1,000,000,000 | 0 | 0 | 121.588 |
| `ranges --count 100000000` | 100,000,000 | 0 | 0 | 7.657 |
| `file --count 2243557 --inputs orchestra/state/F43c-ucrtmath-ms-pow/targets.txt --tag targeted` | 2,243,557 | 0 | 0 | 0.959 |

- Final campaigns have no first mismatch. Both process exits and exact stream counts are checked; retained JSON binds candidate, harness, loader, DLL, corpus, and executable hashes.
- `python3 ucrtmath/ms/pow_targets.py orchestra/state/F43c-ucrtmath-ms-pow` generated: F43 witnesses 3; special-value cross product 3,600; dense near-one 1,204,371; integer/half-integer neighborhoods 201,240; result boundaries 327,760; log-table boundaries 506,583. Some family overlaps are intentional. Near-one uses 8,193 consecutive bases; result transitions scan 4,097 exponent words each. Plugin samples cover [0,4) x [-8,8), and targeted tests include endpoints.
- Explicit W1/W2/W3 replay: zero mismatches both modes. The billion-pair stream uses F43's unchanged F28 raw-word seed/generator, so its first 100 million inputs also replay every input of all four F43 campaigns, including their non-first mismatches.
- `python3 ucrtmath/ms/pow_harness_check.py` returned 0: seven checks passed (valid result, truncated record, wrong count, empty stream, both outputs corrupt, only second mode corrupt, producer missing input). Corruption checks prove each mode rejects mismatches.
- `sh ucrtmath/build.sh "$PWD/orchestra/state/F43c-ucrtmath-ms-pow/library"` returned 0 without diagnostics. Linked `pow_native.c` against the resulting arm64 archive and replayed W1/W2/W3 through the comparator: three pairs, zero mismatches both modes.
- `python3 ucrtmath/ms/pow_retain.py --check` returned 0: three campaigns, current source hashes, and seven harness checks verified. `git diff --check` returned 0.
- Final pow.c SHA256 `b39a37d25a68aed0dbb40d1660487462c96e4cdf086d3a55a1d7bfe98ec33121`; pow_tables.h SHA256 `b1fcbc68a82bcce87ba3de206df62b3b6e2c00e5d93815fe6c4ce955933154b8`.
- Tool rejection at closeout: `rm -f style commands are not permitted. Use a safer approach`. The entire combined command was rejected before execution. Reissued report/check steps separately and cleaned only verified scratch build paths with Python. Worker instruction requires this report to remain blocked after any rejection.
- Peak observed scratch size 81 MiB, below 5 GiB. All started mathematical processes exited. Regenerable build trees and target text were removed; logs/evidence retained. No MAIN, emulator, plugin, gate, ledger, or other-ticket edits; no push/history rewrite.

inference:
- The compensated UCRT log/product and exp reconstruction close the F43 witnesses without further AMD patching. The one initial NaN-sign mismatch was explained by an observed special-value branch.
- The numerical qualification meets the requested corpus bar. It is not exhaustive over all 2^128 input pairs and does not establish AE exactness, errno/exception flag equivalence, or alternate rounding-mode compatibility.
- There is no remaining observed numerical blocker. The blocked disposition is mandated solely by the worker's tool-rejection rule and requires orchestrator review.

changed_files:
- `ucrtmath/ms/pow.c`: independent double implementation.
- `ucrtmath/ms/pow_tables.h`, `pow_extract.py`: minimal data and pinned regeneration.
- `ucrtmath/ms/pow.md`, `README.md`: algorithm, provenance, OLM-internal restriction, reproduction.
- `ucrtmath/ms/pow_native.c`, `pow_compare.c`, `pow_check.py`: bounded native/Rosetta qualification.
- `ucrtmath/ms/pow_targets.py`, `pow_harness_check.py`, `pow_retain.py`: dense corpus, stream checks, evidence validation.
- `ucrtmath/ms/results/pow/*.json`: measured qualification, initial diagnostic, hashes, family counts, harness evidence.
- `ucrtmath/include/ucrtmath.h`, `ucrtmath/build.sh`: declaration/archive member, no call-site integration.
- `orchestra/reports/F43c-ucrtmath-ms-pow.md`: this report.

verify:
Run sequentially from this worktree (one native producer, one Rosetta comparator, no jobs pool):
```sh
state="$PWD/orchestra/state/F43c-ucrtmath-ms-pow"
mkdir -p "$state"
export TMPDIR="$state" PYTHONDONTWRITEBYTECODE=1
python3 ucrtmath/ms/pow_targets.py "$state" > "$state/recheck-targets.log" 2>&1
python3 ucrtmath/ms/pow_check.py file --count 2243557 --inputs "$state/targets.txt" --tag targeted > "$state/recheck-targeted.log" 2>&1
python3 ucrtmath/ms/pow_check.py random --count 1000000000 > "$state/recheck-random.log" 2>&1
python3 ucrtmath/ms/pow_check.py ranges --count 100000000 > "$state/recheck-ranges.log" 2>&1
python3 ucrtmath/ms/pow_harness_check.py > "$state/recheck-harness.log" 2>&1
python3 ucrtmath/ms/pow_retain.py --check
sh ucrtmath/build.sh "$state/library" > "$state/recheck-build.log" 2>&1
git diff --check
```
Expected: all commands return 0; every numerical campaign has zero mismatches in both modes and the counts above. Checker prints `3 qualification campaigns: both modes exact; source hashes and 7 harness checks verified`. Binary hashes/timing are provenance, not portable acceptance requirements. Remove regenerated scratch build directories afterward using a permitted cleanup method.

next:
- Orchestrator reviews implementation and the mandatory tool-rejection disposition; numerical qualification is complete.
- Separate follow-up: worker import shim and Mac call-site integration, explicit mode selection, AEX/plugin boundary regressions. This library result alone authorizes no gate promotion.
