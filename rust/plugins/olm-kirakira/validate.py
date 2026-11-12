"""Use the shared oracle with untouched defaults expressed as omissions.

The generic generator explicitly resends Gain's invalid 0.1 declaration. For a
generated default choice only, omit slot 5 to obtain each plugin's own effective
default; never clamp a numeric edit. Case zero is a genuinely empty assignment.
Everything else (requests, processes, cleanup, hashes, comparison) is the oracle.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/oracle"))
import olm_oracle as oracle

original_generate = oracle.generate_cases
def generate(*args, **kwargs):
    cases = original_generate(*args, **kwargs)
    for c in cases:
        if c["index"] == 0:
            c["assignments"] = []
            c["default_transport"] = "empty assignments; independent effective defaults"
        else:
            omitted = [a for a in c["assignments"] if a["slot"] == 5 and a.get("value") == 0.10000000149011612]
            c["assignments"] = [a for a in c["assignments"] if a not in omitted]
            if omitted:
                c["default_transport"] = "Gain default choice omitted (declared 0.1, effective 1); no explicit edit"
    return cases

if __name__ == "__main__":
    oracle.generate_cases = generate
    raise SystemExit(oracle.main())
