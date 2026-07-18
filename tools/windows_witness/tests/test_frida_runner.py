from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.windows_witness.frida_runner import load_contract, run_parse_only


class FridaRunnerTests(unittest.TestCase):
    def test_actual_agent_shape_is_normalized_and_typed_reads_fail_closed(self) -> None:
        identity = ["run_id", "ae_pid", "module_base", "aex_sha256", "project_bpc", "renderer", "case_id"]
        witness = {
            "run_id_prefix": "fixture",
            "plugin": {"module_filename": "Fx.aex", "aex_sha256": "a" * 64},
            "project": {"renderer": "Software", "bits_per_channel": 16},
            "renderer": {"source": "renderer.jsx", "package_path": "scripts/renderer.jsx"},
            "transport": {
                "kind": "frida",
                "capture_timeout_seconds": 3,
                "agent_config": {"module_name": "Fx.aex", "exports": [{"name": "entry", "export": "entryPointFunc"}]},
            },
            "cases": [{"id": "case_0001"}],
            "validation": {"events": [
                {"name": "module_loaded", "prefix": "module_loaded", "cardinality": {"scope": "global", "min": 1, "max": 1}, "required_fields": identity},
                {
                    "name": "entry",
                    "prefix": "entry",
                    "cardinality": {"scope": "per_case", "min": 1, "max": 1},
                    "required_fields": identity + ["hook", "rva", "reads", "pf_cmd_type", "pf_cmd_value"],
                    "field_constraints": {
                        "hook": {"equals": "entry"},
                        "rva": {"equals": 32},
                        "pf_cmd_type": {"equals": "i32"},
                        "pf_cmd_value": {"pattern": "^-?[0-9]+$"},
                    },
                },
            ]},
        }
        rows = [
            {"event": "module", "run_id": "run-live", "ae_pid": 42, "module": {"name": "Fx.aex", "base": "0x1000", "size": 4096}},
            {"event": "call", "run_id": "run-live", "hook": {"name": "entry", "rva": 32}, "reads": {"pf_cmd": {"type": "i32", "value": 3}}},
            {"event": "return", "run_id": "run-live", "hook": {"name": "entry", "rva": 32}, "return_value": "0x0"},
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            contract_path = root / "contract.json"
            events_path = root / "events.jsonl"
            contract_path.write_text(json.dumps(witness), encoding="utf-8")
            events_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            loaded = load_contract(contract_path, "run-live")
            self.assertEqual(loaded["_runner"]["renderer"], "Software")
            self.assertEqual(run_parse_only(loaded, root / "out", events_path), 0)
            normalized = [json.loads(line) for line in (root / "out" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["event"] for row in normalized], ["module_loaded", "entry"])
            self.assertEqual(normalized[1]["hook"], "entry")
            self.assertEqual(normalized[1]["hook_meta"]["rva"], 32)
            self.assertEqual(normalized[1]["pf_cmd_type"], "i32")
            self.assertEqual(normalized[1]["pf_cmd_value"], 3)

            rows[1].pop("reads")
            events_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            self.assertEqual(run_parse_only(loaded, root / "bad-out", events_path), 1)
            failed = json.loads((root / "bad-out" / "result-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(failed["status"], "failed")


if __name__ == "__main__":
    unittest.main()
