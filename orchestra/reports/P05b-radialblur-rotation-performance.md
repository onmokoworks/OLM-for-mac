status: partial
summary: |
  Angle hoisting restores the original AEX's once-per-angle trig table.
  Heavy 1080p PF8/PF16/PF32 still exceeds 60 seconds with hoisting alone.
  A separately tested four-channel SSE-semantics helper is not yet connected.
  This is an interim checkpoint; validation and performance work continue.
facts:
- Read AGENT_GUIDE.md, tools/emulation/GOTCHAS.md, plan, and RadialBlur ledger restrictions.
- `memory_pressure`: initial 62% free; subsequent checks 54–61%.
- P00b driver retained-bundle baseline: 240x135 PF8 38.977331875 s, PF16 39.743749916 s, PF32 37.803886792 s; 480x270 all depths timeout at 60 s.
- `sample PID 2 1`: baseline hot stack is RenderRotationTyped; ARM64 disassembly at 0xc918 onward is the outer scatter contribution / accumulation loop.
- Original MAIN decomp/OLMRadialBlur.aex.c.txt lines 2054–2065 builds a paired trig table once per angle before radius traversal; lines 835–895 and FUN_180001c90 retain radius/angle/offset scatter traversal.
- Default seed 1 n300 after angle hoist: Smart 275 exact, 20 original rejects, 5 original budgets; no Smart mismatches or Mac-only refusals. Classic 2 exact, 126 mismatches, 172 refusals (contract route is Smart).
- `OLM_TEST_JOBS=1 python3 -m unittest discover -s tests -p 'test_*radialblur*.py'`: after SDK links were prepared, baseline 267 tests, 76 failures, 63 errors. Earlier missing-SDK run had 65 errors and is not the comparison baseline.
- `python3 tests/test_radialblur_scatter_simd_P05b.py`: 105832 scatter tuples / 423328 lane results match scalar SSE helpers, including NaN payloads, infinities, subnormals and signed zero.
inference:
- Hoisting matches original work organization but does not address the dominant heavy scatter cost. No performance-target claim.
changed_files:
- mac/OLMRadialBlur/OLMRadialBlur.cpp
- mac/OLMRadialBlur/RadialScatterSIMD.h (not connected at this checkpoint)
- tests/test_radialblur_scatter_simd_P05b.py
- orchestra/reports/P05b-evidence/verify.py
- orchestra/reports/P05b-radialblur-rotation-performance.md
verify:
- `python3 tests/test_radialblur_scatter_simd_P05b.py` expects OK.
- `python3 orchestra/reports/P05b-evidence/verify.py` runs sequential contract/replay campaigns, retaining real results under ticket scratch; final expected counts are pending.
next:
- Finish hoist measurements and verification; evaluate exact channel SIMD and preserve accumulation order.
- Acceptance, new corpus witnesses, final timing table, and scratch cleanup remain pending.
