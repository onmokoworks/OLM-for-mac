status: partial
summary: |
  Checkpoint: original setup executed successfully for all ten plugins using cached Unicorn worker.
  KiraKira alone registers custom controls: five 310x170 Ramp panels; RadialBlur's custom flag is dormant.
  No imported GDI/user32 drawing APIs were found. Active ramp drawing uses AE Drawbot.
  Current Mac checkout already implements partial ramp editing and several UPDATE handlers.
  Completing address-backed interaction/update details and ordered follow-up tickets next.
facts:
- `python3 orchestra/reports/U01-ui-setup.py orchestra/state/U01-custom-ui-survey/setup`: 10/10 setup commands returned 0; GLOBAL_SETUP and PARAMS_SETUP errors all 0; unsupported suite calls all empty.
- `MAIN/tools/emulation/.venv/bin/python orchestra/reports/U01-ui-inventory.py`: ten PE SHA256/PiPL/import/active-vtable records, in U01-ui-inventory.json.
- Original ECW controls: KiraKira slots 14/20/26/32/38, ui_flags 0x82, 310x170; none of ten registers PF_PUI_ECW_SEPARATOR.
- Numerical rendering comparison was not performed; no pixel mismatch count is claimed.
inference: |
  The highest-value remaining implementation is completing KiraKira's ramp surface, followed by auditing dynamic controls rather than adding arbitrary custom previews to the other nine plugins.
changed_files:
- orchestra/reports/U01-custom-ui-survey.md
- orchestra/reports/U01-ui-inventory.py
- orchestra/reports/U01-ui-inventory.json
- orchestra/reports/U01-ui-setup.py
- orchestra/reports/U01-ui-setup.json
verify: |
  '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' orchestra/reports/U01-ui-inventory.py
  python3 orchestra/reports/U01-ui-setup.py orchestra/state/U01-custom-ui-survey/recheck
  Expected: identical inventory and setup summary; ten exit-zero lines.
next: Complete survey details in this ticket. No plugin source edits.
