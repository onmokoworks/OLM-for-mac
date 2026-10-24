status: done
summary:
- Removed the Smart-only data-pointer alignment refusal; byte-safe callbacks and original ordinary-iterate mapping were already implemented.
- Required Smart campaigns: 1,000 exact, zero mismatches and zero Mac-only refusals; default both-route results unchanged.
- Existing 221 and new 200 corpus cases replay true, with both routes retained.
- Fixed candidate bundle host ordinary iterate; Universal ColorKeep bundle smoke 26 exact; host ASan/UBSan checks pass.
- Historical unit results unchanged: 57 tests, 13 failures, 24 errors, identical test identities.

facts:
- Branch `orch/P04d-colorkeep-cropped-checkout`. MAIN and AEXCompat source remained read-only. No oracle rebuild, release gate, ledger, or other plugin production edits.
- `memory_pressure`: initially 55% free, later 58%; host build manifest records its own measurement. Scratch remained below 40 MiB. All campaigns used jobs=1; at most two build/test processes ran concurrently.
- Baseline `run.py --plugin colorkeep --geometry realistic-v2 --seed 1 --n 100 --jobs 1 --shrink-attempts 0`: Smart 97 exact / 3 refusals, no byte mismatches. Index 29 PF16, 63 PF32 and 99 PF32 all refuse at `ColorKeepValidateWorldPair:world-alignment@219`. Their originals succeed. The ticket's suspected origin/size mapping refusal is actually a data-pointer alignment check.
- Index 29: sampled 11x21, pad3, checkout [4,3,8,14]; input displacement is 3*(11*8+3)+4*8 = 305 bytes, odd for PF16. Index 63: sampled 2x3, pad3, checkout [1,2,2,3]; displacement 86 bytes, 2 modulo 4. Index 99: sampled 1x127, pad7, checkout [0,27,1,116]; displacement 621 bytes, 1 modulo 4.
- Final output hashes for these three cases respectively: `23c08d8951ed0fa956de63ca0884d1ca86418ef90a596092c5adf2e9edbbb3cf`, `8dda477b553ca93c9ec9f6557ef950df56261b86bc9faae9d4753eca24843f89`, `e51d5e47d13c6113925d3b64cac09e8b6e6d43d22017715cf6c6ed6a0806ce4d`. Each matches the original raw output and rectangle exactly. No first differing byte exists for the final Smart runs.
- Original disassembly hash `9b8af3b010371ca654ca85b9b0fb8888c25946d0be6cce3cc50377c2a57e746d`; excerpts in `P04d-evidence/original-dispatch.txt`. PF16 at 0x1800010dc..0x180001106 passes output extent, original input world and output world to ordinary iterate. PF8 has the analogous dispatch; Smart PF32 at 0x180001ebd onward uses output extent bottom-top. No plugin origin-offset arithmetic or pointer-alignment test intervenes. This confirms P02a's existing mapping implementation rather than requiring a new renderer.
- Read-only F53 host source `~/.cache/olm-emu/src-F53/reference-guest/crates/aex-guest-worker/src/x64/iterate_and_suites.rs`, `emulate_iterate_common`: ordinary iterate uses local x/y and min(input/output dimensions), validates optional area, and passes same-coordinate byte offsets to callbacks. Origins are used only by the separate origin variant. This is the emulated host contract, not a claim about every native AE scheduler.

Campaigns (`python3 mac/ColorKeep/tests/verify_cropped_checkout.py`):

| Geometry | Seed | n | Smart exact / mismatch / refusal |
|---|---:|---:|---|
| default | 1 | 300 | 300 / 0 / 0 |
| realistic-v1 (`--geometry realistic`) | 1 | 100 | 100 / 0 / 0 |
| realistic-v1 | 20261025 | 100 | 100 / 0 / 0 |
| realistic-v2 | 1 | 100 | 100 / 0 / 0 |
| realistic-v2 | 20261025 | 100 | 100 / 0 / 0 |
| realistic-v1, odd-even-v1 | 2026 | 150 | 150 / 0 / 0 |
| realistic-v1, odd-even-v1 | 2027 | 150 | 150 / 0 / 0 |

- All final campaigns explicitly selected F53 worker hash `d88c22f67d06c419608d007619df42eac863a35e317ab7cb380617eff2051fb9`. Odd-even flags: `--size-sampler odd-even-v1 --max-size 1920 --size-max-height 1080`. Both routes were evaluated. Default before/after complete result objects match 300/300; Smart 300 exact, Classic 74 exact / 131 mismatch / 95 refusal. Zero exact-to-non-exact transitions. Classic differences remain outside the Smart contract.
- Standard `run.py --replay`: P02a 218/218, T15b 3/3, new P04d 200/200; all `replay_matches_saved: true`. T15b replay uses `--size-sampler odd-even-v1 --max-size 1920`; other sets retain default max-size 256. An initial attempt to apply 1920 to every set failed setup with “Replay requires the corpus --max-size”; corrected per-set flags passed. Search of plugin-tagged corpus JSON found no other ColorKeep sets.
- `unit_geometry.py before` and `final` via `OLM_COLORKEEP_TEST_SCRATCH`: identical per-file/test records, 57 run / 13 failures / 24 errors. Full logs and records retained. These historical failures include missing resources, stale source identities and old fixture contracts, as in P02a; they are not reported as a passing unit suite. Temporary worktree SDK links used by xcodebuild were removed before final unit measurement.
- Candidate bundle host formerly rejected any non-NULL iterate area. It now validates local bounds and supports differing world sizes, retaining byte-safe temporary pixels. Direct 3-depth checks cover different origins/sizes, nonzero area, empty/invalid area, NULL area, odd stride and unaligned bases; ASan+UBSan executable exits 0 (three expected invalid-area diagnostics, no sanitizer findings).
- Universal host cache `~/.cache/olm-emu/P04d-colorkeep-host/`; Universal ColorKeep bundle `~/.cache/olm-emu/P04d-colorkeep-bundle/ColorKeep.plugin`; both registered in INDEX.json. Build metadata/hashes copied into evidence. Bundle executable SHA256 `57121a8f22de4d0811700d3bf98d3481c56d0cc6845a95e55401fbc248bb864c`. No pre-existing registered binary was replaced.
- `smoke_cropped_bundle.py`: seed1 indices 0..9 plus 29/63/99, both realistic-v1 and v2, 26/26 Smart exact against F53. Test explicitly selects the new candidate host; shared adapters remain pinned to their historical hosts. No claim that the default F53 cached host was upgraded.
- `git diff --check` passed. Regenerable bundle build tree and sanitizer executable removed after measurement; logs/evidence retained. No task-owned background process left running.

inference:
- Cropping an odd-stride source shifts the data pointer off natural alignment; rejecting it before the existing memcpy-based callbacks caused the three Mac-only refusals. The Smart-only admission change fixes that cause without changing palette arithmetic or Classic guards.
- Ordinary iterate owns addressing. Adding layer-origin subtraction here would contradict original dispatch and P02a evidence. The measured finite cases establish CPU-emulated AEX agreement, not all-input or native-AE conformance.
- No distinct numerical hypothesis was refuted; the initial alignment hypothesis matched all three boundary witnesses.

changed_files:
- `mac/ColorKeep/ColorKeep.cpp`
- `mac/ColorKeep/tests/{unit_geometry,verify_cropped_checkout,save_cropped_corpus,replay_cropped_corpora,build_cropped_bundle_host,install_cropped_bundle,smoke_cropped_bundle}.py`
- `mac/ColorKeep/tests/iterate_host.cpp`
- `tools/emulation/aexcompat_patches/F47d-native-bridge.cpp` (ColorKeep iterate callback only; explicitly authorized host fix)
- `tests/fuzz_corpus/colorkeep/P04d-cropped-checkout/` (200 cases + README)
- `orchestra/reports/P04d-evidence/` and this report

verify:
Run from worktree, redirect long output to scratch:

```sh
export TMPDIR="$PWD/orchestra/state/P04d-colorkeep-cropped-checkout"
export OLM_COLORKEEP_TEST_SCRATCH="$TMPDIR" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$TMPDIR"
python3 mac/ColorKeep/tests/verify_cropped_checkout.py > "$TMPDIR/campaigns.log" 2>&1
python3 mac/ColorKeep/tests/replay_cropped_corpora.py > "$TMPDIR/replays.log" 2>&1
python3 mac/ColorKeep/tests/unit_geometry.py verify > "$TMPDIR/unit-verify.log" 2>&1
python3 mac/ColorKeep/tests/smoke_cropped_bundle.py > "$TMPDIR/bundle-smoke.log" 2>&1
clang++ -std=c++17 -O1 -g -fsanitize=address,undefined -Wno-pragma-pack -I'/Users/onmk/Documents/Projects/Personal/OLM as/Headers' -I'/Users/onmk/Documents/Projects/Personal/OLM as/Headers/SP' mac/ColorKeep/tests/iterate_host.cpp -o "$TMPDIR/iterate-host-test" > "$TMPDIR/iterate-host-build.log" 2>&1
"$TMPDIR/iterate-host-test" > "$TMPDIR/iterate-host-test.log" 2>&1
git diff --check
```

Expected: 1,000 Smart exact; all replay true (421 cases); historical unit identities unchanged; 26 bundle exact; sanitizer exit0 with three deliberately invalid-area diagnostics. Evidence JSON.gz contains full per-case hashes and original/candidate outcomes.

Optional candidate-only rebuild (not required to verify retained artifacts):

```sh
python3 mac/ColorKeep/tests/build_cropped_bundle_host.py > "$TMPDIR/build-host.log" 2>&1
python3 tools/fuzz/build_F47_bundles.py --plugins ColorKeep --scratch "$TMPDIR/bundle-build" > "$TMPDIR/build-bundle.log" 2>&1
python3 mac/ColorKeep/tests/install_cropped_bundle.py > "$TMPDIR/install-bundle.log" 2>&1
```

The standard bundle builder creates worktree SDK symlinks if missing; remove only newly created links before comparing historical unit results. Delete disposable `bundle-build` after installation. Durable registered host/bundle remain in cache. Corpus generation is reproducible using `save_cropped_corpus.py` after campaigns.

next:
- Orchestrator review and merge. A separate host-cache promotion may update default bundle adapters to a newly qualified host; this ticket's smoke selects its isolated host explicitly.
- Native AE cropped-checkout validation and historical unit/resource repairs remain separate work. Classic mismatches are not promoted or hidden.
