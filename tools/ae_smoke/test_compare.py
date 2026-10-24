"""Byte-contract checks; scratch stays inside the worktree."""
import struct
import unittest
from pathlib import Path
from compare import compare

ROOT=Path(__file__).resolve().parents[2]


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.s=ROOT/'orchestra/state/A01-real-ae-smoke/compare-test'
        self.s.mkdir(parents=True,exist_ok=True)
        self.a,self.b=self.s/'a.argb',self.s/'b.argb'

    def tearDown(self):
        self.a.unlink(missing_ok=True);self.b.unlink(missing_ok=True)
        self.s.rmdir()

    def test_equal_all_depths(self):
        for depth,fmt in ((8,'4B'),(16,'4H'),(32,'4f')):
            raw=struct.pack('<'+fmt,1,0,1,0)
            self.a.write_bytes(raw);self.b.write_bytes(raw)
            self.assertTrue(compare(self.a,self.b,1,1,depth)['exact'])

    def test_first_mismatch_layout(self):
        self.a.write_bytes(bytes([255,1,2,3])*4)
        self.b.write_bytes(bytes([255,1,2,3])*3+bytes([255,1,2,4]))
        r=compare(self.a,self.b,2,2,8)
        self.assertEqual(r['differing_samples'],1)
        self.assertEqual(r['first_mismatch'],dict(x=1,y=1,channel='B',ae_bytes='03',host_bytes='04'))

    def test_float_bit_identity(self):
        self.a.write_bytes(struct.pack('<4I',0x3f800000,0,0x7fc12345,0))
        self.b.write_bytes(struct.pack('<4I',0x3f800000,0x80000000,0x7fc12346,0))
        self.assertEqual(compare(self.a,self.b,1,1,32)['differing_samples'],2)

    def test_wrong_length(self):
        self.a.write_bytes(bytes(4));self.b.write_bytes(bytes(3))
        with self.assertRaises(ValueError):compare(self.a,self.b,1,1,8)


if __name__=='__main__':unittest.main()
