import unittest
from regenerate import merge_subset

class SubsetTests(unittest.TestCase):
    def cases(self):
        return {f'OLMUVMap-{i:02}-{d}':'a'*64 for i in range(18) for d in (8,16,32)}
    def test_replace_preserves_unselected_exclusions(self):
        new=self.cases()
        hashes, exclusions=merge_subset({'OLMBlur-00-8':'b'*64,'OLMUVMap-stale-8':'c'*64},
            {'OLMRadialBlur-01-32':'d'*64},new,{}, {'OLMUVMap'})
        self.assertEqual(hashes, {'OLMBlur-00-8':'b'*64,**new})
        self.assertEqual(exclusions,{'OLMRadialBlur-01-32':'d'*64})
    def test_incomplete_or_overlapping_subset_refused(self):
        new=self.cases(); new.pop(next(iter(new)))
        with self.assertRaises(ValueError): merge_subset({}, {}, new, {}, {'OLMUVMap'})
        new=self.cases()
        with self.assertRaises(ValueError): merge_subset({}, {}, new, {next(iter(new)):'a'*64}, {'OLMUVMap'})
    def test_extra_case_refused(self):
        new=self.cases(); new['OLMUVMap-99-8']='a'*64
        with self.assertRaises(ValueError): merge_subset({}, {}, new, {}, {'OLMUVMap'})

if __name__=='__main__': unittest.main()
