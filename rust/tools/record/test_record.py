import contextlib
import copy
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

import record
from contract import checked_blob, sha, size_expr, validate_profile, witness_spec, write_json


class ContractTests(unittest.TestCase):
    def test_size_expression(self):
        args = [{'type':'i32','bits_le':'03000000'}, {'type':'u32','bits_le':'05000000'}]
        self.assertEqual(size_expr({'mul':[{'arg':0},{'arg':1},16]}, args), 240)

    def test_negative_and_oversize(self):
        with self.assertRaises(ValueError): size_expr({'arg':0}, [{'type':'i32','bits_le':'ffffffff'}])
        with self.assertRaises(ValueError): size_expr(256*1024*1024+1, [])
        with self.assertRaises(ValueError): size_expr({'eval':'1+1'}, [])

    def test_identity_bound_profile(self):
        with self.assertRaises(ValueError):
            record.Capture(Path(__file__), {}, Path('.'), 1, 1)

    def test_bad_signature(self):
        p = {'schema_version':1,'functions':[{'name':'x','rva':'0x1','args':['vector'],'return':'void'}]}
        with self.assertRaises(ValueError): validate_profile(p)

    def test_alias_and_snapshot_integrity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'a.bin').write_bytes(b'abcdef')
            (root/'b.bin').write_bytes(b'cdefgh')
            buffers = [{'name':n,'size':6,'address':hex(a),'before':{'file':n+'.bin','sha256':sha(root/(n+'.bin'))}}
                       for n,a in [('a',100),('b',102)]]
            rec = {'status':'complete','buffers':buffers,'module':'x','rva':'0x1','return':{'type':'void'},
                   'args':[{'type':'ptr','bits_le':(102).to_bytes(8,'little').hex()}]}
            spec, regions = witness_spec(rec, root)
            self.assertEqual(regions, [[100,108]])
            self.assertEqual(bytes.fromhex(spec['buffers']['b0']['hex']), b'abcdefgh')
            self.assertEqual(spec['calls'][0]['args'][0]['offset'], 2)
            (root/'a.bin').write_bytes(b'xxxxxx')
            with self.assertRaises(ValueError): witness_spec(rec, root)

    def test_unresolved_pointer_rejected(self):
        rec = {'status':'complete','buffers':[],'args':[{'type':'ptr','bits_le':'0100000000000000'}]}
        with self.assertRaises(ValueError): witness_spec(rec, Path('.'))

    def test_incomplete_rejected(self):
        with self.assertRaises(ValueError): witness_spec({'status':'entered'}, Path('.'))

    def test_snapshot_traversal(self):
        with self.assertRaises(ValueError):
            checked_blob(Path.cwd(), {'before':{'file':'../escape'},'size':1}, 'before')


@unittest.skipUnless(os.name == 'nt', 'Windows native debug API')
class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = record.HERE / 'target/test-fixtures'
        cls.build.mkdir(parents=True, exist_ok=True)
        for source, crate, output in [('provider','cdylib','record_provider.dll'),('fixture','cdylib','fixture.dll'),('driver','bin','driver.exe')]:
            subprocess.run(['rustc','--edition=2021','--crate-type='+crate,'-C','opt-level=1',
                '-L',str(cls.build),str(record.HERE/f'tests/{source}.rs'),'-o',str(cls.build/output)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=60)
        cls.dll = cls.build / 'fixture.dll'
        import pefile
        with pefile.PE(str(cls.dll)) as pe:
            exports = {x.name.decode():hex(x.address) for x in pe.DIRECTORY_ENTRY_EXPORT.symbols}
        cls.profile = {'schema_version':1,'module_sha256':sha(cls.dll),'functions':[
            {'name':'mixed','rva':exports['mixed'],'args':['u64','f64','u32','f32','u64','ptr'],'return':'u64',
             'buffers':[{'arg':5,'size':8,'stride':8}]},
            {'name':'nested','rva':exports['nested'],'args':['u32'],'return':'u32'},
            {'name':'returned','rva':exports['returned'],'args':['u32','u32'],'return':'ptr','adapter':'fixture.returned',
             'buffers':[{'returned':True,'size':{'arg':0},'stride':1}]}],
            'imports':[{'name':'ippRecordFixture','args':['u64'],'return':'u64'}]}

    def run_fixture(self, mode='normal', max_calls=100, max_bytes=4096, timeout=10, profile=None):
        root = Path(tempfile.mkdtemp(prefix=mode+'-', dir=self.build))
        write_json(root/'profile.json', profile or self.profile)
        write_json(root/'request.json', {'mode':mode})
        args = SimpleNamespace(module=self.dll, profile=root/'profile.json', harness=self.build/'driver.exe',
            out=root/'capture', request=root/'request.json', route='smart8', width=3, height=3, seed=7,
            max_calls=max_calls, max_bytes=max_bytes, timeout=timeout)
        with contextlib.redirect_stdout(io.StringIO()):
            code = record.capture(args)
        out = root/'capture'
        manifest = json.loads((out/'manifest.json').read_text())
        self.assertTrue(manifest['cleanup_verified'])
        self.assertTrue(all(x['exit_code'] is not None for x in manifest['processes'].values()))
        rows = [json.loads(x) for x in (out/'calls.jsonl').read_text().splitlines()]
        return code, out, manifest, rows

    def test_threads_nested_imports_and_buffers(self):
        code, out, m, rows = self.run_fixture()
        self.assertEqual(code, 0, m)
        self.assertEqual(m['counts'], {'mixed':12,'nested':4,'returned':1,'ippRecordFixture':12})
        calls = [r for r in rows if r['name']=='mixed']
        self.assertEqual(len({r['tid'] for r in calls}), 4)
        self.assertEqual(sorted(int.from_bytes(bytes.fromhex(r['args'][0]['bits_le']),'little') for r in calls), list(range(12)))
        for r in calls:
            self.assertEqual(r['args'][1]['bits_le'], struct.pack('<d',-2.5).hex())
            self.assertEqual(r['args'][3]['bits_le'], '00000080')
            self.assertEqual(r['args'][4]['bits_le'], '1032547698badcfe')
            self.assertEqual(checked_blob(out,r['buffers'][0],'after').hex(),r['return']['bits_le'])
        nested = [r for r in rows if r['name']=='nested']
        self.assertEqual([r['return_order'] for r in nested], sorted((r['return_order'] for r in nested),reverse=True))
        returned = next(r for r in rows if r['name']=='returned')
        self.assertEqual(checked_blob(out,returned['buffers'][0],'after'),bytes((250+i)&255 for i in range(16)))
        with contextlib.redirect_stdout(io.StringIO()):
            result = record.replay(SimpleNamespace(record=out/f"calls/{returned['sequence']:06d}/record.json",
                out=out.parent/'replay', timeout=30, adapter=None,
                adapter_exe=record.HERE/'adapter/target/release/record-adapter.exe'))
        self.assertEqual(result,0)

    def test_call_budget(self):
        code, _, m, rows = self.run_fixture(max_calls=3)
        self.assertEqual(code,0,m)
        self.assertEqual(len(rows),3)
        self.assertTrue(m['budget_closed'])

    def test_byte_budget_keeps_render_running(self):
        code, _, m, rows = self.run_fixture(max_bytes=0)
        self.assertEqual(code,0,m)
        self.assertEqual(m['snapshot_bytes_reserved'],0)
        self.assertFalse(any(r['buffers'] for r in rows))
        self.assertEqual(m['budget_closed']['mixed'],'byte_budget')

    def test_zero_calls_not_success(self):
        code, _, m, _ = self.run_fixture(max_calls=0)
        self.assertEqual(code,2)
        self.assertEqual(m['classification'],'incomplete')

    def test_crash_preserves_records_and_cleanup(self):
        code, _, m, rows = self.run_fixture('crash')
        self.assertEqual(code,2)
        self.assertTrue(rows)
        self.assertTrue(all(r['status']=='complete' for r in rows))

    def test_queued_thread_breakpoints_during_single_step(self):
        # Multiple threads may already have queued INT3 events when their peer
        # starts a single-step. All calls must still be recorded exactly once.
        for _ in range(8):
            code, _, manifest, rows = self.run_fixture()
            self.assertEqual(code, 0, manifest)
            self.assertEqual(manifest['counts'], {'mixed':12,'nested':4,'returned':1,'ippRecordFixture':12})
            self.assertTrue(all(r['status']=='complete' for r in rows))

    def test_timeout_cleanup(self):
        code, _, m, _ = self.run_fixture('timeout',timeout=1)
        self.assertEqual(code,2)
        self.assertIn('TimeoutError',m['error'])

    def test_descendant_cleanup(self):
        code, _, m, _ = self.run_fixture('descendant')
        self.assertEqual(code,0,m)
        self.assertGreaterEqual(sum(x['image'].endswith('driver.exe') for x in m['processes'].values()),2)

    def test_oversized_snapshot_reservation(self):
        profile = copy.deepcopy(self.profile)
        profile['functions'][0]['buffers'][0]['size'] = 256*1024*1024
        code, _, m, _ = self.run_fixture(profile=profile,max_bytes=256*1024*1024)
        # Budget reservation includes both snapshots, so this is dropped before reading.
        self.assertEqual(code,0,m)
        self.assertEqual(m['budget_closed']['mixed'],'byte_budget')

    def test_bad_buffer_read_cleanup(self):
        profile = copy.deepcopy(self.profile)
        profile['functions'][0]['args'][0] = 'ptr'
        profile['functions'][0]['buffers'][0]['arg'] = 0
        code, _, m, _ = self.run_fixture(profile=profile)
        self.assertEqual(code, 2)
        self.assertEqual(m['classification'], 'error')

    def test_hash_mismatch_before_launch(self):
        profile = copy.deepcopy(self.profile)
        profile['module_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            self.run_fixture(profile=profile)

    def test_missing_import_before_launch(self):
        profile = copy.deepcopy(self.profile)
        profile['imports'][0]['name'] = 'not_an_import'
        with self.assertRaisesRegex(ValueError, 'absent'):
            self.run_fixture(profile=profile)


if __name__ == '__main__': unittest.main()
