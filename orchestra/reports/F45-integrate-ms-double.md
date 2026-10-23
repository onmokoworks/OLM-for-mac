status: done

summary:
- Integrated FMA double sin/cos/exp into F44 worker import paths and confirmed Mac import call sites.
- F43c reports blocked; obeyed the ticket fallback and left double pow on host.
- Nine million shim and 36 million actual Mac-object raw-bit comparisons pass; three plugins build Universal.
- Registered F45 and switched the default; explicit F44 selection remains available.
- Completed both seeds n300 and all 708 saved cases before/after: zero exact losses, no rebaseline.

facts:
- Branch `orch/F45-integrate-ms-double`, initial HEAD `03ce723f6cb334d2988980885d54e19ca9cdeb0f`, initially clean. Read AGENT_GUIDE, GOTCHAS, compatibility plan, dependency reports, and relevant ledger forbidden-action cells. No subagents, MAIN/emulator checkout edits, gate or ledger changes, push, stash, or history rewrite.
- `python3 tools/emulation/aexcompat_patches/build_F45.py` exited 0. Memory free before Rust build: 60%; cargo/CMake jobs 1. Existing dead-code warning only. Parent F44 source matched its entire retained manifest. All existing `ucrtmath/src` files matched the parent. Source manifest, patch hash, parent hash, command, worker and probe identities are retained in `F45-evidence/build-manifest.json`.
- Worker SHA256 `8849565128e4147bb39b145bf392e20da1983c476498ca4448001ea278a38409`, at `/Users/onmk/.cache/olm-emu/worker-F45-msdouble/aex-guest-worker`. Parent F44 SHA256 `768138633933a872af35ed26ba5af6b7d880e837bfa9de686991e200fe427813`.
- `python3 tools/emulation/aexcompat_patches/validate_F45.py` exited 0: for each of sin/cos/exp, and each CRT DLL name (`api-ms-win-crt-math-l1-1-0.dll`, `ucrtbase.dll`), 1,000,000 random full-width input words in FMA mode, zero complete-64-bit mismatches; no first mismatch. The real Unicorn import hook and XMM input/return boundary are exercised. Rosetta UCRT 10.0.28000.2705 DLL SHA256 `385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3`.
- `python3 tools/emulation/aexcompat_patches/validate_native_F45.py` exited 0: 1,000,000 inputs per function, zero mismatches, no first mismatch. Compiles manifest-verified production callback bodies and FFI module, invokes the actual Win64 ABI under Rosetta. This is isolated callback qualification, not qualification of the complete native carrier.
- `python3 tools/emulation/aexcompat_patches/check_mode_F45.py` exited 0: 1,024 inputs per function; unset mode equals FMA=1 byte-for-byte, malformed mode rejects without output.
- `python3 tools/emulation/aexcompat_patches/build_F45.py --register` exited 0; appended F45 under INDEX lock, preserving F44 and older entries. `run.default_worker()` returns F45; explicit `OLM_AEX_WORKER=<F44>` returns F44.
- MAIN's read-only Python ran `audit_imports_F45.py`, exit 0: all ten pinned AEX import tables agree with the ticket. `F45-evidence/aex-double-imports.json` records hashes and DLL/name sets. `boundaries.md` records original decomp locations and excluded embedded/host-only helpers.
- Initial Mac build failed because AE's Carbon prefix header declares `fraction`, conflicting with a private helper in double.c. Added a Mac translation unit that renames only that internal helper after the prefix header. Standalone qualified ucrtmath source and all arithmetic remain unchanged. `bash tools/fuzz/build_F45.sh` then exited 0: ColorKey, KiraKira, RadialBlur all build x86_64 + arm64. Binary hashes and math-source identities are retained. No installation, signing, or release gate ran.
- DistanceGradation Gaussian exp replacements were withdrawn during static boundary audit: FUN_181285230 calls embedded softdouble FUN_1813a0870, not imported UCRT exp. Imported bilateral exp is distinct. Current matching Mac IPP helpers are unchanged. This prevents a blanket double-call replacement from changing embedded math. No numerical counterexample hypotheses were attempted.
- `python3 tools/emulation/aexcompat_patches/validate_mac_F45.py` exited 0: actual Xcode objects from all three plugins, arm64 and x86_64, sin/cos/exp each with 1,000,000 random full-width inputs in both modes. 18 million input rows, 36 million raw-bit comparisons, zero mismatches, no first mismatch. This directly verifies the prefix-header wrapper fix; object hashes and results are retained.
- Initial `measure_F45.py --before` completed 300 RadialBlur seed1 attempts but that subprocess exited 2: case298 raised OS `PermissionError: [Errno 1] Operation not permitted` inside the harness timeout `os.killpg`. The tool call itself was executed, not rejected by approval policy. Original report/log remain under scratch `initial/`; error and report hash are committed in `initial-framework-error.json`. No process from that case remained. Re-ran the full seed1 campaign with the same settings (`measure_F45.py --before --plugin radialblur --campaigns-only --resume`, after preserving the original report); exit 0, all 300 results present, no framework error. No harness/timeout/admission code was changed.
- Auxiliary `python3 tools/fuzz/recheck_F45.py` exited 1 (`Unresolved status drift`): RadialBlur seed1 case62's original F44 run timed out at the harness's 10-second wall limit, while original F45 was exact. A 60-second-outer-limit F44 recapture succeeded in 8.31 seconds with raw SHA256 `d3d08c4296f99ebc15bfa4e2cb2d9c2dc9890e68802bbcc177a5187d08027042`, identical to the successful original F45 result. The auxiliary F45 recapture stopped at 20.02 seconds before guest return, RIP `0x180001fa2`; unchanged `x64.rs:299` sets `TIMEOUT_MICROSECONDS=20_000_000`. Both observations and full diagnostics are retained in `status-rechecks.json`. This is not a successful same-run pair; successful outputs across the campaign and recapture agree. No expectations or measurements were rewritten and no further timing hypothesis loop was pursued.

- `measure_F45.py --before` and `measure_F45.py` driver exits 0: each measured 6,000 generated cases and replayed 708 saved cases with jobs=1. The initial baseline RadialBlur framework exception and its successful complete rerun are detailed above. Both KiraKira T06 replay subprocesses exit 1 due to the same 23 historical saved-result differences; all other final measurement subprocesses exit 0.
- `summarize_F45.py` exited 0: 20 complete paired campaigns, 11 complete paired corpora, zero individual exact losses across both Classic and Smart, only two oracle status changes, and 30 diagnostic-text differences. No successful-output hash changed between successful paired references; no candidate result changed except the Smart case62 comparison becoming possible. Raw reports are hash-bound in `measurements.json`.
- `rebaseline_F45.py` audit exited 0: zero qualified updates, zero unqualified saved-reference changes. No corpus expectation was modified. Saved-result matches remain 685/708 on both sides.
- Fresh seed45 exposes two unchanged Smart mismatches: DistanceGradation case2 PF8, first byte/word 424, 4 differing bytes/words, Mac `1a`, reference `19`, Mac SHA256 `bc94a91aa42b9251ca331fd53856f177acea8654ee0416ab1b975db80fd1bfee`; RadialBlur case8 PF8, first byte/word 1000, 1 differing byte/word, Mac `a8`, reference `e4`, Mac SHA256 `9578c539714e8ef47a83c67acd6806cc674097b7158c5904947c271e0f382ea4`. Full parameters, reference hashes and results are in retained residuals. No fix was attempted outside this integration ticket.


Paired results (Smart **exact / mismatch / refusal / uncompared**; U includes separately recorded budget statuses):

| Plugin | Seed1 F44 | Seed1 F45 | Seed45 F44 | Seed45 F45 |
|---|---|---|---|---|
| colorkeep | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmblur | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmcolorkey | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmdirectionalblur | 290/0/8/2 | 290/0/8/2 | 287/0/12/1 | 287/0/12/1 |
| olmdistancegradation | 290/0/3/7 | 290/0/3/7 | 279/1/11/9 | 279/1/11/9 |
| olmkirakira | 282/0/18/0 | 282/0/18/0 | 277/0/23/0 | 277/0/23/0 |
| olmsmoother | 205/0/95/0 | 205/0/95/0 | 210/0/90/0 | 210/0/90/0 |
| olmsmoother2 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmtoondilate | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| radialblur | 257/0/40/3 | 258/0/40/2 | 257/1/40/2 | 257/1/40/2 |

Smoother v1 **Classic**:

| Seed | F44 E/M/R/U | F45 E/M/R/U |
|---|---|---|
| 1 | 205/0/95/0 | 205/0/95/0 |
| 45 | 210/0/90/0 | 210/0/90/0 |

All saved corpora:

| Corpus | Cases | F44 E/M/R/U | F45 E/M/R/U | Saved matches F44/F45 |
|---|---:|---|---|---|
| olmblur | 39 | 39/0/0/0 | 39/0/0/0 | 39/39 |
| olmcolorkey | 3 | 3/0/0/0 | 3/0/0/0 | 3/3 |
| olmdirectionalblur | 56 | 56/0/0/0 | 56/0/0/0 | 56/56 |
| olmdistancegradation | 145 | 145/0/0/0 | 145/0/0/0 | 145/145 |
| olmkirakira | 8 | 8/0/0/0 | 8/0/0/0 | 8/8 |
| olmkirakira_gate_off_T06 | 62 | 60/0/2/0 | 60/0/2/0 | 39/39 |
| olmsmoother | 29 | 29/0/0/0 | 29/0/0/0 | 29/29 |
| olmsmoother2 | 8 | 8/0/0/0 | 8/0/0/0 | 8/8 |
| olmtoondilate | 300 | 300/0/0/0 | 300/0/0/0 | 300/300 |
| olmtoondilate_T13 | 23 | 23/0/0/0 | 23/0/0/0 | 23/23 |
| radialblur | 35 | 35/0/0/0 | 35/0/0/0 | 35/35 |

- Second status-only difference: RadialBlur seed45 case158 is refused by the Mac in both variants; its F44 reference succeeded and F45 hit the 10-second harness limit. `recheck_F45.py --resume` added both successful recaptures (15.01s F44 / 14.98s F45), both matching the original F44 SHA256 `9734dca1e491ee71dcc6b5c68b9f8b4f74d6465bdf30528ac3c74657fa6f7ce6`. The auxiliary driver still exits 1 because it retains the case62 internal-limit result. This does not represent an exact-case loss.
- Final `git diff --check` and Python syntax/evidence checks pass. All started processes have exited. Regenerable Rust/Xcode/native/fuzz build trees and task-created SDK links were removed; logs, raw measurement reports and diagnostics remain. Final scratch: 96418990 bytes, below 5 GiB. No tool approval rejection or numerical-hypothesis stop occurred.

inference:
- Qualification establishes the recorded UCRT import boundaries in the tested FMA corpus, not exhaustive input equivalence or native Windows/AE equivalence.
- The Mac wrapper addresses header namespace pollution without changing numerical behavior.
- Both status-drift cases have matching successful old/new output evidence. Their timing variability is not evidence of a numerical regression; this does not claim every rerun finishes within either timeout.

changed_files:
- `core/kirakira_warp.h`, `core/ucrt_ms_double_mac.c`.
- ColorKey and RadialBlur production CPP; ColorKey/KiraKira/RadialBlur Xcode project files.
- `tools/fuzz/run.py`, F45 before/measure/summarize/rebaseline/build helpers.
- F45 worker patch, build/validate/native/mode/import-audit tools and README.
- `orchestra/reports/F45-evidence/*` and this report.

verify:
Run serially from the worktree:
```sh
s="$PWD/orchestra/state/F45-integrate-ms-double"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1 OLM_UCRT_FMA=1
python3 tools/emulation/aexcompat_patches/validate_F45.py > "$s/validate.log" 2>&1
python3 tools/emulation/aexcompat_patches/check_mode_F45.py > "$s/mode-driver.log" 2>&1
python3 tools/emulation/aexcompat_patches/validate_native_F45.py > "$s/native-driver.log" 2>&1
bash tools/fuzz/build_F45.sh > "$s/mac-build.log" 2>&1
python3 tools/emulation/aexcompat_patches/validate_mac_F45.py > "$s/mac-object-driver.log" 2>&1
python3 tools/fuzz/measure_F45.py --before > "$s/measure-before.log" 2>&1
python3 tools/fuzz/measure_F45.py > "$s/measure-after.log" 2>&1
python3 tools/fuzz/summarize_F45.py > "$s/summary.log" 2>&1
python3 tools/fuzz/rebaseline_F45.py > "$s/rebaseline-audit.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/emulation/aexcompat_patches/audit_imports_F45.py > "$s/import-audit.log" 2>&1
git diff --check
```
Expected checks: nine million shim comparisons and 36 million actual Mac-object comparisons with zero mismatches; default-mode assertions and three Universal builds pass. Regression expectations are the tables above: zero exact losses, 685/708 saved matches in both variants, and zero rebaselines. The known T06 subprocess exit 1 is retained by the drivers. Timing statuses may vary; preserve and inspect raw reports. Optional worker rebuild uses a fresh destination as described in README-F45.md; never overwrite existing workers. Cleanup regenerable scratch build outputs after verification.

Optional timing diagnostic: `python3 tools/fuzz/recheck_F45.py` preserves campaigns and uses a 60-second outer limit. The retained run exits 1 on the case62 internal 20-second stop; inspect the evidence above rather than treating this auxiliary assertion as a numerical mismatch.

next:
- Orchestrator reviews and merges; no push or merge performed.
- Separate optional investigation: RadialBlur execution-time variability at the inherited internal limit, and the existing KiraKira T06 saved-result drift. Neither is rebaselined as a double-math change.
- Separate numerical tickets may investigate unchanged DistanceGradation seed45 case2 and RadialBlur seed45 case8; this integration does not claim all generated cases exact.
- Pow integration requires an explicit follow-up overriding F43c's blocked-disposition fallback.
