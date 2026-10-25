status: blocked

summary:
- Required R10 native differential driver rejects `olmsmoother2` before building or rendering.
- Its plugin registry and heavy-preset mapping cover six other plugins, not Smoother2.
- Extending that driver is outside this ticket's explicit source-change boundary.
- No production edits or threading changes were made; no performance or exactness improvement is claimed.

facts:
- Starting commit: `5ed31e8e347b7b9ab128d539244e51d664eae6a1`; branch: `orch/P07b-smoother2-threading`; initial working tree clean.
- Read `AGENT_GUIDE.md`, the Smoother2 decision-matrix restrictions and palette cap in `notes/CONFORMANCE_LEDGER.md`, emulation GOTCHAS, R10 report, shared parallel helper, and Smoother2 fuzz adapter. Inspected compatibility-plan performance references.
- `memory_pressure | tail -5`: system-wide memory free percentage was 61%.
- `rg -n 'OLM_REFERENCE_BUILD|PLUGINS =|HEAVY =' tools/perf/ref_vs_fast.py mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`: driver lines 24/26 contain six plugins, excluding Smoother2; no `OLM_REFERENCE_BUILD` occurrence in this plugin source.
- `core/olm_parallel.h` exists and provides serial reference and GCD fast implementations. P07a helper availability is not the blocker.
- Ran the verify command below with stdout/stderr redirected to `orchestra/state/P07b-smoother2-threading/ref-fast-preflight.log`. Python exited 2 with `argument --plugin: invalid choice: 'olmsmoother2'`. Accepted choices: `olmdirectionalblur`, `radialblur`, `olmblur`, `olmcolorkey`, `olmsmoother`, `olmkirakira`.
- Rendered comparisons: 0. Output hashes and first pixel mismatch: unavailable because argument parsing failed before rendering.
- No benchmarks, sample profiles, builds, unit tests, oracle fuzz, corpus replay, TSan, or concurrent-render tests ran. No background processes or build trees were created. This was an argument-validation check, not a timing run.

inference:
- The R10 merge is present, but its required differential tooling has not yet been extended to this ticket's plugin. Acceptance cannot be completed through the required command within the allowed file scope.
- This is a tooling/scope blocker, not evidence of a numerical defect or unsafe parallelism. Profiling and optimization remain unattempted pending that dependency.

changed_files:
- `orchestra/reports/P07b-smoother2-threading.md`

verify:
```sh
mkdir -p orchestra/state/P07b-smoother2-threading
PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/orchestra/state/P07b-smoother2-threading" \
  python3 tools/perf/ref_vs_fast.py --plugin olmsmoother2 \
  --small 1 --hd 0 --uhd 0 --parallel 1 2 8 --jobs 1 \
  --scratch "$PWD/orchestra/state/P07b-smoother2-threading/ref-fast" \
  > orchestra/state/P07b-smoother2-threading/ref-fast-preflight.log 2>&1
echo "$?"
tail -1 orchestra/state/P07b-smoother2-threading/ref-fast-preflight.log
```
Expected: exit 2 and invalid plugin choice, with no builds or comparisons.

Before/after timing table (no measurements made):

| Cases | Before | After |
| --- | --- | --- |
| Default and heaviest corpus; 1080p/4K; 8/16/32 bpc | Not run | Not run |

next:
- Extend R10's `tools/perf/ref_vs_fast.py` plugin registry and appropriate Smoother2 heavy-case selection, or explicitly expand this ticket's permitted files to do so. Include default and heavy cases at all depths, at 1080p/4K, with caps 1/2/8.
- Resume P07b with lock-protected baseline/sample, unit baseline, dominant-stage threading and faithful reference form, threshold measurement, and all requested differential/oracle/replay/TSan/concurrency acceptance runs. Preserve the existing ledger and release gates.
