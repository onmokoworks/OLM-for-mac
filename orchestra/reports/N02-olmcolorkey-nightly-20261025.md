status: done
summary:
- Restored ColorKey HSV conversion's original unordered comparisons, operand selection, and subtraction semantics.
- Both nightly Smart mismatches are exact after the change; the saved realistic-v2 refusal was already exact at ticket entry.
- Preserved the R10 reference/fast split and prior ColorKey fixes; no other plugin or release-gate changes.
- Added all three nightly witnesses as a labelled corpus set recording both Classic and Smart.

facts:
- Starting commit: `f07f8230`; branch `orch/N02-olmcolorkey-nightly-20261025`.
- Original AEX SHA256: `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`.
- Final production source SHA256: `c201b47689e3932c6dc7d0890895a9a35d7fdea35ffa1df221fc7fe68043742f`.
- Replayed each original witness with `python3 tools/fuzz/run.py --plugin olmcolorkey --jobs 1 --geometry <sampler> --replay orchestra/reports/nightly-20261025/witnesses/<id>.json --scratch orchestra/state/N02-olmcolorkey-nightly-20261025/<id> --report orchestra/state/N02-olmcolorkey-nightly-20261025/<id>.json`. Sampler mapping: `c2d799e6b17314d055e78508=default`, `770c65ddec6545a6e10777aa=realistic`, `14824cffc4b7b148b8992684=realistic-v2`. Retained results: `N02-evidence/before-*.json`.
- Default mismatch reproduced: 6 words / 23 bytes; first word 53, AEX `4523c17f`, Mac `8d8c8c3e`. Realistic mismatch reproduced: 1 word / 1 byte; first word 8, AEX `0000003f`, Mac `00000000`.
- The realistic-v2 saved Mac error 516 **did not reproduce**: entry source already returned success and exact output SHA256 `c85dea12926680c2e69e8f28384f22f5792e2d5893adc6256aa54fe148a43f2a`. No refusal-specific patch was made.
- Initial standard replays exited 1 because the nightly files save only Smart and the standard replay adds Classic. The two Smart mismatch signatures themselves match the saved failures. These saved files were not rewritten.
- Actual PE disassembly at `0x180009e36/4e` uses COMISS/CMOVBE for green/blue selection; `0x180009e6d/75` uses MAXSS/MINSS with red as second operand; `0x180009e7c/83` uses UCOMISS/JNE for maximum/minimum equality, including unordered; `0x180009f08/18` uses UCOMISS/JE for zero saturation, including unordered. `0x180009e7f` is SUBSS. See `N02-evidence/hsv-disassembly.txt`.
- `hsv.py` executes the original leaf up to `0x180009eea` and compiles the extracted current conversion up to the same boundary. All 27 input triples (21 witness pixels plus six boundary probes) match max/delta/hue words exactly, including NaN signs: 81/81 words. The probe stops before fmod and does not substitute a math-library oracle. See `N02-evidence/hsv.json`.
- `verify.py corpus`: all 51 historical saved-route comparisons true (48 existing + 3 new). Separately recorded both routes for every case: Smart 51 exact; Classic 47 mismatches and 4 refusals. No historical saved expectation was changed. Full observations and worker bindings: `N02-evidence/corpus{,-summary}.json*`.
- Classic differences are already documented by the T14 orchestrator decision in `notes/KNOWN_ORIGINAL_BUGS.md`: original ColorKey Classic returns success without writing output, while ordinary AE selects SmartRender. No new undefined-memory claim is needed, and no Classic numerical repair is claimed.

- Final `verify.py campaign` (seeds 2026102601/2026102602/2026102603, n200 each): default 200/200/200 exact; realistic 190/188/176 exact and 10/12/24 original guard rejects; realistic-v2 200/200/200 exact. Default seed 1 n300: 300 exact, zero exact-to-non-exact regressions. Total: 2,054 exact, 46 original-unavailable, zero mismatches and zero Mac-only refusals. The final campaign was rerun after completing the SUBSS intermediate-sign restoration; its evidence is bound to the final source.
- `tools/perf/ref_vs_fast.py --plugin olmcolorkey --jobs 1` with ticket scratch: 225 frames (200 small, 20 HD, 5 UHD), caps 1/2/8, **675 exact**, zero refusals/mismatches. Retained `N02-evidence/perf-{summary,builds}.json` binds both builds to the final source.
- Final `verify.py witnesses` and `replay.py`: all three labelled standard replays return true (exit 0), Smart exact, with both routes recorded; final source hashes verified in witness/corpus/campaign provenance. `git diff --check` passed. Regenerable builds removed; no worker was rebuilt, no background process retained.

inference:
- Ordinary C++ min/max and equality did not preserve the SSE unordered branch decisions. NaN red now yields zero hue and saturation, with NaN value retained; the existing HSV component comparator then makes the original key-selection decision. This accounts for both final-output mismatch signatures without pixel-coordinate or expected-value patches.
- The observed refusal was resolved before this branch; the entry replay proves non-reproduction, but this ticket does not attribute it to an unmeasured earlier commit.
- Claims are limited to the measured CPU AEX/fake-SDK routes; no native AE result or wider compatibility claim is added.

changed_files:
- `mac/OLMColorKey/OLMColorKey.cpp`
- `tests/fuzz_corpus/olmcolorkey/N02-nightly-20261025/*.json` (3)
- `orchestra/reports/N02-evidence/`: reproducible verification scripts, original instruction dump, paired intermediates, replay/campaign/corpus/performance results and bindings.
- `orchestra/reports/N02-olmcolorkey-nightly-20261025.md`

verify:
Run serially from this worktree; logs and build products stay in the ticket scratch:
```sh
export TMPDIR="$PWD/orchestra/state/N02-olmcolorkey-nightly-20261025"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
mkdir -p "$TMPDIR"
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' orchestra/reports/N02-evidence/hsv.py > "$TMPDIR/hsv.log" 2>&1
python3 orchestra/reports/N02-evidence/replay.py > "$TMPDIR/replay.log" 2>&1
python3 orchestra/reports/N02-evidence/verify.py campaign > "$TMPDIR/campaign.log" 2>&1
python3 orchestra/reports/N02-evidence/verify.py corpus > "$TMPDIR/corpus.log" 2>&1
python3 tools/perf/ref_vs_fast.py --plugin olmcolorkey --jobs 1 --scratch "$TMPDIR/perf" > "$TMPDIR/perf.log" 2>&1
git diff --check
```
Expected: 27 exact intermediate pairs; three standard replays true with Smart exact and recorded Classic mismatches; campaign zero mismatches/Mac-only refusals; 51 historical corpus comparisons true; reference/fast clean.

next:
- No remaining N02 Smart numerical acceptance item. The non-reproducing refusal is explicitly reported above. Existing Classic behavior remains governed by the T14 decision; native AE checks remain outside this ticket.
