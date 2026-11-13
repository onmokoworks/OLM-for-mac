# OLM known-function library

`funcdb.py` indexes all internal function bodies discovered by the shared OLM-rs
Ghidra hub in the ten originals. It records address-independent instruction
hashes, referenced-literal hashes, a fuzzy sketch, body size, callers/callees,
direct imports, source evidence, and supported original-to-Rust/C++ mappings.
External imports are counted separately: they have no local body to fingerprint.
This is a function-discovery inventory, not proof that analysis found every
possible machine-code entry point.

All authored files are in this directory. No original binaries, instruction
bytes, disassembly, or decompiled code are stored in the distributable database.
No AE, GUI, render worker, independent Ghidra project, or background watcher is
used. The Cargo stub satisfies the parent workspace's `tools/*` member pattern.

## Run

Python 3.11, the pinned `requirements.txt` packages, and the adjacent hub are
required. The hub client itself uses only Python's standard library.

From the repository root in PowerShell:

```powershell
$py = 'D:/olm-rs-ghidra/venv/Scripts/python.exe'
& $py rust/tools/ghidra-hub/hub.py status
# Only when stopped; retain the returned PID and ownership:
& $py rust/tools/ghidra-hub/hub.py start --port 8766 --workers 3

python rust/tools/funcdb/funcdb.py build --annotate
python rust/tools/funcdb/funcdb.py stats
python rust/tools/funcdb/funcdb.py lookup --aex D:/incoming/New.aex

# Optional human-readable JSON and queryable SQLite (SQLite path must be new):
python rust/tools/funcdb/funcdb.py --db rust/tools/funcdb/local/catalog.json build --sqlite rust/tools/funcdb/local/catalog.sqlite
# Rebuild without one original, for a clean cross-plugin comparison:
python rust/tools/funcdb/funcdb.py --db rust/tools/funcdb/local/without-blur.json.gz build --exclude OLMBlur
python rust/tools/funcdb/funcdb.py --db rust/tools/funcdb/local/without-blur.json.gz lookup --aex '../ghidra_windows_aex/OLMBlur.aex' --out rust/tools/funcdb/runs/blur-holdout.json

# Stop ONLY a hub instance you started, after all your clients finish:
& $py rust/tools/ghidra-hub/hub.py stop
```

Global options `--db`, `--cache`, and `--url` precede the command. `build` accepts
`--originals DIR`, repeatable `--exclude PLUGIN`, `--sqlite PATH`, and
`--annotate`. Default originals are the adjacent `ghidra_windows_aex` directory;
default database is `catalog.json.gz` here (about 9 MB; not committed — regenerate it
with `build` from the originals; the reviewed mappings in `reviewed.json` are committed). `lookup --out` defaults to
`runs/<binary-sha256>/lookup.json.gz`; `--threshold` defaults to 0.65 and
`--exclude` can also exclude database candidates without rebuilding.
`stats` needs no hub. `annotate` writes an existing database's mappings back.

The CLI never starts or stops a server implicitly. `build` rejects a missing,
unanalyzed, or hash-mismatched named original. `lookup` reuses an equal-hash hub
program, or imports an unknown PE once as `funcdb-<stem>@<hash-prefix>` through
`add_program`. Import requires the binary to be accessible to the hub process.
New analyzed versions remain in the persistent project. API/setup failures
return nonzero; partial exports are never published as a complete database.

## Matching and work lists

Exact means equal normalized instructions, literal hashes and directly referenced
import identities. Direct call and out-of-body branch targets are abstracted;
in-body targets use instruction indexes. PE relocations and RIP-relative
addresses are abstracted while register widths, operation order and ordinary
immediates remain significant. Fixed-width loads from immutable non-code data
contribute literal hashes, excluding relocatable pointers, IAT slots and LEA.
Mutable globals and indirect tables are not a complete semantic dependency hash.

Fuzzy matching uses the bottom 48 SHA-256-derived 64-bit hashes of three-instruction
shingles after additionally abstracting immediates and memory displacements.
The score is a sampled Jaccard estimate multiplied by instruction-count ratio,
not an equivalence probability. An immediate-only edit can score 1.0 while failing
the exact hash. Indexed candidate retrieval avoids a full pairwise function scan;
all scored candidates satisfy the length ratio threshold. The top five fuzzy
candidates and total candidate count are reported. Exact duplicates are retained
in full, and tiny functions (fewer than five instructions) are marked.

The work list puts unknown functions first, then fuzzy, then exact, with size
descending inside each class. It distinguishes:

- `already-covered`: identical original binary hash and RVA with an explicit
  Rust mapping qualified by that plugin's existing validation corpus.
- `review-rust-reuse`: a candidate has a qualified Rust mapping, but this new
  function is not thereby proven covered. This includes cross-plugin matches.
- `port-or-classify`: no retained qualified Rust candidate.

Exact normalized matches can still call different functions or use different
global state. Compiler changes, indirect calls, jump tables, and ambiguous
duplicates require review. Shared CRT/IPP/OpenCV functions are included, so low
mapped coverage of a large statically linked plugin does not imply that most of
its effect algorithm remains unported.

## Discovery and evidence

The hub owns function discovery, names, comments, saved analysis and the static
call graph. The local decoder walks direct control flow from hub entries and
checks recovered byte counts against hub body sizes. A failed size check uses
the hub's `export_function` listing, including non-contiguous bodies. This API
also decompiles and writes local exports under `D:/olm-rs-ghidra/exports/`.
No per-function temporary headless analysis is launched.

Ghidra and Capstone disagree on some AVX-512 instructions in the linked libraries.
`decoder_overlap` marks overlapping instruction decodes; unsupported Capstone
instructions use explicitly domain-separated, address-normalized Ghidra listing
text hashes, counted by `listing_only_instructions`. `decoded_bytes` may differ
from the Ghidra body size (which can include data). These remain heuristic
candidates, not verified body reconstructions. Even equal byte counts are only
a structural check, not an independent boundary proof. Static call graphs omit
unresolved indirect calls; imports used are direct IAT references plus separately
named external callees, not exhaustive transitive runtime imports.

`evidence.py` scans the scoped text sources listed in the database's
`evidence_scan`. It records path, line, evidence kind and raw-file SHA-256.
Address mentions are indexed as evidence but do not create mappings. Direct
address-bearing Rust names/comments, explicit C++ entry labels, mechanically
translated same-name Smoother functions, and reviewed chains in `reviewed.json`
create mappings. C++ associations can identify only a component of a larger
original function; this is stated in their basis. Conflicting historical C++
definitions remain separate records. No name-only cross-compiler guessing is
promoted to verified Rust.

`qualification.json` binds qualification to specific existing `VALIDATION.md`
statements. `verified_rust` means **existing plugin-corpus qualification of the
mapped Rust implementation**, not an independent per-function proof or native
AE acceptance. Directional/Radial nondeterminism exclusions, Smoother's 8/16-only
contract, IPP/FMA CPU profiles and other report limits travel with each mapping.
Source hashes bind the inspected source evidence; they do not assert that later
source changes were revalidated against the historical candidate binary.

`--annotate`/`annotate` append source-linked mapping comments using the hub's
atomic-per-program `bulk_edit`; they never rename functions, alter signatures,
or replace imported human names. Repeating identical annotations is idempotent.
The public API has no namespace operation or comment compare-and-swap; comments
are merged from an immediate read. Avoid concurrent comment writers to the same
functions during this command. Transactions are not atomic across programs.

## Database and reproducibility

Canonical JSON uses sorted keys, stable program/RVA ordering, no timestamps,
deduplicated fingerprints, and deterministic gzip metadata. JSON is the canonical
input; optional SQLite exports it into `programs`, `functions`, `fingerprints`,
`mappings`, `evidence`, and `metadata` tables. Connections are explicitly closed.
SQLite output is deterministic with the same Python/SQLite runtime.

`stats` reports separate mapped and qualified-Rust function/byte percentages.
Byte coverage sums the full discovered body sizes for functions with a mapping;
it is not a percentage of individually proven instructions or of PE file bytes.
External imports are outside those denominators. Body overlaps can double-count
addresses. Mapping/evidence references are JSON array indexes.

Ignored `local/cache` stores only hashes and metadata, keyed by binary hash,
normalizer version, and checked hub address/size inventory. Live names are
refreshed. Resumable partial checkpoints are distinct from complete caches.
Delete or choose a fresh **task cache** when changing decoder versions or hub
analysis without changing its function address/size inventory; never delete the
shared hub project to refresh this tool. Final data includes the normalizer ID.

## Validation

```powershell
python -m unittest discover -s rust/tools/funcdb -v
python rust/tools/funcdb/verify_live.py --out rust/tools/funcdb/runs/verified-new
```

The live verifier builds ten separate holdout databases, each omitting its query
plugin's functions, mappings and exclusive fingerprints; it then looks up that
original and requires non-tiny shared matches. The synthetic fixture changes one
CMP immediate in a temporary OLMBlur copy outside the repository, requires
exactly the expected changed function, and verifies removal and original
integrity. A second temporary fixture applies actual PE relocations and changes
ImageBase while preserving import RVAs. Both imports use the persistent hub.
No fixture is executed as native code.

Full lookup reports and detailed diagnostics are ignored in `runs/`.
`retain_validation.py` reruns unit tests and checks completed reports, catalog
identity, shutdown and original hashes before updating `validation.json`.


### Verified on this machine

On 2026-11-12: **14 unittest tests passed**, all **40,880 internal bodies**
from ten originals were indexed, with **913 external functions** counted
separately. The 9,027,915-byte catalog contains **13,947 distinct fingerprint
records**, **2,282 evidence records**, and **104 mapping records** covering
**95 original functions**. **51 original functions** have explicit Rust mappings
qualified by the existing plugin corpora.

Two independent builds produced byte-identical gzip JSON and SQLite files:

- Catalog SHA-256: `cdaeba4bf31baa4d78722cbc66d93f0ed9e6ac39f89d25abce879033ce3394ea`.
- SQLite: 39,448,576 bytes; SHA-256
  `71523526e815b0e5ccbc5dbb2db9e33d5ade360d6d5ceb64af85b56dcd408a73`.
- Retained compact evidence: [validation.json](validation.json).

| Plugin | Internal functions | Mapped functions | Mapped functions % | Mapped bytes % | Qualified Rust functions |
|---|---:|---:|---:|---:|---:|
| ColorKeep | 83 | 3 | 3.614 | 13.734 | 3 |
| DistanceGradation | 16,569 | 1 | 0.006 | 0.001 | 1 |
| OLMBlur | 97 | 4 | 4.124 | 9.775 | 4 |
| OLMColorKey | 437 | 1 | 0.229 | 0.283 | 1 |
| OLMDirectionalBlur | 120 | 3 | 2.5 | 3.824 | 3 |
| OLMKiraKira | 16,323 | 1 | 0.006 | 0.001 | 1 |
| OLMRadialBlur | 469 | 2 | 0.426 | 0.897 | 2 |
| OLMSmoother | 114 | 17 | 14.912 | 61.045 | 14 |
| OLMSmoother2 | 559 | 60 | 10.733 | 18.96 | 19 |
| OLMToonDilate | 6,109 | 3 | 0.049 | 0.165 | 3 |

All ten actual holdout builds passed. No candidate or mapping from the held-out
plugin is present in its search database:

| Query original omitted from DB | Exact | Fuzzy | Unknown | Non-tiny exact matches |
|---|---:|---:|---:|---:|
| ColorKeep | 73 | 0 | 10 | 45 |
| DistanceGradation | 15,509 | 662 | 398 | 14,435 |
| OLMBlur | 81 | 0 | 16 | 49 |
| OLMColorKey | 325 | 67 | 45 | 239 |
| OLMDirectionalBlur | 90 | 5 | 25 | 55 |
| OLMKiraKira | 15,570 | 685 | 68 | 14,623 |
| OLMRadialBlur | 336 | 66 | 67 | 245 |
| OLMSmoother | 76 | 0 | 38 | 46 |
| OLMSmoother2 | 324 | 69 | 166 | 232 |
| OLMToonDilate | 5,925 | 177 | 7 | 5,463 |

A concrete shared noise helper is DirectionalBlur RVA `0x2590` versus RadialBlur
RVA `0x32a0`: both 275 bytes with identical normalized fingerprints. Hub
batch-decompilation also shows the same MT19937 recurrence and tempering
(static interpretation; no runtime claim). The two-program comparison found
75 exact matches. The optimized fuzzy-candidate bound reproduced the complete
Directional holdout candidate identities and scores.

**Synthetic constant edit:** file offset 1308 changes one CMP immediate at
instruction RVA `0x1119`, inside OLMBlur function RVA `0x1000`. Both hub analyses
have 97 functions; lookup against the full database gives **96 exact + 1 fuzzy**,
and the only changed fingerprint is **RVA `0x1000`**, as expected. The original
hash stays `f0611785...e96e5b`; modified hash is `2ed7fb84...5460cb`. The temporary
AEX was removed. A self-lookup of the original returns 97 exact matches and marks
its four explicitly mapped blur helpers `already-covered`.

**Rebase:** changing ImageBase from `0x180000000` to `0x190000000` and applying
DIR64 fixups preserves **97/97 fingerprints**, including literal/import hashes.
The valid relocated image hash is `9c3dddf5...058489`. An initial fixture made
with `pefile.relocate_image` corrupted import RVAs and was rejected; the final
fixture patches only relocation entries and ImageBase. Its rejected hub import
(`funcdb-OLMBlur-rebased@5649d362d40b`) remains recorded, outside the catalog.
The valid synthetic/rebase imports also remain in the persistent hub; temporary
AEX files are removed. No originals were copied into the repository.

**Analysis limits observed:** 147 functions have Ghidra/Capstone boundary
overlaps, including 14 with unsupported-opcode listing fallback; 143 have a
decoded-byte/body-size difference. These are reported in the database and lookup
warnings, not silently treated as verified instruction boundaries. `disasm/`
and `decomp/` are absent in this checkout. The evidence scan inspected 1,749
scoped text files; unmapped functions remain unknown rather than receiving
invented Rust names.

**Hub writeback/lifecycle:** 95 function comments were saved through ten bulk
transactions. All 40,880 names were checked unchanged; repeating annotation
returned no edits. This job started hub PID **3632**, shared its persistent
project, then stopped that exact owned instance. The hub reported graceful
shutdown, `forced=[]`, `remaining=[]`, `exited=true`; subsequent status was
`running=false`. All ten original file hashes were rechecked after completion.

The hub's public export API requires successful decompilation to return a
listing. If a future function cannot be exported, this tool fails with a partial
checkpoint instead of fabricating a fingerprint. A useful future hub API would
batch-export body ranges/instructions without requiring decompilation; no hub,
triage, oracle, scaffold, witness, production Rust or C++ source was edited here.
