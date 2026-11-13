"""Real HTTP throughput, three-reader/one-writer, rollback and add-version checks."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import time

from client import Client
from runtime import HOME, ORIGINALS, atomic_json


def main(skip_throughput=False):
    client = Client()
    programs = client.programs_list()
    originals = [p for p in programs if '@' not in p['name']]
    assert len(originals) == 10 and all(p['analyzed'] for p in originals)
    rows = list(client.all_functions(['OLMBlur', 'OLMRadialBlur']))
    items = [dict(program=r['program'], function=r['address']) for r in rows]
    runs = []
    for parallel in ([] if skip_throughput else [False, True, True, False]):
        client.reset_decompilers()
        start = time.perf_counter()
        result = client.decompile_batch(items=items, parallel=parallel)
        hashes = [hashlib.sha256((r.get('c') or '').encode()).hexdigest() for r in result['results']]
        run = dict(parallel=parallel, server_seconds=result['seconds'], wall_seconds=time.perf_counter()-start,
                   requested=len(items), completed=sum(r['completed'] for r in result['results']),
                   failures=[{k:v for k,v in r.items() if k != 'c'} for r in result['results'] if not r['completed']],
                   output_hashes=hashes)
        runs.append(run)
        atomic_json(HOME/'reports/throughput.json', runs)
        print(json.dumps({k:v for k,v in run.items() if k != 'output_hashes'}), flush=True)
    assert all(r['completed'] == len(items) for r in runs), 'Inspect actual decompilation failures'
    assert all(r['output_hashes'] == runs[0]['output_hashes'] for r in runs)

    chosen = next(r for r in rows if r['program'] == 'OLMBlur' and r['source'] == 'DEFAULT')
    address, original_name = chosen['address'], chosen['name']
    # Abort a transaction after its first mutation, then check the DB and decompiler state.
    try:
        client.bulk_edit(rows=[dict(program='OLMBlur', function=address, name='must_rollback'),
                               dict(program='OLMBlur', function='no_such_function', name='invalid')])
        raise AssertionError('Invalid transaction unexpectedly committed')
    except RuntimeError:
        pass
    assert client.list_functions(programs=['OLMBlur'], query='must_rollback')['total'] == 0
    barrier = threading.Barrier(4)
    def reader(index):
        c = Client()
        barrier.wait(timeout=10)
        completed = 0
        for _ in range(8):
            page = c.list_functions(programs=['OLMBlur', 'OLMRadialBlur'], limit=10)
            assert page['total'] == len(rows)
            result = c.decompile_batch(items=items[:6]+items[-6:])
            assert all(r['completed'] for r in result['results'])
            completed += len(result['results'])
        return dict(client=index, completed=completed)
    def writer():
        c = Client()
        barrier.wait(timeout=10)
        previous = original_name
        try:
            for n in range(8):
                name = f'hub_concurrency_probe_{n}'
                c.bulk_edit(rows=[dict(program='OLMBlur', function=address, name=name,
                                       expected_name=previous)], provenance='concurrency verification')
                previous = name
        finally:
            c.bulk_edit(rows=[dict(program='OLMBlur', function=address, name=original_name,
                                   comment=chosen['comment'])], provenance='restore concurrency probe')
        return dict(writer_transactions=9)
    with ThreadPoolExecutor(4) as executor:
        futures = [executor.submit(reader, i) for i in range(3)]+[executor.submit(writer)]
        stress = [f.result() for f in futures]
    atomic_json(HOME/'reports/concurrency.json', dict(clients=stress, rollback=True,
                                                    restored_name=original_name, functions=len(rows)))
    assert client.list_functions(programs=['OLMBlur'], query='hub_concurrency_probe_')['total'] == 0
    saved = client.export_function(program='OLMBlur', function=address)
    assert (Path(saved['directory'])/'function.c').stat().st_size > 0
    assert client.data_types(program='OLMBlur')['total'] > 0
    assert 'edges' in client.call_graph(program='OLMBlur', functions=[address], depth=1)
    assert 'to' in client.xrefs(program='OLMBlur', address=address)
    atomic_json(HOME/'reports/concurrency.json', dict(clients=stress, rollback=True, export=saved,
                                                    restored_name=original_name, functions=len(rows)))
    print(json.dumps(stress), flush=True)

    import pefile
    with tempfile.TemporaryDirectory(prefix='version-demo-', dir=HOME) as temporary:
        original = ORIGINALS/'OLMBlur.aex'
        data = bytearray(original.read_bytes())
        pe = pefile.PE(data=bytes(data))
        offset = pe.OPTIONAL_HEADER.get_field_absolute_offset('CheckSum')
        pe.close()
        data[offset] ^= 1
        patched = Path(temporary)/'OLMBlur-patched.aex'
        patched.write_bytes(data)
        demo = client.add_version(aex=str(patched), like='OLMBlur')
        demo['patch'] = dict(offset=offset, kind='PE checksum byte XOR 1', original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                             patched_sha256=hashlib.sha256(data).hexdigest())
        assert demo.get('report', {}).get('matched', 0) > 0 or demo.get('reused')
        atomic_json(HOME/'reports/add-version-demo.json', demo)
        print(json.dumps(demo), flush=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-throughput', action='store_true')
    main(parser.parse_args().skip_throughput)
