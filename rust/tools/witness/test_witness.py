import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import witness


def exports(path):
    """Read fixture PE exports without loading it into Python."""
    data = path.read_bytes()
    u16 = lambda p: struct.unpack_from("<H", data, p)[0]
    u32 = lambda p: struct.unpack_from("<I", data, p)[0]
    pe = u32(0x3c)
    sections = pe+24+u16(pe+20)

    def offset(rva):
        for i in range(u16(pe+6)):
            s = sections+i*40
            va, length, raw = u32(s+12), u32(s+16), u32(s+20)
            if va <= rva < va+length:
                return raw+rva-va
        raise ValueError("unmapped export RVA")

    e = offset(u32(pe+24+112))
    functions, names, ordinals = offset(u32(e+28)), offset(u32(e+32)), offset(u32(e+36))
    result = {}
    for i in range(u32(e+24)):
        p = offset(u32(names+i*4))
        name = data[p:data.index(0, p)].decode("ascii")
        result[name] = u32(functions+u16(ordinals+i*2)*4)
    return result


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.spec = {"schema_version": 1, "module": str(Path(__file__).resolve()),
                     "calls": [{"rva": "0x1234", "return": "void", "args": []}]}

    def test_absolute_paths(self):
        n = witness.normalize(self.spec, Path.cwd())
        self.assertTrue(Path(n["module"]).is_absolute())

    def test_oversized_integer(self):
        self.spec["calls"][0]["args"] = [{"type": "i32", "value": 1 << 31}]
        with self.assertRaises(ValueError):
            witness.normalize(self.spec, Path.cwd())

    def test_unsafe_dump_name(self):
        self.spec["buffers"] = {"../escape": {"size": 8}}
        with self.assertRaises(ValueError):
            witness.normalize(self.spec, Path.cwd())

    def test_bad_pointer(self):
        self.spec["buffers"] = {"s": {"size": 8, "pointers": [{"offset": 1, "buffer": "s"}]}}
        with self.assertRaises(ValueError):
            witness.normalize(self.spec, Path.cwd())

    def test_bits_not_decimal_float(self):
        self.spec["calls"][0]["args"] = [{"type": "f32", "bits": "0x7f800123"}]
        self.assertEqual(witness.normalize(self.spec, Path.cwd())["calls"][0]["args"][0]["bits"], "0x7f800123")

    def test_argument_count(self):
        self.spec["calls"][0]["args"] = [{"type": "u64", "value": 0}] * 33
        with self.assertRaises(ValueError):
            witness.normalize(self.spec, Path.cwd())

    def test_f32_overflow_rejected(self):
        self.spec["calls"][0]["args"] = [{"type": "f32", "value": 1.e100}]
        with self.assertRaises(ValueError):
            witness.normalize(self.spec, Path.cwd())

    def test_demo_corpus_reproducible(self):
        import demo
        a = demo.corpus()
        self.assertEqual(a, demo.corpus())
        self.assertNotEqual(a, demo.corpus(2))
        self.assertEqual(len(a["counts"]), 495)
        self.assertEqual(len(a["degrees"]), 5643)
        self.assertIn(4096, a["counts"])


@unittest.skipUnless(os.name == "nt", "native Windows tests")
class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = witness.HERE / "target/test-fixtures"
        cls.root.mkdir(parents=True, exist_ok=True)
        for source, name in [("provider", "witness_provider"), ("fixture", "fixture")]:
            subprocess.run(["rustc", "--edition=2021", "--crate-type=cdylib", "-C", "opt-level=2",
                str(witness.HERE / f"tests/{source}.rs"), "-o", str(cls.root / f"{name}.dll")], check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        cls.dll = cls.root / "fixture.dll"
        cls.exports = exports(cls.dll)
        cls.host = witness.HERE / "target/release/witness-host.exe"
        if not cls.host.exists():
            raise RuntimeError("build --release before Python native tests")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=self.root)
        self.base = Path(self.tmp.name)
        self.spec = {"schema_version": 1, "module": str(self.dll), "calls": []}

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, name, args=(), returns="void"):
        return {"rva": self.exports[name], "args": list(args), "return": returns}

    def run_spec(self, spec=None, timeout=10, suffix="run"):
        out = self.base / suffix
        manifest = witness.run(spec or self.spec, out, self.host, timeout)
        self.assertTrue(manifest["process"]["cleanup_verified"])
        return out, manifest

    def test_mixed_abi_and_generic_iat_stack(self):
        args = [{"type": "u64", "value": 123}, {"type": "f64", "value": 1.25},
                {"type": "f32", "value": -2.5}, {"type": "u64", "value": 77},
                {"type": "f64", "value": 9.5}, {"type": "u64", "value": 19},
                {"type": "f32", "value": .25}, {"type": "ptr", "buffer": "out"}]
        self.spec["buffers"] = {"out": {"size": 8}}
        self.spec["calls"] = [self.call("mixed", args, "f64")]
        self.spec["trace"] = {"budget": 1, "imports": [{"name": "witness_mixed",
            "args": [a["type"] for a in args], "return": "f64"}]}
        out, m = self.run_spec()
        self.assertEqual(m["classification"], "success", (out / "stderr.txt").read_text())
        result = json.loads((out / "result.json").read_text())
        self.assertEqual(result["calls"][0]["return"]["bits_le"], struct.pack("<d", 8.5).hex())
        self.assertEqual((out / "call-000000-out.bin").read_bytes(), struct.pack("<Q", 123 ^ 77 ^ 19))
        trace = json.loads((out / "trace.jsonl").read_text())
        self.assertEqual(trace["args_bits_le"][4], struct.pack("<d", 9.5).hex())
        self.assertEqual(trace["args_bits_le"][6], struct.pack("<f", .25).hex())
        self.assertEqual(trace["result"]["bits_le"], struct.pack("<d", 8.5).hex())

    def test_math_trace_budget_passthrough(self):
        args = [{"type": "f32", "value": 2}, {"type": "f32", "value": 3}, {"type": "f64", "value": .5}]
        self.spec["calls"] = [self.call("math", args, "f64")] * 10
        out, m = self.run_spec(suffix="plain")
        self.assertEqual(m["classification"], "success")
        plain = json.loads((out / "result.json").read_text())
        self.spec["trace"] = {"math": True, "budget": 5, "imports": [{"name": "GetTickCount", "args": [], "return": "u32"}]}
        out, m = self.run_spec(suffix="traced")
        self.assertEqual(m["classification"], "success")
        traced = json.loads((out / "result.json").read_text())
        self.assertEqual([c["return"]["bits_le"] for c in plain["calls"]], [c["return"]["bits_le"] for c in traced["calls"]])
        self.assertEqual(traced["trace"], {"seen": 40, "recorded": 5, "budget": 5, "dropped": 35})
        rows = [json.loads(line) for line in (out / "trace.jsonl").read_text().splitlines()]
        self.assertEqual({r["name"] for r in rows}, {"GetTickCount", "expf", "powf", "sin"})

    def test_file_buffer_and_struct_relocation(self):
        initial = self.base / "data.bin"
        initial.write_bytes(bytes([0, 1, 254, 255]))
        self.spec["buffers"] = {"data": {"size": 4, "file": str(initial)},
            "struct": {"size": 16, "hex": struct.pack("<QQ", 0, 4).hex(),
                "pointers": [{"offset": 0, "buffer": "data"}]}}
        self.spec["calls"] = [self.call("blob", [{"type": "ptr", "buffer": "struct"}], "u64")]
        out, m = self.run_spec()
        self.assertEqual(m["classification"], "success")
        self.assertEqual((out / "call-000000-data.bin").read_bytes(), bytes([1, 2, 255, 0]))

    def test_crash_isolated(self):
        self.spec["calls"] = [self.call("crash")]
        _, m = self.run_spec()
        self.assertEqual(m["classification"], "child_failure")
        self.assertEqual(m["process"]["exit_hex"], "0xc000001d")

    def test_timeout_owned_job(self):
        self.spec["calls"] = [self.call("hang")]
        _, m = self.run_spec(timeout=.5)
        self.assertEqual(m["classification"], "timeout")
        self.assertLess(m["process"]["elapsed_seconds"], 5)

    def test_descendant_cleanup_on_parent_exit(self):
        import ctypes as c
        import time
        from concurrent.futures import ThreadPoolExecutor
        out = self.base / "descendant"
        out.mkdir()
        native = c.create_unicode_buffer(32768)
        c.windll.kernel32.GetModuleFileNameW(None, native, len(native))
        release = out / "release-parent"
        code = ("import subprocess,time,pathlib; p=subprocess.Popen([" + repr(native.value)
                + ",'-c','import time; time.sleep(30)']); print(p.pid,flush=True); "
                + "release=pathlib.Path(" + repr(str(release)) + "); "
                + "\nwhile not release.exists(): time.sleep(.01)")
        k = c.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.argtypes = [c.c_uint32, c.c_int, c.c_uint32]
        k.OpenProcess.restype = c.c_void_p
        k.WaitForSingleObject.argtypes = [c.c_void_p, c.c_uint32]
        k.CloseHandle.argtypes = [c.c_void_p]
        # Retain the actual child's handle before cleanup. Looking up an exited
        # PID after run_owned returns can open an unrelated newly spawned process.
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(witness.run_owned, [native.value, "-c", code], 10, out)
            handle = None
            try:
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    stdout = out / "stdout.txt"
                    if stdout.exists() and stdout.read_text().strip():
                        break
                    time.sleep(.01)
                pid = int(stdout.read_text().strip())
                handle = k.OpenProcess(0x100000, False, pid)
                self.assertTrue(handle)
                self.assertEqual(k.WaitForSingleObject(handle, 0), 258)
                release.touch()
                result = future.result(timeout=15)
                self.assertTrue(result["cleanup_verified"])
                self.assertEqual(k.WaitForSingleObject(handle, 5000), 0)
            finally:
                release.touch()
                if handle:
                    k.CloseHandle(handle)

    def test_buffer_overwrite_detected(self):
        self.spec["buffers"] = {"data": {"size": 8}}
        self.spec["calls"] = [self.call("overwrite", [{"type": "ptr", "buffer": "data"}])]
        out, m = self.run_spec()
        self.assertEqual(m["classification"], "child_failure")
        self.assertIn("redzone", (out / "stderr.txt").read_text())

    def test_missing_import_fails(self):
        self.spec["calls"] = [self.call("hang")]
        self.spec["trace"] = {"imports": [{"name": "missing", "args": [], "return": "void"}]}
        out, m = self.run_spec()
        self.assertEqual(m["classification"], "child_failure")
        self.assertIn("not found", (out / "stderr.txt").read_text())

    def test_completed_calls_survive_later_crash(self):
        self.spec["calls"] = [self.call("math", [{"type": "f32", "value": 2}, {"type": "f32", "value": 3}, {"type": "f64", "value": .5}], "f64"), self.call("crash")]
        out, m = self.run_spec()
        self.assertEqual(m["classification"], "child_failure")
        rows = (out / "calls.jsonl").read_text().splitlines()
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0])["index"], 0)

    def test_no_fma_lane(self):
        self.spec["calls"] = [self.call("math", [{"type": "f32", "value": 2}, {"type": "f32", "value": 3}, {"type": "f64", "value": .5}], "f64")]
        self.spec["fma"] = "no-fma"
        out, m = self.run_spec()
        self.assertEqual(m["classification"], "success")
        self.assertEqual(json.loads((out / "result.json").read_text())["fma"]["effective"], 0)


if __name__ == "__main__":
    unittest.main()
