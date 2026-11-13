"""Fast synthetic tests; real AEX checks live in verify_all.py."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock
import olm_scaffold as s


def pipl(props):
    data=b'\x01\0\0\0\0\0'+struct.pack('<I',len(props))
    for key,value in props:
        data+=b'MIB8'+key[::-1]+struct.pack('<II',0,len(value))+value+b'\0'*((-len(value))%4)
    return data


def example():
    p={"slot":1,"add_index":-1,"supported":True,"name":[80]+[0]*31,"arrays":[],
       "fields":{"uu.id":501,"flags":128,"ui_flags":32,"ui_width":0,"ui_height":0,"param_type":7,
                 "u.pd.value":0,"u.pd.dephault":2,"u.pd.num_choices":3},
       "label":["u.pd.u.namesptr",list(b'A|B|C|D')]}
    cap={"schema_version":1,"version":123,"flags":33554496,"flags2":134222848,"num_params":2,
         "custom_ui_events":4,"params":[p]}
    inv={"parameters":[{"slot":1,"name":"P","supervised":False}],
         "host":{"reported_num_params":2,"parameter_metadata":[{"index":1,"type":"popup"}],
                 "advertised_out_flags":33554496,"advertised_out_flags2":134222848,
                 "image_render_supported":True,"plugin_data":None}}
    return inv,cap


class ScaffoldTests(unittest.TestCase):
    def test_probe_honors_job_target_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); capture=root/'capture';capture.mkdir()
            target=root/'job-target';(target/'debug').mkdir(parents=True)
            (target/'debug/olm_scaffold_probe.dll').write_bytes(b'probe')
            with mock.patch.dict(s.os.environ, {'CARGO_TARGET_DIR':str(target)}), mock.patch.object(s,'run_checked') as run:
                probe=s.build_probe(object(),capture)
            args=run.call_args.args[1]
            self.assertEqual(args[args.index('--target-dir')+1],target.resolve())
            self.assertEqual(probe.read_bytes(),b'probe')
    def test_pipl_short_einf_and_nonascii_bytes_retained(self):
        data=pipl([(b'eINF',b'\0\0'),(b'eVER',b'\0\x88\x08\0')])
        self.assertEqual(s.pipl_properties(data),{'eINF':b'\0\0','eVER':b'\0\x88\x08\0'})

    def test_pipl_truncation_and_trailing_bytes_rejected(self):
        data=pipl([(b'eINF',b'\0\0')])
        for bad in (data[:-1],data+b'\0',b'',data[:10]):
            with self.subTest(bad=bad),self.assertRaises(ValueError):s.pipl_properties(bad)

    def test_duplicate_properties_not_silently_discarded(self):
        with self.assertRaises(ValueError):s.pipl_properties(pipl([(b'name',b'\0'),(b'name',b'\0')]))

    def test_disk_id_flags_popup_count_and_initial_default_are_distinct(self):
        inv,cap=example();s.validate_capture(inv,cap);text=s.params_source(inv,cap)
        for exact in ('p.uu.id = 501;','p.flags = 128;','p.ui_flags = 32;',
                      'p.u.pd.value = 0;','p.u.pd.dephault = 2;','p.u.pd.num_choices = 3;'):
            self.assertIn(exact,text)
        self.assertIn(str(list(b'A|B|C|D\0')),text)

    def test_bits_preserve_negative_zero_nan_and_out_of_range_defaults(self):
        self.assertEqual(s.rust_value({'f32_bits':0x80000000}),'f32::from_bits(2147483648)')
        self.assertEqual(s.rust_value({'f64_bits':0x7ff8000000000001}),'f64::from_bits(9221120237041090561)')
        inv,cap=example();cap['params'][0]['fields']['u.fs_d.dephault']={'f32_bits':0x3dcccccd}
        self.assertIn('p.u.fs_d.dephault = f32::from_bits(1036831949);',s.params_source(inv,cap))

    def test_unknown_type_is_not_guessed(self):
        inv,cap=example();cap['params'][0]['fields']['param_type']=999
        with self.assertRaises(ValueError):s.validate_capture(inv,cap)

    def test_slot_and_host_flag_mismatch_rejected(self):
        inv,cap=example()
        for change in ('slot','flags','count'):
            c=copy.deepcopy(cap)
            if change=='slot':c['params'][0]['slot']=2
            elif change=='flags':c['flags']^=1
            else:c['num_params']=3
            with self.subTest(change=change),self.assertRaises(ValueError):s.validate_capture(inv,c)

    def test_arbitrary_default_and_capture_failure(self):
        inv,cap=example();p=cap['params'][0]
        p['fields']['param_type']=11;p['fields']['u.arb_d.id']=19
        p['arbitrary']={'size_error':0,'flatten_error':0,'default_flat':[0,255,128,7]}
        inv['host']['parameter_metadata'][0]['type']='arbitrary_data'
        s.validate_capture(inv,cap)
        self.assertIn('19 => Some(&[0, 255, 128, 7])',s.params_source(inv,cap))
        p['arbitrary']['flatten_error']=1
        with self.assertRaises(ValueError):s.validate_capture(inv,cap)
        p['arbitrary']['flatten_error']=0;p['arbitrary']['default_flat']=[769]
        with self.assertRaises(ValueError):s.validate_capture(inv,cap)

    def test_field_injection_rejected(self):
        for field in ('x;panic!()', 'u.cd.value.alpha;0', 'u.a[0]'):
            with self.assertRaises(ValueError):s.field_path(field)
        self.assertEqual(s.field_path('u.cd.dephault.alpha'),'p.u.cd.dephault.alpha')

    def test_emitted_package_is_standalone_and_contains_exact_resource(self):
        inv,cap=example();data=pipl([(b'eINF',b'\0\0')])
        res=[{'name':16000,'language':1033,'type':'PIPL','bytes':data}]
        desc={'name':'Synthetic','entry':'entry_point','flags':cap['flags'],'flags2':cap['flags2']}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);original=root/'original.aex';original.write_bytes(b'identity test, not a PE')
            out=root/'generated'
            with mock.patch.object(s,'oracle_module') as oracle:
                oracle.return_value.route_support.return_value=None
                s.emit(out,'scaffold-test',original,inv,cap,res,desc,root/'harness.exe')
            self.assertEqual((out/'resources/pipl-0.bin').read_bytes(),data)
            self.assertIn('[workspace]',(out/'Cargo.toml').read_text())
            self.assertIn('#[export_name = "entry_point"]',(out/'src/ae.rs').read_text())
            self.assertIn('ALGORITHM NOT PORTED',(out/'VALIDATION.md').read_text())
            self.assertEqual(json.loads((out/'scaffold.json').read_text())['original']['sha256'],s.sha(original.read_bytes()))
            with self.assertRaises(FileExistsError):s.emit(out,'scaffold-test',original,inv,cap,res,desc,root/'harness.exe')


if __name__=='__main__':unittest.main()
