from __future__ import annotations
import hashlib,importlib.util,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROBE=ROOT/"tools/emulation/probe_colorkeep_legacy_source_admission_20260813.cpp";SOURCE=ROOT/"mac/ColorKeep/ColorKeep.cpp"
MATRIX=ROOT/"tools/emulation/test_colorkeep_installed_public_covering_matrix_20260812.py"
EXPECTED={(5,"PF8"):"b09c9f20986e1074751239c90c8bacc1c3fec16eecedd05a278140f7c434c4bf",(5,"PF16"):"b1975524e1fdcd40e52da744ee5363da85faafc18394ebc7fa37b7ca8ff4b30b",(5,"PF32"):"2f35cbc422b0823d9de2ba1d581b54bdb4bd49043fd3ff0651747d67e5e6d5f0",(100,"PF8"):"177b18ad027c4d87c570d7e34829eb057191c664a8fab7848398dc7315076f6b",(100,"PF16"):"fa95f8acc4da70deaaa0f9db4a3dcaff4fb3127e03ffcc75b1b696c7ccca93e5",(100,"PF32"):"f5f1d20a84ae5240029453e2b1762e3c25d9ec7514da7db1a6793be7628b09e0"}
def load():s=importlib.util.spec_from_file_location("matrix",MATRIX);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class ColorKeepLegacySourceAdmission(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix="colorkeep-legacy-source-");cls.exe=Path(cls.tmp.name)/"probe";sdk=subprocess.check_output(["xcrun","--show-sdk-path"],text=True).strip();cmd=["clang++","-std=c++17","-O2","-arch","arm64","-isysroot",sdk,"-Wno-pragma-pack","-Wno-deprecated-declarations"]
  for inc in("Headers","Headers/SP","Util","Resources","mac/ColorKeep"):cmd += ["-I",str(ROOT/inc)]
  cmd += [str(PROBE),str(ROOT/"mac/ColorKeep/ColorKeep_Strings.cpp"),str(ROOT/"Util/AEGP_SuiteHandler.cpp"),str(ROOT/"Util/MissingSuiteError.cpp"),"-framework","Cocoa","-o",str(cls.exe)];p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True);assert p.returncode==0,p.stderr;cls.matrix=load()
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def payload(self,count,depth):
  fmt={"PF8":"<4B","PF16":"<4H","PF32":"<4f"}[depth];rows=[(n,self.matrix.promote(v,depth),match) for n,v,match in self.matrix.cases("PF8",count)];return self.matrix.input_frame(fmt,rows)
 def active_sha(self,payload,depth):
  pixel={"PF8":4,"PF16":8,"PF32":16}[depth];rb=11*pixel+12;return hashlib.sha256(b"".join(payload[y*rb:y*rb+11*pixel] for y in range(7))).hexdigest()
 def invoke(self,payload,count,depth):
  pixel={"PF8":4,"PF16":8,"PF32":16}[depth];path=Path(self.tmp.name)/f"{count}-{depth}.bin";path.write_bytes(payload);return subprocess.run([str(self.exe),depth[2:],str(count),str(11*pixel+12),str(path)]).returncode
 def test_all_six_exact_sources_match(self):
  for key,digest in EXPECTED.items():count,depth=key;payload=self.payload(count,depth);self.assertEqual(self.active_sha(payload,depth),digest);self.assertEqual(self.invoke(payload,count,depth),0,key)
 def test_first_middle_last_mutations_reject_all_six(self):
  for count,depth in EXPECTED:
   payload=bytearray(self.payload(count,depth));pixel={"PF8":4,"PF16":8,"PF32":16}[depth];rb=11*pixel+12
   for offset in (0,3*rb+5*pixel,6*rb+11*pixel-1):
    changed=bytearray(payload);changed[offset]^=1;self.assertEqual(self.invoke(changed,count,depth),4,(count,depth,offset))
 def test_production_binds_helper_in_both_entries(self):
  text=SOURCE.read_text();self.assertEqual(text.count("ColorKeepLegacySourceMatches(input"),2);self.assertTrue(all(value in text for value in EXPECTED.values()))
if __name__=="__main__":unittest.main()
