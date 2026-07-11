# OLM Plugin Verification Session Status (Updated 2026-07-06 Sonnet Session)

## Current Objectives
- Resolve conformance discrepancies in legacy plugins (RadialBlur, DirectionalBlur, Smoother2).
- Establish exact logic parity between `mac/` port and Windows decompiled traces.

## Overall Status

### 1. Smoother2 - MAJOR FIXES APPLIED (2026-07-06 Sonnet session)
#### Root Cause Found & Fixed (idx formula)
The build_polygon idx calculation was completely wrong. The Mac implementation used PRESENT-edge bits with wrong neighbor positions, while Ghidra (Windows) uses ABSENT-edge bits from completely different neighbor positions.

#### Root Cause Found & Fixed (Pruning Logic)
Mac port contained a "pruning" logic loop that aggressively zeroed out edge flags in the class plane before scanning. Windows does not use a pruned class plane for the cardinal scans (or at all in this context). 
Because of pruning, Mac scans would bypass intended boundaries and pick up distant colors (e.g. at `x=535`), resulting in vastly different accumulated colors.

#### Results after fixing idx + disabling pruning:
- Pixel (492,676) output exactly matches Windows target `(201, 0, 149)`.
- Legacy Smoke Test cases like `case_0003` are now **EXACT MATCH** (max=0).
- Remaining cases like `case_0004` dropped from `max=150` down to `max=22`, massively reducing errors.

---

### 2. RadialBlur (Zoom & Inner)
- **Zoom**: The alpha mismatch (0.99999994) was corrected, reducing max diff to `max=2`. This is essentially resolved.
- **Inner (IN PROGRESS)**: Subagent identified that the `fade_factor` calculation had the wrong order of operations. The correct logic is `min(span, 3000) * fade_factor`. However, applying this fix caused the C++ smoke test (`case_0011` etc.) to produce catastrophic diffs (`max=65535`).
- **Current Status**: Subagent dispatched to investigate the `65535` NaN/blackout issue.

---

### 3. DirectionalBlur
- **Problem**: angle-0 discrepancy.
- **Root Cause & Fix**: `ctx_render_scale` was falling back to 1.0 on Mac. Subagent fixed `OLMDirectionalBlur.cpp` to correctly fetch `downsample_x` and `downsample_y` from AE's `in_data` and synthesize a scale factor based on the blur angle.
- **Current Status**: Fix implemented at the AE plugin level. CLI tests may need manual scale injection or cannot verify this specific AE-host interaction.

---

## Files Modified This Session
- `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`: Fixed `idx` calculation, removed faulty `pruning` logic.
- `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`: Implemented proper `render_scale` retrieval from AE context.
- `cli/OLMRadialBlur/main.cpp`: Fixed Inner mode `min(span, 3000)` order of operations, and Zoom alpha logic (pending debug).
