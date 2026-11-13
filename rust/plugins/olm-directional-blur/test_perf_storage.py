import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from perf_storage import install

class StorageTests(unittest.TestCase):
    def test_exact_discards_pixels_but_retains_comparison(self):
        with TemporaryDirectory() as temporary:
            folder=Path(temporary)
            (folder/'candidate.rgba32f-le').write_bytes(b'pixel')
            (folder/'input.png').write_bytes(b'input')
            oracle=SimpleNamespace(write_json=lambda p,v: Path(p).write_text(json.dumps(v)))
            install(oracle)
            oracle.write_json(folder/'diff.json',{'status':'exact','sha256':'recorded'})
            self.assertEqual(sorted(p.name for p in folder.iterdir()),['diff.json'])
            self.assertEqual(json.loads((folder/'diff.json').read_text())['sha256'],'recorded')

    def test_mismatch_stays_replayable(self):
        with TemporaryDirectory() as temporary:
            folder=Path(temporary)
            (folder/'candidate.rgba32f-le').write_bytes(b'pixel')
            oracle=SimpleNamespace(write_json=lambda p,v: Path(p).write_text(json.dumps(v)))
            install(oracle)
            oracle.write_json(folder/'diff.json',{'status':'mismatched'})
            self.assertEqual((folder/'candidate.rgba32f-le').read_bytes(),b'pixel')

if __name__=='__main__':unittest.main()
