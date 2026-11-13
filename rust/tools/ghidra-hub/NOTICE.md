`decompiler_pool.py` is vendored from the PyPI `pyghidra-mcp` 0.3.0 wheel
(clearbluejar, https://github.com/clearbluejar/pyghidra-mcp), under Apache-2.0.
Only an attribution header was added. See `LICENSE.pyghidra-mcp`.

The wheel was evaluated before implementation. Its headless multi-program
context and bounded pool are useful; the full application also brings ChromaDB
indexing and ghidrecomp, and does not supply this job's provenance-aware project
migration or atomic table-edit contract. The hub reuses the pool while supplying
its own project owner, transaction gates, batch API and lifecycle. It does not
load the GUI GhidraMCP extension or launch its bridge.

`knowledge.fingerprint` uses the same conservative ideas as the adjacent
`triage/TriageExport.java`: mask address operands and relocation bytes and retain
referenced literals. Its `hub-v1` serialization is distinct. Shape-only matching
is deliberately not used for automatic knowledge writes.
