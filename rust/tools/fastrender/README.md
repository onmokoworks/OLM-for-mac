# Fast oracle feasibility measurement

Historical investigation below predates AEXCompat PR #1828. The follow-up
implementation and current qualification are documented in the
[oracle README](../oracle/README.md#resident-rendering); the proposal and original
measurements here remain unchanged as historical evidence.

**Result: an AEXCompat change is needed.** Existing resident modes retain a
sequence across frames and do not provide an independent-case reset. The
oracle therefore has no new `--resident` option. Its implementation and public
tests are unchanged. The requested design and patch draft are in
[`AEXCOMPAT_PROPOSAL.md`](AEXCOMPAT_PROPOSAL.md).

## Reproduce

Requires the oracle's Python, NumPy and Pillow environment and the installed
Windows harness. From the repository root:

```powershell
python rust/tools/fastrender/measure.py --out rust/tools/fastrender/runs/new-measurement --repeats 3
python -m unittest discover -s rust/tools/fastrender -p 'test_*.py' -v
python -m unittest discover -s rust/tools/oracle -p 'test_*.py' -q
```

The destination must be new. `--harness`, `--originals` and `--seed` override
defaults. Repeats are bounded to 1..10. The tool always runs serially (jobs=1),
passes `--headless`, and uses the oracle's private Windows Job ownership,
timeout, descendant cleanup and child wait. It neither installs nor copies
originals. No daemon, GUI, AE, Git operation or AEXCompat build is involved.
`runs/` and Python caches are ignored; compact evidence is retained separately.

## Worked run on this machine

```text
python rust/tools/fastrender/measure.py --out rust/tools/fastrender/runs/baseline-20261112 --repeats 3
exit 0
all_pairs_exact: true
33 pairs / 66 render invocations
12 resident diagnostic sessions / 48 frames
fastrender unittest: 6 passed
existing oracle unittest: 28 passed
```

All ten use **untouched defaults**, three 97×61 inputs with recorded seeds
20261112, 20261113 and 20261114; downsample 1. Nine use Smart8, OLMSmoother
Classic8. Both sides use the same original file. OLMBlur also has three
320×180 pairs. These are baseline self-comparisons, not port qualification or
resident/process equivalence. No minima/maxima/random parameter sweep was run.

| Original | Exact pairs at 97×61 | Median per-side wall ms | Reported session interval ms | Outside interval ms |
| --- | ---: | ---: | ---: | ---: |
| ColorKeep | 3/3 | 429.5 | 102.0 | 328.0 |
| DistanceGradation | 3/3 | 492.5 | 102.0 | 388.0 |
| OLMBlur | 3/3 | 422.0 | 101.0 | 321.0 |
| OLMColorKey | 3/3 | 422.0 | 101.5 | 321.0 |
| OLMDirectionalBlur | 3/3 | 422.0 | 101.0 | 321.0 |
| OLMKiraKira | 3/3 | 796.0 | 302.0 | 493.5 |
| OLMRadialBlur | 3/3 | 422.0 | 101.5 | 320.0 |
| OLMSmoother | 3/3 | 422.0 | 101.0 | 321.0 |
| OLMSmoother2 | 3/3 | 422.0 | 101.0 | 321.0 |
| OLMToonDilate | 3/3 | 429.5 | 101.0 | 328.5 |

Each timing column is aggregated separately; their medians need not sum.
The reported session interval is `worker_diagnostics.elapsed_ms`, including
frame and close/exit collection. It is **not render-selector time** or a
separate measurement of module load/global setup. The JSON field
`render_worker_lifetime_ms` means this reported interval. The outside residual
includes discovery, harness startup, session-open preparation and image/report
I/O. Standalone controls measured help at 78 ms and inspection at 250 ms;
these are overlapping comparison controls, not extra additive phases.

OLMBlur 320×180: baseline 422 ms/side; existing resident diagnostic session
open 63.570 ms, cold frame 43.191 ms, warm frame 9.855 ms. The **10.83×** ratio
of `(open + cold) / warm` measures the existing repeated-frame facility.
The proposal gives a complete phase table and an explicit sensitivity estimate
for future independent cases. A measured oracle speed-up is not available.

## Evidence and limits

[`evidence/measurement.json`](evidence/measurement.json) records timing data,
binary/source hashes, test counts, raw-log hashes and owned-PID observations.
Full inputs, requests, output PNGs and process logs are local-only under
`runs/baseline-20261112/`. `runs/discovery/` retains help, CLI contract and an
initial performance probe; `runs/pilot/` contains a preliminary OLMBlur pair.
Pilot data is excluded from the 33-pair table.

Harness SHA-256:
`17dea194b332711ebc9c003eaa6ba4aa61f6b068e1a081a8d8f54f39d617e62d`.
Performance diagnostic worker SHA-256:
`0481df5fa425af28f0e8a39ea9386185de13656c3c9d488042bed2244bdf8302`.
The ordinary render reports warn `source_newer_than_worker`. The results bind
these existing executables; no rebuild or source/binary equivalence is claimed.

Performance diagnostics use repeated opaque XY/XOR inputs and retained sequence
state, omit explicit oracle host/render context, and save no rendered images.
Their built-in memory-growth advisory is retained. This bounded measurement
does not qualify long-session memory stability, any 16/32-bit resident output,
varied parameters/layers/downsample, actual Rust candidate equivalence, or native
AE semantics. The proposal lists the behavioral tests and all-ten, both-side
byte-equivalence gate required before adding the opt-in oracle mode.
