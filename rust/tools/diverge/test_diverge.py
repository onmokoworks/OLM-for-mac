"""Focused portable tests; native validations are in validate.py."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import olm_diverge as d


class ComparisonTests(unittest.TestCase):
    def test_first_element_and_coordinates(self):
        a = struct.pack('<6f', 0, 1, 2, 3, 4, 5)
        b = bytearray(a)
        b[16:20] = struct.pack('<I', 0x40800001)
        r = d.compare_bytes(a, b, 'f32', [2, 3])
        self.assertEqual(r['first_difference']['element'], 4)
        self.assertEqual(r['first_difference']['coordinate'], [1, 1])
        self.assertEqual(r['different_elements'], 1)
        self.assertEqual(r['first_difference']['reference']['value'], 4)

    def test_signed_zero(self):
        r = d.compare_bytes(bytes.fromhex('00000000'), bytes.fromhex('00000080'), 'f32', [1])
        self.assertEqual(r['status'], 'different')

    def test_nan_payload(self):
        r = d.compare_bytes(struct.pack('<I', 0x7fc00001), struct.pack('<I', 0x7fc00002), 'f32', [1])
        self.assertEqual(r['first_difference']['reference']['value'], 'nan')
        json.dumps(r, allow_nan=False)

    def test_integer_precision(self):
        a = struct.pack('<Q', 2**64-1)
        r = d.compare_bytes(a, bytes(8), 'u64', [1])
        self.assertEqual(r['first_difference']['reference']['value'], 2**64-1)

    def test_length_shape_type_rejection(self):
        for dtype, shape, raw in [('f32', [1], b''), ('f32', [0], b''), ('no', [1], bytes(4)), ('u8', [True], b'0')]:
            with self.subTest(dtype=dtype, shape=shape):
                with self.assertRaises(ValueError):
                    d.compare_bytes(raw, raw, dtype, shape)

    def test_multiple_mismatches_first_is_stable(self):
        r = d.compare_bytes(bytes(4), bytes([1, 0, 2, 3]), 'u8', [4])
        self.assertEqual(r['different_elements'], 3)
        self.assertEqual(r['first_difference']['element'], 0)


class ReproducerTests(unittest.TestCase):
    def test_closure_and_relocations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'ctx.bin').write_bytes(b'X'*16)
            (root/'data.bin').write_bytes(b'abcd')
            spec = {'schema_version': 1, 'module': 'dummy', 'buffers': {
                'ctx': {'size': 16, 'pointers': [{'offset': 0, 'buffer': 'data'}]},
                'data': {'size': 4}, 'unused': {'size': 100}}, 'calls': [
                {'rva': 1, 'args': []}, {'rva': 2, 'args': [{'type': 'ptr', 'buffer': 'ctx'}]}]}
            r = d.one_call_spec(spec, 1, {'calls': [{'buffers': {'ctx': 'ctx.bin', 'data': 'data.bin'}}]}, root)
            self.assertEqual(set(r['buffers']), {'ctx', 'data'})
            self.assertEqual(bytes.fromhex(r['buffers']['ctx']['hex']), bytes(8)+b'X'*8)
            self.assertEqual(len(r['calls']), 1)
            self.assertEqual(r['buffers']['data']['hex'], '61626364')
            self.assertEqual(len(spec['calls']), 2)

    def test_initial_file_fill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            f = root/'a.bin'
            f.write_bytes(b'x')
            spec = {'buffers': {'data': {'size': 3, 'fill': 65, 'file': str(f)}},
                    'calls': [{'args': [{'buffer': 'data'}]}]}
            r = d.one_call_spec(spec, 0, {}, root)
            self.assertEqual(r['buffers']['data']['hex'], b'xAA'.hex())
            self.assertNotIn('file', r['buffers']['data'])


class RunnerTests(unittest.TestCase):
    def case(self):
        spec = {'buffers': {'x': {'size': 4}}, 'calls': [{}]}
        return {'schema_version': 1, 'scope': 'test', 'stateless_calls': False,
                'reference': {'witness': copy.deepcopy(spec)}, 'candidate': {'witness': copy.deepcopy(spec)},
                'stages': [{'id': name, 'dtype': 'f32', 'shape': [1], 'grounding': 'fixture',
                            'reference': {'call': 0, 'buffer': 'x'}, 'candidate': {'call': 0, 'buffer': 'x'}}
                           for name in ['middle', 'late']]}

    def fake_run(self, spec, out, **kw):
        out.mkdir()
        (out/'x.bin').write_bytes(struct.pack('<f', 1 if out.name == 'reference' else 2))
        d.write_json(out/'result.json', {'calls': [{'buffers': {'x': 'x.bin'}, 'return': {'bits_le': '00000000'}}]})
        return {'classification': 'success', 'process': {'cleanup_verified': True}}

    def test_first_stage_not_last(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(d, 'prepare', side_effect=lambda c,b:c), patch.object(d.witness, 'run', side_effect=self.fake_run):
            r = d.run(self.case(), Path(tmp)/'run')
            self.assertEqual(r['classification'], 'divergent')
            self.assertEqual(r['first_divergent_stage'], 'middle')
            self.assertEqual(len(r['stages']), 2)

    def test_crash_is_not_divergence_or_exact(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(d, 'prepare', side_effect=lambda c,b:c), patch.object(d.witness, 'run', return_value={'classification': 'child_failure', 'process': {'cleanup_verified': True}}):
            r = d.run(self.case(), Path(tmp)/'run')
            self.assertEqual(r['classification'], 'incomplete')
            self.assertIsNone(r['first_divergent_stage'])
            self.assertEqual(r['stages'], [])

    def test_return_status_error_is_incomplete(self):
        c = self.case()
        c['candidate']['return_bits'] = {'0': 'ffffffff'}
        with tempfile.TemporaryDirectory() as tmp, patch.object(d, 'prepare', side_effect=lambda c,b:c), patch.object(d.witness, 'run', side_effect=self.fake_run):
            r = d.run(c, Path(tmp)/'run')
            self.assertEqual(r['classification'], 'incomplete')
            self.assertIn('diagnostic returned', r['error'])

    def test_hash_mismatch_rejected_before_native_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'module').write_bytes(b'bad')
            c = self.case()
            c['reference'].update(sha256='0'*64)
            c['reference']['witness']['module'] = 'module'
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                d.prepare(c, root)

    def test_path_escape_rejected(self):
        stage = self.case()['stages'][0]
        with self.assertRaisesRegex(ValueError, 'escapes'):
            d.select_bytes(stage, 'reference', {'calls': [{'buffers': {'x': '../outside.bin'}}]}, Path('run'))


class MapTests(unittest.TestCase):
    def build(self, plugin='distance', **kw):
        import stage_maps as m
        with patch.object(d.witness, 'sha256', side_effect=lambda p: m.PINS[plugin][1] if Path(p).name == 'original' else '1'*64):
            return m.build(plugin, Path('original'), Path('candidate'), **kw)

    def test_gaussian_native_control_and_abi(self):
        c = self.build()
        self.assertEqual([s['id'] for s in c['stages']], ['input', 'gaussian.row', 'gaussian.column'])
        ref = c['reference']['witness']
        self.assertEqual(ref['buffers']['input_mat']['size'], 40)
        self.assertEqual(ref['buffers']['input_mat']['pointers'][0]['offset'], 24)
        self.assertEqual(len(ref['calls']), 3)
        self.assertEqual(ref['calls'][2]['args'][4]['value'], 11)
        self.assertEqual(c['controls'][0]['right'], 'full')

    def test_special_dispatch_not_misrepresented(self):
        for kw in ({'w': 1}, {'h': 1}, {'kx': 3, 'ky': 3}, {'kx': 4}):
            with self.assertRaises(ValueError):
                self.build(**kw)

    def test_middle_only_injection_and_historical_mode(self):
        c = self.build(inject=0, historical=True)
        calls = c['candidate']['witness']['calls']
        self.assertEqual([x['args'][-1]['value'] for x in calls], [0, -1])
        self.assertEqual([x['args'][-2]['value'] for x in calls], [0, 0])

    def test_directional_rotation_sign_and_pixel_shape(self):
        c = self.build('directional', angle=.5)
        self.assertEqual(c['stages'][1]['shape'], [11,17,4])
        calls = c['reference']['witness']['calls']
        self.assertEqual([x['args'][4]['value'] for x in calls], [.5, -.5])

    def test_capture_preserves_destination_initializer(self):
        import capture
        import stage_maps as m
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d.write_json(root/'stage.json', {'plugin':'directional','width':3,'height':3,'ordinal':1,'angle_bits':0})
            (root/'input.bin').write_bytes(bytes(3*3*16))
            (root/'initial.bin').write_bytes(b'A'*(3*3*16))
            with patch.object(d.witness, 'sha256', side_effect=lambda p: m.PINS['directional'][1] if Path(p).name == 'original' else '1'*64):
                c, _ = capture.from_capture(root, Path('original'), Path('candidate'), 0)
            self.assertEqual(c['stages'][1]['id'], 'rotate[1]')
            self.assertEqual(c['candidate']['witness']['calls'][0]['args'][-1]['value'], -1)
            self.assertEqual(c['candidate']['witness']['buffers']['middle']['hex'], (b'A'*144).hex())


class ReducerTests(unittest.TestCase):
    def fixture(self):
        spec = {'buffers': {'input': {'size':16, 'hex':struct.pack('<4f',1,2,3,4).hex()}}}
        return {'stages':[{'id':'middle','dtype':'f32'}],
                'reference':{'witness':copy.deepcopy(spec)},'candidate':{'witness':copy.deepcopy(spec)}}

    def test_reduces_to_required_two_elements(self):
        import minimize
        def fake(case, *args, **kw):
            b = bytes.fromhex(case['candidate']['witness']['buffers']['input']['hex'])
            different = b[4:8] != bytes(4) and b[12:16] != bytes(4)
            return {'classification':'divergent' if different else 'exact', 'first_divergent_stage':'middle' if different else None}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d.write_json(root/'case.json', self.fixture())
            with patch.object(d,'prepare',side_effect=lambda c,b:c), patch.object(d,'run',side_effect=fake):
                r = minimize.minimize(root/'case.json',root/'out')
            self.assertEqual(r['remaining_indices'],[1,3])
            self.assertTrue(r['one_minimal_under_single_word_zeroing'])

    def test_budget_is_not_a_minimality_claim(self):
        import minimize
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d.write_json(root/'case.json', self.fixture())
            with patch.object(d,'prepare',side_effect=lambda c,b:c), patch.object(d,'run',return_value={'classification':'divergent','first_divergent_stage':'middle'}):
                r = minimize.minimize(root/'case.json',root/'out',budget=1)
            self.assertTrue(r['budget_exhausted'])
            self.assertFalse(r['one_minimal_under_single_word_zeroing'])

    def test_unequal_inputs_refused(self):
        import minimize
        c = self.fixture()
        c['candidate']['witness']['buffers']['input']['hex'] = bytes(16).hex()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d.write_json(root/'case.json',c)
            with patch.object(d,'prepare',side_effect=lambda c,b:c):
                with self.assertRaisesRegex(ValueError,'identical'):
                    minimize.minimize(root/'case.json',root/'out')


if __name__ == '__main__':
    unittest.main()
