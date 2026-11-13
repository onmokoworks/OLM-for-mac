# OLM Ghidra Hub

One headless PyGhidra JVM owns `D:/olm-rs-ghidra/OLM-rs.gpr`. Many Python and
Streamable HTTP MCP clients share the same analyzed programs and bounded
decompiler pools. No Ghidra GUI, AE, installed GUI MCP bridge, autostart, service,
scheduled task, or global Codex configuration change is involved.

## Setup and lifecycle

Qualified installation: Ghidra 12.0.3 at
`C:/ghidra_12/ghidra_12.0.3_PUBLIC`, Temurin 21 at
`C:/Users/optim/jdks/temurin-21`, Python 3.11.9. Java on PATH is 17 and is not used.
Set `OLM_GHIDRA_JAVA_HOME` to select another supported JDK.

From the repository root in PowerShell:

```powershell
python -m venv D:/olm-rs-ghidra/venv
$py = 'D:/olm-rs-ghidra/venv/Scripts/python.exe'
$hub = 'rust/tools/ghidra-hub/hub.py'
& $py -m pip install -r rust/tools/ghidra-hub/requirements.txt
& $py $hub init
& $py rust/tools/ghidra-hub/snapshot.py
& $py rust/tools/ghidra-hub/inspect_projects.py
& $py $hub import-knowledge
& $py $hub start --port 8766 --workers 3
& $py $hub status
& $py $hub stop
```

`init` imports all ten originals from the common-kit binary directory, smallest
first, with full default auto-analysis (external PDB loading disabled), a
persisted analyzed flag, and a save after each program. Existing equal-hash
programs are reused; a different hash cannot replace a named original. Analysis
uses three logical JVM processors and a 12 GiB maximum heap. Only one analysis
runs at a time. Run offline maintenance (`init`, `import-knowledge`) while the
hub is stopped; Ghidra's project lock prevents competing project writers.

`start` launches a hidden process, waits for the correct instance's health check,
prints its PID/port/URL, and stores `hub.pid.json` and `launch.json` in the data
directory. Concurrent starters are guarded by an OS file lock. `stop` verifies
PID creation time, command line and instance token, requests graceful shutdown,
waits, and only if needed terminates the captured owned process tree. It verifies
exit and records `reports/last-stop.json`. An unnamed Windows Job Object contains
the server and future decompiler children, including crash cleanup. Stale PID
files never authorize killing a reused PID. `stop` is safe to repeat.

All projects, snapshot copies, GDT exports, reports, function exports, caches,
temporary files and server logs live under `D:/olm-rs-ghidra/`. Startup is explicit;
the shipped code does not create watchers or automatic restart loops. Stop the
service when the agents using it have finished.

## Python batch API

`client.py` needs only the standard library; clients never start a JVM or open a
Ghidra project. Add this tool directory to `sys.path`, then:

```python
from client import Client
c = Client('http://127.0.0.1:8766')
print(c.programs_list())
page = c.list_functions(programs=['OLMBlur', 'OLMRadialBlur'], query='FUN_', limit=20)
batch = c.decompile_batch(items=[
    {'program': f['program'], 'function': f['address']}
    for f in page['functions']
])
print(batch['seconds'], [r['completed'] for r in batch['results']])
functions = list(c.all_functions())  # paginates across every program
```

Functions can be selected by exact address or unique name; ambiguous names fail.
Function listing/decompilation covers internal function bodies. `programs_list`
separately reports total, internal and external counts; external imports have no
local bodies to decompile.
Pagination is deterministic by program/domain order and function address, but
is not a frozen snapshot across separate requests during writes.

| API | Arguments / result |
| --- | --- |
| `programs_list` | Names, SHA-256, language, analyzed flag, function count |
| `list_functions` | Optional `programs`, case-insensitive `query`, `offset`, `limit` (1..10000); total + rows |
| `decompile_batch` | `items=[{program,function},...]`, `parallel=True`, `timeout=60` per function (1..300); ordered results with explicit failures and timing; max 10000 items |
| `xrefs` | `program`, `address`; incoming and outgoing references |
| `call_graph` | `program`, optional `functions`, `depth` (0..8); nodes and static call edges |
| `data_types` | `program`, optional `query`, `offset`, `limit` (1..1000); definitions and structure fields |
| `bulk_edit` | `rows`, `provenance`; one atomic, saved transaction per affected program |
| `export_function` | `program`, `function`; creates `function.c`, `disassembly.txt`, `function.json` with signature/callees under `exports/<uuid>/` |
| `add_program` | `aex`, optional `name`; imports and analyzes an additional binary |
| `add_version` | `aex`, `like`; imports a hash-named version and carries knowledge forward |
| `reset_decompilers` | HTTP/Python benchmark utility; closes pools for a fresh subsequent run |

A JSON table can mix rename, signature/retype and comment operations. A CSV table
can be loaded with `csv.DictReader` and passed as the same list of dictionaries.

```python
c.bulk_edit(rows=[{
    'program': 'OLMBlur', 'function': '180001000',
    'name': 'ReviewedKernel',
    'signature': 'void ReviewedKernel(void *state)',
    'comment': 'Reviewed mapping; see the named source record.',
    'expected_name': 'FUN_180001000',
}], provenance='job-X: reviewed mapping table')
```

This example is a schema demonstration, not a verified signature for that address.
`expected_name` is optional optimistic concurrency control. Unknown fields and
invalid selectors fail. An error rolls back **all rows in that program**; earlier
program groups in a multi-program table can already be committed. Transactions
are not atomic across programs. Explicit API renames are deliberate user/agent
edits; automated knowledge import has a separate no-overwrite conflict policy.

Writer-preferring per-program reader/writer locks allow concurrent queries and
decompilation. The global decompile executor has at most three workers; each
program has a lazily created pool. Writes wait for readers, run in a Ghidra
transaction, invalidate decompiler caches (also on rollback), and save before
returning. Other programs can still be read. Provenance is stored inside the
same database transaction and mirrored to `logs/transactions.jsonl` after save.
A batch's individual functions are consistent, but an entire batch is not a
multi-program snapshot. Saves also happen during graceful shutdown.

## MCP / Codex

The MCP endpoint is `http://127.0.0.1:8766/mcp` (Streamable HTTP, stateless JSON
responses). MCP exposes the same operations except `reset_decompilers`, with
`list_programs` as the MCP name for `programs_list`. Tools perform work on worker
threads so an HTTP connection does not block other clients.

For one Codex job without editing `~/.codex/config.toml`:

```powershell
codex exec --ignore-user-config --ephemeral --skip-git-repo-check `
  -C D:/olm-rs-ghidra/codex-smoke -s read-only `
  -c 'mcp_servers.olmghidra.url="http://127.0.0.1:8766/mcp"' `
  -c 'mcp_servers.olmghidra.tool_timeout_sec=180' `
  -c 'mcp_servers.olmghidra.default_tools_approval_mode="writes"' `
  'Use olmghidra to list functions in OLMBlur and OLMRadialBlur, then decompile a batch from both.'
```

`--ignore-user-config` isolates this test from unrelated configured MCPs while
retaining existing authentication. Omit it when intentionally using the other
servers in an ordinary job. The target working directory must exist. Official
[Codex MCP configuration documentation](https://learn.chatgpt.com/docs/extend/mcp)
describes URL-based connections. `verify_codex.py` runs the bounded, real CLI
test with an allow-list of only `list_functions` and `decompile_batch`, and
retains JSONL tool events plus its final response. Read tools advertise MCP
`readOnlyHint`; `writes` mode allows those tools and prompts for mutations.

The listener is loopback-only and is intended for trusted local tools. There is
no remote authentication scheme. Do not expose or forward it to an untrusted
network. The small Python HTTP API rejects browser Origin headers and foreign
Host headers; MCP uses SDK transport protections. Shutdown also requires the
instance token from the local PID file.

## Knowledge migration

`snapshot.py` copies the three explicitly supplied projects into numbered
directories under `snapshots/`; it never opens, locks or upgrades the originals.
It hashes copied files, checks source size/mtime stability, and retains a source
manifest. Repeated runs reuse complete snapshots and reject incomplete copies.
It ignores project lock files. `verify_sources.py` checks original hashes,
sizes and modification times against those manifests.

Only the copies are opened as projects; program data is obtained through
`getReadOnlyDomainObject`. Matching source programs export `knowledge.json`
(symbols/namespaces, signatures and source priorities, all five listing comment
kinds, function/repeatable comments, bookmarks, type definitions) and `types.gdt`
(the actual type graph, including structures and dependencies).

Instruction language and compiler ABI must agree before transfer. Identical
binary SHA-256 maps addresses by image-relative offset. Different binaries
require at least one confident match and unique function fingerprints:
exact instruction bytes first, then address/relocation-normalized instruction
bytes with referenced literal data. Functions below five instructions, ambiguous
duplicates and shape-only/name-only guesses are not automatically matched.
Interior annotations transfer across different hashes only with exact instruction
bytes; normalized matches transfer entry annotations only. Global/data addresses
without an identical binary hash are deliberately left unmapped.

Existing `USER_DEFINED` and `IMPORTED` names/signatures are protected. Conflicting
types and bookmarks are recorded and kept; comments are merged with source
provenance. Per-program transactions include provenance and complete match reports
in `OLM Hub Provenance` program options. External reports include applied counts,
conflicts, matches and unmatched functions. Exceptions roll back that source's
transfer and are reported; they do not silently count as success.

Address-bearing excerpts from `notes/IR_*.md` and relevant Rust `VALIDATION.md`
files are added as comments with source path/line, never used to replace human
names. These retain historical evidence and its qualifications; they are not a
new claim that every historical note is current ground truth.

Add another program or a new version while the server is running:

```powershell
& $py $hub add --aex D:/incoming/NewPlugin.aex --name NewPlugin
& $py $hub add-version --aex D:/incoming/OLMBlur.aex --like OLMBlur
```

Versions are named `OLMBlur@<first-12-SHA256>` and do not replace originals.
`reports/<version>/match-report.json` records carry-over. Repeating an already
registered version returns `reused=true`. Fingerprints are heuristics, not proof
of semantic equivalence; compiler changes and indirect calls need human review.

## Verification

```powershell
& $py -m unittest discover -s rust/tools/ghidra-hub -v
& $py rust/tools/ghidra-hub/verify_knowledge.py
& $py $hub start
& $py rust/tools/ghidra-hub/verify_live.py
& $py rust/tools/ghidra-hub/verify_codex.py
& $py $hub stop
& $py rust/tools/ghidra-hub/restore_test_priorities.py
& $py $hub start
& $py rust/tools/ghidra-hub/verify_persistence.py
& $py $hub stop
& $py rust/tools/ghidra-hub/verify_sources.py
```

The live test decompiles every function of OLMBlur and OLMRadialBlur in four
cold-pool runs (sequential, parallel, parallel, sequential), compares C-output
hashes and failure counts, then runs three concurrent HTTP readers plus one
bulk writer. It checks rollback, restores the probe's name/comment, exercises
xrefs/types/graphs/export, and imports a temporary PE-checksum-byte-patched
OLMBlur. The temporary AEX is removed after import; its analyzed version remains
in the persistent project. The public rename API makes probe names `USER_DEFINED`;
the offline restoration helper verifies the saved name/comment and restores only
the test's originally `DEFAULT` priorities. It refuses subsequent user changes.

The seeded JVM fixture independently verifies a name/namespace, typed signature,
structure, interior/function comments, bookmark, and preservation of a conflicting
human name. This is synthetic evidence and is reported separately from the actual
user-project import counts.

<!-- MACHINE_RESULTS_START -->
Verified on **2026-11-12**, Windows, Ghidra 12.0.3 / Temurin 21 / Python 3.11.9.
Full logs and JSON evidence are retained under `D:/olm-rs-ghidra/reports/` and `logs/`.

All **10 originals**, **41,793 total functions** (including external imports), were fully analyzed and saved. Restart checks verified the original hashes, function counts and analyzed flags, plus the persisted demo version.

| Program | Total functions | Initial analysis/import seconds |
| --- | ---: | ---: |
| ColorKeep | 110 | 12.20 |
| OLMDirectionalBlur | 156 | 8.12 |
| OLMBlur | 128 | 9.15 |
| OLMSmoother | 143 | 8.64 |
| OLMColorKey | 493 | 13.96 |
| OLMRadialBlur | 525 | 13.48 |
| OLMSmoother2 | 618 | 14.19 |
| OLMToonDilate | 6,301 | 103.59 |
| OLMKiraKira | 16,540 | 511.02 |
| DistanceGradation | 16,779 | 416.31 |

**Throughput:** all 566 internal bodies (OLMBlur 97 + OLMRadialBlur 469), four runs with fresh decompiler pools. All four completed 566/566 with identical C-output hashes. The 87 external imports in these two programs have no local bodies.

| Order | Mode | Server seconds | HTTP wall seconds |
| ---: | --- | ---: | ---: |
| 1 | Sequential | 7.631 | 7.657 |
| 2 | Parallel (3) | 3.113 | 3.136 |
| 3 | Parallel (3) | 3.116 | 3.128 |
| 4 | Sequential | 6.651 | 6.663 |

Mean server time: **7.141s sequential vs 3.114s parallel; 2.29× speedup**. This is a local batch wall-time measurement, not a guarantee on other binaries or machines.

**Concurrency and features:** three independent HTTP clients each completed 96 decompilations (288 total), concurrently with nine saved writer transactions. Immediate rollback of a partially applied invalid table passed. Xrefs, call graphs, composite/dynamic type queries and the three-file function export passed. Probe names, comments and DEFAULT source priorities were restored and verified again after restart.

**Actual project knowledge:** qualified final application counts below. Zero means zero; the saved sources do not establish the expected months of human annotations.

| Program | Names | Signatures | Types | Comments | Bookmarks | Conflicts | IR/validation excerpts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ColorKeep | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| DistanceGradation | 0 | 0 | 0 | 0 | 0 | 1 | 45 |
| OLMBlur | 0 | 0 | 0 | 0 | 0 | 3 | 24 |
| OLMColorKey | 0 | 0 | 0 | 0 | 0 | 1 | 14 |
| OLMDirectionalBlur | 0 | 0 | 0 | 0 | 0 | 2 | 46 |
| OLMKiraKira | 0 | 0 | 0 | 0 | 0 | 2 | 35 |
| OLMRadialBlur | 0 | 0 | 0 | 0 | 0 | 2 | 65 |
| OLMSmoother | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| OLMSmoother2 | 0 | 0 | 0 | 0 | 0 | 1 | 99 |
| OLMToonDilate | 0 | 0 | 0 | 0 | 0 | 2 | 4 |

The expanded snapshot inventory checked 240 AEX/hash-related entries and found 0 USER_DEFINED symbols in readable entries. The targeted migration recorded 192 source records: 175 incompatible/unmatched records skipped, 1 unreadable entry, and 16 preserved conflicts. Analyzed `.aex.0` duplicates were found through metadata hashes. Other saved AEXs were often unanalyzed 16-bit real-mode imports. The unreadable source is the OLM2025 archived `OLMToonDilate/Plugins/64/2024/OLMToonDilate.aex` entry; Ghidra reports `EOFException: Buffer index too large (276 > 269)`. No repair or upgrade was attempted on originals.

An initial trial admitted unused Mach-O format types from unmatched C++ build artifacts. Those 89 `/MachO/` definitions were removed; the final policy rejects incompatible ABIs and unmatched binaries before applying types. The original trial and its correction remain in `knowledge-import-initial-trial.json` and `import-trial-correction.json`; remaining primitive dependency types are unused catalog entries, not applied signatures/data layouts.

**Seeded knowledge test (separate from user data):** name, namespace, signature, structure, EOL/comment, bookmark, conflict all passed. Applied 2 names, 2 types, 1 signature, 2 comments and 1 bookmark. A second transfer preserved a conflicting human name.

**Version demo:** flipped one PE checksum byte at file offset 352; imported `OLMBlur@9a46fbe75f29`, matched 65 functions and carried 12 comments. Ambiguous/tiny functions and unsafe interior/global annotations remain explicitly unmatched. The actual `add-version` CLI returned `reused=true` after restart, without re-analysis.

**Codex:** the real CLI exited 0; two successful `list_functions` calls reported 97/469 internal functions, then one `decompile_batch` returned 4/4 completed. Successful MCP tool events are retained in `logs/codex-smoke.jsonl`. An initial attempt correctly refused unannotated tools; the final run used read-only MCP annotations, `default_tools_approval_mode="writes"`, and a two-tool allow-list. No global Codex config was changed.

**Regression fixes verified:** raw DomainFile program ownership removed GhidraProject’s hidden outer transaction, making immediate rollback real; read-only MCP annotations and ASGI-scoped service shutdown preserve shared project lifetime; dynamic types no longer receive the composite-only `getComponents()` call. Ten unittest tests passed, plus the real JVM, HTTP, CLI and restart checks above.

**Source integrity:** all 4,076 original project files matched their copy-time SHA-256, size and mtime; originals were never opened as projects.

**Final shutdown:** server PID `23744` and owned PIDs `[49016, 2216, 2244, 64376, 23744, 61056]` exited; `forced=[]`, `remaining=[]`, `exited=true`. The server is stopped.
<!-- MACHINE_RESULTS_END -->

## Limits and evaluated reuse

This is a static-analysis tool, not an AE host or behavioral oracle. Ghidra's
analysis can miss indirect calls, function boundaries or types. Large batches
should use pagination/chunks. In-process writes are serialized; bypassing the hub
to edit the project in another process is unsupported. Cancellation of a client
does not cancel an in-flight transaction; per-function decompilation has a timeout.
Forced shutdown is reported separately and may abandon an in-flight unsaved
transaction. Normal transactions save before returning.

The installed GUI GhidraMCP README/TOOLS were inspected. Its per-window bridge does
not supply this shared project owner. The
[pyghidra-mcp 0.3.0 release](https://pypi.org/project/pyghidra-mcp/0.3.0/) was
downloaded and its code evaluated before implementing this hub. Its bounded pool
is reused with attribution; see [NOTICE.md](NOTICE.md). Full Chroma indexing and
the GUI plugin are not dependencies. The Cargo stub only satisfies the parent
workspace's `tools/*` member pattern. No other tool directory is modified.
