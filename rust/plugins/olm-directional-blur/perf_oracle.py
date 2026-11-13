"""Shared oracle with exact-case pixel deletion; mismatches remain replayable."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'rust/tools/oracle'))
import olm_oracle
from perf_storage import install
install(olm_oracle)
if __name__=='__main__':raise SystemExit(olm_oracle.main(sys.argv[1:]))
