import ast,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import autoport as a
class TargetDirectoryTests(unittest.TestCase):
    def test_final_oracle_cargo_target_override_is_child_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            config={'target_dir':str(root/'target'),'crate_name':'fixture','aex':'original','oracle_seconds':5}
            with patch.object(a,'run',return_value={'returncode':1,'timeout':False}):
                a.final_oracle(config,root,{'functions':{}},{'nodes':{},'frontier':[]})
            source=(root/'oracle_driver.py').read_text();ast.parse(source)
            self.assertIn("if str(argv[0]) == 'cargo':",source)
            self.assertIn(str(root/'target').replace('\\','\\\\'),source)
            self.assertIn("**kwargs.get('env_overrides', {})",source)
