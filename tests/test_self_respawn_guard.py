"""Self-spawn safety checks; never run an emulation campaign."""
from __future__ import annotations

import ast
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOTS = ("tools", "tests", "scripts", "refs/scripts", "handoffs")
CHILD = "OLM_SELF_SPAWN_CHILD"


def self_command(node):
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

    def test_malformed_children_exit_two_promptly(self):
        scripts = (
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
