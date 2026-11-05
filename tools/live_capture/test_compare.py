"""Bit/ULP reporting boundaries for live-capture evidence."""
import struct
import unittest
from replay_aex import compare


def words(*bits):
    return b''.join(struct.pack('<I', value) for value in bits)


class CompareTests(unittest.TestCase):
    def test_binary32_adjacent_words_and_first_coordinate(self):
        a = words(0, 0, 0, 0, 0x3f800000, 0xbf800000, 0, 0)
        b = words(0, 0, 0, 0, 0x3f800001, 0xbf800002, 0, 0)
        result = compare(a, b, 32, 2)
        self.assertEqual((result['different_words'], result['different_pixels'], result['max_ulp']), (2, 1, 2))
        self.assertEqual((result['first']['x'], result['first']['channel']), (1, 'A'))
        self.assertEqual(result['first']['aex_value'], 1.0)
        self.assertEqual(result['first']['ulp'], 1)

    def test_signed_zero_and_nonfinite_words_stay_bit_exact(self):
        result = compare(words(0x80000000), words(0), 32, 1)
        self.assertEqual((result['different_words'], result['max_diff'], result['max_ulp']), (1, 0, 1))
        self.assertEqual(compare(words(0x7fc00001), words(0x7fc00001), 32, 1)['status'], 'exact')
        result = compare(words(0x7fc00001), words(0x7fc00002), 32, 1)
        self.assertEqual(result['different_words'], 1)
        self.assertIsNone(result['max_ulp'])

    def test_integer_counts(self):
        for depth, a, b in ((8, b'\x00\xff', b'\x01\xfe'),
                            (16, b'\x00\x00\xff\xff', b'\x01\x00\xfe\xff')):
            result = compare(a, b, depth, 1)
            self.assertEqual((result['different_words'], result['different_pixels'], result['max_diff']), (2, 1, 1))
            self.assertNotIn('max_ulp', result)


if __name__ == '__main__':
    unittest.main()
