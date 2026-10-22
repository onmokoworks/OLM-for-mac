"""Static resource-budget checks; do not start pools or emulator campaigns."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
POOL_NAMES = {"ThreadPoolExecutor", "ProcessPoolExecutor", "Pool", "ThreadPool"}
CAP = ast.parse('int(os.environ.get("OLM_TEST_JOBS", "2"))', mode="eval").body


def pool_calls(tree):
    # Include imported aliases and qualified multiprocessing/context factories.
    aliases = {alias.asname or alias.name for node in ast.walk(tree)
               if isinstance(node, ast.ImportFrom) for alias in node.names
               if alias.name in POOL_NAMES}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            if name in POOL_NAMES | aliases:
                yield node


def is_capped(node):
    value = next((k.value for k in node.keywords if k.arg in ("max_workers", "processes")),
                 node.args[0] if node.args else None)
    return (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
            and value.func.id == "min" and len(value.args) == 2
            and ast.dump(value.args[1]) == ast.dump(CAP))


class PoolJobCapTests(unittest.TestCase):
    def test_all_pools_honor_job_budget(self):
        checked = 0
        for directory in ("tests", "tools/emulation"):
            for path in sorted((ROOT / directory).rglob("*.py")):
                if any(p.startswith(".venv") or p == "__pycache__" for p in path.parts):
                    continue
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for node in pool_calls(tree):
                    checked += 1
                    with self.subTest(path=str(path.relative_to(ROOT)), line=node.lineno):
                        self.assertTrue(is_capped(node), "pool must cap its existing limit with OLM_TEST_JOBS (default 2)")
        self.assertGreaterEqual(checked, 59)

    def test_scan_detects_aliases_defaults_and_positional_limits(self):
        tree = ast.parse('''
from concurrent.futures import ThreadPoolExecutor as Workers
Workers()
concurrent.futures.ProcessPoolExecutor(max_workers=6)
multiprocessing.Pool(4)
multiprocessing.get_context("spawn").Pool(processes=3)
ThreadPool(8)
Workers(max_workers=min(6, int(os.environ.get("OLM_TEST_JOBS", "2"))))
''')
        self.assertEqual([is_capped(n) for n in pool_calls(tree)], [False] * 5 + [True])


if __name__ == "__main__":
    unittest.main()
