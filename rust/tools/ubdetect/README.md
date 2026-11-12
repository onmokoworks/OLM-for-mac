# Original undefined-read / instability classifier

`ubdetect.py classify --case CASE_DIR` consumes an oracle `case.json`, verifies
executable and asset hashes, and runs fresh sequential headless workers. It
returns `original_ub`, `stable_mismatch`, or `inconclusive`, with raw renders,
pixel masks, memory events, process records and a machine-readable verdict.
Oracle and AEXCompat sources are not modified. No AE, GUI, attach-to-PID,
installation, service, or plug-in binary modification is used.

Requirements: Windows x64 Python 3.11+, NumPy, Pillow, pefile, and the sibling
oracle/record/witness Python modules. No native witness build is required.
The Cargo manifest is only a marker for the existing `tools/*` workspace glob.

```powershell
python rust/tools/ubdetect/ubdetect.py classify --case CASE_DIR --repeats 5 --out rust/tools/ubdetect/runs/new-result
python -m unittest discover -s rust/tools/ubdetect -p test_ubdetect.py -v
python rust/tools/ubdetect/validate_real.py --out rust/tools/ubdetect/runs/new-qualification
```

`CASE_DIR` must be an existing oracle case, not its parent campaign. Output
directories must be new. Defaults: five original and five candidate renders,
one read-only debug control, then two interleaved runs of each of two fill
patterns when a matching profile exists. Every planned trial runs; there is
no stop-on-first-mismatch or cherry-picking. All renders are sequential (one
active worker tree). `--timeout` is both process and host frame deadline,
default 120 seconds, maximum 600. `--repeats` accepts 2–100.

`--profile auto` selects a binary/route-bound known profile; `none` disables
instrumentation; a JSON path supplies a reviewed custom contract.
`--patterns 00000000,3f3f3f3f` and `--poison-repeats 2` control the differential.
An unknown binary still gets stability checking; there is no automatic search
for arbitrary uninitialized addresses. New memory layouts require a profile.

## Oracle module API and verdict semantics

```python
import sys
sys.path.insert(0, "rust/tools/ubdetect")
from ubdetect import classify
report = classify(case_dir, repeats=5, out=new_directory)
print(report["verdict"])
```

The pure `decide()` function is also exposed for consumers testing verdict
policy without launching workers. CLI stdout is one compact JSON result;
progress goes to stderr. Exit 0 means a completed decisive classification
(`original_ub` **or** `stable_mismatch`), 2 means inconclusive/setup failure,
and 130 means cancellation. These codes are **not** oracle pass/fail codes.

* `original_ub`: original-route outputs vary with unchanged assets, or a
  reviewed undefined-memory differential is repeatable, or an original
  instruction is observed reading outside its binary-grounded object bounds.
  The `reason` distinguishes these evidence types. Nondeterminism alone
  establishes original-route instability, not the root cause inside the host
  versus plug-in. The three supplied cases additionally have direct poisoning
  evidence; the two blurs have address traces.
* `stable_mismatch`: successful finite trials give one original output and one
  different candidate output, with no observed original instability/UB.
  This does not prove absence of undefined behavior in untested memory/paths.
* `inconclusive`: incomplete render/cleanup evidence, unstable candidate only,
  or an exact comparison (`reason: no_mismatch`). Exact cases are deliberately
  not called `stable_mismatch`; this three-verdict interface has no `exact` enum.

A UB verdict does not automatically excuse every candidate difference. The
report counts mismatch pixels outside observed variation/poison influence;
`automatic_mismatch_exclusion` also requires a stable candidate and complete
pixel support. Even that field is measured pixel localization, not a proof
that no second candidate bug exists at those same pixels. Baseline mismatches
are preserved; these runs are never added to original campaign exact totals.

## Evidence and intervention scope

`verdict.json` records identities, all output hashes, distinct counts, trials,
coverage and paths. `reference-variation`, `candidate-variation`, `mismatch`
and `poison-difference` have PNG masks plus compressed NPZ boolean arrays
containing **every pixel**, not a truncated coordinate list. Pixels use the
oracle's decoded 8-bit PNG samples, native 16-bit words or raw 32-bit words;
signed zero and NaN payload changes remain differences. PNG file encoding is
not compared. Raw outputs, stdout/stderr and `process.json` live in each trial.

Same-pattern output must be constant across all its repeats before different
patterns count as proof. Otherwise the between-pattern mask is exploratory
only and `pattern_dependence_proven` is false. Observer output is compared
against the uninstrumented population and kept separate from that population.
`unobserved_hooks` exposes routes that did not execute requested probes.

[Profile contracts](profiles/README.md) explain exact RVAs and byte ownership.
Distance's classic local stack fields are filled before use. Blur table reads
are poisoned only outside the 101-float table, then restored immediately after
the read while siblings remain suspended. `radial-host.json` separately fills
fresh PF Handle Suite buffers before initialization. Generic hooks also support
world padding, reviewed param/handle spans and allocator returns.

Full automatic host padding / arbitrary / param-handle coverage needs the
[harness fill proposal](HARNESS_PROPOSAL.md). No real campaign for those
unexposed scopes is claimed. Do not apply a blanket fill to initialized objects.

Both normal and instrumented workers are created suspended and assigned to a
private kill-on-close Job Object. Only their PIDs/descendants are controlled.
The debug path drains exit events, verifies the job active count reaches zero,
and waits for the retained process handle, including timeout/error paths.
The 18-test unit suite includes a real Windows debugger timeout cleanup check.

## Worked real run on this machine

Windows x64, November 12, 2026. Full raw data are local-only under ignored
`runs/qualification-final/`; compact results are in `evidence.json`. Reproduce
with `validate_real.py` above. It refreshes **copies** of historical oracle
case manifests with current executable identities, preserving input/request
hashes and historical provenance. Ordinary classify never silently accepts
a changed binary. The harness now has SHA-256
`17dea194b332711ebc9c003eaa6ba4aa61f6b068e1a081a8d8f54f39d617e62d`;
the historical saved manifests used `81676eae...`.

Observed final command:

```powershell
python rust/tools/ubdetect/validate_real.py --out rust/tools/ubdetect/runs/qualification-final
# exit 0; 9/9 cases satisfy their assertions; 84/84 render trials succeed
```

| Case | Verdict / reason | Distinct originals (3 trials) | Poison-dependent pixels |
| --- | --- | ---: | ---: |
| Distance classic8 | original_ub | 2 | 21 |
| Directional Smart8, negative offset | original_ub | 2 | 10 |
| Radial Smart32, negative offset | original_ub | 2 | 8 |
| Four exact controls | inconclusive / no_mismatch | 1 each | 0 in the two instrumented controls |
| Deliberate Rust output-byte bug | stable_mismatch | 1 | Not instrumented |
| Radial host-suite fill control | inconclusive / no_mismatch | 1 | 0 |

Directional's observer recorded indices -2/-1 at `0x37f3/0x37f8`.
Radial's observer recorded -3..-1 at `0x95cd` and -4..-1 at `0x95d8`.
All 84 trial records verify cleanup; all transient poison events verify
restoration. The separate 18-test unit suite passes, including timeout cleanup.

The suite uses three original/candidate repeats and two repeats per pattern.
It requires the three known cases to return `original_ub` **and** show
repeatable poison dependence, and requires actual OOB events for both blurs.
Controls cover Blur Smart8, Directional Smart16, Radial Smart32 and a Rust
Smoother Classic8 forwarding wrapper. The deliberate Rust variant in
`bug_fixture.rs` flips one output byte after a successful Classic8 render;
the otherwise identical forwarding wrapper is an exact control. Only new
test DLLs receive the PiPL resource from the existing **Rust** Smoother;
the original binaries are never copied. Production Rust files are untouched.

The host-suite control changes only Radial Noise Offset to zero and fills its
1,860-byte plane plus 404-byte table with each pattern: no output pixel changes.
This tests live host-suite buffers independently of the invalid-read probe.

All claims are AEXCompat CPU observations, not native AE/macOS qualification.
Distance classic8 is explicitly a non-AE debug route. Runtime instrumentation
changes scheduling; a read-only observer is evidence about this case, not a
universal timing-transparency guarantee. No commits or pushes are performed.
