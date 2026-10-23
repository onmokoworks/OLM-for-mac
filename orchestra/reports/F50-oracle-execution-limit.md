status: blocked

summary:
- Identified F46's internal 20-second wall-clock limit, disabled instruction limit, and independent harness limits.
- Prepared an unbuilt candidate patch using 2,000,000,000 instructions per scheduler slice; no numerical implementation changes.
- Two build-location approaches failed at Unicorn's rejection of spaces in the physical build directory; stopped under the worker brief's two-hypothesis rule.
- No F50 executable or INDEX entry exists. Corpus equivalence, S01 completion, and seed-1 outcomes remain unmeasured.
- Committed the candidate patch, build/verification recipes, and actual build-failure evidence; fuzz defaults remain F46.

facts:

FACT — mechanism (read from retained `~/.cache/olm-emu/src-F46/reference-guest`):

- `crates/aex-guest-worker/src/x64.rs:292–299`: `MAX_INSTRUCTIONS = 0` (Unicorn counting disabled), `TIMEOUT_MICROSECONDS = 20_000_000`.
- `x64/engine.rs:1721,1731`: normal Win64 and floating-result calls pass that timeout to `call_win64_with_timeout`.
- `x64/engine.rs:1832–1853`: each call starts an `Instant`; each scheduler resumption receives the remaining part of that same 20-second budget in `emu_start(begin, RETURN_ADDRESS, remaining_timeout_microseconds, MAX_INSTRUCTIONS)`. There are at most 257 scheduler slices (indices 0 through 256).
- `x64/engine.rs:2381–2384`: when emulation returns successfully but RIP is not the return sentinel, the worker emits `execution stopped before the guest returned (RIP=...)`. Thus this text alone does not uniquely identify a timeout, but these production calls have no instruction-count cutoff and do have an internal wall-clock cutoff. F50 did not execute the two cited cases to independently observe their exact stop reason.
- `tools/fuzz/run.py`: default per-subprocess timeout 10 seconds, campaign budget 30 minutes. Replays inherit recorded `case_timeout_seconds` unless explicitly overridden.
- `tools/fuzz/core.py:77–99`: `communicate` uses `min(case timeout, remaining campaign time)`. On expiry it invokes process-group cleanup and returns `budget`, reason `wall timeout`. This is distinct from a worker-reported guest stop.

FACT — candidate, not validated:

- `F50-budget.patch` changes only `x64.rs` and `x64/engine.rs`. Production calls request zero microseconds (Unicorn wall timeout disabled), with 2 billion instructions per scheduler slice. Explicit nonzero timeout callers retain their existing elapsed-time logic.
- The retained 257-slice scheduler bound makes the main loop's instruction ceiling 514 billion per call; this is a per-slice budget, not a cumulative 2-billion-per-call counter. It does not bound time spent in native host callbacks or guarantee a real-time duration under arbitrary load.
- `verify_F50.py` is an **unexecuted** resumable serial recipe: compare both available corpus oracle routes byte-for-byte, re-evaluate S01 DG/Radial rows whose Smart oracle failed, and run DG/Radial seed 1 n300 with both workers. It explicitly requests a 3600-second subprocess watchdog and a 1440-minute campaign budget. Those values are proposed, not measured to exceed the instruction budget's execution duration.
- Current corpus inventory: 769 JSON cases in 11 nonempty directories (23 ToonDilate T13, 61 RadialBlur, 39 Blur, 29 Smoother, 8 Smoother2, 300 ToonDilate, 83 DirectionalBlur, 8 KiraKira, 62 KiraKira T06, 9 ColorKey, 147 DistanceGradation). ColorKeep directory has zero cases. None replayed in this ticket.

FACT — commands and actual outcomes:

1. `python3 tools/emulation/aexcompat_patches/build_F50.py > orchestra/state/F50-oracle-execution-limit/build-driver.log 2>&1` with direct scratch `CARGO_TARGET_DIR`: Python exit 1, underlying cargo exit 101 / CMake build exit 2. Unicorn configure reports `ERROR: main directory cannot contain spaces nor colons`; compilation then reports `Int128`/`__int128` typedef redefinition. Evidence: `F50-evidence/rebuild-spaces-failed.log`.
2. Same command after using `~/.cache/olm-emu/F50-build-scratch` as a space-free symlink to this ticket's scratch: same exit codes and configure/compiler diagnostics. Evidence: `F50-evidence/rebuild.log` and `build-driver.log`. The second build's preceding `memory_pressure` reported 50% free, satisfying the >=30% precondition. Both builds used Cargo/CMake jobs=1 and ran serially. Trailing spaces were trimmed from the committed memory-pressure log.
3. The build script verified the entire retained F46 source tree against committed `F46-evidence/build-manifest.json` before copying it; both attempts passed that assertion and applied the two-file patch.
4. Python `compile(...)` syntax checks for both new scripts passed. `git diff --check` passed before staging. The fresh two-file application check below also passed; it checks patch application only.
5. Parent worker SHA256: `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`. Candidate patch SHA256: `a60866763c08b0e597776cd9a0de2c3027246d2a509524ce726d1f7dc95f32bb`. Other recipe hashes are in `F50-evidence/hashes.json`.
6. Both build processes exited. Both regenerable build trees were removed in `finally`. Failed cache source/output directories and the task-created symlink were removed; INDEX has no `worker-F50-budget` entry. Scratch measured 32 KiB before the small patch-application check. No MAIN, original AEXCompat source, plugin source, corpus expectations, release gates, or ledger edits; no push, stash, subagents, or permission rejection.
7. Executed corpus comparisons: 0. Executed generated cases: 0. Measured first mismatch: none available. No exactness or timeout-resolution claim is made.

inference:

INFERENCE: The internal wall timer explains why an otherwise unchanged guest can stop at different PCs under load. The outer 10-second watchdog independently explains additional uncompared cases. Changing only the outer timeout cannot eliminate F46's internal cutoff.

INFERENCE: A finite instruction budget should remove the worker's production wall-time dependency, but the proposed budget and performance remain unqualified. The candidate must not become the default on this evidence.

INFERENCE: A physically space-free build location is likely necessary for the unchanged Unicorn build system. Both direct worktree scratch and its cache symlink failed at the same configure boundary; no further build-location hypothesis was attempted under the explicit stop rule. A follow-up should resolve that build-location constraint before spending time on replay runs.

changed_files:

- `tools/emulation/aexcompat_patches/F50-budget.patch` — unbuilt candidate.
- `tools/emulation/aexcompat_patches/build_F50.py` — retained failed symlink-based recipe, not a working build claim.
- `tools/emulation/aexcompat_patches/verify_F50.py` — syntax-checked only, no execution qualification.
- `orchestra/reports/F50-evidence/{rebuild-spaces-failed.log,rebuild.log,build-driver.log,memory-pressure.log,hashes.json}`.
- This report.

verify:

Run from this worktree. This verifies candidate patch application without building or editing retained sources:

```sh
python3 - <<'PY'
from pathlib import Path
import shutil, subprocess
root = Path.cwd()
s = root/'orchestra/state/F50-oracle-execution-limit/patch-check'
s.mkdir(parents=True, exist_ok=True)
source = Path.home()/'.cache/olm-emu/src-F46/reference-guest'
for rel in ('crates/aex-guest-worker/src/x64.rs', 'crates/aex-guest-worker/src/x64/engine.rs'):
    target = s/rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source/rel, target)
subprocess.run(['patch', '-p1', '-i', str(root/'tools/emulation/aexcompat_patches/F50-budget.patch')], cwd=s, check=True)
for name in ('build_F50.py', 'verify_F50.py'):
    p = root/'tools/emulation/aexcompat_patches'/name
    compile(p.read_text(), str(p), 'exec')
shutil.rmtree(s)
print('Patch application and Python syntax PASS; no executable validation')
PY
git diff --check
```

Expected: both patch hunks apply, Python syntax passes, exit 0. Re-running the retained build recipe in this checkout is expected to reproduce the recorded path failure, not produce a worker.

next:

- Follow-up: establish an authorized physically space-free build directory (e.g. a disposable build tree inside the requested cache worker installation) or qualify a build-system fix while honoring the scratch constraint. Rebuild, install/register F50, and test deterministic exhaustion plus normal return before long runs.
- Run `verify_F50.py smoke`, `corpus`, `slow`, and `campaigns` serially with logs redirected inside this ticket's scratch. Inspect every uncompared outcome rather than treating it as equality. Confirm instruction budget sufficiency and the watchdog margin; increase only from measured evidence.
- Report every corpus pair, all S01 slow-case transitions, DG/Radial seed-1 exact/mismatch/refusal/uncompared totals, and any newly exposed numerical mismatch. No plugin fix belongs here.
- **Proposal only:** after those validations pass, switch the fuzz default worker to F50 and explicitly adopt the qualified larger harness timeout. Neither switch was applied.
