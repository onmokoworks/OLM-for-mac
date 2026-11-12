import copy
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import olm_triage as t


def param(slot=1, name="Amount", kind="float", value=5, lo=1, hi=100):
    return dict(slot=slot, name=name, kind=kind, value=value, minimum=lo, maximum=hi,
                components=[0, 0, 0], color=[255, 0, 0, 0], layer_path=None)


def resource(props):
    data = struct.pack("<HII", 1, 0, len(props))
    for key, value in props:
        data += b"MIB8" + key.encode()[::-1] + struct.pack("<II", 0, len(value))
        data += value + b"\0" * (-len(value) % 4)
    return data


def function(address, name="FUN_x", hash="same", shape="shape", named=False, size=20):
    return dict(address=address, name=name, hash=hash, shape_hash=shape, named=named,
                size=size, instructions=10, calls=[], callers=[], rva=int(address, 16))


class PiPLTests(unittest.TestCase):
    def test_fields_and_short_alignment(self):
        raw = resource([("eINF", b"\0\0"), ("eMNA", b"\x04Test"),
                        ("ePVR", struct.pack("<HH", 2, 0)), ("eSVR", struct.pack("<HH", 13, 28)),
                        ("eVER", struct.pack("<I", 591872)), ("eGLO", struct.pack("<I", 0x6000040)),
                        ("eGL2", struct.pack("<I", 0x8001400))])
        d = t.decode_pipl(raw)
        self.assertEqual(d["fields"]["eMNA"], "Test")
        self.assertEqual(d["fields"]["eSVR"], {"major": 13, "minor": 28})
        self.assertEqual(d["fields"]["depths"], [8, 16, 32])
        self.assertEqual(d["fields"]["effect_version"], dict(major=1, minor=2, bug=1, stage=0, build=0))
        self.assertEqual(d["properties"][0]["raw_hex"], "0000")

    def test_truncation_is_not_an_empty_valid_resource(self):
        for raw in (b"", resource([("eMNA", b"\x04Test")])[:-5], struct.pack("<HII", 1, 0, 5000)):
            with self.assertRaises(ValueError):
                t.decode_pipl(raw)

    def test_unknown_properties_retained(self):
        d = t.decode_pipl(resource([("XXXX", b"\xfe\xff")]))
        self.assertEqual(d["properties"][0]["raw_hex"], "feff")
        self.assertIsNone(d["fields"]["depths"])

    def test_pe_extracts_every_language_and_preserves_zero_resource_id(self):
        raw = resource([("eMNA", b"\x04Test")])
        leaf = lambda lang: SimpleNamespace(id=lang, data=SimpleNamespace(struct=SimpleNamespace(OffsetToData=100, Size=len(raw))))
        entry = SimpleNamespace(id=0, name=None, directory=SimpleNamespace(entries=[leaf(1033), leaf(1041)]))
        pe = mock.MagicMock()
        pe.__enter__.return_value = pe
        pe.DIRECTORY_ENTRY_RESOURCE.entries = [SimpleNamespace(name="PIPL", directory=SimpleNamespace(entries=[entry]))]
        pe.DIRECTORY_ENTRY_IMPORT = pe.DIRECTORY_ENTRY_DELAY_IMPORT = pe.sections = []
        pe.get_data.return_value = raw
        with tempfile.TemporaryDirectory() as root, mock.patch.object(t.pefile, "PE", return_value=pe):
            result = t.pe_inventory(Path("fixture.aex"), Path(root))["pipl"]
            self.assertEqual([r["language"] for r in result], [1033, 1041])
            self.assertEqual(result[0]["id"], 0)
            for r in result:
                self.assertEqual((Path(root) / r["raw_file"]).read_bytes(), raw)


class ParameterTests(unittest.TestCase):
    def test_moved_slots_and_new_params(self):
        old, new = [param()], [param(3), param(1, "New")]
        m = t.match_parameters(old, new)
        self.assertEqual(m["matched"][0]["new_slot"], 3)
        self.assertEqual(m["added_or_unmatched"][0]["name"], "New")
        c = t.oracle.generate_cases(old, 2, 12)[1]
        before = copy.deepcopy(c)
        mapped = t.remap_case(c, m, new)
        self.assertEqual(mapped["assignments"][0]["slot"], 3)
        self.assertEqual(c, before)

    def test_renamed_or_retyped_slot_is_not_silently_matched(self):
        for p in (param(name="Other"), param(kind="integer")):
            m = t.match_parameters([param()], [p])
            self.assertFalse(m["matched"])

    def test_duplicate_names_only_match_by_exact_slot(self):
        self.assertFalse(t.match_parameters([param()], [param(2), param(3)])["matched"])
        self.assertEqual(t.match_parameters([param()], [param(1), param(3)])["matched"][0]["new_slot"], 1)

    def test_new_range_rejected_not_clamped(self):
        old, new = [param()], [param(hi=20)]
        c = t.oracle.generate_cases(old, 3, 12)[2]
        with self.assertRaises(ValueError):
            t.remap_case(c, t.match_parameters(old, new), new)

    def test_sensitivity_is_one_control_same_input_and_default_untouched(self):
        cases, skipped = t.sensitivity_cases([param(), param(2, "Toggle", "integer", 0, 0, 1)], 12, (17, 9))
        self.assertEqual(cases[0]["assignments"], [])
        self.assertFalse(skipped)
        self.assertTrue(all(len(c["assignments"]) == 1 for c in cases[1:]))
        self.assertEqual(len({c["input_seed"] for c in cases}), 1)

    def test_invalid_declared_default_is_never_resent(self):
        cases, _ = t.sensitivity_cases([param(value=.1)], 12, (17, 9))
        self.assertTrue(all(a["value"] >= 1 for c in cases for a in c["assignments"]))

    def test_unsupported_control_is_explicit(self):
        cases, skipped = t.sensitivity_cases([param(kind="arbitrary")], 12, (17, 9))
        self.assertEqual(len(cases), 1)
        self.assertEqual(skipped[0]["kind"], "arbitrary")

    def test_sensitivity_does_not_call_failures_exact(self):
        row = dict(parameter={"slot": 1, "name": "Amount"}, route="smart8", label="slot-1")
        result = t.sensitivity_summary({"cases": [dict(route="smart8", label="defaults", status="exact"),
                                                   dict(row, status="mismatched"), dict(row, status="reference_timeout")]})[0]
        self.assertEqual(result["incomplete"], 1)
        self.assertTrue(result["change_exposed_from_equal_defaults"])


class FunctionTests(unittest.TestCase):
    def test_shifted_code_matches_hash_not_address(self):
        d = t.match_functions([function("100")], [function("900", name="FUN_900")])
        self.assertEqual(d["summary"]["unchanged"], 1)
        self.assertEqual(d["matched"][0]["basis"], "unique normalized hash")

    def test_named_constant_change_and_callers(self):
        old = function("100", name="legacy_gain", named=True)
        new = function("300", name="legacy_gain", named=True, hash="changed")
        new["callers"] = ["500"]
        d = t.match_functions([old], [new])
        self.assertEqual(d["summary"]["changed"], 1)
        self.assertEqual(d["changed"][0]["new"]["callers"], ["500"])

    def test_unnamed_constant_shape_match_is_labelled_heuristic(self):
        d = t.match_functions([function("100")], [function("500", hash="changed")])
        self.assertIn("heuristic", d["changed"][0]["basis"])

    def test_referenced_literal_change_is_distinct_from_instruction_change(self):
        old, new = function("100"), function("300", hash="different")
        old["code_hash"] = new["code_hash"] = "same instructions"
        d = t.match_functions([old], [new])
        self.assertEqual(d["changed"][0]["change_kind"], "referenced data")
        self.assertEqual(d["summary"]["referenced_data_changes"], 1)

    def test_duplicate_hashes_do_not_disappear(self):
        d = t.match_functions([function("100"), function("200")], [function("500")])
        self.assertEqual(d["summary"]["unchanged"], 1)
        self.assertEqual(d["summary"]["removed"], 1)

    def test_unmatched_lists_are_preserved(self):
        d = t.match_functions([function("100")], [function("500", hash="different", shape="different")])
        self.assertEqual((len(d["added"]), len(d["removed"])), (1, 1))

    def test_import_families_and_case_insensitive_dll(self):
        self.assertEqual(t.import_family("ippcore.dll!ippInit"), "IPP")
        self.assertEqual(t.import_family("opencv_world.dll"), "OpenCV")
        self.assertEqual(t.import_family("api-ms-win-crt-math-l1-1-0.dll!sin"), "UCRT/CRT")
        a = dict(dll="KERNEL32.dll", name="Sleep", kind="normal")
        self.assertEqual(t.import_delta([a], [dict(a, dll="kernel32.DLL")]), dict(added=[], removed=[]))


class ProcessTests(unittest.TestCase):
    def test_output_and_launch_pid_survive_owned_process_cleanup(self):
        with tempfile.TemporaryDirectory() as root:
            result = t.run_headless([sys.executable, "-c", "print('triage-child')"], Path(root), 10)
            self.assertEqual(result["returncode"], 0)
            self.assertIn("triage-child", result["stdout"])
            self.assertTrue(result["owned_process_cleanup_verified"])
            self.assertTrue((Path(root) / "ghidra.launch.json").exists())

    def test_timeout_closes_owned_child_without_pipe_draining(self):
        # Keep logs in the ignored task tree if a lifecycle assertion fails.
        base = t.HERE / "local" / "process-tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as root:
            code = "import time,subprocess,sys; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); print(p.pid,flush=True); time.sleep(30)"
            result = t.run_headless([sys.executable, "-c", code], Path(root), .5)
            self.assertTrue(result["timeout"])
            self.assertTrue(result["owned_process_cleanup_verified"])
            self.assertNotEqual(result["returncode"], 0)
            self.assertTrue(result["stdout"].strip().isdigit())
            if t.os.name == "nt":
                self.assertIn(int(result["stdout"].strip()), result["owned_pids_at_cleanup"])


if __name__ == "__main__":
    unittest.main()
