# OLM RadialBlur UI setup actual-AEX gate — 2026-08-06

Status: **PASS (bounded public UI exact)**

The pinned Windows AEX executes `GLOBAL_SETUP -> PARAMS_SETUP` under Unicorn and emits all 30 definitions. The current Mac source emits the same public order, disk IDs, types, names, defaults, ranges, and precision.

The actual AEX's supervised/custom-UI flags and related global bits are recorded but intentionally not advertised on Mac until its EVENT/UPDATE handlers are ported. Group controls use native GROUP_START/GROUP_END, so the former unsupported NO_DATA preview controls are no longer present.
