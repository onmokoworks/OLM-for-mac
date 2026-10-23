"""Self-spawn safety checks; never run an emulation campaign."""
from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOTS = ("tools", "tests", "scripts", "refs/scripts", "handoffs")
CHILD = "OLM_SELF_SPAWN_CHILD"


def self_command(node):
    # Commands may append payload arguments with list concatenation. Inspect
    # the interpreter/script prefix, including nested str(Path(__file__)).
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return self_command(node.left)
    if not isinstance(node, (ast.List, ast.Tuple)) or len(node.elts) < 2:
        return False
    interpreter, script = map(ast.unparse, node.elts[:2])
    return "sys.executable" in interpreter and (
        any(isinstance(n, ast.Name) and n.id == "__file__" for n in ast.walk(node.elts[1]))
        or "sys.argv[0]" in script
    )


def inventory():
    for directory in SEARCH_ROOTS:
        for path in sorted((ROOT / directory).rglob("*.py")):
            if any(part.startswith(".venv") or part == "__pycache__" for part in path.parts):
                continue
            source = path.read_text(encoding="utf-8")
            if "sys.executable" not in source:
                continue
            tree = ast.parse(source)
            commands = [n for n in ast.walk(tree) if self_command(n)]
            if not commands:
                continue
            # This record is reported as provenance; it is never executed.
            if path.relative_to(ROOT).as_posix() == "tools/perf/run_generic_beta_smoke.py":
                continue
            yield path, tree, commands


class SelfRespawnGuardTests(unittest.TestCase):
    def test_all_self_spawns_have_environment_timeout_and_dispatch_guard(self):
        checked = 0
        for path, tree, commands in inventory():
            with self.subTest(script=str(path.relative_to(ROOT))):
                checked += 1
                main = next(n for n in tree.body if isinstance(n, ast.If)
                            and "__name__" in ast.unparse(n.test))
                dispatch = main
                if path.name == "run_olm_generic_beta_gate.py":
                    dispatch = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                                    and n.name == "main")
                guards = [n for n in ast.walk(dispatch) if isinstance(n, ast.If)
                          and CHILD in ast.unparse(n.test)]
                self.assertTrue(guards, "child environment must guard parent dispatch")
                self.assertTrue(any("SystemExit(2)" in ast.unparse(n)
                                    or "parser.error(" in ast.unparse(n) for n in guards))
                self.assertTrue("startswith('--')" in ast.unparse(dispatch)
                                or "parse_args(" in ast.unparse(dispatch),
                                "unknown actions must be rejected")
                parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
                def scope(node):
                    while node in parents:
                        node = parents[node]
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            return node
                    return tree
                names = {(scope(n), target.id) for n in ast.walk(tree) if isinstance(n, ast.Assign)
                         and self_command(n.value) for target in n.targets
                         if isinstance(target, ast.Name)}
                launches = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                            and ast.unparse(n.func) in ("subprocess.run", "subprocess.Popen")
                            and n.args and (self_command(n.args[0])
                            or isinstance(n.args[0], ast.Name) and (scope(n), n.args[0].id) in names)]
                if path.name == "run_olm_generic_beta_gate.py":
                    runner = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                                  and n.name == "run_captured_process_group")
                    self.assertIn('OLM_SELF_SPAWN_CHILD=', ast.unparse(runner))
                    self.assertIn('communicate(timeout=timeout)', ast.unparse(runner))
                    continue
                self.assertTrue(launches, "self command must be tracked to its launcher")
                for launch in launches:
                    keywords = {k.arg: k.value for k in launch.keywords}
                    self.assertIn("env", keywords)
                    env = ast.unparse(keywords["env"])
                    if env == "env":
                        env = " ".join(ast.unparse(n.value) for n in ast.walk(tree)
                                       if isinstance(n, ast.Assign) and any(
                                           isinstance(t, ast.Name) and t.id == "env" for t in n.targets))
                    self.assertIn(CHILD, env)
                    if ast.unparse(launch.func) == "subprocess.run":
                        self.assertIn("timeout", keywords)
                        self.assertGreater(ast.literal_eval(keywords["timeout"]), 0)
                    else:
                        self.assertIn("process.wait(timeout=timeout)", ast.unparse(tree))
        self.assertGreaterEqual(checked, 48)

    def test_scan_covers_wrapped_paths_and_concatenated_commands(self):
        for source in (
            '[sys.executable, str(Path(__file__)), "--actual"]',
            '[sys.executable, str(Path(__file__).resolve())] + args',
            '[sys.executable, sys.argv[0]] + args',
        ):
            with self.subTest(source=source):
                self.assertTrue(self_command(ast.parse(source, mode="eval").body))
        paths = {path.name for path, _, _ in inventory()}
        self.assertTrue({
            "test_olmradialblur_rotation_pf32_ellipse_actual_aex_20260811.py",
            "test_olmradialblur_zoom_pf32_ellipse_actual_aex_20260811.py",
        } <= paths)

    def test_gate_self_test_in_child_process(self):
        script = ROOT / "scripts/run_olm_generic_beta_gate.py"
        # Exercise the real child dispatcher and existing I02/independent-tool
        # cases without requiring SDK assets used by other gate self-tests.
        with tempfile.TemporaryDirectory(prefix="gate_child_") as raw:
            probe = Path(raw) / "test_gate_child.py"
            probe.write_text(
                "import importlib.util, os, unittest\n"
                "def test_child_dispatch():\n"
                f"    assert {CHILD!r} not in os.environ\n"
                f"    spec = importlib.util.spec_from_file_location('gate_tests', {str(ROOT / 'tests/test_run_olm_generic_beta_gate.py')!r})\n"
                "    module = importlib.util.module_from_spec(spec)\n"
                "    spec.loader.exec_module(module)\n"
                "    suite = unittest.TestSuite(module.GenericBetaGateTests(name) for name in (\n"
                "        'test_main_publishes_running_before_execution_then_final_same_run_id',\n"
                "        'test_optimized_interpreter_is_rejected_before_evidence_collection'))\n"
                "    assert unittest.TextTestRunner().run(suite).wasSuccessful()\n"
            )
            result = subprocess.run(
                [sys.executable, str(script), "--run-test-file", str(probe)],
                env=dict(os.environ, OLM_SELF_SPAWN_CHILD="1", PYTHONDONTWRITEBYTECODE="1"),
                capture_output=True, text=True, timeout=30,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_i02_explicit_main_call_under_child_environment(self):
        spec = importlib.util.spec_from_file_location(
            "f33_gate_tests", ROOT / "tests/test_run_olm_generic_beta_gate.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        case = module.GenericBetaGateTests(
            "test_main_publishes_running_before_execution_then_final_same_run_id"
        )
        with mock.patch.dict(os.environ, {CHILD: "1"}):
            result = unittest.TestResult()
            case.run(result)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)

    def test_gate_cli_rejects_unmatched_child_before_launch(self):
        for args in ((), ("--unknown-child-mode",)):
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts/run_olm_generic_beta_gate.py"), *args],
                    env=dict(os.environ, OLM_SELF_SPAWN_CHILD="1", PYTHONDONTWRITEBYTECODE="1"),
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                if not args:
                    self.assertIn("refusing child invocation", result.stderr)

    def test_ellipse_parent_rejects_malformed_actions(self):
        # Three fast affected-script smoke tests: no emulator or campaign runs.
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        env.pop(CHILD, None)
        for variant in ("rotation_pf32_ellipse", "zoom_pf32_ellipse", "pf32_ellipse_32x18"):
            script = ROOT / "tools/emulation" / f"test_olmradialblur_{variant}_actual_aex_20260811.py"
            with self.subTest(script=script.name):
                result = subprocess.run([sys.executable, str(script), "--production"],
                                        env=env, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("refusing child invocation", result.stderr)

    def test_malformed_children_exit_two_promptly(self):
        scripts = (
            "test_olmradialblur_rotation_pf32_ellipse_actual_aex_20260811.py",
            "test_olmradialblur_zoom_pf32_ellipse_actual_aex_20260811.py",
            "test_olmradialblur_pf32_ellipse_32x18_actual_aex_20260811.py",
            "test_olmradialblur_zoom_pf32_noise_32x18_actual_aex_20260810.py",
            "probe_olmradialblur_zoom_size_variation_32x18_actual_aex_20260811.py",
        )
        for script in scripts:
            for args in (("--production",), ("--unknown-child-mode",), ()):
                with self.subTest(script=script, args=args):
                    result = subprocess.run(
                        [sys.executable, str(ROOT / "tools/emulation" / script), *args],
                        env=dict(os.environ, OLM_SELF_SPAWN_CHILD="1", PYTHONDONTWRITEBYTECODE="1"),
                        capture_output=True, text=True, timeout=10,
                    )
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("refusing child invocation", result.stderr)


if __name__ == "__main__":
    unittest.main()
