"""Capture the candidate's complete PF declarations with the existing scaffold probe."""
import json
from pathlib import Path
import sys
crate=Path(__file__).resolve().parents[1]
repo=crate.parents[2]
sys.path.insert(0,str(repo/'rust/tools/oracle'))
import olm_oracle as o
candidate=Path(sys.argv[1]).resolve()
out=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else crate/'validation/upstream/final-declarations'
out.mkdir(exist_ok=False)
capture=out/'declarations.json'
probe=repo/'rust/tools/scaffold/local/all-ten-final/probe/capture.aex'
harness=Path('D:/Projects/01_Project/04_Tools/AEXCompat-wt-main/broker/target/release/aexcompat-harness.exe')
result=o.run_process([harness,'--headless','--inspect-experimental-with-deps',probe,candidate.parent],60,
    {'OLM_SCAFFOLD_ORIGINAL':str(candidate),'OLM_SCAFFOLD_ENTRY':'entryPointFunc',
     'OLM_SCAFFOLD_CAPTURE':str(capture)})
o.write_json(out/'process.json',result)
assert result['returncode']==0 and not result['timeout'],result['stderr']
reference=repo/'rust/tools/triage/runs/U-triage-20261112/declarations/DistanceGradation/2025/declarations.json'
diff=o.differences(json.loads(reference.read_text()),json.loads(capture.read_text()))
o.write_json(out/'comparison.json',dict(candidate=o.identity(candidate),reference=o.identity(reference),
    captured=o.identity(capture),differences=diff))
print(json.dumps(diff,indent=2))
