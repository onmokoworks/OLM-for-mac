# Windows Witness

`tools/windows_witness` compiles a declarative witness-spec JSON file into a
sendable Windows After Effects evidence package. CDB, an injected collector,
and Frida share one hash-pinned AE queue and one fail-closed return contract.

## M0 contract

A generated package contains:

- `witness-contract.json`: normalized, machine-readable execution and evidence contract.
- `artifacts/run_witness.ps1`: stable desktop AE/CDB launcher shared by every package.
- `scripts/ae_witness_queue.jsx`: generated serial case queue.
- `scripts/renderer.jsx` and `request/`: spec-selected renderer and request payload.
- `cdb/*.cdb.in`: plugin-specific probe templates, one resolved instance per case.
- `scripts/witness_runtime.py`: fail-closed trace validator and deterministic return bundler.
- `package-manifest.json` and a deterministic package ZIP.

The launcher requires a fresh interactive desktop AE session. It verifies the
on-disk and loaded AEX SHA-256, waits for a ready marker containing the case ID,
`effect_loaded=1`, and `parameters_applied=1`, discovers exactly one matching
AE process/module, and pins one PID/module base across every serial case. It
starts CDB before writing the continue marker. The final case requests AE quit;
the launcher also stops any surviving launched AE/CDB process after the return
bundle is complete, allowing the next one-shot job to preserve the fresh-process
contract.

Trace validation accepts only configured event prefixes followed by whitespace-
separated `key=value` fields. Event cardinality is global or per-case. Every
event declares its required fields and optional exact/regex constraints. Shared
identity must include `run_id`, `ae_pid`, `module_base`, `aex_sha256`,
`project_bpc`, `renderer`, and `case_id`; all runtime values must match the
launcher binding, hash pin, configured bpc, and `Software` renderer.

Required exports are collected only after a successful trace. A missing export
changes `answered` to `exact_bind_failure`. Success and failure both produce a
deterministic return ZIP containing the return JSON, available exports, and the
compiler-enumerated AE/CDB/handshake logs. ZIP entries are sorted, carry a fixed
timestamp and mode, and use deterministic deflate settings.

## Compile

From the repository root:

```bash
python3 tools/windows_witness/compile.py \
  tools/windows_witness/examples/synthetic/witness-spec.json \
  --output-dir /tmp/windows-witness-synthetic \
  --zip /tmp/windows-witness-synthetic.zip
```

Paths in a spec are relative to the spec file. Output paths must be relative to
the runtime work directory and may use `{case_id}`. The compiler has no external
Python dependencies; `witness-spec.schema.json` is provided for editors and CI,
while `core.py` enforces the same M0 shape directly.

## CDB templates

Templates must use this exact truncating trace form so stale output can never be
accepted:

```text
.logopen /t "{{TRACE_PATH}}"
```

Supported runtime placeholders are:

- `{{RUN_ID}}`, `{{AE_PID}}`, `{{MODULE_BASE}}`, `{{AEX_SHA256}}`
- `{{PROJECT_BPC}}`, `{{RENDERER}}`, `{{CASE_ID}}`, `{{TRACE_PATH}}`
- `{{ADDRESS:name}}` for module base plus a case `addresses` RVA
- `{{CASE_VALUE:name}}` for a case `template_values` value

Unknown or unresolved placeholders fail compilation or execution. Probe
templates must emit the identity fields literally in each machine-readable
event. CDB setup, breakpoint conditions, register interpretation, and event
details remain plugin-specific.

## Windows usage

Run the generated package from the interactive Windows desktop session:

```powershell
.\artifacts\run_witness.ps1
```

The contract supplies default AEX, AfterFX, and CDB paths; all three can be
overridden with launcher parameters. `-ParseOnly -TracePath <path>
-IdentityPath <json>` runs the bundled validator without launching AE. Runtime
requires Windows PowerShell 5.1+ and `py -3`.

## One-click batch

The current high-value witnesses can be rebuilt as one outer request from a
clean checkout:

```bash
python3 scripts/package_windows_witness_batch_20260713.py
```

This regenerates the inner packages and writes
`refs/runtime_trace_packages/windows_witness_batch_20260713.zip`. Extract that
ZIP on the interactive Windows desktop, close After Effects and CDB, then
double-click `RUN_WINDOWS_WITNESS_BATCH.cmd`. The outer runner preflights every
AfterFX/CDB/AEX path and AEX hash before the first render, then executes each
inner witness serially with a fresh AE process. Every job has a bounded timeout;
one failed or timed-out job does not discard the other evidence. Each job also
records `satisfies_request_ids`, which binds
the new common witness ID to the legacy pending requests it can answer; staging
checks reject a batch that cannot prove those inner IDs and package hashes.

The run writes `windows_witness_batch_return.zip` beside the launcher. Intake
must bind it to the exact request ZIP:

```bash
python3 scripts/intake_windows_witness_batch.py \
  path/to/windows_witness_batch_return.zip \
  --request-batch refs/runtime_trace_packages/windows_witness_batch_20260713.zip \
  --output-json refs/reports/windows_witness_batch_intake.json
```

Partial evidence is rejected by default. `--allow-partial-evidence` is only for
salvaging successfully captured jobs before building a narrowed retry; it does
not promote the batch to complete evidence.

The request ZIP is deterministic. Intake proves that returned bytes match that
exact request, but it cannot prove that a previously valid return was captured
recently. Archive old returns and run from a freshly extracted request whenever
fresh-capture provenance matters.

## Tests

```bash
python3 -m unittest discover -s tools/windows_witness/tests -v
python3 tools/windows_witness/smoke.py
```

The tests cover strict spec validation, template safety, serial generation,
stable launcher source invariants, field/cardinality/identity failures,
required artifact handling, and byte-for-byte deterministic package and return
ZIPs. The synthetic example is compile-only and does not require Windows or AE.

## Frida entry-to-core transport

`transport.kind = "frida"` is the default discovery tool when the unresolved
question is which AEX path a real AE render takes. The generated package:

- attaches to the exact AE PID and hash-pinned loaded AEX before releasing the
  renderer;
- hooks the exported PF entrypoint and conservative evidence-backed core RVAs;
- records typed argument/return reads and bounded buffer chunks as canonical
  JSONL;
- remains attached until the AE renderer publishes its result marker; and
- fails closed on module, case, run, renderer, bit-depth, cardinality, read, or
  timeout drift.

The shared 2025 AEX map is
`frida_profiles/olm_entrypoints_20260718.json`. Broad instruction tracing is
deliberately disabled. Use CDB after the Frida trace has selected a narrow
callsite that needs stepping, register inspection, or a data watchpoint.

Build the six-lane entry survey with:

```bash
python3 scripts/package_windows_frida_entrypoint_batch_20260718.py
```

The generated outer ZIP contains one interactive Windows launcher. Intake is
bound to that exact request manifest and all six inner package hashes:

```bash
python3 scripts/intake_windows_frida_entrypoint_batch_20260718.py \
  path/to/RETURN_OLM_FRIDA_ENTRYPOINT_BATCH_20260718.zip \
  --request-batch refs/runtime_trace_packages/windows_frida_entrypoint_batch_20260718.zip \
  --output-json refs/reports/windows_frida_entrypoint_batch_intake_20260718.json
```
