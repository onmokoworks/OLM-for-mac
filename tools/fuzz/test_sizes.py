"""Default invariance, parity coverage, and procedural/embedded replay contracts."""
import copy, json, os, tempfile, unittest
from pathlib import Path
from core import sha, save_corpus, load_corpus, apply_operation
from geometry import sample
from sizes import dimensions, VERSION
from test_geometry import adapter, PLUGINS
from run import ROOT

class SizeTests(unittest.TestCase):
    def test_default_3000_unchanged(self):
        expected=json.loads((ROOT/'tools/fuzz/data/T15b/default-generation-before.json').read_text())
        for name in PLUGINS:
            a=adapter(name);rows=[]
            for seed in (2026,2027):
                for i in range(150):
                    c=a.generate(seed,i);c['pixels']=sha(c['pixels']);rows.append(c)
            self.assertEqual(sha(json.dumps(rows,sort_keys=True).encode()),expected[name],name)

    def test_independent_parities_and_sizes(self):
        pairs=[dimensions(s,i,256) for s in (2026,2027) for i in range(150)]
        for axis in (0,1):
            self.assertTrue(120 <= sum(p[axis]%2 for p in pairs) <= 180)
            self.assertTrue({1,2,3,5,7}.issubset({p[axis] for p in pairs}))
        self.assertEqual(len({(w%2,h%2) for w,h in pairs}),4)
        self.assertTrue(any(w==h for w,h in pairs))
        self.assertTrue(any(w==1 and h>1 for w,h in pairs))
        self.assertTrue(any(h==1 and w>1 for w,h in pairs))
        for maximum in (1,2,3,17,256,4096):
            for i in range(200):
                self.assertTrue(all(1<=n<=maximum for n in dimensions(2026,i,maximum)))

    def test_both_corpus_encodings(self):
        a=adapter('colorkeep');a.size_sampler=VERSION;a.size_max_height=17
        original=sample(a.generate(2026,2),'realistic')
        reduced=apply_operation(a,original,{'kind':'crop','geometry':[1,1]})
        with tempfile.TemporaryDirectory(dir=os.environ['OLM_FUZZ_TEST_SCRATCH']) as td:
            path=Path(td)/'case.json'
            data=save_corpus(path,a,original,reduced,{},dict(accepted=[{'kind':'crop','geometry':[1,1]}]),{})
            legacy=adapter('colorkeep')
            self.assertEqual(load_corpus(path,legacy)[0],reduced)
            data.pop('pixels_zlib_base64');path.write_text(json.dumps(data))
            self.assertEqual(load_corpus(path,legacy)[0],reduced)
            self.assertEqual(legacy.size_sampler,'default')
            # New CLI switches must not alter procedural legacy corpus inputs.
            old=legacy.generate(2026,2)
            data=save_corpus(path,legacy,old,old,{},dict(accepted=[]),{})
            data.pop('pixels_zlib_base64',None);path.write_text(json.dumps(data))
            self.assertEqual(load_corpus(path,a)[0],old)

if __name__=='__main__':unittest.main()
