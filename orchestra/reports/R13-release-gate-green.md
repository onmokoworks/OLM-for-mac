status: partial
summary:
- Both KiraKira tests bisect to b49bb48d (P02c); repaired stale request/preserve-RGB expectations without production changes.
- Corpus replay groups by all five saved configuration fields, including mixed directories and retry invocations.
- Refreshed the SDK native iterate bridge into new R13 cache entries; old workers remain unchanged.
- ColorKey probe derives its struct from the production header and checks the distinct Classic/Smart coordinate contracts.
- Complete gate and R12-recipe package audit are running; no release authorization or publication.

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
54 matrix rows exit 0 (before adding both preserve flag values, which the complete
gate will recheck); native-smoke six tests PASS; release decision tests six PASS.
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
R13's actual ColorKeep comparison counts will be reported independently below.

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

Expected decision tests: six PASS. Full gate result pending.

next:
- Finish the full gate, archive exact outcomes and audit/register the unpublished R13 ZIP.
