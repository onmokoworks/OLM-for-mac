status: partial

summary:
- Finite PF32 Legacy admission closes the first cluster, without numerical changes.
- Seed 1 Smart 283/0/17 -> 296/0/4; fresh seed 43 281/0/19 -> 296/0/4 (exact/mismatch/refusal).
- Independent finite Legacy matrix 720/720 exact; nonfinite gate-off matrix 384/384 exact.
- Preserves all 564 baseline exact campaign cases; sanitizer campaigns and retained controls pass.
- Nonfinite Legacy and non-Legacy admissions remain for subsequent commits.

facts:
Base `c1d1f1943e2e3c9ab6e62e1094ba279643f73385`, branch `orch/C32-olmblur-smart-r7`. Read AGENT_GUIDE, OLMBlur ledger restrictions, compatibility plan, GOTCHAS, T09/C05/C10/C12/C15/C21/C24 and F10/F12/F31/F38 reports. No changes to MAIN, emulator, cached workers, release gates, ledger, other plugins, numeric core or work budget. All campaigns use jobs=1; at most two build/emulator workloads. Scratch and compiler temporary files are ticket-local.

Oracle: `/Users/onmk/.cache/olm-emu/worker-F32-deep/aex-guest-worker`, SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`. Original MAIN `plugins_2025/OLMBlur.aex` SHA256 `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`. Full source/core/candidate provenance and measured transitions are in `orchestra/reports/C32-evidence/`.

First cluster (finite Legacy): extends the existing small-frame Legacy admission to PF32. The existing [-16,16] ARGB source scan, all parameter/world/storage/downsample/work guards and exact-fixture precedence remain. Source samples are never modified. F31 already restored `ucrt_expf` in the PF32 Legacy coefficient builder; F38 already restored generated-NaN signs in the helpers. No arithmetic operation is changed by this ticket.

| Campaign | Baseline E/M/R | Gate-off E/M/R | Finite Legacy E/M/R |
|---|---|---|---|
| seed 1 n300 | 283/0/17 | 300/0/0 | 296/0/4 |
| seed 43 n300 | 281/0/19 | 300/0/0 | 296/0/4 |

All original-route oracle objects and Classic results remain identical. Seed-1 refusals: 13 finite Legacy, 2 nonfinite Legacy, 2 nonfinite non-Legacy. Seed-43 refusals: 15 finite Legacy, 1 nonfinite Legacy, 3 nonfinite non-Legacy. Work-budget refusals: 0 in both measured campaigns; budget unchanged. No first mismatching output or stage exists in these completed gate-off campaigns.

Executed baseline `tools/fuzz/run.py --plugin olmblur --n 300 --seed 1 --jobs 1 --shrink-attempts 0`; sanitized baseline seed43 and gate-off seeds1/43 via `blur_campaign_C12.py`; explicit ticket scratch/report/corpus destinations. Initial gate-off setup failed because the older diagnostic build lacked the new UCRT include tree/library. Added a scratch symlink and UCRT static library link; rerun completed. This was a build-scaffold error, not a numerical hypothesis or permission rejection.

Independent original-AEX matrices via `verify_blur_C32.py` (F32, serial, ASan/UBSan, odd strides, full public Smart entry):
- Finite Legacy: 720 exact; 480 prior exact unchanged, 240 refusals become exact. Six geometries, ten Amount values including adjacent FLOAT32 boundaries and 1000, Repeat 1/2/3/4/9/10, both Bias values, Smoothness 1/62.5/100, independent signed HDR random/edge sources in [-16,16], signed zeros/subnormals.
- Nonfinite diagnostic: 384 exact; 193 prior exact unchanged, 191 refusals become exact. Four geometries, four Amounts, three Repeats, both Bias/Legacy modes, signed infinities, distinct signed quiet/signaling NaNs, plus mixed finite/HDR/subnormal inputs. This supplements an initial 192-row all-nonfinite run, also exact; final committed evidence is the expanded run.
- Each matrix's retained positive replay: 80/80 exact, exit 0, empty sanitizer stderr. Source, guards, callback lifecycle and padding assertions are inherited from the public hosts. Leak detection is disabled; ASan/UBSan abort on findings.
- Seven existing Classic/generic unit checks pass. Python AST syntax, shell syntax and `git diff --check` pass.

inference:
The prior C24 math/oracle barriers have been resolved sufficiently for these measured admission domains by F31/F32/F38. The evidence supports widening the general gate; it is not a new numeric fix or proof of arbitrary native Windows/AE/GPU behavior. Larger finite PF32 values remain outside the small-frame verified domain. No per-case/coordinate/output correction is used.

changed_files:
- mac/OLMBlur/OLMBlur.cpp — finite PF32 Legacy admission.
- tools/fuzz/blur_campaign_C12.py — UCRT include tree for scratch variants.
- tools/fuzz/triage_olmblur.py — UCRT library linkage for diagnostic builds.
- tools/fuzz/verify_blur_C32.py — independent serial sanitized matrices and retained replay.
- tools/fuzz/summarize_blur_C32.py — strict campaign/oracle/exact-preservation and corpus assertions.
- tools/fuzz/recheck_blur_C32.sh — serial sanitized campaign/replay driver.
- orchestra/reports/C32-evidence/*.json — measured provenance, transitions and matrices.
- orchestra/reports/C32-olmblur-smart-r7.md — report.

verify:
From this worktree, at the first-cluster commit:
```sh
bash tools/fuzz/recheck_blur_C32.sh finite
s="$PWD/orchestra/state/C32-olmblur-smart-r7"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/verify_blur_C32.py --scratch "$s" --report "$s/legacy-recheck.json" --before c1d1f194 --mode legacy --require-exact
python3 tools/fuzz/verify_blur_C32.py --scratch "$s" --report "$s/nonfinite-recheck.json" --before c1d1f194 --mode nonfinite --gate-off --require-exact
PYTHONPATH=tests python3 -m unittest test_olmblur_generic_classic_beta_20260822 test_olmblur_generic_beta_lane_20260820
```
Expected campaigns 296/0/4 each; strict corpus replay 39/39 unchanged; finite matrix 720/720, diagnostic nonfinite 384/384, retained80/80 per matrix, seven tests pass. Full campaign logs remain in scratch. No rebaseline command is needed.

next:
Promote nonfinite Legacy, then nonfinite non-Legacy as separate clusters, retaining the finite magnitude boundary and all work/storage guards.
