# OLM RadialBlur UI setup actual-AEX gate — 2026-08-06

Status: **PASS (setup and registration exact)**

The pinned Windows AEX executes `GLOBAL_SETUP -> PARAMS_SETUP` under Unicorn and emits all 30 definitions. The current Mac source emits the same public order, disk IDs, types, names, defaults, ranges, and precision.

The Mac implementation now emits the exact global flags and per-parameter flags/UI flags. The actual setup does not call `PF_REGISTER_UI`; neither does Mac. Group controls remain native GROUP_START/GROUP_END, and no unsupported NO_DATA preview placeholder is present. Dynamic enable-state behavior is covered by the focused selector contract gate.
