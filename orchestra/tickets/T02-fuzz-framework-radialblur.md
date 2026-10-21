## Goal
Build a reusable **random differential fuzzer** (`tools/fuzz/`), first wired to
OLMRadialBlur. This replaces hand-enumerated per-parameter probe campaigns as the
primary way to find and count remaining mismatches.

## Why
The project has 1,300+ dated probe scripts that each enumerate conditions for one
parameter family. That never tells us how much is left. A fuzzer gives a measurable
residual: "N random legal cases, K mismatches, clustered into M causes".

## Requirements
1. Generator: random **legal** parameters (respect the real AEX parameter builder
   ranges/popups/units already recovered in the repo; reuse existing helpers, do
   not re-derive) + random inputs: depth 8/16/32, sizes incl. 1x1, 1-row, 1-col,
   odd strides, and up to ~256x256 by default; SDR, HDR, signed, NaN/inf only for
   PF32, transparent/semi-transparent alpha. Seeded and reproducible.
2. Oracle: the original AEX via the existing Unicorn emulation path (reuse the
   modules the RadialBlur probes in tools/emulation/ already use for "public AEX"
   replays). Candidate: Mac production public path (Classic and Smart).
3. Compare raw output bits. On mismatch, auto-**shrink** (smaller geometry, params
   toward defaults, simpler pixels) while the mismatch persists.
4. For a shrunk case, if the existing harness exposes intermediate stages, record
   the first mismatching stage; otherwise just the raw diff stats.
5. Cluster mismatches by a cheap signature (stage, param-set that differs from
   default, depth) and emit `reports/fuzz/radialblur_<date>.json` summary + a
   corpus dir of shrunk counterexamples (small files only) under `tests/fuzz_corpus/radialblur/`.
6. CLI: `python3 tools/fuzz/run.py --plugin radialblur --n 2000 --seed 1 --jobs 4
   --budget-minutes 30`. Must respect jobs/time budget and disk rules.
7. Design `tools/fuzz/` so another plugin is added by writing one adapter module
   (generator ranges + oracle call + candidate call). Document that in
   `tools/fuzz/README.md` (short).
8. Classify AEX-side "reject"/budget refusals and Mac-side refusals separately
   from pixel mismatches.

## Done when
`--n 500` run completes and the summary is committed, with a short honest
statement of residual mismatch clusters. Do NOT fix plugin mismatches in this ticket.
