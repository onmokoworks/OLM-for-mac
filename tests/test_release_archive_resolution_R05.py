"""Worktree archive lookup must preserve the release gate's tamper rejection."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('release_R05', ROOT/'scripts/run_olm_release_gate_20260806.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class ArchiveResolution(unittest.TestCase):
    def test_resolution_and_tamper(self):
        scratch = ROOT/'orchestra/state/R05-regenerate-stale-bindings'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            base = Path(directory)
            work, main = base/'work', base/'main'
            work.mkdir(); main.mkdir()
            payload = json.loads(gate.WINDOWS_BOUNDARY_INTAKE.read_text())
            for field in ('contract_archive', 'return_archive'):
                import hashlib
                payload[field] = field+'.zip'
                payload[field+'_sha256'] = hashlib.sha256(field.encode()).hexdigest()
                (main/payload[field]).write_bytes(field.encode())
            intake = work/'intake.json'
            intake.write_text(json.dumps(payload))
            with patch.object(gate, 'ROOT', work), patch.object(gate, 'main_assets', return_value=main), patch.object(gate, 'WINDOWS_BOUNDARY_INTAKE', intake):
                self.assertEqual(gate.windows_boundary_gate()['accepted_rows'], 7)
                local = work/'return_archive.zip'
                local.write_bytes(b'tampered')
                with self.assertRaisesRegex(ValueError, 'digest mismatch'): gate.windows_boundary_gate()
                local.unlink()
                (main/'return_archive.zip').write_bytes(b'tampered')
                with self.assertRaisesRegex(ValueError, 'digest mismatch'): gate.windows_boundary_gate()
                for path in ('../escape.zip', str(main/'contract_archive.zip')):
                    with self.assertRaisesRegex(ValueError, 'outside'): gate.boundary_archive_path(path)
                outside = base/'outside.zip'
                outside.write_bytes(b'data')
                local.symlink_to(outside)
                with self.assertRaisesRegex(ValueError, 'outside'): gate.boundary_archive_path(local.name)
                local.unlink()
                (main/'return_archive.zip').unlink()
                (main/'return_archive.zip').symlink_to(outside)
                with self.assertRaisesRegex(ValueError, 'outside'): gate.boundary_archive_path(local.name)

if __name__ == '__main__': unittest.main()
