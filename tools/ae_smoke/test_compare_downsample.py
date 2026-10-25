"""Codec boundaries for the real-AE comparator, without launching AE."""
import os
from pathlib import Path
import tempfile
import unittest
import numpy as np
import OpenEXR
from compare_downsample import load_rgba

class CodecTests(unittest.TestCase):
    def test_png_preserves_hidden_rgb(self):
        from PIL import Image
        with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as td:
            path = Path(td)/'straight.png'
            rgba = np.array([[[32, 64, 128, 0], [2, 3, 4, 255]]], dtype=np.uint8)
            Image.fromarray(rgba).save(path)
            self.assertTrue(np.array_equal(load_rgba(path, 8), rgba))
            with self.assertRaisesRegex(ValueError, '8 bpc RGBA PNG'):
                load_rgba(path, 16)

    def test_ae16_float_export_inverse_and_fraction_rejection(self):
        with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as td:
            path = Path(td)/'input.exr'
            words = np.arange(32769, dtype=np.float32).reshape(1,-1)
            values = words/np.float32(32768)
            OpenEXR.File({}, {c:values for c in 'RGBA'}).write(str(path))
            decoded = load_rgba(path,16)
            self.assertTrue(np.array_equal(decoded[:,:,0], words))
            values = np.full((1,1),np.float32(.1))
            OpenEXR.File({}, {c:values for c in 'RGBA'}).write(str(path))
            with self.assertRaisesRegex(ValueError, 'not exact integer'):
                load_rgba(path,16)
    def test_half_float_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as td:
            path=Path(td)/'half.exr'
            OpenEXR.File({}, {c:np.ones((1,1),dtype=np.float16) for c in 'RGBA'}).write(str(path))
            with self.assertRaisesRegex(ValueError,'FLOAT EXR required'):
                load_rgba(path,32)

if __name__=='__main__': unittest.main()
