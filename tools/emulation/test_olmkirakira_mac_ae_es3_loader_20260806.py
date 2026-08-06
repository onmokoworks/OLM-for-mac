#!/usr/bin/env python3
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/"scripts/run_olmkirakira_mode4_case01_mac_ae_20260805.py").read_text(encoding="utf-8")
ast.parse(source)
for token in ('def loader_jsx(', 'LOADER_ENTER payload=', 'try{$.evalFile(payloadFile);', 'LOADER_RETURN', 'LOADER_FAIL error=', 'line=', 'file='):
    assert token in source,token
loader_section=source[source.index('def loader_jsx('):source.index('def main():')]
assert 'alert(' not in loader_section and 'throw ' not in loader_section and 'JSON.' not in loader_section
payload_section=source[source.index('def jsx('):source.index('def loader_jsx(')]
assert '$.evalFile' not in payload_section
assert 'if(app.project)app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);' in payload_section
assert 'app.newProject();var project=app.project;if(!project)' in payload_section
assert 'var project=app.newProject()' not in payload_section
print('PASS_OLMKIRAKIRA_MAC_AE_ES3_LOADER_20260806')
