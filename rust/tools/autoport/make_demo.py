"""Create bounded evaluation inputs; contains ABI/vector fixtures, no translated algorithms."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINALS = HERE.parents[3]/"ghidra_windows_aex"


def demos(originals):
    common = {"max_functions":8,"max_nodes":120,"attempts":2,
              "generation_seconds":90,"attempt_seconds":120,"function_seconds":240,
              "seed":20261112,"fma":"fma","effort":"low","annotate":True,"oracle":True}
    ck = {**common,"program":"ColorKeep","aex":str(originals/"ColorKeep.aex"),
          "crate_name":"autoport-colorkeep","roots":["180001ca0","180001280","180001580","180001850"],
          "root_evidence":"hub decompilation: SmartRender dispatcher plus three indirect pixel callback roots; unresolved host callbacks retained",
          "contracts":{}}
    for address, depth in [("180001280",16),("180001580",8),("180001850",32)]:
        ck["contracts"][address] = {"fixture":f"color{depth}",
            "abi":{"args":["ptr","u64","u64","ptr","ptr"],"return":"u64"},
            "rust_signature":f"pub unsafe extern \"C\" fn autoport_{address}(context: *const u8, x: u64, y: u64, input: *const u8, output: *mut u8) -> u64",
            "notes":"Windows x64 pixel callback. Context count i32 at byte 0x24 and float32 ARGB palette at 0x28. Input/output are one ARGB pixel. Count domain -1..24, allocated for all active entries. No AE suite calls in this function. Pointer parameters represented by byte pointers; use unaligned typed loads if needed."}
    toon = {**common,"program":"OLMToonDilate","aex":str(originals/"OLMToonDilate.aex"),
            "crate_name":"autoport-toondilate","roots":["1801a5970"],
            "root_evidence":"Imported hub comment from notes/IR_OLMToonDilate.md: entry_point command 0x18 dispatches MyEffect vtable +0x20 to 1801a5970. Only this reviewed render root, not all 6109 functions.",
            "contracts":{}}
    for address, depth in [("1801ac880",8),("1801ac8b0",16),("1801ac8e0",32)]:
        toon["contracts"][address] = {"fixture":f"copy{depth}",
            "abi":{"args":["ptr","ptr"],"return":"void"},
            "rust_signature":f"pub unsafe extern \"C\" fn autoport_{address}(input: *const u8, output: *mut u8)",
            "notes":"Decompiled two-pointer ARGB copy helper. Both null and overlapping pointer cases occur in corpus; preserve ordered scalar stores. Return void; raw RAX is unspecified and must not be compared."}
    for address, depth in [("1801ac6c0",8),("1801ac730",16),("1801ac7a0",32)]:
        toon["contracts"][address] = {"fixture":f"unpack{depth}",
            "abi":{"args":["ptr"]*5,"return":"void"},
            "rust_signature":f"pub unsafe extern \"C\" fn autoport_{address}(r: *mut f32, g: *mut f32, b: *mut f32, a: *mut f32, input: *const u8)",
            "notes":"Decompiled ABI: four output float pointers in R,G,B,A order, input points to one ARGB pixel. Preserve arithmetic precision. Return void."}
    return {"ColorKeep":ck,"OLMToonDilate":toon}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,default=HERE/"local/configs")
    p.add_argument("--originals",type=Path,default=ORIGINALS)
    a = p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    for name, config in demos(a.originals.resolve()).items():
        (a.out/f"{name}.json").write_text(json.dumps(config,indent=2),encoding="utf-8")
        print(a.out/f"{name}.json")
