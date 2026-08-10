from __future__ import annotations
import importlib.util,json,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"scripts/olmradialblur_type3_pf32_pilot_contract_20260811.py"
PACKAGER=ROOT/"scripts/package_olmradialblur_type3_windows_ae_pilot_20260811.py"
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Type3PilotTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.c=load(CONTRACT,"type3_contract");cls.p=load(PACKAGER,"type3_packager")
 def test_exact_eight_row_scope(self):
  rows=self.c.cases();self.assertEqual(len(rows),8);self.assertEqual({r["depth"] for r in rows},{32});self.assertEqual({r["case_id"] for r in rows},{"pf32_zoom_pattern","pf32_zoom_inverse","pf32_rotation_pattern","pf32_rotation_inverse"});self.assertEqual({r["repeat"] for r in rows},{1,2});self.assertTrue(all(r["parameters"]["OLM RadialBlur-0022"]==3 for r in rows))
 def test_package_is_deterministic_and_pins_identity(self):
  with tempfile.TemporaryDirectory() as td:
   a=Path(td)/"a.zip";b=Path(td)/"b.zip";self.p.build(a);self.p.build(b);self.assertEqual(a.read_bytes(),b.read_bytes())
   with zipfile.ZipFile(a) as z:
    req=json.loads(z.read("BATCH_CONTRACT.json"));names=set(z.namelist())
   self.assertEqual(req["target"]["ae_version"],"26.3x87");self.assertEqual(req["plugin"]["sha256"],self.c.AEX_SHA256);self.assertEqual(req["target"]["output_template"],"OLM EXR 32 Float");self.assertIn("scripts/ae_render.jsx",names);self.assertIn("RUN_WINDOWS.ps1",names);self.assertIn("VERIFY_RETURN.py",names);self.assertIn("tools/olmradialblur_type3_pf32_pilot_contract_20260811.py",names)
   self.assertEqual(len({v["sha256"] for v in req["fixtures"].values()}),3)
 def test_validator_requires_unique_pids_and_repeat_exactness(self):
  fixtures={"primary_rgba":self.c.png_rgba("primary"),"pattern":self.c.png_rgba("pattern"),"inverse":self.c.png_rgba("inverse")};req=self.c.contract(fixtures)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/"BATCH_CONTRACT.json").write_text(json.dumps(req));ret=root/"return"
   for i,r in enumerate(req["rows"]):
    d=ret/"outputs"/r["row_id"];d.mkdir(parents=True);raw=(r["case_id"]+" exr").encode();(d/"effect_on.exr").write_bytes(raw)
    params=[{"match_name":k,"value":v} for k,v in r["parameters"].items()];att={"row_id":r["row_id"],"case_id":r["case_id"],"repeat":r["repeat"],"execution_row_sha256":r["execution_row_sha256"],"ae_version":"26.3x87","ae_pid":100+i,"renderer":"Software","depth":32,"aex_sha256":self.c.AEX_SHA256,"source_sha256":req["fixtures"]["primary_rgba"]["sha256"],"noise_layer_sha256":req["fixtures"][Path(r["noise_layer_member"]).stem]["sha256"],"noise_layer_written":2,"noise_layer_readback":2,"noise_layer_source_name":r["noise_layer_expected_source_name"],"parameters_before":params,"parameters_after":params,"output_template":"OLM EXR 32 Float","output_settings":{},"output_member":f"outputs/{r['row_id']}/effect_on.exr","output_sha256":self.c.digest(raw)}
    (d/"attestation.json").write_text(json.dumps(att))
   self.assertEqual(self.c.validate_return(root,ret)["rows"],8)
   p=ret/"outputs"/req["rows"][1]["row_id"]/"attestation.json";bad=json.loads(p.read_text());bad["ae_pid"]=100;p.write_text(json.dumps(bad))
   with self.assertRaisesRegex(ValueError,"unique fresh AE PIDs"):self.c.validate_return(root,ret)
 def test_extracted_package_verifier_resolves_its_package_root(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)/"package";ret=Path(td)/"return";archive=Path(td)/"pilot.zip";self.p.build(archive)
   with zipfile.ZipFile(archive) as z:z.extractall(root)
   req=json.loads((root/"BATCH_CONTRACT.json").read_text())
   for i,r in enumerate(req["rows"]):
    d=ret/"outputs"/r["row_id"];d.mkdir(parents=True);raw=(r["case_id"]+" exr").encode();(d/"effect_on.exr").write_bytes(raw);params=[{"match_name":k,"value":v}for k,v in r["parameters"].items()]
    att={"row_id":r["row_id"],"case_id":r["case_id"],"repeat":r["repeat"],"execution_row_sha256":r["execution_row_sha256"],"ae_version":"26.3x87","ae_pid":200+i,"renderer":"Software","depth":32,"aex_sha256":self.c.AEX_SHA256,"source_sha256":req["fixtures"]["primary_rgba"]["sha256"],"noise_layer_sha256":req["fixtures"][Path(r["noise_layer_member"]).stem]["sha256"],"noise_layer_written":2,"noise_layer_readback":2,"noise_layer_source_name":r["noise_layer_expected_source_name"],"parameters_before":params,"parameters_after":params,"output_template":"OLM EXR 32 Float","output_settings":{},"output_member":f"outputs/{r['row_id']}/effect_on.exr","output_sha256":self.c.digest(raw)};(d/"attestation.json").write_text(json.dumps(att))
   run=subprocess.run([sys.executable,str(root/"VERIFY_RETURN.py"),str(ret)],capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stderr);self.assertIn('"rows": 8',run.stdout)
 def test_runner_fails_closed_on_no_value_layer_stream(self):
  jsx=(ROOT/"scripts/ae_render_olmradialblur_type3_windows_ae_pilot_20260811.jsx").read_text()
  self.assertIn("NOISE_LAYER_BINDING_UNAVAILABLE",jsx);self.assertIn("lp.setValue(written)",jsx);self.assertIn("Number(lp.value)!==written",jsx)
if __name__=="__main__":unittest.main()
