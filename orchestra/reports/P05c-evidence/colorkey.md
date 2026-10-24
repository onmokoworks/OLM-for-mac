status: partial
summary:
- Lazily cache each enabled key's unmutated Lab triple within RenderTyped; copy it before each ordered comparator mutation.
- UCRT, Lab conversion arithmetic, per-pixel cmp mutation, and key traversal order are unchanged.
- Heavy corpus05 improved from 1.85–1.87 to 0.84–0.86 s at 1080p and 7.41–7.61 to 3.57–3.73 s at 4K.
- Contract Smart: 766 exact / 34 original-AEX rejects across 800 generated cases; 0 mismatches / 0 Mac-only refusals. All 44 corpora replay true.
- Full post-change unit suites are still running; no final acceptance claim yet.

facts:

| Depth | Before 1080p | After 1080p | Before 4K | After 4K |
|---|---:|---:|---:|---:|
| PF8 | 1.851300 | 0.853339 | 7.412181 | 3.726432 |
| PF16 | 1.861862 | 0.843513 | 7.603104 | 3.697015 |
| PF32 | 1.865819 | 0.860443 | 7.613296 | 3.566349 |

- Fresh Universal Release builds succeeded. P00b `ae_realism_audit.py` with `--plugins olmcolorkey --cases corpus05 --situations full 4k --jobs 1`: before/after both 6 OK. Shared-machine, single render-selector observations in the SDK host; not native AE timings.
- `sample PID 2 1 -file PATH` on PF32 4K: before/after sample and host return 0. Top-of-stack sample counts: powf 881→231, RGBToPluginLab76 261→33, atan2f 210→700. These are sampled counts, not call counts; atan2f now dominates the remaining work.
- Default seed 1 n300: Smart 300 exact before and after; all 600 paired Classic/Smart output hashes are unchanged. Classic already had 300 mismatches before: first case index 0, byte/word 1, expected `00`, actual `93`, 1461 differing bytes. This ticket does not promote Classic to exact.
- Final realistic-v1 n100: seed 1 = 91 exact / 9 original-AEX rejects; fresh seed 2026102505 = 90 exact / 10 rejects. Final odd-even-v1 n150, max width 1920 / height 1080: seed 2026 = 142 exact / 8 rejects; seed 2027 = 143 exact / 7 rejects. All contract-route mismatches and Mac-only refusals are zero. The prior date-seed 20261024 run (89 exact / 11 rejects) is retained as an additional 100-case check; it is not counted as the fresh seed. Uncompared cases are not counted as exact. Example original rejection: realistic seed 1 index 12, original worker reports corrupted output pixel guard after negotiated rectangle [1,0,2,1]; candidate returns 0.
- Standard both-route corpus replay: root 9, P02i-realistic 8, T15b 3, new P05c-lab-key-cache 24; all `replay_matches_saved=true` (44 total). New actual-AEX witnesses cover PF8/PF16/PF32, Lab76/Lab94, component/scalar predicates, 2/25 keys, disabled keys and repeated palette pixels.
- Pre-change unittest modules: 30 run / 21 nonzero returns. Pre-change module-level function suites: 8 run / 3 nonzero returns. Full logs retained. This includes successful O2/sanitizer owner, Lab94, Lab-boundary, typed-control and YUV replay tests; historical evidence/asset failures remain visible.
- A verification script initially required every realistic case to be oracle-comparable and stopped at the 9 AEX rejects. Its assertion was corrected to the requested contract (0 mismatches / 0 Mac-only refusals, with original rejects separately counted). The interrupted post-change unit process and its child were terminated and the suite restarted; no partial run is claimed as a completed test suite.
- Registered generated bundles: `~/.cache/olm-emu/P05c-key-before` and `~/.cache/olm-emu/P05c-key`; SHA-256 identities are in `key-cache.json`. No original AEX, UCRT implementation, oracle worker, release gate, ledger, MAIN or emulator source was modified.

inference:
- Repeated key Lab conversion was the removable invariant. The first visit uses the same in-place conversion; subsequent visits copy its exact stored bytes. Caching precedes Lab76ComparatorMutate so its effects on both key and cmp still occur at each comparison.
- The 34 AEX rejects limit evidence coverage; they are not a refusal budget and no Mac admission rule changed.

changed_files:
- mac/OLMColorKey/OLMColorKey.cpp
- tests/fuzz_corpus/olmcolorkey/P05c-lab-key-cache/*.json
- orchestra/reports/P05c-evidence/check_plugin.py, key_witnesses.py, profile_plugin.py, retain_plugin.py, units.py
- orchestra/reports/P05c-evidence/key-* and colorkey.md
- orchestra/reports/P05c-blur-colorkey-smoother-performance.md

verify:
```sh
python3 orchestra/reports/P05c-evidence/check_plugin.py olmcolorkey key-recheck
python3 orchestra/reports/P05c-evidence/units.py olmcolorkey key-units-recheck
python3 orchestra/reports/P05c-evidence/functions.py olmcolorkey key-functions-recheck
python3 tools/fuzz/ae_realism_audit.py --phase matrix --cache "$HOME/.cache/olm-emu/P05c-key" --state orchestra/state/P05c-blur-colorkey-smoother-performance/key-performance-recheck --plugins olmcolorkey --cases corpus05 --situations full 4k --jobs 1
```
Expected campaign/replay counts above, six OK timing rows. Historical unittest failures are not represented as a green suite. Do not run more than two build/emulator processes concurrently.

next:
- Finish and compare post-change unittest and function suites, then complete this per-plugin report and proceed to Smoother.
