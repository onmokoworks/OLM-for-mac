# KiraKira SDK UI comparison

`python3 mac/OLMKiraKira/tests/ui_compare.py` builds an Objective-C++ SDK host
and replays every committed KiraKira U03 witness plus `ui_witnesses/`. Exit 0
requires exact event snapshots and ordered suite calls on all 13 sessions / 159
dispatches. `--only KiraKira-presets` limits investigation; `--no-build` requires
a matching source/executable binding. Output and builds go only to
`orchestra/state/U02b-kirakira-ui-vs-original/`.

The host includes production `OLMKiraKira.cpp` and calls `EffectMain` for EVENT,
UPDATE, and setdown. Each original session's **first before snapshot** is an
explicit initial condition, loaded via actual arbitrary UNFLATTEN callbacks.
It is not a test of ParamsSetup. Later snapshots read the live SDK scalar fields
and actual arbitrary FLATTEN output, never expected results. Theme/picker inputs,
context window type, frame, continuation, time and original RNG seed are supplied
from the request. NewDefaultFont sizes, UTF-16, coordinates and colors are
recorded as exact bits. U03 does not inject a font rasterizer or screen scale;
these sessions do not call font-size/scale query APIs. Unknown suites abort;
unimplemented callbacks cannot silently succeed. Objects must be released.

The JSON event object has U03's keys and values. The Mac file additionally stores
RNG before/after, checked against the original image-state observations when
requested. Original setup/provenance fields are not copied into Mac output and
are not claimed to describe Mac setup. `ui-build.json` binds the host and plugin
sources; fixture request/compressed hashes are checked before replay.

KiraKira's saved format is version 1, count, and capacity for sixteen 20-byte
records: 325 bytes. Comparison checks the version/count/active records exactly;
it separately reports raw payload differences and retains full raw Mac output.
Original unused capacity contains unstable stack bytes, including apparent
pointers. No raw-buffer equality is claimed, and no original tail is injected
into results. Production saved-project callbacks remain unchanged: the Mac
writer zeroes inactive capacity. `persistence.py` independently checks all 34
original valid preset payloads through real UNFLATTEN/COPY/FLATTEN callbacks.

`python3 mac/OLMKiraKira/tests/ui_matrix.py` regenerates the additional original
witnesses with the immutable cached U03 worker, using natural clicks/drags only.
This intentionally updates their raw-tail bytes and manifest hashes. Added
coverage includes 0/1/16 stops and rejected seventeenth insertion; horizontal
marker ±5/±6 and vertical 59/60/70/71 boundaries; all five slots and hover;
non-gray themes; first and last valid preset selection and maximum scroll.
Existing U03 witnesses cover +20/+21 deletion, insertion, picker accept/cancel,
copy across ramps, two randomizations, flip and negative contexts.

This establishes handler-call parity for these requests. Native AE scheduling,
font rasterization, undo and project reopening remain separate host acceptance.
