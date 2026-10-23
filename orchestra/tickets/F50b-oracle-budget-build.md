# F50b: build and validate the deterministic-budget worker (continue F50)

## Facts
Read `orchestra/reports/F50-oracle-execution-limit.md` first. F46 stops guest execution on an internal 20 s wall-clock
limit, which makes slow cases load-dependent. F50 prepared a candidate patch (instruction budget of 2,000,000,000 per
scheduler slice) but could not build: Unicorn's build rejects spaces in the physical build directory (`OLM as`).

## Authorization (orchestrator)
Build in a space-free directory: `~/.cache/olm-emu/build-F50/` (create it; delete it after install). This satisfies the
scratch rule for this ticket. Install to `~/.cache/olm-emu/worker-F50-budget/` and add an INDEX entry.

## Do
Run F50's `next` steps 1-3 exactly: rebuild, smoke (deterministic exhaustion and normal return), corpus equivalence for
every plugin vs F46 (byte-identical), S01 slow-case transitions, DG/Radial seed 1 n300 totals. Propose (do not apply) the
fuzz default switch and the matching harness timeout.

## Rules
1-2 processes; `memory_pressure` >= 30% free before the Rust build. No plugin source changes. Never edit `04_Tools/AEXCompat*`.
