# OLMKiraKira Executable Rejection Matrix

Date: 2026-07-16
Status: **pass**

## FACT

- Mode 1 and Mode 2 dispatch are statically grounded and retained by the local dispatch regression.
- Actual-AEX Mode 3 evidence grounds CV_32FC1, Size(0,1), and sigmaX=length*0.5.
- The portable Gaussian replay is exact against the local Unicorn diagnostic words, not a live-Windows oracle.
- The local merge-mode-1 compose and final 8bpc rounding invariant has one complete passing witness row.

## Matrix

| Check | Status | Decision | Evidence basis |
| --- | --- | --- | --- |
| `mode-1-dispatch-preserved` | **PASS** | retain one-pass dispatch | static audit marks Mode 1 as one boxFilter pass and the retained dispatch smoke passed |
| `mode-2-dispatch-preserved` | **PASS** | retain three-pass dispatch | static audit marks Mode 2 as three boxFilter passes and the retained dispatch smoke passed |
| `mode-3-aex-to-portable-replay` | **PASS** | accept only the call contract and keep replay diagnostic | actual-AEX captures CV_32FC1, Size(0,1), and sigma length*0.5; the portable Gaussian exists but is not wired |
| `mode-3-live-gaussian-promotion` | **REJECT** | reject production Gaussian promotion | live coefficient return is absent; retained dispatch audit labels its 63-word output emulation-only |
| `mode-4-implementation` | **REJECT** | reject inferred recursive/exponential implementation | static dispatch is known, but recurrence ordering and edge/writeback semantics remain unobserved |
| `merge-mode-2-compose` | **REJECT** | reject compose-mode-2 production claim | merge-mode-2 target is statically identified, but its post-aggregation compose behavior is unwitnessed |
| `merge-mode-1-local-compose` | **PASS** | retain screen RGB with source-alpha passthrough locally | local invariant report passes its complete witness row |
| `final-quantization-scope` | **REJECT** | retain nearest 8bpc rounding only within the local witness scope | one complete local row passes; three rows are incomplete and no cross-host exactness is claimed |

## INFERENCE

- No production Mode 3 Gaussian change is justified until a same-run live coefficient/output return is captured.
- No Mode 4 recurrence, merge-mode-2 compose, or broad final-quantization rewrite is justified by the current evidence.
- The strongest current advance is a fail-closed executable boundary that preserves grounded behavior and rejects unsupported promotions.

## LIMIT

- This matrix does not establish AE exactness or Windows/Mac equality.
- It intentionally does not edit the shared conformance ledger or production KiraKira render behavior.

## Reproduction

```sh
python3 scripts/audit_olmkirakira_rejection_matrix_20260716.py
```
