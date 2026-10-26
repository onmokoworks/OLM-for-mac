status: blocked
summary:
- Reproduced all seven nightly DistanceGradation witnesses: six Smart refusals and one PF32 mismatch.
- Fixed the general symmetric five-tap Gaussian horizontal reduction; the mismatch is now byte-exact.
- Independent original-AEX Gaussian matrix: 2020/2020 float words exact; labelled seven-witness set replays true on both routes.
- Reverted provisional bilateral admission changes after two hypotheses failed wider direct-original probes.
- Stopped under the ticket's two-refuted-hypotheses rule; full acceptance is incomplete.

facts:

Base commit: `114799ee6ba3330a5a4a60824cc06508c9360826`.
Branch: `orch/N02-olmdistancegradation-nightly-20261025`.
Original AEX SHA256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.
Final production source SHA256: `c2b7708d75e3275d6d318284738e55f40b797fdce3fbde0cf02d78427f5ca7cc`.
No MAIN, emulator source/worker, release gate, ledger, or other plugin changes.
No pushes, stash, history rewrites, or permission rejections.

`sh orchestra/reports/N02-evidence/replay.sh` uses standard `tools/fuzz/run.py
--replay`, jobs 1, and each witness's matching sampler flags and hash-bound
worker. All seven original Smart failure signatures reproduce. The initial
odd-even invocation omitted `--max-size 1920`; rerunning with that and
`--size-max-height 1080` completed successfully. Baseline results are committed
as `N02-evidence/baseline-*.json.gz`. Nightly saved only the target route; the
standard replay records Classic as well, so old saved-result equality is not
claimed. `witness-summary.json` preserves both routes.

| Witness prefix | Sampler | Baseline Smart | Final Smart | Final Classic |
|---|---|---|---|---|
| e9fe643c | default | refusal | refusal | exact |
| ac576b49 | realistic | refusal | refusal | exact |
| e3f91969 | realistic | refusal | refusal | mismatch |
| 1aeb5797 | realistic-v2 | refusal | refusal | exact |
| 5ba5b90d | realistic-v2 | refusal | refusal | mismatch |
| cce92f24 | realistic-v2 | mismatch | exact | mismatch |
| d8611b58 | odd-even-v1 | refusal | refusal | exact |

**Gaussian boundary.** The original public Smart mismatch has five differing
PF32 words, first word 12 / byte 48: original LE `bd61a43e`, Mac `bc61a43e`.
`gaussian_probe.py` captures the production pre/post-filter scalar planes and
calls original `cvSmooth` at `1812864d0`, with no numerical detour, on the same
pre-plane using a 5x3 Gaussian kernel. Baseline post-filter has four differing
words, first word 3: original `863cb73e`, Mac `883cb73e`. Original execution uses
22144 instructions. The corrected reduction has zero differing filter words
and zero differing public output bytes (192 bytes).

The embedded OpenCV decomp identifies `SymmRowSmallFilter<float,float,...>` and
its symmetric-kernel size <=5 selection (`N02-evidence/static.txt`, including
original decomp hash and line numbers). The five-tap row reduction is center,
near pair, far pair, with separate float products/additions. The old Mac path
used a sequential five-product sum. Both square and rectangular Smart Gaussian
paths now use the symmetric reduction; Classic and R10 reference/fast selection
are unchanged. No output-byte correction or tolerance was introduced.

Independent direct-original matrix: widths/heights 1x7, 4x3, 6x17, 17x9, 33x7;
horizontal kernel 5 and vertical kernels 1/3/5/7; seed 26026 random FLOAT32
fields. All 20 cases, 2020 float words, match exactly. See
`gaussian-before.json`, `gaussian-after.json`, and `gaussian-matrix.json`.
Diagnostic setup first encountered the old variant helper's geometry-shim
redefinition and the loader's unsupported stack-float argument API; the final
probe uses the geometry shim and integer zero bit patterns in stack slots.
These were harness errors, not numerical hypothesis results.

**Bilateral investigation and stop.** A provisional general admission patch
admitted fractional Power in existing unblurred/radius-one paths, the declared
radius range through 4096, and radius-two scalar rendering without its old
shape restriction. All seven Smart witnesses became exact, with unchanged
Classic results (`provisional-*.json.gz`). Its source is retained as
`rejected-admission-candidate.cpp.gz`, SHA256
`26afd237a8b5a266693cddc42903ce1ba3b412f20522eaabd4f57759a05b9afb`, verified against
actual replay build provenance. It is NOT the final implementation.

The direct IPP probe invokes original init `18000c280` and filter `18000c2f0`
on independent seed-26026 fields, radius two:

1. Hypothesis: the existing specialized scalar radius-two body can cover all
   image shapes. It matches 1x1, 4x9, 5x17, 6x17, 7x17, 8x17, 9x17, but fails
   17x9 at 62 words and 33x7 at 92 words. First 17x9 difference: word 0,
   original `9ebbf03e`, Mac `a0bbf03e`.
2. Hypothesis: selecting the already recovered vector exponential and exponent
   order in vector-dispatched tiles suffices. It still fails 17x9 at 42 words
   (first word 9, original `b7dde23e`, Mac `b8dde23e`) and 33x7 at 70 words.
   Narrow shapes remain exact. See `bilateral-scalar.json` and
   `bilateral-vector-exp.json`.

No paired internal numerator/denominator boundary was obtained between these
hypothesis tests; both compare the same post-filter boundary. This triggers
the ticket stop rule. All provisional bilateral/source-admission changes were
removed. No uninitialized original read was established, so no original-bug
classification or KNOWN_ORIGINAL_BUGS edit is justified.

One provisional-source default campaign finished before stopping:
`run.py --plugin olmdistancegradation --jobs 1 --seed 26026 --n 200
--shrink-attempts 0 --budget-minutes 90`, with scratch/corpus/report paths from
`N02-evidence/campaigns.sh`. Smart: 194 exact, 0 mismatch, 1 refusal with an
unsuccessful original, 5 uncompared; original Smart rejects: 6; Mac-only
refusals: 0. Classic: 10 exact, 190 mismatch. This is not final-source acceptance.
Seed 26027 started but was terminated; no completed result is claimed. The
campaign shell and all descendant processes were stopped.

Final-source labelled-set verification:
`sh orchestra/reports/N02-evidence/verify-retained.sh` completed 1 default,
2 realistic, 3 realistic-v2, and 1 odd-even cases; all four reports have
`replay_matches_saved: true`. Both routes are recorded. These saved expectations
explicitly retain six Smart refusals; replay true does NOT mean all cases exact.

Acceptance still NOT run/completed: three fresh n200 seeds per failing sampler
on final source; default seed1 n300 exact-to-non-exact comparison; replay of all
older corpora; `tools/perf/ref_vs_fast.py --plugin olmdistancegradation`.

inference:

The Gaussian discrepancy is caused by arithmetic grouping at a demonstrated
filter boundary. The bilateral failures indicate missing vector radius-two
accumulation behavior in addition to exponential selection. Decomp of
`1806b7240` shows different grouped numerator/denominator ordering, but that
ordering has not been paired to live registers, implemented, or verified here.
Admitting the wider domain based only on the seven reduced witnesses would be
unsound; the final change therefore preserves the six refusals.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`: Smart five-tap Gaussian reduction only.
- `tests/fuzz_corpus/olmdistancegradation_N02/`: seven labelled witnesses, original inputs and nightly history, both final route expectations.
- `orchestra/reports/N02-evidence/`: reproducible probes/replay scripts, static excerpt, compressed replay/campaign evidence and rejected candidate source.
- `orchestra/reports/N02-olmdistancegradation-nightly-20261025.md`.

verify:

From this worktree (all scratch remains within this ticket):

```sh
export TMPDIR="$PWD/orchestra/state/N02-olmdistancegradation-nightly-20261025"
mkdir -p "$TMPDIR"
export OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
sh orchestra/reports/N02-evidence/verify-retained.sh
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" orchestra/reports/N02-evidence/gaussian_probe.py > "$TMPDIR/gaussian-verify.log" 2>&1
"$py" orchestra/reports/N02-evidence/bilateral_probe.py > "$TMPDIR/bilateral-scalar-verify.log" 2>&1
"$py" orchestra/reports/N02-evidence/bilateral_probe.py --vector-exp > "$TMPDIR/bilateral-vector-verify.log" 2>&1
git diff --check
```

Expected: all seven saved expectations replay true, with the route statuses
above; Gaussian 20-case/2020-word matrix and public witness have zero differences.
The two bilateral diagnostic commands intentionally report the documented
62/92 and 42/70 word failures; they do not modify production source or claim a pass.

next:

Follow-up ticket: capture paired vector radius-two weights and grouped sums in
`1806b7240`, restore its arithmetic and dispatch, then reconsider the retained
admission patch and the six refusal witnesses. Run all original N02 acceptance
checks after that fix. This ticket is blocked, not ready for a full-conformance
merge claim; the isolated Gaussian correction is reviewable separately.

Final housekeeping: diagnostic Python syntax and `git diff --check` pass.
The committed vector-exponential probe was rerun after restoration and reproduced
42/70 differing words. Regenerable scratch build directories were deleted;
remaining scratch is below 5 MiB. No ticket render process remains.
