status: done

summary:
- Built/registered F44 from pinned F32, routing sinf/cosf/log2f through internal ucrtmath in default FMA mode on both import paths.
- Nine million shim comparisons pass: six million through actual Unicorn hooks and three million through isolated production native Win64 callbacks.
- Switched confirmed Mac float trig imports and the default oracle; F32 remains selectable. Genuine double calls remain unchanged.
- Completed both seeds (1 and fresh 44), n300 for all ten plugins, plus all 708 saved cases, before and after: zero individual Classic or Smart exact losses.
- No rebaselines; inherited DistanceGradation mismatch and KiraKira saved-result drift remain recorded. One refused RadialBlur case had oracle timing drift; F44 recapture matches the original F32 hash.

facts:
- Branch `orch/F44-integrate-ms-float`; baseline commit `f23b5a664f13a42663fbac9a8d39b37600995ad0`. Read AGENT_GUIDE, GOTCHAS, compatibility plan, and the relevant ledger rows. No permission rejection or numerical-hypothesis stop occurred. No release gate, ledger, MAIN, original AEXCompat checkout, or other plugin implementation changed.
- `python3 tools/emulation/aexcompat_patches/build_F44.py`: final exit 0, release build 2m55s, one existing dead-code warning. Memory free was 52% before the successful Rust build; cargo/CMake jobs were 1. The initial build under the space-containing worktree path exited 1 because Unicorn's configure step rejects spaces; the final recipe uses the authorized cache worker build directory like F30/F32, and removes that regenerable tree. The failed tree was also removed. No numerical implementation was changed to work around the build error.
- Parent source matches every hash in F32's committed manifest. All six existing `ucrtmath/src/` files match F32 byte-for-byte; only the additional MS float implementation is compiled. The patch, full compiled source manifest, build command and parent identities are retained in `F44-evidence/build-manifest.json`.
- Worker: `~/.cache/olm-emu/worker-F44-msfloat/aex-guest-worker`, SHA256 `768138633933a872af35ed26ba5af6b7d880e837bfa9de686991e200fe427813`. Parent F32 SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`.
- `python3 tools/emulation/aexcompat_patches/validate_F44.py`: exit 0. For each of sinf/cosf/log2f and each of `api-ms-win-crt-math-l1-1-0.dll` / `ucrtbase.dll`, 1,000,000 random full-width input words in FMA mode, 0 raw-bit mismatches, no first mismatch. Real production Unicorn callbacks and XMM argument/return boundaries are exercised. Rosetta oracle: pinned UCRT 10.0.28000.2705, DLL SHA256 `385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3`.
- `python3 tools/emulation/aexcompat_patches/validate_native_F44.py`: exit 0. Production callback bodies and FFI module are source-manifest-verified, compiled for x86_64, and called through their actual Win64 ABI under Rosetta. Each function has 1,000,000 comparisons, 0 mismatches, no first mismatch. Memory free before this Rust build: 58%. Native export-name dispatch entries are asserted. This is isolated callback qualification, not a full native-carrier host/loader qualification. The fixed RadialBlur log2f(2^32) return is also asserted as bits `42000000` (32).
- `python3 tools/emulation/aexcompat_patches/check_mode_F44.py`: exit 0; each function's 1,024 raw outputs with unset mode equal FMA=1; malformed mode fails with no output. `build_F44.py --register`: exit 0, added F44 only under the INDEX lock, preserving F32 and all other entries.
- `bash tools/fuzz/build_F44.sh`: exit 0; ColorKey and DirectionalBlur both build Universal x86_64 + arm64. Hashes are in `mac-build-identities.json`. No installation, signing or release gate was run.
- MAIN's Python ran `audit_imports_F44.py`: exit 0; the ten AEX import tables confirm ColorKey uses sinf, DirectionalBlur cosf/sinf, RadialBlur log2f, and the other seven use none of this set. `boundaries.md` records the exact source/disassembly boundaries. RadialBlur's Mac MT19937 specialization already has one draw, equivalent to ceil(24/log2f(2^32)); it has no host log2f call to replace. RadialBlur's float-cast results of genuine double sin/cos are unchanged.
- `python3 tools/fuzz/measure_F44.py --before` and `python3 tools/fuzz/measure_F44.py`: both driver exits 0, each completing 6,000 generated plus 708 saved cases with `--jobs 1`. Every subprocess exits 0 except the existing `olmkirakira_gate_off_T06-replay`, which exits 1 in both variants because 23 saved results differ. Those are not new F44 failures.
- `python3 tools/fuzz/summarize_F44.py`: exit 0; 20 complete paired campaigns, 11 complete paired corpora, zero exact losses across both routes, and no changed successful reference output hashes. Original reports are hash-bound in `measurements.json`. All Mac route results are unchanged. There is one oracle status change and 36 diagnostic-text differences, separately retained without treating diagnostic text as numerical evidence.

Counts below are Smart **exact / mismatch / refusal / uncompared**. U includes the separately retained `budget` status (one DistanceGradation seed44 case); underlying statuses are not relabeled in the JSON.

| Plugin | Seed 1 F32 | Seed 1 F44 | Seed 44 F32 | Seed 44 F44 |
|---|---|---|---|---|
| colorkeep | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmblur | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmcolorkey | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmdirectionalblur | 290/0/8/2 | 290/0/8/2 | 288/0/12/0 | 288/0/12/0 |
| olmdistancegradation | 290/0/3/7 | 290/0/3/7 | 276/1/9/14 | 276/1/9/14 |
| olmkirakira | 282/0/18/0 | 282/0/18/0 | 271/0/29/0 | 271/0/29/0 |
| olmsmoother | 205/0/95/0 | 205/0/95/0 | 198/0/102/0 | 198/0/102/0 |
| olmsmoother2 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmtoondilate | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| radialblur | 255/0/43/2 | 255/0/43/2 | 259/0/41/0 | 259/0/41/0 |

The one generated Smart mismatch is unchanged DistanceGradation seed44 case70 (PF8): first byte/word 232, 8 differing bytes/words, Mac `38`, reference `39`; Mac raw SHA256 `596f9e7fe504f8d66df8a5bc0cae11252acc154308c080ef4f22f18af83bd3cf`. Complete result and reference hash are in `measurements.json` residuals. This ticket does not claim all admitted cases are exact.

| Corpus | Cases | F32 E/M/R/U | F44 E/M/R/U | Saved matches, both |
|---|---:|---|---|---:|
| olmblur | 39 | 39/0/0/0 | 39/0/0/0 | 39 |
| olmcolorkey | 3 | 3/0/0/0 | 3/0/0/0 | 3 |
| olmdirectionalblur | 56 | 56/0/0/0 | 56/0/0/0 | 56 |
| olmdistancegradation | 145 | 145/0/0/0 | 145/0/0/0 | 145 |
| olmkirakira | 8 | 8/0/0/0 | 8/0/0/0 | 8 |
| olmkirakira_gate_off_T06 | 62 | 60/0/2/0 | 60/0/2/0 | 39 |
| olmsmoother | 29 | 29/0/0/0 | 29/0/0/0 | 29 |
| olmsmoother2 | 8 | 8/0/0/0 | 8/0/0/0 | 8 |
| olmtoondilate | 300 | 300/0/0/0 | 300/0/0/0 | 300 |
| olmtoondilate_T13 | 23 | 23/0/0/0 | 23/0/0/0 | 23 |
| radialblur | 35 | 35/0/0/0 | 35/0/0/0 | 35 |

- Saved-result matches are 685/708 in both variants. The KiraKira T06 corpus has the same 60 Smart exact / 2 refused and the same 23 historical saved-result disagreements. No expectation was rewritten.
- `python3 tools/fuzz/rebaseline_F44.py`: audit exit 0; 0 qualified updates, 0 unqualified saved-reference changes. Rebaselined cases: **none**.
- Timing exception: RadialBlur seed1 case280 is refused by the Mac in both variants. Original F32 oracle succeeded with SHA256 `5a19de28aece7b23b644e5f2533da7f662677e3d6a837b9a96d88a53726487f8`; F44 hit the campaign's 10-second wall limit. Campaign data are retained unchanged. Two F44 recaptures with a 60-second outer limit succeeded in about 8.9 seconds and matched that original F32 hash exactly.
- Auxiliary `recheck_F44.py` exits 1 because its **fresh F32** recaptures stop at about 20.02 seconds, while both F44 recaptures succeed. The isolated F32 diagnostic says execution stopped before guest return at RIP `0x180002860`; the unchanged worker source has a 20,000,000-microsecond internal limit. Concurrent and isolated rechecks are retained separately. The first diagnostic was not retained by the initial helper; the final helper preserves diagnostics. The initial helper also encountered a single-oracle schema KeyError before any recapture; it was corrected to accept both existing report schemas. No new worker timeout, admission guard, expected value or reference hash was changed to hide these outcomes.
- Default F44 and explicit `OLM_AEX_WORKER=<F32>` override were asserted. `git diff --check` passes. All started commands have exited; regenerable build trees and temporary SDK links are removed. Scratch remains below 5 GiB (final size recorded below).

inference:
- The restricted worker patch and unchanged old math sources isolate successful output changes to the three new float imports. In these campaigns/corpora there are no such successful-output changes, and no existing exact route is lost.
- The F44 case280 recaptures reproduce the original F32 reference, so the campaign timeout does not demonstrate a numerical regression. The repeat F32 internal-limit stop is an auxiliary execution limitation; its detailed timing cause is unconfirmed and no further hypothesis loop was pursued.
- Qualification covers the recorded original-AEX CPU/Unicorn tests and isolated native callbacks. It does not claim native Windows/AE, full native-carrier operation, all parameter combinations, or whole-plugin exhaustive equality.

changed_files:
- `core/dblur_rotate.cpp`
- `mac/OLMColorKey/OLMColorKey.cpp`
- `mac/OLMColorKey/Mac/OLMColorKey.xcodeproj/project.pbxproj`
- `mac/OLMDirectionalBlur/Mac/OLMDirectionalBlur.xcodeproj/project.pbxproj`
- `tools/fuzz/run.py`
- `tools/emulation/aexcompat_patches/F44-msfloat.patch`
- `tools/emulation/aexcompat_patches/{build_F44.py,validate_F44.py,validate_native_F44.py,compare_F44.c,check_mode_F44.py,audit_imports_F44.py}`
- `tools/fuzz/{before_F44.py,measure_F44.py,summarize_F44.py,rebaseline_F44.py,recheck_F44.py,build_F44.sh}`
- `orchestra/reports/F44-evidence/*`
- `orchestra/reports/F44-integrate-ms-float.md`

verify:
Run serially from this worktree, using the registered worker and read-only MAIN assets:
```sh
s="$PWD/orchestra/state/F44-integrate-ms-float"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1 OLM_UCRT_FMA=1
python3 tools/emulation/aexcompat_patches/validate_F44.py > "$s/validate.log" 2>&1
python3 tools/emulation/aexcompat_patches/check_mode_F44.py > "$s/mode-driver.log" 2>&1
python3 tools/emulation/aexcompat_patches/validate_native_F44.py > "$s/native-validation.log" 2>&1
python3 tools/fuzz/measure_F44.py --before > "$s/measure-before.log" 2>&1
python3 tools/fuzz/measure_F44.py > "$s/measure-after.log" 2>&1
python3 tools/fuzz/summarize_F44.py > "$s/summary.log" 2>&1
python3 tools/fuzz/rebaseline_F44.py > "$s/rebaseline-audit.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/emulation/aexcompat_patches/audit_imports_F44.py > "$s/import-audit.log" 2>&1
bash tools/fuzz/build_F44.sh > "$s/mac-build.log" 2>&1
git diff --check
```
Expected: nine million raw-bit comparisons with zero mismatches, mode checks pass, both Universal builds pass, the Smart tables above and zero individual exact losses, 685/708 saved-result matches in both variants, and zero rebaseline updates. Timing statuses can vary: retain raw reports and inspect changes, never rebaseline an execution-status change as math. The measurement drivers intentionally retain the known T06 subprocess exit 1. The auxiliary command `python3 tools/fuzz/recheck_F44.py > "$s/status-rechecks.log" 2>&1` currently exits 1 on the fresh F32 internal-limit stop described above; its successful F44 hash must equal the original F32 hash. A rerun with no timing drift has no rechecks. Rebuild the worker only in a fresh cache destination via `python3 tools/emulation/aexcompat_patches/build_F44.py --cache-root "$HOME/.cache/olm-emu/recheck-F44"`; it refuses to overwrite existing builds, checks memory >=30%, and uses one job. Do not register that optional rebuild over F44.

next:
- Orchestrator review and merge; no push or merge was attempted.
- F43 genuine double imports remain separate. The inherited DistanceGradation seed44 case70 mismatch and T06 saved-result drift need their own scope if pursued.
- Optional separate F32 execution-limit investigation for RadialBlur seed1 case280; preserve its successful original reference and both new-worker recaptures. No new F44 numerical counterexample remains from this ticket.

Final scratch: 90228912 bytes (logs, measurement reports, and small diagnostics; regenerable build trees removed).
