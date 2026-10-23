status: blocked

summary:
- Removed ColorKeep's redundant DEEP-flag admission test; existing pixel-format-suite checks establish the world types and SmartRender retains requested-bitdepth dispatch.
- Source seed 1/n300: Smart 300/300 exact; all result dictionaries unchanged from F19.
- Independent input/output DEEP/WRITEABLE combinations: 48/48 Smart AEX exact; F19 corpora replay 300/300 and 100/100 unchanged.
- Universal Release bundle builds, but its required n100 render verification is blocked by the missing retained F47d worker. No emulator rebuild was attempted.

facts:
- Read AGENT_GUIDE, GOTCHAS, compatibility plan and targeted ColorKeep ledger rows. No release gate, ledger, other plugin or MAIN file was changed.
- Original decomp (MAIN `decomp/ColorKeep.aex.c.txt`): `FUN_180001ca0` at 0x180001ca0 reads the short at SmartRender input +0x2c, dispatches 8/16/32, and uses iterateFloat for 32. It does not test world flags, query pixel format, or infer depth from rowbytes/width. Classic EffectMain case 0xb tests output world +0x10 bit 0, dispatching iterate8/iterate16. These are distinct original contracts; no original float DEEP restriction was found.
- SDK 25.2 `Headers/AE_Effect.h:484,500` defines DEEP as bit 0 and PF_WORLD_IS_DEEP as a bit test. `Headers/AE_EffectCBSuites.h:428-451` supplies WorldSuite2 / PF_GetPixelFormat. [SDK world documentation](https://ae-plugins.docsforadobe.dev/effect-basics/PF_EffectWorld/) describes DEEP for 16-bpc; [format documentation](https://ae-plugins.docsforadobe.dev/effect-details/image-buffer-management-functions/) identifies ARGB32/64/128 as 8/16/32-float. Neither establishes an exclusive DEEP-clear requirement on float worlds. Actual native AE PF32 flag bits remain unconfirmed: no native AE capture was run.
- Other ports inspected: OLMBlur.cpp:1497, OLMKiraKira.cpp:2666, OLMSmoother2_port.cpp:4971 expect DEEP for both high depths; their format queries distinguish the actual types. This is port/host evidence, not proof of native AE flags.
- ColorKeep already queries both input and output via WorldSuite2: Classic verifies matching supported formats; Smart verifies each against requested bitdepth. Removed only the additional shared flag test, retaining bounds/stride/alignment/overlap/type checks and all pixel arithmetic. Default source harness is unchanged. The new regression harness varies input/output flags independently without modifying the bridge or AEX.
- Commands in verify below were run with one job. Source campaign exit 0: Smart 300 exact, zero Smart mismatches/refusals; Classic 74 exact, 131 mismatches, 95 refusals (existing). F19 `check()` reports 300/300 complete dictionaries identical. First existing Classic mismatch seed 1/index 0, PF8, byte 8: expected 00, actual ff; 191 different bytes. First Smart mismatch: none.
- Flag matrix exit 0: three generated depths, each with input flags 0..3 and output flags 0..3, 48/48 exact. Full and shrunk F19 replays exit 0: 300/300 and 100/100 matches_saved. Tracked `tests/fuzz_corpus/colorkeep` has only README; the test reconstructs actual retained cases from committed F19 evidence instead of treating an empty corpus as a pass.
- Universal Release ColorKeep build exit 0, `x86_64 arm64`, one Xcode job. Bundle executable SHA256: c9883667820758c59cf3d1301391d38ed0849dd314614d34448ba4391b601e5f. Source SHA256: 5a8502ad3cd11a78f16cd800736fb53ac43c6c4abf2eacdebb192f3a1924e284.
- Source/corpus oracle: cached F46 worker SHA256 6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903. Full source provenance, flag results, replay counts and decomp/bundle hashes are retained in the adjacent JSON.
- `verify_F47d.py --plugins colorkeep --candidates plugin-bundle` with the reported F47d worker path prints `colorkeep-plugin-bundle 2 None None`: child run.py rejects the absent executable before rendering. Wrapper exit 0 is not a verification pass. Cache INDEX lists F47 load-only, not F47d; searches of cache, MAIN orchestra, worktrees and Personal project F47d paths found no retained F47d executable. Its reported MAIN `orchestra/state/F47d-native-plugin-all/checked/aex-guest-worker` is absent. User was asked for its location; rebuilding is forbidden by this ticket brief.
- Initial use of F19's CLI snapshot with R02 scratch hit its ticket-specific path assertion; the R02 script calls the existing snapshot function directly with R02-local destinations. The subsequent replays above passed.
- Existing callback, generic-world and ROI checks: 6 tests passed (4.494 seconds). `git diff --check` passed. Regenerable Xcode products and flag-test object/library/executable files were deleted after recording hashes; logs and reports remain. No background process remains.

inference:
- The extra flag equality caused F47d's PF32 refusals; removing it agrees with original Smart dispatch and the existing SDK format checks. The 48 flag tests establish that this candidate's output is independent of these flag combinations for the tested inputs.
- A built bundle and source-host success do not establish the required F47d bundle 100/100 result. Native AE's actual PF32 flags also cannot be inferred from AEXCompat's chosen bits.

changed_files:
- mac/ColorKeep/ColorKeep.cpp
- tools/fuzz/verify_colorkeep_R02.py
- orchestra/reports/R02-colorkeep-pf32-world-flags.md
- orchestra/reports/R02-colorkeep-pf32-world-flags.json

verify:
```sh
s="$PWD/orchestra/state/R02-colorkeep-pf32-world-flags"
w=/Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
unset OLM_COLOR_TRIAGE_BYPASS OLM_COLOR_TRIAGE_HOST_FLAGS OLM_COLOR_TRIAGE_SANITIZE
python3 tools/fuzz/run.py --plugin colorkeep --seed 1 --n 300 --jobs 1 \
  --worker "$w" --scratch "$s/source" --report "$s/source.json" \
  --corpus "$s/source-corpus" --shrink-attempts 0 --shrink-seconds 0 > "$s/source.log" 2>&1
PYTHONPATH=tools/fuzz python3 -c 'from pathlib import Path; from verify_colorkeep_F19 import check,read; check(read(Path("orchestra/state/R02-colorkeep-pf32-world-flags/source.json")),read(Path("reports/fuzz/colorkeep_F19.json")))'
# Expected: Smart 300 exact; complete result dictionaries 300/300 match F19.
python3 tools/fuzz/verify_colorkeep_R02.py --scratch "$s/flags" --worker "$w" > "$s/flags.log" 2>&1
# Expected: 48/48 Smart flag combinations exact; reconstructs both corpora.
for phase in after shrunk; do
  python3 tools/fuzz/run.py --plugin colorkeep --replay "$s/flags/corpus-$phase" \
    --jobs 1 --worker "$w" --scratch "$s/replay-$phase" \
    --report "$s/replay-$phase.json" --corpus "$s/disposable" > "$s/replay-$phase.log" 2>&1
done
# Expected: replay_complete, 300/300 and 100/100 matches_saved.
PYTHONPATH=tools/fuzz python3 -c 'from verify_colorkeep_F19 import tests; tests()' > "$s/tests.log" 2>&1
python3 tools/fuzz/build_F47_bundles.py --plugins ColorKeep --scratch "$s/bundles" > "$s/build.log" 2>&1
# Expected: ColorKeep x86_64 arm64.
python3 tools/fuzz/verify_F47d.py --plugins colorkeep --candidates plugin-bundle \
  --state "$s" --worker '/Users/onmk/Documents/Projects/Personal/OLM as/orchestra/state/F47d-native-plugin-all/checked/aex-guest-worker' > "$s/bundle-verify.log" 2>&1
# Currently blocked: child exit 2, missing worker. Once a retained F47d worker is
# supplied, substitute its absolute path and require 100/100 Smart AEX exact.
git diff --check
```

next:
- Restore/provide the retained F47d native-render worker and run the bundle command above. Do not substitute cached F47 (load-only) or claim 100/100 before execution.
- Native AE PF32 flag capture, if required as a runtime fact, needs a separate host observation; the fix does not depend on either bit convention.
