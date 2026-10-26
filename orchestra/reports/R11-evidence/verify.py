#!/usr/bin/env python3
"""Audit R11 ZIP contents, including text in nested validation ZIPs."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

root = Path(__file__).resolve().parents[3]
scratch = root / 'orchestra/state/R11-release-package-and-notes'
scratch.mkdir(parents=True, exist_ok=True)
package = Path(sys.argv[1]).resolve()
evidence = Path(sys.argv[2]) if len(sys.argv) > 2 else scratch
text_count = 0
nested_count = 0
path_hits = []
# Machine-specific absolute paths; ~ and /path/to examples are portable docs.
local_path = re.compile(r'/(?:Users|Volumes|private|tmp|var/folders|home|Applications)/|[A-Za-z]:[\\/]')

def scan(archive, prefix=''):
    global text_count, nested_count
    for entry in archive.infolist():
        if entry.is_dir():
            continue
        data = archive.read(entry)
        name = prefix + entry.filename
        if entry.filename.endswith('.zip'):
            nested_count += 1
            with zipfile.ZipFile(io.BytesIO(data)) as child:
                scan(child, name + '!/')
            continue
        try:
            value = data.decode('utf-8')
        except UnicodeDecodeError:
            continue
        if '\0' in value:
            continue
        text_count += 1
        for number, line in enumerate(value.splitlines(), 1):
            if local_path.search(line):
                path_hits.append({'file': name, 'line': number, 'text': line})

def command(*args):
    return subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).stdout.strip()

with zipfile.ZipFile(package) as archive:
    listing = archive.namelist()
    scan(archive)
assert not path_hits, path_hits
with tempfile.TemporaryDirectory(dir=scratch, prefix='audit-') as tmp:
    command('ditto', '-x', '-k', str(package), tmp)
    stage = Path(tmp) / 'OLM_Mac_Plugins_Release'
    manifest = json.loads((stage / 'manifest.json').read_text())
    assert manifest['git_dirty'] is False, manifest['git_dirty']
    assert manifest['configuration'] == 'Release'
    fields = ['install_guide_ja', 'install_guide_en', 'beta_support', 'beta_support_en',
              'known_limitations', 'known_limitations_en', 'release_notes_ja',
              'release_notes_en', 'readme_ja', 'readme_en', 'license']
    for field in fields:
        assert (stage / manifest[field]).is_file(), field
    assert not any('OLM_MAC_RELEASE_NOTES_20260806' in x for x in listing)
    assert len(list(stage.glob('*.plugin'))) == len(manifest['plugins']) == 10
    rows = []
    for plugin in manifest['plugins']:
        bundle = stage / plugin['bundle']
        binary = bundle / 'Contents/MacOS' / plugin['name']
        archs = command('lipo', '-archs', str(binary)).split()
        assert set(archs) == {'arm64', 'x86_64'}
        minos = {}
        for arch in archs:
            build = command('xcrun', 'vtool', '-show-build', '-arch', arch, str(binary))
            minos[arch] = re.search(r'\bminos\s+(\S+)', build)[1]
            assert minos[arch] == '11.0'
        detail = command('codesign', '-dv', '--verbose=4', str(bundle))
        assert 'Signature=adhoc' in detail.splitlines()
        command('codesign', '--verify', '--deep', '--strict', str(bundle))
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        assert digest == plugin['binary_sha256']
        assert minos == plugin['minimum_macos']
        assert plugin['signing_kind'] == 'adhoc'
        rows.append({'name': plugin['name'], 'architectures': archs,
                     'minos': minos, 'signature': 'adhoc', 'binary_sha256': digest})
    # Check all relative Markdown links in public docs (anchors are not file paths).
    public = list(stage.glob('*.md')) + list((stage / 'docs').glob('*.md'))
    for doc in public:
        for link in re.findall(r'\]\(([^)]+)\)', doc.read_text()):
            if '://' in link or link.startswith('#'):
                continue
            target = link.split('#', 1)[0]
            assert (doc.parent / target).is_file(), (doc.name, target)
    for language in ['JA', 'EN']:
        name = f'RELEASE_NOTES_{language}.md'
        assert (stage / 'docs' / name).read_bytes() == (root / 'docs' / name).read_bytes()
summary = {'package': str(package), 'sha256': hashlib.file_digest(package.open('rb'), 'sha256').hexdigest(),
           'git_commit': manifest['git_commit'], 'git_dirty': manifest['git_dirty'],
           'zip_entries': len(listing), 'text_files_checked': text_count,
           'nested_zips_checked': nested_count, 'local_path_hits': path_hits, 'plugins': rows}
evidence.mkdir(parents=True, exist_ok=True)
(evidence / 'zip-contents.txt').write_text('\n'.join(listing) + '\n')
(evidence / 'package-audit.json').write_text(json.dumps(summary, indent=2) + '\n')
print(f"PASS: 10 Universal/ad-hoc bundles, minos 11.0; {text_count} text files, {nested_count} nested ZIPs; no local paths; docs and links present")
print('SHA-256:', summary['sha256'])
