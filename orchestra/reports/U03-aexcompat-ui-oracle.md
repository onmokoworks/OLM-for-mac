status: blocked
summary: |
  Created the requested AEXCompat worktree and branch from current origin/main.
  Two Release build attempts failed in Unicorn configure/C compilation before guest Rust compilation.
  Direct scratch and a space-free symlink to that scratch both hit the same whitespace-path rejection.
  Stopped under the ticket's two-refuted-hypotheses rule; removed the uncompiled implementation draft.
  No UI oracle, EVENT/UPDATE witnesses, installed worker, or plugin changes are delivered.

## facts

- AEXCompat worktree: `/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-olm-U03`.
- Branch: `olm/U03-ui-session`; starting SHA `8d102ae455ecab5483a243f459c3cc529823b70c`.
- Final AEXCompat documentation SHA: `f402b7713c81ef235f5899621406841c3e8df1c5` (reviewed documentation-only change).
- Read shared `AGENT_GUIDE.md`, U01 survey/ABI plan, emulation `GOTCHAS.md`, compatibility analysis plan, relevant decision-matrix plugin rows, and AEXCompat `AGENTS.md` / `CLAUDE.md`.
- `git fetch origin` exited 0. Requested `git worktree add ... -b olm/U03-ui-session origin/main` exited 0. Main's existing untracked handoff ZIP was left untouched.
- `gh issue list --state open --limit 100` returned 34 rows; `gh pr list --state open --limit 100` returned no rows. No claim comments, PRs, pushes, or other external messages were posted. The user explicitly overrides the repository's posting requirements.
- `memory_pressure` before the builds reported **55%** and **56%** system-wide free, above the required 30%.
- Rust toolchain pin: **1.93.1**. `clang --version`: **Apple clang 17.0.0 (clang-1700.6.4.2)**, target `arm64-apple-darwin24.6.0`.
- Both builds used **one job**, sequentially. Both exited **101**, in `unicorn-engine-sys v2.1.5`'s custom build command. Neither reached guest Rust compilation or a behavioral self-test.
- First diagnostic in both configure logs: `ERROR: main directory cannot contain spaces nor colons`. Subsequent C error: `qemu/include/qemu/int128.h:150:16: error: typedef redefinition with different types ('Int128' (aka 'struct Int128') vs '__int128')`.
- `qemu/configure` checks both `source_path` and `$PWD` for whitespace/colons. The second CMake invocation names the space-free symlink path, yet configure emits the same rejection.
- Build target size after both attempts: **172 MiB**, measured with `du -sh`. No reference worker was rebuilt in place; `~/.cache/olm-emu/INDEX.json` was read but not changed.
- Full scratch log SHA256:
  - `build.log`: `bbe639e64de250a958aaec169b74aad469e3631ad11f735f90b2d11cf9994718`
  - `build2.log`: `4f30591d41a7bfc5a86a33c0a8984c1503462cd2be832135a485e768034a4147`
- A draft of an explicit UPDATE session and ParamUtils recorder was written while the dependency build ran. It was **not compiled or executed** and was removed before delivery. No production source changes remain in either repository.
- Witnesses: **0**. Original EVENT dispatches: **0**. Original UPDATE dispatches: **0**. Pixel/draw mismatch count and first mismatch: **not measured**, not zero.

### Exact build commands run

From the AEXCompat U03 worktree, first:

```sh
mkdir -p '/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/U03-aexcompat-ui-oracle/orchestra/state/U03-aexcompat-ui-oracle/build-tmp'
TMPDIR='/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/U03-aexcompat-ui-oracle/orchestra/state/U03-aexcompat-ui-oracle/build-tmp' CARGO_TARGET_DIR='/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/U03-aexcompat-ui-oracle/orchestra/state/U03-aexcompat-ui-oracle/target' cargo build --release --locked --manifest-path guest/Cargo.toml -p aex-guest-worker -j 1 > '/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/U03-aexcompat-ui-oracle/orchestra/state/U03-aexcompat-ui-oracle/build.log' 2>&1
```

Then:

```sh
ln -s '/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/U03-aexcompat-ui-oracle/orchestra/state/U03-aexcompat-ui-oracle/target' /Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-olm-U03-target
memory_pressure
TMPDIR='/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/U03-aexcompat-ui-oracle/orchestra/state/U03-aexcompat-ui-oracle/build-tmp' CARGO_TARGET_DIR=/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-olm-U03-target cargo build --release --locked --manifest-path guest/Cargo.toml -p aex-guest-worker -j 1 > '/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/U03-aexcompat-ui-oracle/orchestra/state/U03-aexcompat-ui-oracle/build2.log' 2>&1
```

## inference

- Hypothesis 1: the current guest Release build can use the mandated scratch directory directly. **Refuted:** configure rejects whitespace before the guest compile.
- Hypothesis 2: a space-free symlink to that same scratch avoids the rejection without violating the scratch rule. **Refuted:** identical rejection and downstream compiler error; no new execution boundary.
- The likely cause is physical path resolution below Cargo/CMake, but the precise subprocess mechanism was **not traced**. The downstream `Int128` error may be caused by missing configure output; this causal interpretation has not been tested independently.
- Further compiler flags, vendored configure changes, relocation, or cached-build substitution would be a third hypothesis without a new boundary. The explicit ticket stop rule requires reporting the blocker now.

## changed_files

OLM:

- `orchestra/reports/U03-aexcompat-ui-oracle.md` — this report.

AEXCompat branch `olm/U03-ui-session`:

- `docs/olm/U03-ui-session-build-blocker.md` — portable reproduction, observed diagnostics, and stop boundary.

No `tests/ui_oracle/` traces were created because no UI execution occurred. No OLM plugin, release gate, ledger, main checkout content, registered worker, or cache index was modified.

## verify

Documentation validation, from each respective worktree:

```sh
git diff --check
git status --short
```

Expected after final commits: exit 0 and empty status in both ticket worktrees.
To reproduce the blocker, use the exact build commands above after `memory_pressure`
confirms at least 30% free. Expected on the observed host: both exit 101 and the
recorded configure/C diagnostics. Reproduction is **not a passing oracle test**.
The AEXCompat document also gives environment-variable-based commands for an
orchestrator with a different checkout path.

## CLI usage and witness list

No new CLI is delivered. `ui-session` was only an unvalidated draft and must not
be assumed available in the cached workers. All requested KiraKira draw/click/drag,
picker, copy/paste, randomize, flip, preset traces and all seven UPDATE matrices
remain unexecuted. Existing setup evidence remains U01's evidence, not a U03 run.

## Draft claim text (not posted)

作業をclaimします: U03 — Unicorn guest に明示的 UI-session oracle を追加します。
Scope: original GLOBAL_SETUP/PARAMS_SETUP/arbitrary lifecycle, explicit EVENT and
UPDATE_PARAMS_UI dispatch, exact Win64 ABI, recording suites, and OLM witnesses;
render mode remains unchanged. Completion: focused behavioral tests, Release
build/self-test, local adversarial review, and original-AEX traces. Current
blocker: the required scratch path prevents Unicorn configure from completing;
resolve this before implementation resumes. No GitHub issue number was assigned
by this ticket; do not invent a `Closes #N` reference.

## Draft PR body (not posted; documentation-only blocked handoff)

U03's Release preflight fails before guest Rust compilation when the required
scratch path contains whitespace. A space-free symlink to that path produces the
same configure rejection and downstream Int128 typedef error. Record both
attempts and a reproducible blocker handoff; no UI implementation or compatibility
claim is included.

Validation: two sequential `cargo build --release --locked ... -j 1` attempts,
both exit 101. Behavioral self-tests and original-AEX witnesses were not reached.
Local review boundary and disposition are recorded below. No PR should describe
this documentation as completion of the UI-session oracle.

## next

Establish a working Release build recipe within the specified scratch constraint,
or have the orchestrator explicitly revise that constraint. Resume U03 only after
that boundary is resolved. Then implement and test the explicit UI-session mode,
install a new worker at `~/.cache/olm-emu/worker-U03-ui/`, register its measured
hash, and execute the requested original-AEX witness set. U02/U04/U05 cannot use
this report as UI oracle evidence.

## cleanup and local review

- A separate review agent inspected the AEXCompat document, both build logs, the toolchain pin, and configure guard. No blocking findings or rejected findings. Memory/size/compiler observations were checked against this session's tool results; they are not claimed to come from the build logs.
- AEXCompat reviewed boundary: `f402b7713c81ef235f5899621406841c3e8df1c5`. Its worktree is clean.
- Both build processes exited 101 and were reaped; no background process started by this task remains.
- Build tree, temporary alias, and unvalidated draft were removed. Remaining scratch logs occupy **32 KiB** (`du -sh`).
- Cleanup's initial `rm -rf` tool call was rejected before execution: `rm -f style commands are not permitted. Use a safer approach`. After inspecting the exact directory and symlink with `ls -ld`, `rm -r` without force succeeded. No permission was requested; the final status remains blocked.
- `git diff --check` passed in both worktrees. The separate review agent also reviewed this OLM handoff and found no blocking findings or unsupported success claims. Its sole finalization note (an unfinished review placeholder) is resolved by this sentence.
