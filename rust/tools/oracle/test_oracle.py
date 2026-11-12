import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import olm_oracle as o


def native_python():
    if os.name != "nt":
        return sys.executable
    import ctypes as c
    native = c.create_unicode_buffer(32768)
    c.windll.kernel32.GetModuleFileNameW(None, native, len(native))
    return native.value


def param(slot=1, kind="float", **kw):
    return dict(slot=slot, kind=kind, minimum=1, maximum=10, value=5,
                color=[255, 12, 34, 56], components=[0, 0, 0], **kw)


class OracleTests(unittest.TestCase):
    def test_deterministic_generation_and_parallel_inputs(self):
        params = [param(), param(2, "integer"), param(3, "color"), param(4, "point"), param(5, "layer")]
        cases = o.generate_cases(params, 20, 184)
        self.assertEqual(cases, o.generate_cases(params, 20, 184))
        self.assertNotEqual(cases, o.generate_cases(params, 20, 185))
        def pixels(c):
            return o.input_pixels(*c["size"], c["input_seed"]).tobytes()
        with ThreadPoolExecutor(4) as pool:
            self.assertEqual(list(map(pixels, cases)), list(pool.map(pixels, cases)))
        self.assertEqual(cases[0]["untouched_defaults"][0]["value"], 5)
        self.assertEqual([c["assignments"][0]["value"] for c in cases[1:3]], [1, 10])
        for c in cases:
            for a in c["assignments"]:
                if a["slot"] in (1, 2):
                    self.assertTrue(1 <= a["value"] <= 10)
                if a["slot"] == 2:
                    self.assertIsInstance(a["value"], int)

    def test_untouched_out_of_range_default_and_typed_defaults(self):
        scalar = param()
        scalar.update(minimum=1, maximum=100, value=0.10000000149011612)
        cases = o.generate_cases([scalar, param(2, "color"), param(3, "point")], 50, 777123)
        self.assertEqual(cases[0]["assignments"], [])
        self.assertEqual(len(cases[0]["untouched_defaults"]), 3)
        for case in cases:
            request = o.make_request(case)
            for a in case["untouched_defaults"]:
                self.assertEqual(a["reason"], "untouched default")
                self.assertNotIn(a["slot"], [x["slot"] for x in request["assignments"]])
            for a in request["assignments"]:
                if a["slot"] == 1:
                    self.assertTrue(1 <= a["value"] <= 100)
        # Equality with a default is untouched even when selected as a minimum.
        at_minimum = param()
        at_minimum["value"] = 1
        self.assertEqual(o.generate_cases([at_minimum], 2, 1)[1]["assignments"], [])

    def test_default_omission_preserves_legacy_draws_and_inputs(self):
        import ast
        import math
        import random
        snapshot = Path(__file__).parent / "evidence/olm_oracle.campaign.py.txt"
        tree = ast.parse(snapshot.read_text(encoding="utf-8"))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "generate_cases")
        namespace = {"random": random, "math": math, "SIZES": o.SIZES}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(snapshot), "exec"), namespace)
        scalar = param()
        scalar["value"] = 0.1
        params = [scalar, param(2, "integer"), param(3, "color"), param(4, "angle"),
                  param(5, "point"), param(6, "point3d"), param(7, "layer")]
        for seed in (0, 184, 777123):
            previous = namespace["generate_cases"](params, 50, seed)
            current = o.generate_cases(params, 50, seed)
            for old, new in zip(previous, current):
                for key in ("index", "size", "input_seed", "downsample", "unassigned"):
                    self.assertEqual(old[key], new[key])
                restored = new["assignments"] + [{k: v for k, v in a.items() if k not in ("kind", "reason")}
                                                 for a in new["untouched_defaults"]]
                self.assertEqual(old["assignments"], sorted(restored, key=lambda a: a["slot"]))

    def test_invalid_explicit_value_is_rejected_without_clamping(self):
        invalid = param(kind="integer")
        invalid.update(minimum=1.5, maximum=2.5, value=2)
        with self.assertRaises(ValueError):
            o.generate_cases([invalid], 2, 1)
        case = o.generate_cases([param()], 1, 1)[0]
        with self.assertRaises(ValueError):
            o.make_request(case, [(1, 100)])

    def test_alpha_and_hidden_rgb(self):
        a = o.input_pixels(97, 61, 20)
        self.assertEqual(set(np.unique(a[..., 3])), {0, 1, 32, 128, 255})
        self.assertTrue(np.all(a[..., 2][a[..., 3] == 0] != 0))

    def test_integer_diff_and_coordinates(self):
        a = np.zeros((7, 3, 4), np.uint16)
        b = a.copy()
        b[2, 1, 3] = 32768
        r = o.compare_samples(a, b, 16)
        self.assertFalse(r["exact"])
        self.assertEqual(r["mismatching_pixels"], 1)
        self.assertEqual(r["max_abs_diff"], 32768)
        self.assertEqual(r["first_coordinates"], [{"x": 1, "y": 2}])

    def test_float_signed_zero_nan_payloads_and_infinity(self):
        a = np.array([0, 0x7fc00001, 0x7f800000, 0x3f800000], dtype="<u4").reshape(1, 1, 4)
        self.assertTrue(o.compare_samples(a, a.copy(), 32)["exact"])
        b = np.array([0x80000000, 0x7fc00002, 0xff800000, 0x3f800001], dtype="<u4").reshape(1, 1, 4)
        r = o.compare_samples(a, b, 32)
        self.assertEqual(r["mismatching_samples"], 4)
        self.assertEqual(r["max_abs_diff"], "Infinity")
        json.dumps(r, allow_nan=False)

    def test_shape_mismatch(self):
        self.assertFalse(o.compare_samples(np.zeros((1, 2, 4)), np.zeros((2, 1, 4)), 8)["exact"])

    def test_sidecars_and_png(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "a.png"
            a = o.input_pixels(3, 7, 42)
            Image.fromarray(a).save(p)
            np.testing.assert_array_equal(a, o.load_output(p, 8))
            for depth, suffix, dtype in [(16, ".rgba16le", "<u2"), (32, ".rgba32f-le", "<u4")]:
                b = np.arange(84, dtype=dtype).reshape(7, 3, 4)
                p.with_suffix(suffix).write_bytes(b.tobytes())
                np.testing.assert_array_equal(b, o.load_output(p, depth))
                p.with_suffix(suffix).write_bytes(b"bad")
                with self.assertRaises(ValueError):
                    o.load_output(p, depth)

    def test_inventory_all_fields(self):
        a = {"parameters": [param(enabled=True, choices=["a", "b"])], "host": {"advertised_out_flags": 0}}
        b = json.loads(json.dumps(a))
        self.assertEqual(o.inventory_diff(a, b), [])
        b["parameters"][0]["enabled"] = False
        b["parameters"][0]["choices"][1] = "c"
        b["host"]["advertised_out_flags"] = 1
        self.assertEqual(len(o.inventory_diff(a, b)), 3)

    def test_routes_and_summary_reference_failure(self):
        inv = {"host": {"advertised_out_flags": 1 << 25, "advertised_out_flags2": (1 << 10) | (1 << 12)}}
        self.assertIsNone(o.route_support(inv, "smart32"))
        self.assertIsNotNone(o.route_support(inv, "classic32"))
        row = {"case": 0, "route": "smart8", "status": "reference_unrenderable",
               "processes": {"reference": {"ok": False}, "candidate": {"ok": False}}}
        summary = {"routes": o.summarize([row], {"smart8": None, "smart16": "undeclared"})}
        self.assertEqual(o.exit_code(summary), 2)
        self.assertEqual(summary["routes"]["smart8"]["candidate_failure"], 0)
        self.assertEqual(summary["routes"]["smart8"]["candidate_harness_failures"], 1)
        summary["routes"]["smart8"]["mismatched"] = 1
        self.assertEqual(o.exit_code(summary), 1)
        json.dumps(summary, allow_nan=False)

    def test_ae_dispatch_contract_and_forced_classic_label(self):
        smart = {"host": {"advertised_out_flags": 1 << 25, "advertised_out_flags2": (1 << 10) | (1 << 12)}}
        classic = {"host": {"advertised_out_flags": 1 << 25, "advertised_out_flags2": 0}}
        for route in ("classic8", "classic16"):
            self.assertIn("AE does not dispatch", o.route_support(smart, route))
            self.assertIsNone(o.route_support(smart, route, force_classic=True))
            self.assertIsNone(o.route_support(classic, route))
        self.assertIsNotNone(o.route_support(smart, "classic32", force_classic=True))
        self.assertIsNotNone(o.route_support(classic, "smart8"))
        result = o.summarize([], {"classic8": None}, ["classic8"])
        self.assertEqual(result["classic8"]["route_scope"], "non_ae_debug")

    def test_render_default_timeout_and_force_classic_cli(self):
        from unittest.mock import patch
        args = ["render", "--reference", __file__, "--candidate", __file__, "--harness", __file__]
        with patch.object(o, "render", return_value=0) as render:
            self.assertEqual(o.main(args), 0)
            self.assertEqual(render.call_args.args[0].timeout, 120)
            self.assertFalse(render.call_args.args[0].force_classic)
            self.assertEqual(o.main(args + ["--timeout", "30", "--force-classic"]), 0)
            self.assertEqual(render.call_args.args[0].timeout, 30)
            self.assertTrue(render.call_args.args[0].force_classic)

    def test_reference_timeout_is_not_unrenderable(self):
        from unittest.mock import patch
        manifest = {"route": "smart8", "case": {"index": 2},
                    "harness": {"path": "unused"}, "reference": {"path": "unused"},
                    "candidate": {"path": "unused"}}
        result = {"timeout": True, "returncode": 124, "stdout": "", "stderr": ""}
        with tempfile.TemporaryDirectory() as temp, patch.object(o, "run_process", return_value=result):
            row = o.evaluate_case(Path(temp), manifest, 120)
        self.assertEqual(row["status"], "reference_timeout")
        summary = {"routes": o.summarize([row], {"smart8": None})}
        self.assertEqual(summary["routes"]["smart8"]["reference_unrenderable"], 0)
        self.assertEqual(summary["routes"]["smart8"]["reference_timeout"], 1)
        self.assertEqual(o.exit_code(summary), 2)

    def test_internal_frame_deadline_is_timeout(self):
        from unittest.mock import patch
        manifest = {"route": "smart8", "case": {"index": 2},
                    "harness": {"path": "unused"}, "reference": {"path": "unused"},
                    "candidate": {"path": "unused"}}
        result = {"timeout": False, "returncode": 1, "stdout": "",
                  "stderr": "render session invalidated (frame_deadline): frame 0 exceeded the 30000ms deadline"}
        with tempfile.TemporaryDirectory() as temp, patch.object(o, "run_process", return_value=result) as run:
            row = o.evaluate_case(Path(temp), manifest, 120)
            self.assertEqual(run.call_args.kwargs["env_overrides"], {"AEXCOMPAT_FRAME_DEADLINE_MS": "120000"})
        self.assertEqual(row["status"], "reference_timeout")
        self.assertTrue(row["processes"]["reference"]["harness_frame_timeout"])

    def test_child_environment_override_is_local(self):
        key = "OLM_ORACLE_TEST_CHILD_ENV"
        before = os.environ.get(key)
        result = o.run_process([native_python(), "-c", f"import os; print(os.environ[{key!r}])"], 10,
                               env_overrides={key: "owned-child"})
        self.assertEqual(result["stdout"].strip(), "owned-child")
        self.assertEqual(os.environ.get(key), before)
        self.assertEqual(o.frame_deadline_environment(120), {"AEXCOMPAT_FRAME_DEADLINE_MS": "120000"})

    def test_downsample_perturb_and_extent(self):
        case = o.generate_cases([param()], 1, 0, downsample=["1/2"])[0]
        req = o.make_request(case, [(1, 0.25)], [0, 0, 1, 1])
        self.assertEqual(req["assignments"][0]["value"], 5.25)
        self.assertEqual(case["assignments"], [])
        self.assertEqual(case["untouched_defaults"][0]["value"], 5)
        self.assertEqual(req["host_context"]["spatial"]["downsample_x"], {"numerator": 1, "denominator": 2})
        with self.assertRaises(ValueError):
            o.make_request(case, extent=[0, 0, 1, 1], route="classic8")

    def test_process_timeout_and_success(self):
        ok = o.run_process([native_python(), "-c", "print('done')"], 10)
        self.assertEqual(ok["returncode"], 0)
        self.assertIn("done", ok["stdout"])
        expired = o.run_process([native_python(), "-c", "import time;time.sleep(30)"], .15)
        self.assertTrue(expired["timeout"])
        self.assertNotEqual(expired["returncode"], 0)

    def test_cancel_terminates_running_and_prevents_new_children(self):
        timer = threading.Timer(.15, o.CANCELLED.set)
        timer.start()
        try:
            result = o.run_process([native_python(), "-c", "import time;time.sleep(30)"], 10)
            self.assertTrue(result["cancelled"])
            self.assertFalse(result["timeout"])
            with self.assertRaises(RuntimeError):
                o.run_process([native_python(), "-c", "print('must not start')"], 10)
        finally:
            timer.join()
            o.CANCELLED.clear()

    def test_inspection_failure_still_writes_summary(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            args = SimpleNamespace(out=Path(temp) / "run", harness=Path(__file__),
                                   reference=Path(__file__), candidate=Path(__file__),
                                   timeout=1, seed=9, cases=3)
            with patch.object(o, "inspect", side_effect=RuntimeError("inspection failed")):
                with self.assertRaises(RuntimeError):
                    o.render(args)
            summary = json.loads((args.out / "summary.json").read_text())
            self.assertFalse(summary["complete"])
            self.assertEqual(summary["exit_code"], 2)
            self.assertIn("inspection failed", summary["setup_error"])

    @unittest.skipUnless(os.name == "nt", "Windows job ownership test")
    def test_owned_descendant_is_collected_after_parent_exits(self):
        # The descendant outlives its immediate parent unless the oracle's job
        # cleanup works. Inspect only this exact child PID, never process names.
        # Use the native executable, not the Store app-execution alias broker.
        import ctypes as c
        from ctypes import wintypes as w
        result = o.run_process([native_python(), "-c",
            "import subprocess,sys; p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],"
            "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); print(p.pid)"], 10)
        self.assertEqual(result["returncode"], 0)
        pid = int(result["stdout"].strip())
        k = c.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        k.OpenProcess.restype = w.HANDLE
        k.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        k.CloseHandle.argtypes = [w.HANDLE]
        handle = k.OpenProcess(0x100000, False, pid)
        if handle:
            try:
                self.assertEqual(k.WaitForSingleObject(handle, 1000), 0, f"owned child {pid} remains alive")
            finally:
                k.CloseHandle(handle)
        else:
            self.assertEqual(c.get_last_error(), 87)  # PID already reaped


if __name__ == "__main__":
    unittest.main()
