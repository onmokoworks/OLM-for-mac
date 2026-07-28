# Generic Windows Codex batch handoff packager

`scripts/package_windows_codex_batch_handoff_20260728.py` combines immutable
Windows job ZIPs without modifying or executing them.

Each job has a JSON manifest beside its ZIP:

```json
{
  "schema": "windows_codex_batch_job_v1",
  "job_id": "unique_lowercase_id",
  "package": "package.zip",
  "package_sha256": "64 lowercase hex characters",
  "entrypoint": "run.ps1",
  "failure_policy": "independent",
  "request_id": "optional child request binding",
  "description": "optional human-readable objective"
}
```

Paths are POSIX relative to the job manifest. The packager rejects missing or
drifted checksums, duplicate job IDs, duplicate child SHA-256 values, traversal,
Windows-case-colliding ZIP members, symlinks, and `__MACOSX`. The declared
entrypoint must be an exact, case-sensitive regular-file member; a directory or
case-only match is rejected. Windows portability checks also reject reserved
DOS device basenames (including extensions and the Windows `COM¹`–`COM³` /
`LPT¹`–`LPT³` aliases), colon/alternate-data-stream names, trailing-dot or
trailing-space components, and file/directory hierarchy collisions.
Windows-forbidden characters (`<`, `>`, `"`, `|`, `?`, `*`) and ASCII controls
are rejected, IDs cannot end in a dot, and each component is limited to 255
UTF-16 code units. Member paths must use one canonical POSIX spelling (aliases
such as repeated separators are rejected). Unix-created members with explicit
type bits must be regular files, or directories whose type and trailing-slash
pathname agree; FIFOs, sockets, devices, and mismatched directory metadata are
rejected.

Build in the desired execution order:

```bash
python3 scripts/package_windows_codex_batch_handoff_20260728.py \
  --batch-id my_windows_batch_20260728 \
  --job-manifest /absolute/path/job_one.json \
  --job-manifest /absolute/path/job_two.json \
  --output /absolute/path/my_windows_batch_20260728.zip
```

The output JSON reports the parent ZIP SHA-256 and the tool also writes
`my_windows_batch_20260728.zip.sha256`. The parent contains `START_GATE.txt`,
`BATCH_MANIFEST.json`, shared instructions, a single return contract, an intake
schema, complete member checksums, and ordered byte-for-byte child ZIPs.

Packaging is fail-closed. Every child package is read once into an immutable
byte snapshot; ZIP validation, SHA-256, size, and embedding all use that same
snapshot. Before any output write, the resolved parent and sidecar paths are
checked against one another and every manifest/package input. Existing outputs,
existing sidecars, and aliases are rejected—there is no overwrite option.
After validation, the packager atomically reserves both targets, writes and
`fsync`s same-directory temporary files, replaces only its own reservations,
and removes reservations and temporary files if either install fails or the
operation is interrupted by `KeyboardInterrupt`/`SystemExit`.

The start gate is always `HOLD`. After explicit user release, the Windows owner
runs every expected job exactly once in manifest order under the shared
no-preferences/no-cache/no-modal automation policy. Each job must reach
`answered` or `exact_bind_failure`; failures are independent and do not stop
collection of later jobs.

The v2 parent manifest, return contract, and intake schema impose an
`all_jobs_terminal` completion barrier. No interim result or per-job return ZIP
may be emitted, uploaded, attached, or returned. Every nested ZIP below `jobs/`
is forbidden, whether identified by a `.zip` extension (including `return.zip`),
leading ZIP magic, or a valid ZIP directory behind a renamed SFX/preamble.
Each expected job must appear exactly once and in request order in
`BATCH_RETURN.json`, with its bound request SHA and at least one direct regular
evidence file. The evidence path remainder below its ordered job root must be
exactly one non-empty component; nested paths such as `nested/evidence.txt` are
invalid even when no directory entry exists. Each evidence record carries the
file path, SHA-256, non-empty kind, and non-empty description; failure
diagnostics may be used as evidence.

The returned archive allowlist is exact: `BATCH_RETURN.json`, immutable byte-for-
byte copies of `BATCH_MANIFEST.json` and `BATCH_RETURN_CONTRACT.json`,
`CHECKSUMS.sha256`, and only evidence files referenced once by a job record.
Directories, unreferenced files, unexpected files, and incomplete or surplus
checksum entries are rejected. To avoid a circular self-hash,
`CHECKSUMS.sha256` is the sole allowlisted member deliberately absent from its
own contents. It lists every other exact allowlisted regular-file member once,
in lexicographic canonical member-name order. Checksum lines may spell a member
canonically (`BATCH_MANIFEST.json`) or with exactly one leading `./`
(`./BATCH_MANIFEST.json`); the validator removes that one optional prefix
before duplicate, ordering, allowlist, self-entry, and hash checks. Repeated
`./`, dot segments elsewhere, backslashes, traversal, aliases that normalize to
the same member, missing members, and entries for any other path fail
validation. Parent status is derived from child statuses, and failure records
are required only for `exact_bind_failure`.

Validate a return deterministically with:

```bash
python3 scripts/package_windows_codex_batch_handoff_20260728.py \
  --validate-return /absolute/path/request_batch.zip \
  /absolute/path/consolidated_return.zip
```

Only after every expected job has a terminal status and checksum-bound evidence
may Windows Codex emit exactly one consolidated ZIP. The parent is `answered`
iff every child answered, `partial_success` iff at least one child answered and
at least one failed, and `exact_bind_failure` iff zero children answered. A
`partial_success` return retains and checksum-binds every answered child.
Exactly-one delivery and its timing are external Windows Codex session policy:
archive intake can prove the properties of the one archive it received, but
cannot prove that no other file was previously delivered or when delivery
occurred.

Child request manifests remain `windows_codex_batch_job_v1`. Their immutable
input-package binding and terminal status vocabulary are unchanged; only the
parent handoff, batch return, and intake schemas advance to v2.
