import copy
import json
from pathlib import Path
import tempfile
import unittest
import random

import capstone as cs
from binary import Image, similarity
from evidence import adjacent_comments, mentions, CPP_FN
from funcdb import Matcher, encoded, exact_key, lookup, read, save, sqlite_export, stats


def image(code, base=0x180000000, data=b'\x00'*64, relocations=None):
    obj = object.__new__(Image)
    obj.base = base
    obj.sections = [(base, code, 0x60000000), (base+0x1000,data,0x40000000)]
    obj.imports = {}
    obj.relocations = relocations or {}
    obj.decoder = cs.Cs(cs.CS_ARCH_X86,cs.CS_MODE_64)
    obj.decoder.detail = True
    return obj


def fp(code, base=0x180000000, **kwargs):
    obj = image(code,base,**kwargs)
    instructions = list(obj.decoder.disasm(code,base))
    return obj.fingerprint(instructions)


class NormalizationTests(unittest.TestCase):
    def test_rebase_call_and_rip_targets(self):
        # mov eax,[rip+...]; call ...; ret. Targets differ, values do not.
        a = fp(bytes.fromhex('8b05fa0f0000e800000100c3'),data=b'\x11'*64)
        b = fp(bytes.fromhex('8b05fa0f0000e800000200c3'),base=0x190000000,data=b'\x11'*64)
        self.assertEqual(exact_key(a),exact_key(b))

    def test_branch_destination_is_structural(self):
        a = fp(bytes.fromhex('74019090c3'))
        b = fp(bytes.fromhex('74029090c3'))
        self.assertNotEqual(a['exact'],b['exact'])

    def test_immediate_edit_is_fuzzy(self):
        a = fp(bytes.fromhex('b80100000083c00383e802c3'))
        b = fp(bytes.fromhex('b80200000083c00383e802c3'))
        self.assertNotEqual(a['exact'],b['exact'])
        self.assertEqual(similarity(a,b),1)

    def test_literal_edit_detected(self):
        code = bytes.fromhex('8b05fa0f0000c3')
        a, b = fp(code,data=b'\x01'*64),fp(code,data=b'\x02'*64)
        self.assertEqual(a['exact'],b['exact'])
        self.assertNotEqual(a['literals'],b['literals'])

    def test_absolute_relocations(self):
        a = fp(bytes.fromhex('48b80010008001000000c3'),relocations={0x180000002:8})
        b = fp(bytes.fromhex('48b80010009001000000c3'),base=0x190000000,relocations={0x190000002:8})
        self.assertEqual(a['exact'],b['exact'])

    def test_noncontiguous_body(self):
        obj = image(bytes.fromhex('eb029090b801000000c3'))
        ins = obj.recover(obj.base,8,{obj.base})
        self.assertEqual([i.address-obj.base for i in ins],[0,4,9])
        self.assertIsNone(obj.recover(obj.base,9,{obj.base}))

    def test_import_identity_retained(self):
        obj = image(bytes.fromhex('ff25fa0f0000'))
        obj.imports[obj.base+0x1000]='ucrtbase.dll!expf'
        result = obj.fingerprint(list(obj.decoder.disasm(obj.sections[0][1],obj.base)))
        self.assertEqual(result['imports'],['ucrtbase.dll!expf'])


def database():
    finger = fp(bytes.fromhex('b80100000083c00383e802c3'))
    function = dict(rva='1000',size=12,name='helper',fingerprint_id='f')
    return dict(schema=1,normalizer='test',fingerprints={'f':finger},evidence=[],evidence_scan={},
                programs=[dict(program=p,sha256=p,functions=[copy.deepcopy(function)],external_functions=0) for p in ['A','B']],
                mappings=[dict(program='A',rva='1000',verified_rust=True,rust={'fn':'helper'})])


class DatabaseTests(unittest.TestCase):
    def test_duplicates_preserved_and_holdout_excluded(self):
        db = database()
        fp0 = db['fingerprints']['f']
        f = db['programs'][0]['functions'][0]
        self.assertEqual(len(Matcher(db).match(f,fp0)['candidates']),2)
        m = Matcher(db,exclude=['A']).match(f,fp0)
        self.assertEqual([c['program'] for c in m['candidates']],['B'])
        self.assertFalse(m['candidates'][0]['verified_rust'])

    def test_new_binary_does_not_inherit_verification(self):
        db = database()
        f = dict(db['programs'][0]['functions'][0],fingerprint=db['fingerprints']['f'])
        result = lookup(db,dict(sha256='new',program='new',functions=[f]))['port_work'][0]
        self.assertFalse(result['verified_rust'])
        self.assertEqual(result['port_status'],'review-rust-reuse')
        result = lookup(db,dict(sha256='A',program='A',functions=[f]))['port_work'][0]
        self.assertTrue(result['verified_rust'])

    def test_unknown_ranked_by_size(self):
        db = database()
        f = dict(rva='1',name='x',size=10,fingerprint=fp(bytes.fromhex('0f57c00f58c0c3')))
        g = dict(f,rva='2',size=20)
        result = lookup(db,dict(sha256='new',program='new',functions=[f,g]))
        self.assertEqual([f['size'] for f in result['port_work']],[20,10])
        self.assertEqual(result['counts'],{'unknown':2})

    def test_deterministic_json_and_sqlite(self):
        db = database()
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/'a.json.gz',Path(tmp)/'b.json.gz'
            save(a,db);save(b,db)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            self.assertEqual(read(a),db)
            a,b=Path(tmp)/'a.sqlite',Path(tmp)/'b.sqlite'
            sqlite_export(a,db);sqlite_export(b,db)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with self.assertRaises(ValueError):
                sqlite_export(a,db)

    def test_coverage_counts_only_real_mappings(self):
        db=database()
        self.assertEqual(stats(db)[0]['verified_rust_functions_percent'],100)
        self.assertEqual(stats(db)[1]['mapped_functions'],0)

    def test_fuzzy_pruning_upper_bound(self):
        rng=random.Random(19)
        for _ in range(300):
            a=dict(fuzzy=sorted(set(rng.choices(range(100),k=rng.randrange(1,70))))[:48],instructions=rng.randrange(1,200))
            b=dict(fuzzy=sorted(set(rng.choices(range(100),k=rng.randrange(1,70))))[:48],instructions=rng.randrange(1,200))
            count=len(set(a['fuzzy']) & set(b['fuzzy']))
            ratio=min(a['instructions'],b['instructions'])/max(a['instructions'],b['instructions'])
            bound=count/max(len(a['fuzzy']),len(b['fuzzy']))*ratio
            self.assertLessEqual(similarity(a,b),bound+0.000001)

    def test_comment_boundaries(self):
        text='// caller FUN_180001000\nvoid previous() {}\n// FUN_180002000: definition\nstatic void\nTarget(int x)\n{'
        m=list(CPP_FN.finditer(text))[-1]
        context=adjacent_comments(text,m.start())
        self.assertEqual(mentions(context,0x180000000),[0x2000])
        self.assertEqual(m[1],'Target')


if __name__=='__main__':
    unittest.main()
