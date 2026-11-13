# Original/Rust CPU render benchmark

Run from the repository root with Python, NumPy and Pillow installed:

```powershell
python -X utf8 rust/tools/bench/bench.py --out rust/tools/bench/runs/new-run --frame-cap 20 --batch-cap 130
python -m unittest discover -s rust/tools/bench -p 'test_*.py' -v
python rust/tools/bench/report.py rust/tools/bench/runs/new-run/evidence.json --out rust/tools/bench/evidence/new-run.json
python rust/tools/bench/audit.py rust/tools/bench/evidence/new-run.json --out rust/tools/bench/evidence/new-run-audit.json
```

`--staged` selects an external directory containing all twelve Rust `.aex`
files. The default is the main-build staging directory supplied for Job B-speed.
`--harness` selects the already-built AEXCompat harness. Six originals are
selected uniquely from `upstream_20261112/extracted/*/*/Plugins/64/2025/`;
the unchanged six come from `ghidra_windows_aex`. No originals are copied.
Every executable is SHA-256 bound. Rendered frames are deleted right after hashing (their digests are the evidence); pass `--keep-frames` to retain them for diagnosis. `--only OLMBlur` and `--sizes 1x1,960x540`
allow bounded subsets. Always use a new output directory.

Each cell uses one resident `--render-request-batch` per side: one discarded
warm-up and five measured frames, all independent fresh sequences with shared
module/global state. Original-first and Rust-first orders alternate by cell.
Execution is strictly serial; the harness is explicitly assigned normal process
priority before resuming. This does not limit plug-in-internal threads. Oracle
private Windows Jobs own all descendants, verify active count zero on cleanup,
and wait for the child, including on failure or interruption. There is no AE,
GUI, daemon, installation, or global process-name kill.

The default finite caps are 10 seconds per frame, 70 seconds per side batch,
and 28 minutes for starting cells. A cell already started finishes both sides,
so the campaign may exceed the start budget by at most two batch caps plus
cleanup/preparation. Failed/timeout cells remain incomplete. No partial batch
median, invented timing, or automatic replacement run is accepted.
The reproduction command above allows the measured expensive Kira preset to
finish at 1080p. Active original RadialBlur currently fails the resident
protocol even with ample time; exit 1 and incomplete heavy rows are expected
with the recorded harness. See [the measured report](../../BENCHMARK.md).

Inputs are deterministic oracle PCG64 images (seed 20261113): horizontal red
gradient, two green regions, seeded blue, and cycling alpha 0/1/32/128/255.
The same image is repeated for the six frames, measuring a warm-cache fixed
workload, not six independent images. PNG-derived deep input is not arbitrary
HDR. UV Map gets a same-size independently seeded texture in slot 1, including
its default case; other default assignments are empty. Downsample is 1,
straight input, software CPU rendering, color management off. Smoother uses
Classic8/16, all others Smart8/16/32. Both 1920×1080 and 960×540 run the full
matrix; 1×1 runs the same presets/depths as fixed-cost controls.

`HEAVY` and `assignments()` define bounded expensive presets. Evidence includes
exact requests and original parameter metadata for every edited slot. Palette
effects use deterministic distinct colors; heavy UV Map raises trilinear
smoothness to 1 (there is no iteration/radius setting). Radial uses Rotation,
strengths 30/15, quality 10, deliberately below the quality-50 extreme. Kira's
invalid declared gain default is never explicitly assigned or clamped.
`--radial-zoom` selects a separate active Zoom preset (strengths 80/40,
quality 10) for a bounded alternative when Rotation cannot complete in the
resident host. It does not silently replace failed Rotation observations.

`report.py --replacement path/to/evidence.json` replaces the entire matrix of
each plug-in in that follow-up, checks matching harness/worker identities and
cell keys, and preserves the first campaign's observations under `superseded`.
It never splices only favorable frames into a median. Failure annotations
distinguish internal frame deadlines from outer process timeouts and preflight
or protocol errors. `audit.py` verifies raw-report hashes, all accepted PNG/deep
files, actual dispatch depths, loaded worker hashes, and recomputed statistics.

The primary clock is `performance_diagnostics.render_selector_ns`, converted
to milliseconds. It excludes process startup but includes host work inside
selector dispatch and callbacks. Worker-render and broker-frame clocks are
retained separately. Table entries show **median (minimum)**. Ratios divide
Rust median by original median; below 1 means faster. `report.py` also subtracts
each side's matching 1×1 median from its five full-image samples. Negative
adjusted samples are marked unresolved, never clamped. This estimates fixed
cost only: 1×1 still runs plug-in code, and image-dependent copying, allocations,
callback validation and dispatch costs remain. It is not a pure kernel clock.

Whole-Job CPU time (user + kernel, including discovery, harness and worker) is
divided by whole-batch wall time. A ratio well above 1 supports concurrent CPU
work, but a ratio below 1 cannot rule out short parallel phases. These are not
per-frame CPU samples. No affinity or machine-wide isolation is applied.

Every warm-up and measured original/Rust output is compared by PNG-file hash
and native deep-sidecar hash, after validating complete batch population,
IDs, indices, route, admitted plug-in hash, case cleanup and final global
close. Mismatches remain visible alongside their observed timing; they cannot
support a claim of equivalent performance. This is a sanity check, not a new
qualification or native AE acceptance.

Raw requests, manifests, reports and images stay in ignored `runs/`; only the
compact evidence JSON and human report are committed. The raw process report
hashes in evidence bind the full harness diagnostics and owned PID records.
Unit tests cover units, ordering, invalid/partial reports, medians, minima and
overhead subtraction. They do not launch the harness.
