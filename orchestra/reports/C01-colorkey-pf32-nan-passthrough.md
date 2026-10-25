status: done
summary:
- Restored the AEX's unordered-accepting Lab76/Lab94 component predicates.
- Restored positive PF32 Thin's unordered-alpha copy branch exposed by the unreduced witness.
- Preserved R10 reference/fast dispatch; changed only ColorKey production source.
- Added four labelled corpus cases: N01's reduced witness and all three original mismatches.

facts:
- Baseline commit: `6a6074aa620ade3813ee4f6b181a8a5e58b9526a`. Original AEX SHA256: `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`.
- Initial command: `python3 tools/fuzz/run.py --plugin olmcolorkey --replay orchestra/reports/N01-evidence/witnesses --jobs 1 --scratch orchestra/state/C01-colorkey-pf32-nan-passthrough/replay --report orchestra/state/C01-colorkey-pf32-nan-passthrough/before.json`. Smart reproduced 3 different words / 12 bytes, first word 25, expected `b7b6b63e`, actual `4523c17f`. Generic replay added a Classic observation, so its saved-result comparison returned false; subsequent checks explicitly preserve historical route sets.
- `python3 orchestra/reports/C01-evidence/verify.py scan`: examined all 144 PF32 Lab component cases in N01's 18,377 observed indices plus the reduced witness. Baseline: 141 exact, 4 mismatches (three unreduced plus reduced). Recovered sibling indices 3790 and 5995. This scan's after-results are the intermediate comparator-only patch, not the final Thin patch: 2081 improved from 48 differing words to 18, first remaining word 205 expected `9f87573f`, actual `b7b6b63e`; its source alpha is NaN. Other three became exact.
- Static command in verify below: `COMISS + JA` at Lab76 `0x180004476/488/49a` and Lab94 `0x1800045c7/5e1/5f3` rejects only ordered-greater differences. Scalar comparators use `SETAE` with reversed operands and still reject unordered. Positive PF32 Thin uses `UCOMISS + JNE` at `0x180009b9c/9f`, then distance `COMISS + JB` and source RGBA copy at `0x180009bc7..9c11`. No CVTTSS2SI conversion or min/max selects the replacement on this witness path.
- `python3 orchestra/reports/C01-evidence/verify.py witnesses`: final 4/4 Smart exact. Reduced output SHA256 `8fe301e23bc89a0df5dc21c66a74f0225723d26ff5a2129517d27ba55940061d` equals AEX. Full raw hashes for all witnesses are in `C01-evidence/witnesses-summary.json`.
- `python3 orchestra/reports/C01-evidence/verify.py campaign`: PF32-only nonfinite-heavy default + realistic-v1, seeds 1/2026/2027, 100 cases per cell. Default: 300/300 exact. Realistic-v1: 94/91/96 exact, respectively; 6/9/4 AEX output-guard rejects (uncompared). Total 581 exact, 19 uncompared, 0 mismatches, 0 Mac refusals. Each pixel has one deterministically chosen nonfinite alpha/R/G/B word; source includes positive/negative qNaNs, sNaN and both infinities. Original generator controls and geometry remain intact.
- `python3 orchestra/reports/C01-evidence/verify.py default`: default seed 1 n300, baseline and final Smart: 300 exact -> exact, zero regressions.
- `python3 orchestra/reports/C01-evidence/verify.py corpus`: all 48 ColorKey corpus files (44 existing + 4 new), hash-validated historical workers and historical route sets: 48 `True`, zero changes.
- `tools/perf/ref_vs_fast.py --plugin olmcolorkey --jobs 1` with ticket scratch: 225 frames (200 small, 20 HD, 5 UHD), three parallel caps per frame: 675 exact comparisons, 0 refusals, 0 mismatches. Final source binding is recorded in `C01-evidence/perf-builds.json`.
- `git diff --check` passed. Regenerable scratch builds were removed; no reference worker was rebuilt or installed.
- Final source SHA256: `6e8bfc33449fdbcb493602f347d53456efeb658f8eeb7c1245d3e57c45c7821f`.

inference:
- NaN RGB produces unordered Lab differences. The former C++ `<=` rejected them, retaining source NaN; original component predicates accept them and select finite replacement RGB.
- Premultiplication by NaN alpha exposes the same match in unreduced 2081. Later positive Thin treats its NaN matte as zero and restores source RGBA; testing the boolean match flag previously suppressed this copy. Reusing the already-established distance mask reproduces the original branch generally.
- No hypotheses were refuted; the second boundary was observed at NaN alpha after the first fix. No tolerance, coordinate exceptions or expected-byte adjustment was used.
- Evidence is original CPU AEX under retained Unicorn workers and Mac SDK harnesses, not a new native AE claim. The 19 realistic guard rejects supply no numerical oracle and are not counted exact.

changed_files:
- mac/OLMColorKey/OLMColorKey.cpp
- tests/fuzz_corpus/olmcolorkey/C01-pf32-nan/ (README and four witnesses)
- orchestra/reports/C01-evidence/ (serial verification script, static decoder, raw measurement reports and summaries)
- orchestra/reports/C01-colorkey-pf32-nan-passthrough.md

verify:
Run from the ticket worktree, serially, with `PYTHONDONTWRITEBYTECODE=1`:
- `python3 orchestra/reports/C01-evidence/verify.py witnesses`: 4 exact; refreshes only this ticket's labelled corpus results.
- `python3 orchestra/reports/C01-evidence/verify.py campaign`: counts listed above; no mismatch/refusal. Scratch and TMPDIR are confined to this ticket by the script.
- `python3 orchestra/reports/C01-evidence/verify.py default`: 300 exact -> exact; baseline source is pinned to the commit above.
- `python3 orchestra/reports/C01-evidence/verify.py corpus`: `{'True': 48}`; exit 0. Preserves original Classic/Smart route sets rather than adding observations to Smart-only corpus entries.
- `TMPDIR="$PWD/orchestra/state/C01-colorkey-pf32-nan-passthrough" python3 tools/perf/ref_vs_fast.py --plugin olmcolorkey --jobs 1 --scratch orchestra/state/C01-colorkey-pf32-nan-passthrough/perf`: no mismatches.
- `'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' orchestra/reports/C01-evidence/static.py`: reproduces committed original instruction listing.
- `git diff --check`: clean.

next:
- Separately investigate the 19 realistic-v1 AEX output-guard rejects if numerical coverage of those geometries is required; no worker changes belong to C01.
