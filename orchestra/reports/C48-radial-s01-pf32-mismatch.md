status: done
summary:
- Fixed Zoom's no-fade prepass to use the separate size plane, not the noise-composed scatter span.
- Original seed102 case8 PF32 and its reduced witness are now bit-exact; no admission narrowing.
- Complete paired planes on the reduced witness identify B150 prepass as the first divergence and all match after the fix.
- Seed1/102 n300 Smart have zero mismatches; all baseline exact outputs are preserved (one timeout rechecked).
- Corpus: 56 fresh exact + 1 retained-reference exact; independent controls and witnesses: 38/38 ASan/UBSan exact.

facts:

FACT: Starting revision `d6cd18daa05d1106718faa2594d4fe7a3b089564`, branch
`orch/C48-radial-s01-pf32-mismatch`. Read AGENT_GUIDE, GOTCHAS, compatibility plan,
and Radial ledger restrictions. No MAIN, emulator source, worker, gate, ledger,
or other plugin changes. No reference-worker rebuild.

FACT: Public raw replays used retained F46
`/Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker`, SHA-256
`6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
Original AEX SHA-256:
`ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
Full-plane trace worker was the retained default of `trace_radialblur_smart_C06.py`,
SHA-256 `93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`.
Its reduced-witness public and traced final hashes equal F46's reference hash.
No changed math imports or approximate comparisons.

FACT: `python3 tools/fuzz/verify_radialblur_C48.py --revision HEAD --output
orchestra/state/C48-radial-s01-pf32-mismatch/raw-baseline` (HEAD then was the
starting revision) reproduced both supplied failures:

| Input | First word | Mac bits | AEX bits | Different words |
| --- | ---: | --- | --- | ---: |
| Original 1x217 PF32 | 120 | 0x3eb5863d | 0x3f0ee30a | 2 |
| Reduced 1x54 PF32 | 116 | 0x3d658b04 | 0x3de58a2a | 12 |

Baseline exit 1 is the expected numerical failure; 36 independent controls were exact.
`python3 tools/fuzz/verify_radialblur_C48.py --sanitize --output
orchestra/state/C48-radial-s01-pf32-mismatch/raw-fixed` exited 0: 38/38 exact,
including those 36 controls (1x54 / 54x1 / 7x9, PF8/16/32,
Size/Noise 100/100, 100/0, 0/100, 50/100, fades disabled).
Original fixed output SHA-256:
`5f60c8538260c0851c7bc1182ad3a9bba95175d2bec870418fe40f0117dbfc23`.
Reduced fixed output SHA-256:
`271f2b89a58de3ff6a3896ce611435b1a51158efff19e56f0a8820f51cf4fd7f`.
The sanitizer report records the enabled sanitizer build and successful public calls.

FACT: Full paired trace used a lossless PNG transport for the reduced binary-valued
PF32 input. Both native and Mac polar dimensions were 30x1800 (54,000 cells).
Before/after differing counts:

| Stage | Before | After |
| --- | ---: | ---: |
| Gaussian weights (9 words) | 0 | 0 |
| Polar RGBA (216,000 words) | 0 | 0 |
| Eligibility (54,000 bytes) | 0 | 0 |
| Scatter span (54,000 words) | 0 | 0 |
| B150 prepass RGBA (216,000 words) | 13,596 | 0 |
| B150 prepass maximum alpha (54,000 words) | 3,399 | 0 |
| Post-scatter RGBA / maximum alpha | 13,596 / 3,399 | 0 / 0 |
| Normalized RGBA (216,000 words) | 13,596 | 0 |

First divergent prepass cell is 629, RGBA word 2516: native little-endian
`ffe7bb3c`, Mac `00000000`. Its native polar alpha and prepass maximum alpha
are both `0x3cbbe800` (0.022937774658203125), while the scatter span is zero.
AEX B150 `b251` loads its factor from R8; `b26b..b26e` tests that factor for zero
before fade loops, even when both fade lengths are zero. See retained `b150.asm`.
Production previously supplied the noise-composed span to this check without
fades; it now materializes and samples the separate size plane on all enabled
size-variation Zoom paths. No sample weights, coordinates, or final bytes were patched.

FACT: The full stage trace is for the reduced witness. The original HDR input
was replayed as raw PF32 through public Smart before/after, without PNG conversion;
no complete original-HDR intermediate-plane trace is claimed.
The initial F46 trace invocation rejected typed Angle syntax (not a permission
failure); its legacy-angle prefix replay worked. Its R9 diagnostic is a source-alpha
argument, so the prefix tool's `prepass_factor` label is not used as factor evidence.
Full-plane retained-worker traces above, not that prefix comparison, establish the
stage boundary. The existing C06 `--revision` path also failed to build relocated
headers; the committed C48 verifier rebases includes and links the source headers.
These were tooling failures, not refuted numerical hypotheses.

FACT: Campaign commands used `python3 tools/fuzz/run.py --plugin radialblur --n 300
--seed S --jobs 1 --shrink-attempts 0 --scratch D/work --report D/report.json
--corpus D/corpus`, with stdout/stderr redirected to scratch logs. Baseline seed1
ran both routes. Fixed campaigns restricted `Adapter.routes=('smart',)` through
a Python launcher; seed1 also set `Adapter.oracle_routes={'smart':'smart'}`.
The exact reproducible launcher is in verify below. Default timeout was 10 seconds.

| Smart measurement | Exact | Mismatch | Refusal | Uncompared |
| --- | ---: | ---: | ---: | ---: |
| Baseline seed1, current parent source | 270 | 0 | 17 | 13 |
| Fixed seed1 initial | 269 | 0 | 17 | 14 |
| Fixed seed1 after case62 recheck | 270 | 0 | 17 | 13 |
| S01 seed102 baseline (archived) | 267 | 1 | 29 | 3 |
| Fixed seed102 | 271 | 0 | 13 | 16 |

`python3 tools/fuzz/verify_radialblur_C48.py --seed 1 --indices 62 --output
orchestra/state/C48-radial-s01-pf32-mismatch/retry1` exited 0, exact at the
30-second limit. Its input/output hashes match the baseline case. Initial reports
are retained unchanged. Uncompared counts include oracle rejection/budget results;
they are not exact claims. Seed102 baseline is S01, not a second parent-source
campaign; intervening admission changes are not attributed to C48.

FACT: Compared matching input hashes and output hashes for every baseline exact
row: seed1 270/270 preserved after the documented recheck; S01 seed102 267/267
preserved. No exact-to-refusal/mismatch or unresolved baseline-exact rows remain.

FACT: `verify_radialblur_C48.py --corpus --revision HEAD --output .../corpus-before`
and `verify_radialblur_C48.py --corpus --output .../corpus-fixed` replayed all 57
retained corpus inputs with F46, one at a time, timeout 30 seconds. Before:
56 exact / 1 mismatch (the S01 witness). After: 56 fresh exact / 0 mismatch / 1 uncompared.
All 57 fixed outputs equal the successful baseline AEX output hashes, including
the previously mismatching S01 case, and all 56 previously exact Mac outputs
retain identical input and output hashes. Baseline and fixed runs exit 1.

The remaining `C46_seed1_case000280.json` oracle reported `reject`: guest execution
stopped before returning at `RIP=0x180002860`. This is the concrete diagnostic;
its internal stop reason is not established as a wall timeout. A separate
`verify_radialblur_C48.py --case tests/fuzz_corpus/radialblur/C46_seed1_case000280.json
--timeout 60 --output .../corpus-retry` also exited 1 with the same oracle rejection.
Both fixed candidate runs succeeded and returned SHA-256
`5a19de28aece7b23b644e5f2533da7f662677e3d6a837b9a96d88a53726487f8`, exactly the
successful baseline AEX output for the identical input and F46 worker.
`C48-evidence/corpus-audit.json` records this retained-reference comparison.
This establishes output preservation without claiming a fresh successful oracle
for that row. This corpus comparison deliberately uses the
same current worker on both sides instead of mixing historical worker math.

FACT: Compressed complete campaign/public reports, paired trace reports, disassembly,
logs and a SHA-256 manifest are in `orchestra/reports/C48-evidence/`.
The source-only comment was moved above the predicate after raw/trace/campaign
builds; the final corpus build uses the final source text. Scratch stayed below
110 MiB before cleanup, disposable build trees were deleted, and all started
candidate/worker processes exited. `git diff --check` passed.

inference:

INFERENCE: The one-column geometry exposed a general size/noise field-ownership
error, not a special one-column sampling or normalization rule. Keeping the size
factor separate allows B150 to retain a nonzero seed when noise makes its later
scatter span zero. Full paired-stage equality and the raw original replay support
this cause. This is a port bug; no new undefined-read semantics or KNOWN_ORIGINAL_BUGS
entry is warranted. Finite emulator and SDK-harness coverage does not establish
all-input or native AE equivalence.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`: use size-only prepass factor without fades.
- `tools/fuzz/verify_radialblur_C48.py`: raw witnesses, independent controls, corpus and bounded rechecks.
- `orchestra/reports/C48-evidence/*`: measured evidence and integrity manifest.
- `orchestra/reports/C48-radial-s01-pf32-mismatch.md`: this report.

verify:

Run from this worktree (choose fresh output paths; each verifier creates its directory):

```sh
D="$PWD/orchestra/state/C48-radial-s01-pf32-mismatch/recheck"
mkdir -p "$D"
python3 tools/fuzz/verify_radialblur_C48.py --sanitize --output "$D/raw" > "$D/raw.log" 2>&1
python3 tools/fuzz/verify_radialblur_C48.py --corpus --output "$D/corpus" > "$D/corpus.log" 2>&1
for S in 1 102; do
  python3 -c "import sys; sys.path.insert(0,'tools/fuzz'); from adapters.radialblur import Adapter; Adapter.routes=('smart',); Adapter.oracle_routes={'smart':'smart'}; import run; sys.exit(run.main())" \
    --plugin radialblur --n 300 --seed "$S" --jobs 1 --shrink-attempts 0 \
    --scratch "$D/seed$S/work" --report "$D/seed$S.json" --corpus "$D/seed$S/corpus" > "$D/seed$S.log" 2>&1
done
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' \
  tools/fuzz/trace_radialblur_smart_C06.py --output "$D/trace" \
  --cases-from orchestra/reports/C48-evidence/trace-before.json --indices 8 > "$D/trace.log" 2>&1
git diff --check
```

Expected: raw 38/38 exact (exit 0); corpus zero mismatches and all 57 outputs
matching the retained baseline AEX hashes (fresh oracle rejection may cause exit 1); both campaigns
complete with zero Smart mismatches; all paired-plane differing counts zero and
public output exact. For corpus comparisons, `corpus-before.json.gz` retains a successful AEX hash
for every input. Match input and worker hashes before comparing fixed outputs
against those references; do not silently treat `uncompared` as fresh exact.
Timeout counts can vary under shared-machine load. Recheck any
formerly exact timed-out index with the committed verifier's `--seed S --indices I`
(30 seconds) before claiming a regression. To reproduce failures, run the raw or
corpus verifier with `--revision d6cd18daa05d1106718faa2594d4fe7a3b089564`;
expect respectively 2 or 1 mismatches and exit 1.

next:
- No output regression remains for this witness or the requested retained comparisons.
- Investigate intermittent original-AEX execution stoppage for C46 seed1 case280;
  current Mac output is exact against the successful same-worker baseline reference.
- Original-HDR full-plane tracing requires a lossless raw-input paired-trace transport;
  current retained full-trace CLI accepts PNG. Native AE qualification remains separate.
