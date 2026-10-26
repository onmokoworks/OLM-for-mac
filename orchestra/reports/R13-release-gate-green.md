status: done
summary:
- Complete release gate: 7/7 PASS, local_gate_pass=true; 2,998/2,998 corpus replays and 45/45 selected test files pass.
- Both KiraKira failures bisect to P02c; fixed AEX-grounded stale host contracts and ColorKey's stale struct/ROI expectations, with no production changes.
- Refreshed native iterate hosts: ColorKeep 100/100 original comparisons exact and 521/521 architecture pairs render equally.
- Fresh seeds: 6,000 complete, 5,694 exact / 0 mismatch / 250 refusal / 56 uncompared / 0 errors under unchanged predicates.
- R13 ZIP rebuilt, audited, separately bundle-compared and registered in the cache; nothing published.

facts:

## Bisect and test contract

Independent commands (TMPDIR was the R13 scratch `tmp` directory):

```sh
git bisect start 853db347 fa1af7d2
git bisect run sh -c 'rev=$(git rev-parse --short HEAD); python3 -B tests/test_olmkirakira_generic_beta_sanitizers_20260820.py > orchestra/state/R13-release-gate-green/bisect-san-$rev.log 2>&1; rc=$?; echo "$rev exit=$rc"; exit "$rc"'
git bisect reset
git bisect start 853db347 d13ff809
git bisect run sh -c 'rev=$(git rev-parse --short HEAD); python3 -B tests/test_olmkirakira_native_smoke_tuple_20260820.py > orchestra/state/R13-release-gate-green/bisect-native-$rev.log 2>&1; rc=$?; echo "$rev exit=$rc"; exit "$rc"'
git bisect reset
```

Both identify **b49bb48db89ef968dfe96b96f5b59d9238c486c7**. Both tested
`5a367085` successfully. Its KiraKira production tree, both Python tests, generic
C++ harness and included bounded C++ harness have identical Git blob identities
to the first bad commit's parent `5bb59841` (retained `history-blobs.json`).
Complete bisect commands, exits and test output are in `bisect-results.json.gz`.
The branch was restored after each bisect.

P02c's retained original-AEX evidence (`P02c-kirakira-geometry.md`) identifies
`181151710..1811517cc` as forwarding the incoming request without forcing
preserve-RGB, and `181234f10` as unioning checkout bounds. The old synthetic
host required a full-frame request and the old test required forced preserve-RGB.
The repaired callback checks the complete forwarded request byte-for-byte.
The matrix checks both preserve-RGB values, and retains render success,
Classic/Smart/repeat active-byte equality, independent strides, immutable headers
and source bytes, padding, parameter ordering, checkins and handle cleanup.
Partial/downsample pre-render tests now assert successful forwarding and exact
checkout-bound output rectangles and release the returned pre-render data.
The native diagnostic assertion uses the current explicit checkout-result log.

Measured standalone results: ColorKey ROI entrypoint exit 0; KiraKira sanitizer
54 matrix rows exit 0; the complete gate also passed after adding both
preserve flag values; native-smoke six tests PASS; release decision tests six PASS.
The sixth decision test exercises a mixed-configuration directory and both
120-second retry invocations, checking preserved witness identities and flags.

ColorKey's private struct lacked P01c's distance fields. It now extracts the
production `OLMColorKeyInfo` declaration, rather than maintaining another copy.
After compilation was repaired, the old Smart/Classic ROI equality assertion
also failed. This separate expectation became stale at P02i (`122c97ac`),
whose retained AEX disassembly and measurements are in
`P02i-colorkey-geometry.md` (91/100 and 89/100 Smart exact, with only original
guard-corruption refusals unavailable; Classic unchanged). The original Smart workers `0x9000/0x94b0/0x9960` read the local
input prefix (documented in production `Render.inc`), whereas Classic retains
origin mapping. The repaired test compares every active byte against its
route-specific full-frame region and retains every padding/admission assertion.

## Host and replay changes

Replay passes saved `max_size`, `size_sampler`, `size_max_height`,
`geometry_sampler` and `color_sampler`; `realistic-v1` maps to the CLI's
`--geometry realistic`. Groups are symlink views of unchanged witnesses.
Worker SHA checks, exact saved-result comparison and persistent-stop predicates
are unchanged. Retries receive the same configuration as their group.

The native bridge already had iterate source code, but pinned F47d/F51 binaries
predated the needed implementation. The refreshed bridge also adopts the existing
P00 SDK host's rectangle clipping to both worlds, with independent byte strides
and callback-error propagation. Existing color, parameter and world callbacks
cover the sibling calls. `test_P00b_iterate.cpp` now also compiles against this
bridge; its clipping/untouched-destination assertions passed.

New registered cache entries:
- `worker-R13-bundle/aex-guest-worker`: SHA-256 `1695ef9fab31b607bb240079e41dd3a9c28bccf90f5e9a879a7e85ed8000bc3e`.
- `worker-R13-universal/plugin-host`: see retained build manifest (both architectures).

Build manifests and commands are retained. The first worker build compiled but
failed copying its result because the build directory variable was shadowed by
the `build.rs` path. The corrected existing recipe completed and cleaned its
no-space source/Cargo build directories. No original emulator checkout was edited.

The F47d predicate permits a complete campaign containing only refusals. R12's
100 ColorKeep refusals therefore passed that predicate: **this is a weakness**,
not evidence of exact bundle rendering. No refusal-tolerant predicate was loosened.
R13 independently measured 100/100 ColorKeep exact cases in F47d and
521/521 equal renders in F51 (zero refusals, uncompared cases or host errors).


## Complete release gate

Exit **0**:

```sh
python3 -B scripts/run_olm_release_gate_v2.py \
  --state orchestra/state/R13-release-gate-green/complete --jobs 1 \
  > orchestra/state/R13-release-gate-green/complete.log 2>&1
```

`local_gate_pass=true`, **7/7 PASS**, `release_authorized=false`.

| Stage | Result | Actual result |
| --- | --- | --- |
| Framework | PASS | 50 tests run, 3 skipped |
| Universal build | PASS | 10 bundles, arm64 + x86_64 |
| Corpus | PASS | 2,998 PASS / 0 FAIL / 0 ORACLE-STOP |
| Fresh seeds | PASS | 6,000 complete; E=5,694 / M=0 / R=250 / U=56 / errors=0 |
| Bundle checks | PASS | F47d E=941 / M=0 / R=46 / U=13 / errors=0; F51 3,870 equal renders + 128 equal refusals, 0 differences |
| Selected plugin tests | PASS | 45/45 files, including all three repaired failures |
| Static | PASS | All 10 Release settings and PiPL predicates pass |

The 134 missing-configuration failures are resolved without changing any corpus
record or saved-result predicate. All 521 ColorKeep architecture comparisons now
render equally instead of returning host errors. F47d ColorKeep is 100 exact /
0 refusal / 0 uncompared. There is no first differing byte in these comparisons.
Non-owner Classic diagnostics remain in the fresh reports and are not promoted.
56 uncompared cases remain uncompared; the gate's existing owner and refusal /
oracle-unavailability policies are unchanged. Timing-sensitive counts can vary.

The run began at `1750eac1`; later commits changed the worker build recipe and
reports only. All 45 selected test hashes and the gate script hash match the
completed run (`run-head-binding.json`). Production files are unchanged.
`R13-evidence/gate-evidence.tar.gz` preserves **244 reports/logs**, including every
F51 row; the archive manifest records its hash and contents.

## Unpublished package and its actual binaries

R12 recipe (exit 0), then audit (exit 0):

```sh
OLM_PACKAGE_STATE="$PWD/orchestra/state/R13-release-gate-green/package" \
OLM_RELEASE_CACHE="$HOME/.cache/olm-emu/release-R13" \
bash orchestra/reports/R12-evidence/build.sh > orchestra/state/R13-release-gate-green/package-build.log 2>&1
python3 orchestra/reports/R12-evidence/verify.py "$HOME/.cache/olm-emu/release-R13/OLM_Mac_Plugins_Release_20261026.zip" orchestra/state/R13-release-gate-green/package-audit
```

ZIP SHA-256: **`a568e7640e84a6c4d26f788f4bc4e865f411437a70ca0868515d89f2665d5852`**.
Source commit `cb801c68895e4259a1b908b4ddbeee83b1dea689`, `git_dirty=false`.
Audit: 132 entries, ten Universal/ad-hoc bundles, both slices minimum macOS 11.0,
76 text files and six nested ZIPs checked, no local paths, required docs and
relative links present, executable hashes equal the package manifest.

The retained R12 packaging recipe uses the Debug Xcode configuration with O3
and writes Release products; the main gate builds the actual Release/O2
configuration. All ten executable hashes differ. To avoid equating those builds,
the **actual package products** also ran the unchanged Gate.bundles method in
`orchestra/state/R13-release-gate-green/package-comparisons`. Its bundle tree
links to `package/products/<plugin>/<plugin>.plugin`, the files audited in the
ZIP. This extra stage passed:

- F47d: 941 exact / 0 mismatch / 46 refusal / 13 uncompared / 0 errors, 1,000 cases.
- ColorKeep: 100/100 exact, no refusal or uncompared case.
- F51: 3,870 equal renders + 128 equal refusals, zero differences, 3,998 pairs.
- Per-case results, hashes and commands: `R13-evidence/package-comparisons/`.

`run-head-binding.json` records that production files are unchanged from both
the main gate's starting commit and the package source commit. The gate script
hash still matches the running gate. This is an explicit binding across later
recipe/report-only commits, not a replacement of the recorded starting commit.


inference:
- The bisected KiraKira failures are stale synthetic-host expectations after an
  AEX-grounded request contract correction, not evidence of a pixel regression.
- No production plugin change was needed; the conditional G1 production-change
  campaign does not apply. `git diff 44fd470b -- mac` is empty.

changed_files:
- `scripts/run_olm_release_gate_v2.py`
- `tests/test_release_gate_v2.py`
- `tests/test_olmcolorkey_generic_roi_tile.py`
- `tests/olmkirakira_generic_beta_sanitizer_harness.cpp`
- `tests/test_olmkirakira_native_smoke_tuple_20260820.py`
- `tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py`
- `tools/emulation/aexcompat_patches/F47d-native-bridge.cpp`
- `tools/emulation/aexcompat_patches/F47d-native-host.md`
- `tools/emulation/aexcompat_patches/build_F47d.py`
- `tools/emulation/aexcompat_patches/build_F51.py`
- `tools/fuzz/verify_F51.py`
- `tools/fuzz/test_P00b_iterate.cpp`
- `orchestra/reports/R12-evidence/{build.sh,verify.py,archive_gate.py}` (output-path options; existing recipes reused)
- `orchestra/reports/R13-release-gate-green.md`, `orchestra/reports/R13-evidence/*`

verify:

```sh
scripts/setup_ae_sdk_links.sh
export TMPDIR="$PWD/orchestra/state/R13-release-gate-green/recheck-tmp"
mkdir -p "$TMPDIR"
export OLM_TEST_JOBS=1
python3 -B tests/test_release_gate_v2.py
python3 -B scripts/run_olm_release_gate_v2.py --state orchestra/state/R13-release-gate-green/recheck --jobs 1 > "$TMPDIR/gate.log" 2>&1
```

Expected: six decision tests PASS; full gate exits 0 with seven PASS stages,
`local_gate_pass=true`. Use a fresh state directory. Counts of unavailable oracle
runs can vary with shared-machine load; they never count as exact.

Audit the durable ZIP (expected exit 0 and the SHA-256 above):

```sh
python3 orchestra/reports/R12-evidence/verify.py "$HOME/.cache/olm-emu/release-R13/OLM_Mac_Plugins_Release_20261026.zip" "$TMPDIR/package-audit"
git diff --exit-code 44fd470b -- mac core ucrtmath
git diff --check
```

The exact host build commands used were:

```sh
python3 -B tools/emulation/aexcompat_patches/build_F51.py --state orchestra/state/R13-release-gate-green/host --cache-name worker-R13-universal
python3 -B tools/emulation/aexcompat_patches/build_F47d.py --state orchestra/state/R13-release-gate-green/worker --cache-name worker-R13-bundle --build-root "$HOME/Documents/Projects/Personal/04_Tools/AEXCompat-build-R13"
clang++ -std=c++17 -O2 -Wno-pragma-pack -DTEST_F47D_HOST -IHeaders -IHeaders/SP tools/fuzz/test_P00b_iterate.cpp -o "$TMPDIR/test-iterate"
"$TMPDIR/test-iterate"
```

Expected compile/regression exits: 0. The registered workers are already present;
use a **new** cache name and empty no-space source directory for an independent
rebuild rather than overwriting the retained identities. The gate uses the R13
registered paths; both build manifests are retained. The first build's copy-path
failure and the successful retry are disclosed above.

For package comparison reproduction, rebuild with the package command above,
then use a fresh state (same existing gate method used for the measured run):

```sh
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python3' -B - <<'CHECK'
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('gate', 'scripts/run_olm_release_gate_v2.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
s = m.ROOT/'orchestra/state/R13-release-gate-green/package-recheck'
s.mkdir()
for name in m.PLUGINS.values():
    p = s/'bundles/xcode'/name/'products'; p.mkdir(parents=True)
    (p/(name+'.plugin')).symlink_to(m.ROOT/'orchestra/state/R13-release-gate-green/package/products'/name/(name+'.plugin'), target_is_directory=True)
g = m.Gate(s, m.MAIN/'tools/emulation/.venv/bin/python3', 1)
g.stage('bundle-checks', g.bundles)
raise SystemExit(g.summary['stages'][0]['status'] != 'PASS')
CHECK
```

Exact launched F47d/F51 commands and all outputs are also retained in
`package-comparisons/gate-results.json` and its archive. Expected: exit 0,
zero differences; ColorKeep 100 exact and 521 equal renders. The regular full
gate command alone does not test the O3 package executables.

next:
- Ticket-local work is complete. Native AE / Windows-host / installed-identity
  obligations remain outside this local gate; no release authorization is inferred.
- Registered `release-R13` in `~/.cache/olm-emu/INDEX.json` with `published=false`,
  `local_gate_pass=true`, `release_authorized=false`; retained registration is
  `R13-evidence/cache-registration.json`.
- Regenerable build trees and scratch executables were removed after evidence
  retention. No started background process remains. Nothing was pushed, installed,
  published, or written into MAIN.
