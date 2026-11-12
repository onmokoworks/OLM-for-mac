"""Real Ghidra normalization regression: rebase a synthetic Rust DLL by 256 MiB."""
import argparse
import struct
from pathlib import Path
from types import SimpleNamespace
import pefile
import olm_triage as t


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--aex", required=True, type=Path, help="Use the synthetic Rust build, never an original")
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    a.out = a.out.resolve()
    a.out.mkdir(parents=True, exist_ok=False)
    rebased = a.out / "rebased.aex"
    with pefile.PE(str(a.aex)) as pe:
        before = pe.OPTIONAL_HEADER.ImageBase
        after = before + 0x10000000
        data = bytearray(a.aex.read_bytes())
        for block in pe.DIRECTORY_ENTRY_BASERELOC:
            for entry in block.entries:
                if entry.type == 0:
                    continue
                assert entry.type == 10, "fixture expects PE64 DIR64 relocation"
                offset = pe.get_offset_from_rva(entry.rva)
                struct.pack_into("<Q", data, offset, struct.unpack_from("<Q", data, offset)[0] + after - before)
        struct.pack_into("<Q", data, pe.OPTIONAL_HEADER.get_field_absolute_offset("ImageBase"), after)
        rebased.write_bytes(data)
    args = SimpleNamespace(ghidra=None, cache=t.HERE / "local" / "ghidra-cache", analysis_timeout=300)
    binaries = []
    for name, path in (("old", a.aex.resolve()), ("rebased", rebased)):
        directory = a.out / name
        directory.mkdir()
        binaries.append(t.binary_analysis(path, directory, args))
    old, new = [{f["rva"]: f for f in b["functions"]} for b in binaries]
    changed = [{"rva": rva, "old": old[rva]["name"], "new": new[rva]["name"]}
               for rva in old.keys() & new.keys() if old[rva]["hash"] != new[rva]["hash"]]
    result = dict(old_image_base=before, new_image_base=after, changed=changed,
                  old_functions=len(old), new_functions=len(new),
                  old=binaries[0]["binary"], new=binaries[1]["binary"],
                  same_function_rvas=old.keys() == new.keys())
    t.oracle.write_json(a.out / "validation.json", result)
    assert not changed and result["same_function_rvas"], result
    print(f"PASS: {len(old)} function hashes unchanged across image-base shift and PE relocation fixups")
