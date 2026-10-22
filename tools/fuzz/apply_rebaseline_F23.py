"""Apply audited F23 production baselines, blocking whole plugins on regressions."""
import json
from pathlib import Path
import subprocess
import sys

subprocess.run([sys.executable, '-B', 'tools/fuzz/classify_rebaseline_F23.py'], check=True)
audit = json.loads(Path('orchestra/reports/F23-corpus-rebaseline-all-transitions.json').read_text())
blocked = {item['plugin'] for item in audit if item['forbidden']}
for item in audit:
    if item['plugin'] in blocked or not item['changes']:
        continue
    subprocess.run([
        sys.executable, '-B', 'tools/fuzz/rebaseline_corpus.py',
        '--plugin', item['plugin'], '--corpus', f'tests/fuzz_corpus/{item["corpus"]}',
        '--report', f'orchestra/state/F23-corpus-rebaseline-all/before-{item["corpus"]}.json',
        '--production-rebaseline', 'F23-corpus-rebaseline-all',
    ], check=True)
if blocked:
    raise SystemExit(f'Blocked plugins (not rebaselined): {sorted(blocked)}')
