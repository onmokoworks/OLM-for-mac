# OLMDistanceGradation case_0023 — 65px inside=1.0 family converges to reference-path-split (2026-07-06)

Follow-up to `olmdistancegradation_case0023_compose_emulation_grounded_20260705.md` and
`tools/emulation/DG_FIELD_GEN_REPORT.md`. Full report:
`tools/emulation/DG_NORMALIZE_65PX_REPORT.md`.

## What was grounded (all via local .aex emulation + static disasm, no Windows trip)

The entire Windows CPU field/compose pipeline for case_0023 is now binary-grounded:
`convert (FUN_1812aef70 = cv::Mat::convertTo) → distanceTransform (DIST_L2/PRECISE)
→ threshold (THRESH_BINARY, strict >) → normalize (FUN_18117ca50 = cv::normalize
NORM_MINMAX, beta = 32768 for 16bpc / 255 / 1.0 read live from PE) → compose`.

- case_0023: Interpolation Mode = 1 = INTERP_CONSTANT; Both(3); Inside=36; Outside=0;
  Invert=0; use_bg=1; **GPU Rendering=1**.
- Both-mode combine on Windows = `FUN_181182b20 = cv::add`; the Mac port uses `std::max`
  (`OLMDistanceGradation.cpp:508`). See "latent difference" below.

## The 65px finding (negative certainty)

- Compose driven with real colors: **field_x=0 → blue (7195,0,61165) = Mac output;
  field_x=1 → red (65535,0,0) = reference.** So reference wants field_x=1, Mac has 0.
- Reconstructing the confirmed Windows CPU pipeline on the RECORDED distances
  (inside=1.0, outside=0.0): both sides fall to 0 under strict `>`, `cv::add(0,0)=0`
  → field_x=0 (blue). A scipy cross-check gives win_fx == mac_fx (0 px difference).
- **Conclusion (FACT): the 65px divergence does NOT arise in convert, normalize, or
  cvAdd-vs-max.** All are binary-grounded and reproduce Mac's blue on the recorded
  distances. The reference red is structurally UNREACHABLE from this CPU pipeline +
  recorded distances.

## Convergence with OLMRadialBlur

This is the **same pattern as OLMRadialBlur tiny Rotation (1614,6)**: the CPU `.aex`
path, faithfully emulated, produces the Mac value, and the reference PNG shows the
opposite — with **GPU Rendering=1** on the reference. Two independent hard lanes now
point at reference-path-split (GPU-vs-CPU or stale packaged PNG). This elevates it from
a RadialBlur one-off to a cross-plugin project-level question.

Reference red source is one of: (a) Windows CPU actual distances differ from the recorded
values, or (b) GPU-path / stale reference. `GPU Rendering=1` plus the lane_state
provenance-split (packaged PNG stale; live Windows matches Mac) make **(b) the leading
hypothesis**, but NOT asserted — no direct Windows CPU distance witness at these pixels.

## Latent Mac-vs-Windows difference found (not the 65px cause; flag for later)

Windows Both-mode combine is `cv::add` (saturating sum); Mac uses `std::max`
(`OLMDistanceGradation.cpp:508`). These agree where one side is 0 (as at the 65px), so
this is not the 65px cause — but they DIFFER in support-overlap regions where both inside
and outside fields are nonzero. This is a real latent porting difference to evaluate
separately (do not fix from this note; Mac source is frozen per the 2026-07-02 oracle
until a witness demands it).

## Remaining / next

1. Highest value: one typed Windows CPU witness of the `FUN_181174760` input inside/outside
   distance at a 65px pixel → decides (a) vs (b).
2. GPU-vs-CPU-software reference recapture (matches the existing `current_aex_recapture`
   request) — the strategic close-out.
3. 8px threshold-crossing family remains the separate provenance/export-first
   threshold-family lane; do not mix it with the 65px reference-path split
   question.
4. cvAdd-vs-max: evaluate in support-overlap regions.
