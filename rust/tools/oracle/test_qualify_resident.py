import unittest
import json
from pathlib import Path
import tempfile
from qualify_resident import lifecycle_cases, compare_modes


class QualificationCorpusTests(unittest.TestCase):
    def parameters(self):
        return [{"slot": 1, "kind": "float", "minimum": 0, "maximum": 100,
                 "value": 5, "name": "Amount"}]

    def test_seeded_reset_blocks_and_scale_groups(self):
        plans = lifecycle_cases(self.parameters(), 60, 20261112)
        self.assertEqual(plans, lifecycle_cases(self.parameters(), 60, 20261112))
        self.assertNotEqual(plans[0]["input_seed"], lifecycle_cases(self.parameters(), 60, 42)[0]["input_seed"])
        self.assertEqual(len(plans), 60)
        self.assertEqual([p["index"] for p in plans], list(range(60)))
        for block in range(10):
            group = plans[block*6:block*6+6]
            self.assertEqual(group[0]["input_seed"], group[2]["input_seed"])
            self.assertEqual(group[2]["input_seed"], group[5]["input_seed"])
            self.assertEqual(group[1]["input_seed"], group[4]["input_seed"])
            self.assertEqual(group[3]["assignments"], [{"slot": 1, "value": 6}])
            self.assertTrue(all(not p["assignments"] for p in group if p is not group[3]))
            self.assertEqual(len({p["downsample"] for p in group}), 1)
        self.assertEqual({p["downsample"] for p in plans}, {"1", "1/2", "1/4"})

    def test_invalid_declared_default_is_never_submitted(self):
        params = self.parameters()
        params[0].update(minimum=1, value=.1)
        plans = lifecycle_cases(params, 6, 1)
        self.assertEqual(plans[0]["assignments"], [])
        self.assertEqual(plans[3]["assignments"], [{"slot": 1, "value": 2}])
        self.assertEqual(params[0]["value"], .1)

    def test_matching_failures_without_outputs_do_not_prove_equivalence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for mode in ("resident", "per_process"):
                case = root / mode / "case-0000-smart8"
                case.mkdir(parents=True)
                (case / "case.json").write_text(json.dumps({"assets": {}}))
            summary = {"campaign_wall_seconds": 1,
                       "results": [{"case": 0, "route": "smart8", "status": "reference_unrenderable"}]}
            result = compare_modes(root, summary, summary)
            self.assertEqual(result["verdicts_equal"], 1)
            self.assertFalse(result["all_equivalent"])
            self.assertEqual(result["side_outputs_equal"], 0)


if __name__ == "__main__":
    unittest.main()
