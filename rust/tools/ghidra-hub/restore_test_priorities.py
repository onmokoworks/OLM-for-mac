"""Offline restoration of DEFAULT symbol priorities changed by the live writer test."""
import json
from runtime import HOME, ORIGINALS, atomic_json, open_project, sha256, start_jvm


def main():
    rows = {}
    for line in (HOME/'logs/transactions.jsonl').read_text(encoding='utf-8').splitlines():
        event = json.loads(line)
        if event.get('provenance') == 'restore concurrency probe':
            for row in event['rows']:
                rows[(row['program'], row['function'])] = row
    start_jvm()
    from ghidra.program.model.symbol import SourceType
    project = open_project()
    restored = []
    try:
        for (name, address), row in rows.items():
            if name != 'OLMBlur' or not row['name'].startswith('FUN_'):
                raise ValueError('Unexpected verification record')
            p = project.openProgram('/', name, False)
            assert str(p.getExecutableSHA256()) == sha256(ORIGINALS/'OLMBlur.aex')
            f = p.getFunctionManager().getFunctionAt(p.getAddressFactory().getAddress(address))
            if str(f.getName()) != row['name'] or str(f.getComment() or '') != row.get('comment', ''):
                raise RuntimeError('Probe was changed since restoration; refusing to overwrite')
            tx = p.startTransaction('Restore verification-only source priority')
            ok = False
            try:
                f.setName(None, SourceType.DEFAULT)
                assert str(f.getName()) == row['name']
                ok = True
            finally:
                p.endTransaction(tx, ok)
            project.save(p)
            restored.append(dict(program=name, address=address, name=row['name'], source='DEFAULT'))
    finally:
        project.close()
    atomic_json(HOME/'reports/restored-test-priorities.json', restored)
    print(json.dumps(restored))


if __name__ == '__main__':
    main()
