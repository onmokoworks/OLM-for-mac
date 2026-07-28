from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/attest_olmsmoother2_mac_process_20260728.py"
SPEC = importlib.util.spec_from_file_location("smoother_attestor", PATH)
assert SPEC and SPEC.loader
attestor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(attestor)


class AttestorTests(unittest.TestCase):
    def fixture(self, root: Path):
        files = {}
        for name, body in (("no.exr", b"no"), ("no.json", b"{}"), ("yes.exr", b"yes"), ("yes.json", b"{}"), ("result.json", b'{"result":1}')):
            path = root / name
            path.write_bytes(body)
            files[name] = path
        digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        ae = root / "After Effects"
        module = root / "OLMSmoother2"
        ae.write_bytes(b"ae")
        module.write_bytes(b"module")
        ae_stat = ae.stat()
        module_stat = module.stat()
        nonce = "a" * 64
        challenge = {
            "kind": "olmsmoother2_mac_process_challenge",
            "schema_version": 1,
            "run_nonce": nonce,
            "wrapper_sha256": "b" * 64,
            "expected": {
                "ae_executable": {"path": str(ae), "sha256": digest(ae)},
                "module": {"path": str(module), "sha256": digest(module)},
            },
            "result_path": str(files["result.json"]),
            "outputs": {
                "no_effect_control": {"exr": str(files["no.exr"]), "settings": str(files["no.json"])},
                "effect_on": {"exr": str(files["yes.exr"]), "settings": str(files["yes.json"])},
            },
        }
        pre = {
            "kind": "olmsmoother2_mac_process_pre_request",
            "schema_version": 1,
            "run_nonce": nonce,
            "challenge_sha256": attestor.canonical_sha256(challenge),
            "sequence": 1,
        }
        snapshot = {
            "process": {"pid": 42, "birth_token": "1:2", "executable_path": str(ae), "executable_sha256": digest(ae), "dev": ae_stat.st_dev, "ino": ae_stat.st_ino, "size": ae_stat.st_size, "mtime_ns": ae_stat.st_mtime_ns},
            "module": {"path": str(module), "sha256": digest(module), "dev": module_stat.st_dev, "ino": module_stat.st_ino, "size": module_stat.st_size, "mtime_ns": module_stat.st_mtime_ns, "vmmap_match_count": 1},
        }
        post = {
            "kind": "olmsmoother2_mac_process_post_request",
            "schema_version": 1,
            "run_nonce": nonce,
            "challenge_sha256": attestor.canonical_sha256(challenge),
            "sequence": 2,
            "pre_request_sha256": attestor.canonical_sha256(pre),
            "pre_snapshot_sha256": attestor.canonical_sha256(snapshot),
            "result_sha256": digest(files["result.json"]),
            "artifacts": {
                "no_effect_control": {"exr_sha256": digest(files["no.exr"]), "settings_sha256": digest(files["no.json"])},
                "effect_on": {"exr_sha256": digest(files["yes.exr"]), "settings_sha256": digest(files["yes.json"])},
            },
        }
        return challenge, pre, post, snapshot

    def run_case(self, mutate=None):
        with tempfile.TemporaryDirectory(prefix="smoother_attestor_") as raw:
            challenge, pre, post, snapshot = self.fixture(Path(raw).resolve())
            post_snapshot = copy.deepcopy(snapshot)
            if mutate:
                mutate(challenge, pre, post, snapshot, post_snapshot)
            return attestor.run_once(challenge, pre, post, lambda phase: snapshot if phase == "pre" else post_snapshot)

    def test_valid_attestation(self):
        result = self.run_case()
        self.assertEqual(result["status"], "attested")
        self.assertTrue(all(result["invariants"].values()))

    def test_nonce_replay_rejected(self):
        with self.assertRaisesRegex(attestor.AttestationError, "nonce"):
            self.run_case(lambda c, p, q, a, b: q.__setitem__("run_nonce", "c" * 64))

    def test_phase_order_rejected(self):
        with self.assertRaisesRegex(attestor.AttestationError, "sequence"):
            self.run_case(lambda c, p, q, a, b: q.__setitem__("sequence", 1))

    def test_boolean_schema_and_sequence_rejected(self):
        for target in ("challenge_schema", "pre_schema", "pre_sequence"):
            def mutate(challenge, pre, post, before, after, selected=target):
                if selected == "challenge_schema":
                    challenge["schema_version"] = True
                elif selected == "pre_schema":
                    pre["schema_version"] = True
                    post["pre_request_sha256"] = attestor.canonical_sha256(pre)
                else:
                    pre["sequence"] = True
                    post["pre_request_sha256"] = attestor.canonical_sha256(pre)
            with self.subTest(target=target), self.assertRaises(attestor.AttestationError):
                self.run_case(mutate)

    def test_extra_schema_fields_rejected(self):
        with self.assertRaisesRegex(attestor.AttestationError, "schema"):
            self.run_case(lambda c, p, q, a, b: c.__setitem__("unbound", True))

    def test_pre_digest_chain_rejected(self):
        with self.assertRaisesRegex(attestor.AttestationError, "digest chain"):
            self.run_case(lambda c, p, q, a, b: q.__setitem__("pre_request_sha256", "0" * 64))

    def test_pid_or_birth_reuse_rejected(self):
        for key, value in (("pid", 43), ("birth_token", "9:9")):
            with self.subTest(key=key), self.assertRaisesRegex(attestor.AttestationError, "process identity changed"):
                self.run_case(lambda c, p, q, a, b, k=key, v=value: b["process"].__setitem__(k, v))

    def test_executable_or_module_swap_rejected(self):
        for section, key, value in (("process", "ino", 99), ("module", "mtime_ns", 99), ("module", "sha256", "f" * 64)):
            with self.subTest(section=section, key=key), self.assertRaises(attestor.AttestationError):
                self.run_case(lambda c, p, q, a, b, s=section, k=key, v=value: b[s].__setitem__(k, v))

    def test_vmmap_cardinality_rejected(self):
        for count in (0, 2, True):
            with self.subTest(count=count), self.assertRaisesRegex(attestor.AttestationError, "exactly one"):
                self.run_case(lambda c, p, q, a, b, n=count: b["module"].__setitem__("vmmap_match_count", n))

    def test_artifact_hash_or_role_tamper_rejected(self):
        with self.assertRaises(attestor.AttestationError):
            self.run_case(lambda c, p, q, a, b: q["artifacts"]["effect_on"].__setitem__("exr_sha256", "0" * 64))
        with self.assertRaisesRegex(attestor.AttestationError, "roles"):
            self.run_case(lambda c, p, q, a, b: q["artifacts"].__setitem__("extra", {}))

    def test_hardlink_role_alias_rejected(self):
        def mutate(challenge, pre, post, before, after):
            source = Path(challenge["outputs"]["no_effect_control"]["exr"])
            alias = source.parent / "hardlink-effect.exr"
            Path(challenge["outputs"]["effect_on"]["exr"]).unlink()
            alias.hardlink_to(source)
            challenge["outputs"]["effect_on"]["exr"] = str(alias)
            post["challenge_sha256"] = attestor.canonical_sha256(challenge)
            pre["challenge_sha256"] = post["challenge_sha256"]
            post["pre_request_sha256"] = attestor.canonical_sha256(pre)
            post["artifacts"]["effect_on"]["exr_sha256"] = attestor.file_sha256(alias)
        with self.assertRaisesRegex(attestor.AttestationError, "duplicate"):
            self.run_case(mutate)

    def test_self_reported_stat_rejected(self):
        with self.assertRaisesRegex(attestor.AttestationError, "stat identity"):
            self.run_case(lambda c, p, q, a, b: (a["module"].__setitem__("ino", a["module"]["ino"] + 1), b["module"].__setitem__("ino", b["module"]["ino"] + 1)))

    def test_wrapper_or_challenge_tamper_breaks_chain(self):
        with self.assertRaises(attestor.AttestationError):
            self.run_case(lambda c, p, q, a, b: c.__setitem__("wrapper_sha256", "c" * 64))

    def test_atomic_writer_refuses_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="smoother_attestor_write_") as raw:
            path = Path(raw).resolve() / "proof.json"
            attestor.atomic_write_json(path, {"a": 1})
            with self.assertRaisesRegex(attestor.AttestationError, "overwrite"):
                attestor.atomic_write_json(path, {"a": 2})
            self.assertEqual(json.loads(path.read_text()), {"a": 1})

    def test_no_live_or_destructive_actions(self):
        source = PATH.read_text()
        for forbidden in ("osascript", "pkill", "os.kill", "terminate(", "Popen("):
            self.assertNotIn(forbidden, source)
        self.assertIn('["/bin/ps", "-axo", "pid=,comm="]', source)
        self.assertIn('["/usr/bin/vmmap", str(pid)]', source)
        self.assertNotIn("stdout=subprocess.PIPE", source)
        self.assertIn("tempfile.TemporaryFile()", source)
        self.assertIn("resource.RLIMIT_FSIZE", source)


class LiveSnapshotAdapterTests(unittest.TestCase):
    def fixture(self, root: Path):
        executable = root / "After Effects"
        module = root / "OLMSmoother2.plugin"
        executable.write_bytes(b"ae executable")
        module.write_bytes(b"module")
        digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        expected = {
            "ae_executable": {"path": str(executable), "sha256": digest(executable)},
            "module": {"path": str(module), "sha256": digest(module)},
        }
        return executable, module, expected

    @staticmethod
    def completed(stdout="", returncode=0):
        return SimpleNamespace(stdout=stdout, stderr="", returncode=returncode)

    def runner(self, executable: Path, module: Path, initial=None, vmmap=None, hook=None):
        calls = []

        def run(command, timeout):
            calls.append(command)
            if hook:
                hook(command, len(calls))
            if command == ["/bin/ps", "-axo", "pid=,comm="]:
                text = initial if initial is not None else f" 42 {executable}\n"
                return self.completed(text)
            if command[:3] == ["/bin/ps", "-p", "42"]:
                return self.completed(f" 42 {executable}\n")
            if command == ["/usr/bin/vmmap", "42"]:
                text = vmmap if vmmap is not None else f"__TEXT 0000000100000000-0000000100002000 [ 8K] r-x/r-x SM=COW  {module}\n"
                return self.completed(text)
            raise AssertionError(command)

        return run, calls

    def capture(self, mutation=None, **runner_kwargs):
        with tempfile.TemporaryDirectory(prefix="smoother_live_") as raw:
            executable, module, expected = self.fixture(Path(raw).resolve())
            runner, calls = self.runner(executable, module, **runner_kwargs)
            if mutation:
                mutation(executable, module, expected, runner, calls)
            result = attestor.snapshot_from_macos(expected, runner, lambda pid: "100:200")
            attestor.validate_snapshot(result, expected, "live")
            return result, calls

    def test_valid_live_snapshot_and_absolute_commands(self):
        snapshot, calls = self.capture()
        self.assertEqual(snapshot["process"]["pid"], 42)
        self.assertEqual(snapshot["module"]["vmmap_match_count"], 1)
        self.assertEqual(calls[0], ["/bin/ps", "-axo", "pid=,comm="])
        self.assertEqual(calls[-1], ["/bin/ps", "-p", "42", "-o", "pid=,comm="])

    def test_candidate_cardinality_and_exact_executable(self):
        with tempfile.TemporaryDirectory(prefix="smoother_live_") as raw:
            executable, module, expected = self.fixture(Path(raw).resolve())
            cases = ("", f"1 {executable}\n2 {executable}\n", f"42 {executable} Helper\n")
            for output in cases:
                runner, _ = self.runner(executable, module, initial=output)
                with self.subTest(output=output), self.assertRaisesRegex(attestor.AttestationError, "exactly one"):
                    attestor.snapshot_from_macos(expected, runner, lambda pid: "1:2")

    def test_vmmap_grammar_substring_rejected_and_multi_region_accepted(self):
        with tempfile.TemporaryDirectory(prefix="smoother_live_") as raw:
            executable, module, expected = self.fixture(Path(raw).resolve())
            for output in (
                f"garbage 0000000100000000-0000000100002000 {module}\n",
                f"garbage __TEXT 0000000100000000-0000000100002000 [ 8K] r-x/r-x SM=COW  {module}\n",
                f"__TEXT 0000000100000000-0000000100002000 [ 8K] r-x/r-x SM=COW  {module}.old\n",
                "",
            ):
                runner, _ = self.runner(executable, module, vmmap=output)
                with self.subTest(output=output), self.assertRaisesRegex(attestor.AttestationError, "exactly one exact"):
                    attestor.snapshot_from_macos(expected, runner, lambda pid: "1:2")
            multi = (
                f"__TEXT 0000000100000000-0000000100002000 [ 8K] r-x/r-x SM=COW  {module}\n"
                f"__DATA 0000000100002000-0000000100004000 [ 8K] rw-/rw- SM=COW  {module}\n"
            )
            runner, _ = self.runner(executable, module, vmmap=multi)
            self.assertEqual(attestor.snapshot_from_macos(expected, runner, lambda pid: "1:2")["module"]["vmmap_match_count"], 1)

    def test_command_failure_timeout_and_boolean_returncode_rejected(self):
        with tempfile.TemporaryDirectory(prefix="smoother_live_") as raw:
            _, _, expected = self.fixture(Path(raw).resolve())

            def failure(command, timeout):
                return self.completed("", 1)

            def timeout(command, timeout):
                raise TimeoutError()

            def boolean(command, timeout):
                return self.completed("", True)

            def raw_string(command, timeout):
                return ""

            for runner in (failure, timeout, boolean, raw_string):
                with self.subTest(runner=runner.__name__), self.assertRaises(attestor.AttestationError):
                    attestor.snapshot_from_macos(expected, runner, lambda pid: "1:2")
            with self.assertRaisesRegex(attestor.AttestationError, "too large"):
                attestor._command_text(
                    lambda command, timeout: self.completed("x" * (8 * 1024 * 1024 + 1)),
                    ["/bin/ps", "-axo", "pid=,comm="],
                )

    def test_birth_drift_and_invalid_boolean_birth_rejected(self):
        with tempfile.TemporaryDirectory(prefix="smoother_live_") as raw:
            executable, module, expected = self.fixture(Path(raw).resolve())
            runner, _ = self.runner(executable, module)
            values = iter(("1:2", "1:3"))
            with self.assertRaisesRegex(attestor.AttestationError, "birth identity changed"):
                attestor.snapshot_from_macos(expected, runner, lambda pid: next(values))
            runner, _ = self.runner(executable, module)
            with self.assertRaisesRegex(attestor.AttestationError, "birth token"):
                attestor.snapshot_from_macos(expected, runner, lambda pid: True)

    def test_pid_replacement_after_vmmap_rejected(self):
        with tempfile.TemporaryDirectory(prefix="smoother_live_") as raw:
            executable, module, expected = self.fixture(Path(raw).resolve())
            pinned_reads = 0

            def runner(command, timeout):
                nonlocal pinned_reads
                if command == ["/bin/ps", "-axo", "pid=,comm="]:
                    return self.completed(f"42 {executable}\n")
                if command[:3] == ["/bin/ps", "-p", "42"]:
                    pinned_reads += 1
                    path = executable if pinned_reads == 1 else executable.parent / "Replacement"
                    return self.completed(f"42 {path}\n")
                return self.completed(f"__TEXT 0000000100000000-0000000100002000 [ 8K] r-x/r-x SM=COW  {module}\n")

            with self.assertRaisesRegex(attestor.AttestationError, "pinned process"):
                attestor.snapshot_from_macos(expected, runner, lambda pid: "1:2")

    def test_executable_and_module_drift_rejected(self):
        for selected in ("executable", "module"):
            with tempfile.TemporaryDirectory(prefix="smoother_live_") as raw:
                executable, module, expected = self.fixture(Path(raw).resolve())
                target = executable if selected == "executable" else module

                def hook(command, count, target=target):
                    if command == ["/usr/bin/vmmap", "42"]:
                        target.write_bytes(target.read_bytes() + b" drift")

                runner, _ = self.runner(executable, module, hook=hook)
                with self.subTest(selected=selected), self.assertRaises(attestor.AttestationError):
                    attestor.snapshot_from_macos(expected, runner, lambda pid: "1:2")

    def test_expected_path_hash_and_stat_drift_rejected(self):
        with tempfile.TemporaryDirectory(prefix="smoother_live_") as raw:
            executable, module, expected = self.fixture(Path(raw).resolve())
            runner, _ = self.runner(executable, module)
            expected["module"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(attestor.AttestationError, "file/hash mismatch"):
                attestor.snapshot_from_macos(expected, runner, lambda pid: "1:2")


if __name__ == "__main__":
    unittest.main()
