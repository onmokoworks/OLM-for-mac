# Windows Codex owner work-order — OLM direct-evidence batch

Date: 2026-07-28
Owner: Windows Codex
Mac counterpart: OLM Mac Codex
State on receipt: **HOLD — do not launch After Effects until the user explicitly releases this work-order**

## Mission and reason for the work

Own the complete Windows-local construction, repair, test, and evidence loop for
the three OLM jobs below. The user should not have to ferry a succession of
Mac-built retry ZIPs to Windows. Inspect the supplied sources and the failed r1
attempt, patch the runners locally, run unit and package smoke tests locally,
and—only after explicit user release—perform the necessary Windows After
Effects runs. Retry locally until every job has a defensible terminal result.
Return exactly one consolidated direct-evidence ZIP.

The goal is not merely to obtain plausible rendered pixels. OLM is a
binary-compatibility port: a Mac implementation can look close while reading
the wrong host buffer, choosing the wrong depth path, rounding at the wrong
boundary, or reproducing a test fixture instead of the installed Windows AEX.
Binary-grounded Windows evidence identifies the actual loaded AEX, executed
instruction boundary, typed input and output storage, raw channel words, and
same-run render/export identity. That evidence is what permits a later,
bounded Mac implementation or conformance claim.

The repository's CLIs are reconstruction and diagnosis tools. **CLI exact does
not mean AE exact.** CLI agreement may narrow an algorithm or validate a
portable kernel, but only a hash-bound, same-run installed-AEX/AE observation
can support an AE claim. Never promote a CLI match, a debugger replay, an input
copy, or an artifact-presence check into `AE exact`.

## Authority, chronology, and current boundary

The authoritative source history for this handoff is:

- `28c0913e` — consolidated Windows evidence batch tooling and the initial
  RadialBlur, DirectionalBlur, and DistanceGradation jobs.
- `4b97a2ad` — DistanceGradation PF16 boundary capture and Mac-side adapter
  instrumentation.
- `da485985` — Mac-side conformance analysis harnesses. These consume returned
  evidence; they do not substitute for Windows direct evidence.
- The commit containing this work-order — return-validator compatibility
  fixes and locally tested reference repairs for all three r1 runner failures.
- AEXCompat issue `#553` is closed, issue `#569` is closed, and PR `#570` is
  merged. Treat those upstream investigations as completed context, not as
  authorization to broaden this Windows job into AEXCompat work.

These reference repairs are available for Windows Codex to inspect, adapt, and
test on the actual host. They are not pre-approved AE evidence:

- RadialBlur r4 child reference SHA-256:
  `8d09010a2265c4e41964de1dcdd50c6764e5b7be846f3e25b5384110c5e0d60b`.
  It adds the installed `MediaCore\OLM` directory to the exact AEX path.
- DirectionalBlur r4 child reference SHA-256:
  `f93a97db8ed99e97845df07d4b2801dbe3f917d5b63b45935b019b196d881f7d`.
  It stages and hash-verifies the run-unique input before AE launch and
  returns direct input-copy/readiness diagnostics.
- DistanceGradation r3 child reference SHA-256:
  `29b7a265c21a98977e209d8bc0f720ff4c2ae351b6453603f2df44f2e4dd2287`.
  It fixes the duplicate `-LiteralPath` parse/binding defect.

Windows Codex owns subsequent batch construction. It may use these references
as known-tested starting points, patch them further in its Windows-local source
workspace, and retry locally. It must preserve diffs and must not treat the
reference package SHA as runtime proof.

The r1 request batch is
`refs/handoffs/windows_codex_batches_20260728/olm_windows_batch_20260728_r1.zip`,
SHA-256
`809c3760c4e5b1f96e6747f2e9188435b3f2caaca6f229cf0ba061384cbc84ab`.
Its three exact child bindings, in order, are:

1. `olmradialblur_case0010_upstream_sampler_20260728_r3` —
   `6a8d9404e60de3656877aa55ca97546c5fa1f4cab33c50e9a9fc9984b5781774`.
2. `olmdirectionalblur_target_writer_20260728_r3` —
   `42226b5764fbf3618102f2c91feea2cbcd412a5317f85454446f03ba4590e5a4`.
3. `olmdistancegradation_pf16_boundary_20260728_r2` —
   `8e931aa7bc8a7a67829c6c5b4c94ac8cdfeac10599690d0e7891a429c0985027`.

The actual first Windows r1 return is
`/Volumes/onmk/olm_pr/new/mac_returns/OLM_WINDOWS_BATCH_RETURN_20260728T044305Z.zip`,
SHA-256
`fffe03721f84e64c34b03074824a9e9ff40160b09cc71b92f48ad019740dfec2`,
size `8811` bytes. Its parent result is `exact_bind_failure`, not evidence
success.

The initial Mac validator rejected that archive for two Mac-side contract
defects: its checksum interpretation incorrectly required a circular/self
entry for `CHECKSUMS.sha256`, and it did not accept the standard `./` path
prefix used by the return. Both validator/contract defects are now fixed
locally. With those fixes, this exact archive should intake structurally as a
parent `exact_bind_failure`; validator acceptance preserves the failure
diagnostics and does not turn any child into answered evidence.

The three genuine r1 job failures are:

1. RadialBlur could not find the AEX because its runner omitted the installed
   `MediaCore\OLM` path.
2. DirectionalBlur created/retained the run-unique input copy but never
   received the required ready marker, so no writer evidence was established.
3. DistanceGradation failed runner binding because `Test-Path` received
   `-LiteralPath` twice.

Preserve this return unchanged in provenance; do not relabel it as evidence
success and do not overwrite it.

The known Windows host facts from that attempt are operational requirements:

- PowerShell `-r`/direct script dispatch is unreliable on this host. Use a full
  explicit command or the locally supported Windows Codex/desktop launch path.
- CDB attach can disturb or terminate the render. Treat attach as a material
  risk, bind the exact PID first, attach only where the job requires it, and
  classify attach-induced loss as a failed attempt rather than evidence.
- The installed OLM plug-ins are under
  `C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM`.
  In particular use `OLMRadialBlur.aex`, `OLMDirectionalBlur.aex`, and
  `DistanceGradation.aex` there unless read-only preflight proves a different
  packaged exact path. Do not silently fall back to the MediaCore parent or an
  AE Support Files copy.

What is exact today is limited to the already declared, case-specific slices
in the repository ledgers and accepted evidence. These three jobs remain
incomplete at their stated boundaries. A successful return may close those
boundaries; it does not establish whole-plugin, all-parameter, all-depth,
cross-renderer, production, CLI-exact, or AE-exact behavior.

## Windows-owned working loop

Windows Codex owns the runners, not just their execution:

1. Unpack the immutable request and failed attempt into a new, run-specific
   local work root. Record hashes before modification.
2. Copy runner sources to a clearly named local source workspace. Patch the
   local copies; never mutate the immutable input archive.
3. Preserve the correct non-circular parent checksum behavior:
   `CHECKSUMS.sha256` lists every other allowed member exactly once in
   lexicographic order and never lists itself. Standard `./` member prefixes
   are compatible with the locally fixed Mac validator; do not invent a
   self-hash workaround.
4. Repair RadialBlur path discovery to require the exact
   `MediaCore\OLM\OLMRadialBlur.aex` identity and fail closed on absence/hash
   mismatch.
5. Preserve the working DirectionalBlur ready/input-copy behavior and repair
   only the missing continuation/writer capture. Do not discard the unique
   source-copy provenance while fixing the trace path.
6. Repair the DistanceGradation `Test-Path` call so it has one and only one
   `-LiteralPath` binding. Audit nearby generated invocations for the same
   duplicate-parameter defect.
7. Run PowerShell parse/unit tests and all supplied Python/package smoke tests
   without AE. Add narrow regression tests for every repair. Continue until
   local construction and validation are clean.
8. Preserve every source change as a unified diff plus full patched files,
   exact test commands, stdout/stderr, exit codes, and SHA-256 values.
9. Stop at the HOLD gate. Launch AE only after the user explicitly says to
   start in the Windows task.
10. After release, preflight exact identities and execute the three jobs
    sequentially. A job failure does not prevent collection of the later jobs.
    Retry locally with a new attempt/run identity after fixing a runner defect.
11. Keep all attempts. Never edit a failed trace into a passing form. Select
    the final direct evidence only after all three jobs are terminal.

## Non-negotiable safety and scope

- Do not change or delete Adobe preferences, disk cache, media cache, plug-in
  cache, user projects, or installed AEX files.
- Do not automate, dismiss, answer, toggle, or guess through modal dialogs.
  Stop, preserve state and logs, and ask the user.
- Never broadly kill After Effects or Adobe processes. Resolve the exact PID
  created and owned by the current attempt; if ownership is ambiguous, do not
  terminate it.
- Every accepted event must share the exact-owned identity required by its
  job: run ID, owned AE PID, installed and loaded module path/base/SHA, case and
  project identity, renderer, bit depth, source-copy hash, and output.
- Fail closed on missing artifacts, path/hash drift, mixed run identity,
  stale/cache-like output, zero-duration execution, debugger failure,
  unexpected host state, or ambiguous cleanup.
- No unrelated repository, Mac plug-in, AEXCompat, NAS, preference, cache,
  installed-plugin, or conformance-ledger work. Do not upload evidence to a
  public service.

## Evidence goals and explicit nonclaims

### 1. OLMRadialBlur case_0010

Capture the packaged coordinate `(1614,6)` in one exact run at the declared
upstream plane and direct sampler boundary, including raw typed values,
addresses/coordinates, executed RVAs, run/PID/module identity, retained input,
and required rendered artifact presence. The purpose is to determine what
value the installed 2025 AEX supplies at this boundary.

This does **not** claim final writeback, exported-pixel causality, complete
RadialBlur semantics, production readiness, CLI exactness, or AE exactness.
Do not infer a final output pixel from the upstream/sampler word alone.

### 2. OLMDirectionalBlur target writer

For packaged coordinate `(494,169)`, capture the raw target-writer FLOAT32
words and writer-buffer address, the typed PF ARGB8 store bytes and actual PF
output address, plus the same-run PF output and exported PNG. Retain and hash
the run-unique input copy and prove it equals the packaged source input.

Ready state or input-copy success alone is not an answer. This narrow witness
does **not** prove all rows, angles, alpha modes, depths, production readiness,
CLI exactness, or whole-plugin AE exactness.

### 3. OLMDistanceGradation PF16 boundary

Capture the packaged PF16 entry/boundary with the RCX entry anchor, executed
address/RVA, exact pointers and geometry, and finite/in-range typed values
required by the r2 contract. Bind them to the actual installed
`DistanceGradation.aex`, exact run, input, render, and artifact.

This is a boundary/adapter witness. It does **not** prove the entire field
generator, all coordinates or cases, an export conversion, the Mac adapter,
CLI exactness, or whole-plugin AE exactness.

## Bit depth and raw-word discipline

Bit depth is evidence, not presentation metadata. Record the AE project depth,
world/pixel format, rowbytes, channel order, pointer/address calculation, and
the exact bytes read from or written to memory.

- PF8: preserve raw channel bytes (`uint8`) and declared ARGB/RGBA ordering.
- PF16: preserve the four raw 16-bit words and their little-endian bytes. Do
  not normalize them to 0–1 and discard the originals; AE/PF16 nominal scale
  and a full `uint16` storage range are not interchangeable assumptions.
- PF32: preserve each raw 32-bit word/byte sequence and its FLOAT32
  interpretation, including signed zero, NaN/Inf classification, and
  endianness. Decimal text alone is insufficient.
- For every conversion, report source raw word, typed interpretation,
  conversion rule, and destination raw word. Never compare PNG display bytes
  as a substitute for an internal PF16/PF32 word.

## Success, failure, and terminal barrier

A child is `answered` only if every required observation and artifact in its
contract is present, nonempty, hash-bound, internally consistent, and shares
one exact-owned run identity. Anything less is `exact_bind_failure`, with
machine-readable failure stage/reason and direct diagnostic files. There is no
“mostly answered” child status.

All three children must reach one of those terminal statuses before delivery.
The parent is:

- `answered` when all three children are answered;
- `partial_success` when at least one is answered and at least one is
  `exact_bind_failure`;
- `exact_bind_failure` when none is answered.

Terminal success for this work-order means: local runner fixes and tests are
preserved; all jobs are terminal; the consolidated return passes the same
validator contract locally; and exactly one final archive is delivered.
Do not stop merely because one trace attempt failed if a safe local runner fix
or retry remains.

## The one permitted return

Return one and only one consolidated direct-evidence ZIP after the terminal
barrier. Do not return interim archives, per-job return ZIPs, or any child ZIP
inside the consolidated ZIP. Include:

- `BATCH_RETURN.json`;
- byte-identical request copies of `BATCH_MANIFEST.json` and
  `BATCH_RETURN_CONTRACT.json`;
- `CHECKSUMS.sha256`, containing every other allowed member exactly once,
  sorted lexicographically, and deliberately not containing itself;
- one flat evidence area per ordered job, with every file referenced exactly
  once from the job record;
- final direct traces/artifacts and, for failures, direct diagnostics;
- the exact SHA-256 of the original r1 request and failed r1 return;
- the complete patched runner/source files and unified diffs from their
  immutable originals;
- exact build, unit, smoke, AE-run, retry, packaging, and validation commands,
  with stdout/stderr, timestamps, exit codes, host/tool versions, and attempt
  identities;
- SHA-256 values for sources, installed/loaded AEX files, input copies,
  outputs, logs, evidence, and the final ZIP.

No child return ZIPs, nested ZIPs, renamed ZIP/SFX payloads, unreferenced files,
or hand-authored summaries standing in for direct evidence are permitted.

## Mac intake and validator handoff

Mac Codex will first preserve and hash the received ZIP, then run the
repository validator against the immutable r1 request:

```bash
python3 scripts/package_windows_codex_batch_handoff_20260728.py \
  --validate-return \
  refs/handoffs/windows_codex_batches_20260728/olm_windows_batch_20260728_r1.zip \
  /absolute/path/to/the_one_consolidated_return.zip
```

The validator checks immutable request copies, job order and exact child
bindings, terminal-status derivation, evidence paths and hashes, ZIP safety and
allowlisting, and the non-circular checksum manifest. Passing intake means the
archive satisfies the transport/evidence contract; it does not itself make an
algorithmic or AE-exact claim. Mac Codex will then inspect direct records,
compare the Windows words against the relevant Mac harnesses introduced by
`4b97a2ad` and `da485985`, update bounded IR/conformance conclusions, and
request follow-up only where the returned evidence genuinely leaves a boundary
open.

## Owner checklist

- [ ] Preserve and hash immutable r1 request and failed return.
- [ ] Work only in a new Windows-local source/attempt root.
- [ ] Preserve the non-circular checksum rule; do not add a checksum self-entry.
- [ ] Repair RadialBlur exact installed `OLM` path binding.
- [ ] Preserve DirectionalBlur ready/input-copy evidence and close writer path.
- [ ] Remove DistanceGradation duplicate `-LiteralPath` binding.
- [ ] Add/run narrow regression, parse, unit, and package smoke tests.
- [ ] Preserve patched files, diffs, commands, logs, exit codes, and hashes.
- [ ] Wait for explicit user release before any AE launch.
- [ ] Preflight exact AEX, input, project, renderer, depth, and PID identity.
- [ ] Execute sequentially; retry locally and preserve every attempt.
- [ ] Give every child exactly one terminal status.
- [ ] Build and locally validate one consolidated direct-evidence ZIP.
- [ ] Confirm there are no interim, per-child, nested, or renamed ZIP payloads.
- [ ] Report the final ZIP SHA-256 and deliver that single archive.
