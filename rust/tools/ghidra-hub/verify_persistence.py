"""Read after restart and exercise the actual add-version CLI's reuse path."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import pefile
from client import Client
from runtime import HOME, ORIGINALS, atomic_json


def main():
    c = Client()
    programs = c.programs_list()
    by_name = {p['name']: p for p in programs}
    for original in json.loads((HOME/'reports/bootstrap.json').read_text()):
        p = by_name[original['program']]
        assert p['sha256'] == original['sha256'] and p['analyzed']
        assert p['functions'] == original['functions']
    assert c.list_functions(programs=['OLMBlur'], query='hub_concurrency_probe_')['total'] == 0
    assert c.list_functions(programs=['OLMBlur'], query='must_rollback')['total'] == 0
    rows = list(c.all_functions(['OLMBlur']))
    for restored in json.loads((HOME/'reports/restored-test-priorities.json').read_text()):
        row = next(r for r in rows if r['address'] == restored['address'])
        assert row['source'] == 'DEFAULT' and row['name'] == restored['name']
    version = json.loads((HOME/'reports/add-version-demo.json').read_text())['program']
    assert by_name[version]['analyzed']
    version_rows = list(c.all_functions([version]))
    assert any('[Imported add-version:OLMBlur]' in r['comment'] for r in version_rows)
    items = [dict(program=version, function=version_rows[0]['address']),
             dict(program='OLMBlur', function=rows[0]['address'])]
    result = c.decompile_batch(items=items)
    assert all(r['completed'] for r in result['results'])
    with tempfile.TemporaryDirectory(prefix='reuse-', dir=HOME) as temporary:
        data = bytearray((ORIGINALS/'OLMBlur.aex').read_bytes())
        pe = pefile.PE(data=bytes(data))
        data[pe.OPTIONAL_HEADER.get_field_absolute_offset('CheckSum')] ^= 1
        pe.close()
        patched = Path(temporary)/'patched.aex'
        patched.write_bytes(data)
        process = subprocess.run([sys.executable, str(Path(__file__).with_name('hub.py')),
                                  'add-version', '--aex', str(patched), '--like', 'OLMBlur'],
                                 capture_output=True, text=True, timeout=30, check=True)
        reuse = json.loads(process.stdout)
        assert reuse['reused'] and reuse['program'] == version
    report = dict(programs=programs, originals_verified=10, restored_priorities=True,
                  persisted_version=version, decompiled_after_restart=2, cli_reuse=reuse)
    atomic_json(HOME/'reports/persistence.json', report)
    print(json.dumps({k:v for k,v in report.items() if k != 'programs'}))


if __name__ == '__main__':
    main()
