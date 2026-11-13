import copy
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image
import olm_oracle as o
import oracle_resident as r


class ResidentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def entry(self, index, side="reference", route="smart8", size=(5, 7), scale="1", edits=()):
        case = {"index": index, "size": size, "downsample": scale, "input_seed": index,
                "assignments": list(edits)}
        identity = {"path": str(self.root / "plugin.aex"), "sha256": "abc"}
        directory, manifest = o.prepare_case(self.root, case, route,
                                             {key: identity for key in ("harness", "reference", "candidate")})
        request = json.loads((directory / "requests" / f"{side}.json").read_text())
        return {"directory": directory, "manifest": manifest, "request": request,
                "side": side, "id": f"{directory.name}/{side}"}

    def report(self, entries):
        return {"schema": r.SCHEMA, "schema_version": 1, "isolation": "fresh_sequence",
                "route": entries[0]["manifest"]["route"], "plugin_sha256": "abc", "complete": True,
                "session_close": {"independent_cases_clean": True}, "cases": [
                    {"id": e["id"], "case_index": i, "passed": True, "case_cleanup": True,
                     "evidence_valid": True, "evidence_provisional": False, "plugin_sha256": "abc",
                     "requested_route": e["manifest"]["route"]} for i, e in enumerate(entries)]}

    def test_values_pixels_and_current_time_vary_in_one_group(self):
        a, b = self.entry(0), self.entry(1, edits=[{"slot": 1, "value": 12}])
        a["request"]["timing"] = {"frame": 0, "fps": 30, "duration_frames": 300}
        b["request"]["timing"] = {"frame": 10, "fps": 30, "duration_frames": 300}
        self.assertEqual(len(r.partition([a, b], 120)), 1)
        self.assertEqual(a["request"]["timing"]["frame"], 0)

    def test_size_scale_route_settings_and_side_split(self):
        a = self.entry(0)
        variations = [self.entry(1, size=(6, 7)), self.entry(2, scale="1/2"),
                      self.entry(3, route="smart16"), self.entry(4, side="candidate"), self.entry(5)]
        variations[-1]["request"]["render_settings"]["premultiplication"] = "opaque"
        self.assertEqual(len(r.partition([a, *variations], 120)), 6)

    def test_layer_content_not_filename_controls_grouping(self):
        a, b = self.entry(0), self.entry(1)
        for entry, name in [(a, "first.png"), (b, "second.png")]:
            Image.new("RGBA", (2, 3), (1, 2, 3, 4)).save(entry["directory"] / name)
            entry["request"]["assignments"] = [{"slot": 2, "layer": name}]
        self.assertEqual(len(r.partition([a, b], 120)), 1)
        Image.new("RGBA", (2, 3), (4, 3, 2, 1)).save(b["directory"] / "second.png")
        self.assertEqual(len(r.partition([a, b], 120)), 2)

    def test_128_case_limit_and_stable_order(self):
        entries = [self.entry(i) for i in range(129)]
        groups = r.partition(entries, 120)
        self.assertEqual([len(g) for g in groups], [128, 1])
        self.assertEqual([e["id"] for g in groups for e in g], [e["id"] for e in entries])

    def test_byte_limit_splits_manifest(self):
        entries = [self.entry(i) for i in range(3)]
        path = self.root / "manifest.json"
        o.write_json(path, r.batch_manifest(entries[:2], 120))
        limit = path.stat().st_size
        self.assertEqual(r.manifest_bytes(entries[:2], 120), limit)
        with patch.object(r, "MAX_MANIFEST_BYTES", limit):
            self.assertEqual([len(g) for g in r.partition(entries, 120)], [2, 1])

    def test_replay_labels_resident_source_as_per_process(self):
        entry = self.entry(0)
        manifest = entry["manifest"]
        manifest["transport"] = "resident"
        plugin = self.root / "plugin.aex"
        plugin.write_bytes(b"identity fixture")
        for key in ("harness", "reference", "candidate"):
            manifest[key] = o.identity(plugin)
        manifest["tool"] = o.identity(o.__file__)
        o.write_json(entry["directory"] / "case.json", manifest)
        out = self.root / "replay"
        args = SimpleNamespace(case_dir=entry["directory"], out=out, timeout=120)
        with patch.object(o, "evaluate_case", return_value={"case": 0, "route": "smart8", "status": "exact"}):
            self.assertEqual(o.replay(args), 0)
        saved = json.loads((out / "summary.json").read_text())
        self.assertEqual(saved["transport"], "per_process")
        self.assertEqual(saved["replay_source_transport"], "resident")

    def test_mapping_uses_ids_not_reply_order(self):
        entries = [self.entry(i) for i in range(2)]
        report = self.report(entries)
        report["cases"].reverse()
        self.assertEqual(r.map_report(report, entries)[entries[0]["id"]]["case_index"], 0)

    def test_missing_duplicate_and_misindexed_results_rejected(self):
        entries = [self.entry(i) for i in range(2)]
        for corruption in ("missing", "duplicate", "index"):
            report = self.report(entries)
            if corruption == "missing": report["cases"].pop()
            elif corruption == "duplicate": report["cases"][1]["id"] = report["cases"][0]["id"]
            else: report["cases"][0]["case_index"] = 1
            with self.subTest(corruption=corruption), self.assertRaises(ValueError):
                r.map_report(report, entries)

    def test_unclean_provisional_or_wrong_identity_never_accepted(self):
        entries = [self.entry(0)]
        for corruption in ("close", "provisional", "identity"):
            report = self.report(entries)
            if corruption == "close": report["session_close"]["independent_cases_clean"] = False
            elif corruption == "provisional": report["cases"][0]["evidence_provisional"] = True
            else: report["cases"][0]["plugin_sha256"] = "changed"
            with self.subTest(corruption=corruption), self.assertRaises(ValueError):
                r.map_report(report, entries)

    def test_recoverable_failure_does_not_revoke_success(self):
        entries = [self.entry(i) for i in range(2)]
        report = self.report(entries)
        report["cases"][0].update(passed=False, evidence_valid=False, outcome="render_error")
        mapped = r.map_report(report, entries)
        self.assertFalse(mapped[entries[0]["id"]]["passed"])
        self.assertTrue(mapped[entries[1]["id"]]["passed"])

    def test_memory_fill_explicitly_rejected(self):
        entry = self.entry(0)
        entry["request"]["diagnostics"] = {"memory_fill": {"pattern_hex": "00"}}
        with self.assertRaisesRegex(ValueError, "memory_fill"):
            r.partition([entry], 120)

    def test_authority_replay_preserves_assets_and_resident_outputs(self):
        entry = self.entry(0)
        directory, manifest = entry["directory"], entry["manifest"]
        (directory / "reference.png").write_bytes(b"resident evidence")
        expected = {"status": "mismatched"}
        with patch.object(o, "evaluate_case", return_value=expected) as evaluate:
            self.assertEqual(r.rerun_authority(directory, manifest, 120, o), expected)
        self.assertEqual((directory / "reference.png").read_bytes(), b"resident evidence")
        target = evaluate.call_args.args[0]
        self.assertEqual(o.sha256(target / "input.png"), manifest["assets"]["input.png"])
        self.assertEqual(json.loads((target / "case.json").read_text())["transport"], "per_process")

    def test_timeout_budget_is_per_case_plus_startup(self):
        entries = [self.entry(i) for i in range(2)]
        report = self.report(entries)
        report["passed"] = True
        process = {"argv": [], "pid": 1, "returncode": 0, "timeout": False, "cancelled": False,
                   "environment_overrides": {}, "elapsed_seconds": .5, "stdout": json.dumps(report), "stderr": ""}
        with patch.object(o, "run_process", return_value=process) as run:
            mapped, _ = r.execute_batch(0, entries, self.root, 10, o)
        self.assertEqual(run.call_args.args[1], 30)
        self.assertTrue(all(item["ok"] for item in mapped.values()))

    def test_failure_rerun_exact_does_not_replace_resident_failure(self):
        out = self.root / "campaign"
        out.mkdir()
        identity = {"path": str(self.root / "plugin.aex"), "sha256": "abc"}
        identities = {key: identity for key in ("harness", "reference", "candidate")}
        args = SimpleNamespace(out=out, jobs=1, timeout=10, perturb_candidate=[], extent=None)
        plans = [{"index": 0, "size": [5, 7], "input_seed": 1, "downsample": "1", "assignments": []}]
        summary = {"results": [], "routes": {}, "complete": False, "inventory_diff": []}
        def fail_batch(index, entries, root, timeout, oracle):
            return ({e["id"]: {"ok": False, "timeout": False, "harness_frame_timeout": False,
                                "returncode": 1} for e in entries}, {"cases": len(entries)})
        authority = {"case": 0, "route": "smart8", "status": "exact"}
        with patch.object(r, "execute_batch", side_effect=fail_batch), patch.object(r, "rerun_authority", return_value=authority) as rerun:
            code = r.render_campaign(args, plans, identities, {"smart8": None}, [], summary, o)
        self.assertEqual(code, 2)
        self.assertEqual(rerun.call_count, 1)
        self.assertEqual(summary["results"][0]["status"], "reference_unrenderable")
        self.assertEqual(summary["results"][0]["per_process_authority"]["status"], "exact")
        self.assertEqual(summary["routes"]["smart8"]["exact"], 0)
        self.assertEqual(summary["per_process_rerun_routes"]["smart8"]["exact"], 1)


if __name__ == "__main__":
    unittest.main()
