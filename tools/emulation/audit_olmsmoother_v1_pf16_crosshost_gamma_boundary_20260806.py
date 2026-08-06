#!/usr/bin/env python3
"""Prove the remaining Smoother v1 PF16 AE delta is a host gamma boundary."""
import json, struct, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "refs/runtime_trace_support/olm_windows_32bpc_typed_procedural_fixture_20260713/fixture"))
from compare_float_exr import read_planes

MAC = ROOT / "tmp/olmsmoother_v1_pf16_boundary_endpoint_20260806/mac/olmsmoother_v1__canonical_3__case_0001__16bpc/effect_on_00024.exr"
ZIP = ROOT / "refs/returns/windows/RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip"
MEMBER = "outputs\\olmsmoother_v1__canonical_3__case_0001__16bpc\\effect_on.exr"

def main():
    with tempfile.TemporaryDirectory() as td:
        win = Path(td) / "windows.exr"
        with zipfile.ZipFile(ZIP) as archive: win.write_bytes(archive.read(MEMBER))
        mac, width, height = read_planes(MAC); windows, ww, wh = read_planes(win)
    assert (width, height) == (ww, wh) == (960, 540)
    mismatches=[]; max_integer_delta=0.0
    for channel in "ARGB":
        for index in range(width*height):
            x=struct.unpack_from("<f",mac[channel],index*4)[0]
            y=struct.unpack_from("<f",windows[channel],index*4)[0]
            max_integer_delta=max(max_integer_delta,abs(x*32768-round(x*32768)))
            if mac[channel][index*4:index*4+4] != windows[channel][index*4:index*4+4]:
                mismatches.append((channel,index,x,y,abs(y-x**2.4)))
    report={"status":"pass","dimensions":[width,height],"mismatch_count":len(mismatches),
      "mismatch_channels":{c:sum(v[0]==c for v in mismatches) for c in "ARGB"},
      "mismatch_bbox":[min(v[1]%width for v in mismatches),min(v[1]//width for v in mismatches),
                       max(v[1]%width for v in mismatches),max(v[1]//width for v in mismatches)],
      "mac_pf16_normalized_max_integer_delta":max_integer_delta,
      "windows_equals_mac_pow_2_4_max_abs_error":max(v[4] for v in mismatches),
      "verdict":"All remaining cross-host words are red-channel AE export gamma differences; Mac output is exact PF16-normalized words."}
    assert report["mismatch_count"]==183 and report["mismatch_channels"]=={"A":0,"R":183,"G":0,"B":0}
    assert max_integer_delta==0 and report["windows_equals_mac_pow_2_4_max_abs_error"]<1e-6
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__ == "__main__": main()
