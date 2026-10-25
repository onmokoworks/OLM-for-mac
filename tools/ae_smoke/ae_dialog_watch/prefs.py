"""Scoped, reversible AE 26.3 scripting preference for authorized test runs."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

PREFS = Path.home() / 'Library/Preferences/Adobe/After Effects/26.3/Adobe After Effects 26.3 環境設定-indep-general.txt'
SECTION = b'["Main Pref Section v2"]'
KEY = b'"Pref_SCRIPTING_FILE_NETWORK_SECURITY"'


def idle():
    processes = subprocess.check_output(['ps', '-axo', 'comm='], text=True)
    if any(line.rstrip().endswith(('/MacOS/After Effects', '/aerender'))
           for line in processes.splitlines()):
        raise RuntimeError('AE busy; scripting preference untouched (retry --restore after exit)')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def enable_bytes(data):
    lines = data.splitlines(keepends=True)
    headers = [i for i, line in enumerate(lines) if line.strip() == SECTION]
    if len(headers) != 1:
        raise RuntimeError('Expected exactly one Main Pref Section v2')
    start = headers[0]
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith(b'[')), len(lines))
    matches = [i for i, line in enumerate(lines) if KEY in line]
    if len(matches) > 1 or any(not start < i < end for i in matches):
        raise RuntimeError('Ambiguous scripting preference location')
    before = None
    if matches:
        i = matches[0]
        match = re.fullmatch(rb'(\s*' + KEY + rb'\s*=\s*)(00|01)(\s*)', lines[i])
        if not match:
            raise RuntimeError('Unexpected scripting preference format')
        before = match[2].decode()
        lines[i] = match[1] + b'01' + match[3]
    else:
        newline = b'\r\n' if lines[start].endswith(b'\r\n') else lines[start][-1:]
        if newline not in (b'\r', b'\n', b'\r\n'):
            raise RuntimeError('Missing section newline')
        lines.insert(start + 1, b'\t' + KEY + b' = 01' + newline)
    return b''.join(lines), before


def scripting_prefs(directory, *, restore=False, source=None):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    record = directory / 'scripting-prefs.json'
    idle()
    if restore:
        result = json.loads(record.read_text())
        source = Path(result['source'])
        backup = Path(result['backup'])
        original = backup.read_bytes()
        if digest(original) != result['before_sha256']:
            raise RuntimeError('Scripting prefs backup hash mismatch')
        result['restore_before_sha256'] = digest(source.read_bytes())
        record.write_text(json.dumps(result, indent=2))
        idle()
        shutil.copy2(backup, source)
        result['restored_sha256'] = digest(source.read_bytes())
        result['restored'] = result['restored_sha256'] == result['before_sha256']
        record.write_text(json.dumps(result, indent=2))
        if not result['restored']:
            raise RuntimeError('Preference restore hash mismatch')
        return result
    if record.exists():
        raise RuntimeError('Use fresh prefs directory; never overwrite original backup')
    source = Path(source) if source is not None else PREFS
    original = source.read_bytes()
    enabled, before = enable_bytes(original)
    backup = directory / 'indep-general.original.txt'
    if backup.exists():
        raise RuntimeError('Original backup already exists')
    shutil.copy2(source, backup)
    if backup.read_bytes() != original:
        raise RuntimeError('Preference changed during backup')
    result = dict(source=str(source), backup=str(backup), before=before,
                  before_sha256=digest(original), backup_sha256=digest(backup.read_bytes()), restored=False)
    record.write_text(json.dumps(result, indent=2))
    idle()
    if source.read_bytes() != original:
        raise RuntimeError('Preference changed before write')
    source.write_bytes(enabled)
    actual = source.read_bytes()
    _, after = enable_bytes(actual)
    result.update(after=after, after_sha256=digest(actual))
    record.write_text(json.dumps(result, indent=2))
    if actual != enabled or after != '01':
        raise RuntimeError('Scripting preference readback failed')
    return result
