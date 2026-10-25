status: partial
summary: |
  Checkpoint: factored UI-only ramp/button logic and draw-command builder, integrated AE suites.
  Unit interaction/drawing assertions pass; render regression and scratch-only bundle build running.
  Found ticket/U01 discrepancy: original has 34 presets, not 64 (64 is preview width).
  Implemented the 34 valid presets following original-binary ground truth; UI trace comparison pending U03.
facts:
  - `TMPDIR="$PWD/orchestra/state/U02-kirakira-ramp-editor" clang++ -std=c++17 -O2 -ffp-contract=off mac/OLMKiraKira/tests/ramp_editor.cpp -o orchestra/state/U02-kirakira-ramp-editor/ramp_editor` and executable: exit 0, interaction/drawing assertions passed.
  - MAIN emulation Python ran `mac/OLMKiraKira/tests/original_ui_constants.py`: exit 0; constructor bytes assert count=0x22, preview width=0x40; first 34 payload counts are 3 or 5, entry34 count=2172092144.
  - Static original handlers inspected: 181235bb0,181235950,181236260,1812366b0,181236520,181235000,181235250,1812355e0,181235760,181236130,1812342a0,181233ed0,181234320,181239220,181235460,1812346f0,1812392b0,181233860,181232080,181230cd0,181156780.
  - Real callback flatten/unflatten/copy/flatten: 34 valid original presets byte-identical; zero live handles.
  - Universal Release scratch build succeeded for x86_64 and arm64.
  - Initial 383 size-256 corpus cases replay true; final source replay running.
  - U03 worker directory and tests/ui_oracle absent at checkpoint.
inference: |
  The original preset count was confused with its preview width in U01. Reading 64 entries would consume unrelated PE data.
  Draw-call resource ordering is not yet oracle-qualified; source inspection and unit assertions do not establish exact UI parity.
changed_files:
  - mac/OLMKiraKira/OLMKiraKira.cpp
  - mac/OLMKiraKira/RampEditor.h
  - mac/OLMKiraKira/RampPresets.h
  - mac/OLMKiraKira/tests/persistence.cpp
  - mac/OLMKiraKira/tests/persistence.py
  - mac/OLMKiraKira/tests/render_unchanged.py
  - mac/OLMKiraKira/tests/replay_corpora.py
  - mac/OLMKiraKira/tests/ramp_editor.cpp
  - mac/OLMKiraKira/tests/original_ui_constants.py
  - orchestra/reports/U02-kirakira-ramp-editor.md
verify: |
  mkdir -p orchestra/state/U02-kirakira-ramp-editor
  TMPDIR="$PWD/orchestra/state/U02-kirakira-ramp-editor" clang++ -std=c++17 -O2 -ffp-contract=off mac/OLMKiraKira/tests/ramp_editor.cpp -o orchestra/state/U02-kirakira-ramp-editor/ramp_editor
  orchestra/state/U02-kirakira-ramp-editor/ramp_editor
  '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' mac/OLMKiraKira/tests/original_ui_constants.py
  Expected: exit 0, assertions passed; evidence records 34 valid table entries and exact float constants.
next: Finish verification; original resource/query ordering and UI payload/draw trace comparison pending U03. Native AE checks later with user.
