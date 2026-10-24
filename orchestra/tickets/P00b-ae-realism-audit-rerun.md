# P00b: rerun the real-bundle AE-realism audit on current HEAD (finishes P00)

## State
- P00's worker died after measuring but before writing its report. Its work is committed on branch `orch/P00-ae-realism-refusal-audit` (commit aa3b435f):
  - host patch `tools/emulation/aexcompat_patches/P00-host-realism.{cpp,md}`;
  - driver `tools/fuzz/ae_realism_audit.py`;
  - its scratch helpers and matrix data, in `orchestra/reports/P00-ae-realism-refusal-audit/stale-pre-P02/`.
- Start with `git merge orch/P00-ae-realism-refusal-audit` and read the original ticket `orchestra/tickets/P00-ae-realism-refusal-audit.md`.
- **P00's data is stale.** It used bundles built before the P01/P02/P02i/P02j geometry fixes, so the refusal counts there no longer apply. One finding is still worth rechecking: nondefault DirectionalBlur and RadialBlur cases timed out (>15 s) at 1080p/4K.
- This audit is the only check that runs the real `.plugin` bundles at real sizes (1080p, 4K, layer larger than comp). The fuzz oracle stops at 1920x1080 and cannot do PF32 full HD.

## Do
1. Build fresh HEAD bundles with `tools/fuzz/build_F47_bundles.py`, then rerun P00's matrix with the committed driver/host. That covers the 10 plugins × downsample 1/1, 1/2, 1/3, 1/4, 1/8 and asymmetric, sizes 1920x1080 / 3840x2160 / 1000x1000 / 1279x719 / layer > comp, padding, extent_hint and ROI sub-rects, aspect 0.9/2.0, and 8/16/32 bpc, with default params plus 10 corpus params each.
2. Report a per-plugin table of situation → OK / refusal tag / PF error / crash / timeout, plus not-all-zero output. For every remaining refusal, say whether the original plausibly refuses too (cite F52c/T15b evidence or disassembly), or whether it is Mac-only (that one would be black in AE).
3. Performance: time per frame at 1920x1080 and 3840x2160 for 8/16/32 bpc, with defaults and with the heaviest corpus params. Flag anything over 2 s at 1080p. For each slow case, profile it (`sample` or Instruments CLI) and name the hot function.
4. Write `orchestra/reports/P00b-ae-realism-audit-rerun.md`. In `next`, propose concrete fix tickets: one per Mac-only refusal group, and one per performance hotspot.

## Rules
- Use 1-2 processes, and check `memory_pressure` (≥30% free). Use a per-case wall timeout of 60 s and record timeouts; do not wait forever.
- **Commit partial results at least every 30 minutes**, so a dead worker loses nothing.
- Make no plugin source changes. Do not touch the release gate or ledger, and never edit `04_Tools/AEXCompat*`.
- The stop rule applies. Do 8 bpc defaults at 1080p and 4K with ds 1/1, 1/2 and 1/4 for all 10 plugins first.
