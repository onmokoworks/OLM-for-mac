"""Read-only U02 evidence; run with MAIN/tools/emulation/.venv/bin/python."""
import hashlib
import json
import struct
from pathlib import Path
import pefile

main = Path('/Users/onmk/Documents/Projects/Personal/OLM as')
source = main / 'plugins_2025/OLMKiraKira.aex'
pe = pefile.PE(str(source))
def read(va, n):
    return pe.get_data(va - pe.OPTIONAL_HEADER.ImageBase, n)
constants = {}
for va in (0x1814d9bec, 0x1814d9bf8, 0x1814d6928, 0x1814d692c,
           0x1814d6930, 0x1814d9be8, 0x181486c14, 0x18148dbc4,
           0x18148dbd0, 0x1814c4210, 0x1814d6740):
    raw = read(va, 4)
    constants[hex(va)] = {'bits': hex(struct.unpack('<I', raw)[0]), 'float': struct.unpack('<f', raw)[0]}
counts = [struct.unpack('<I', read(0x1814d7030 + i * 0x144, 4))[0] for i in range(64)]
assert all(0 < n <= 16 for n in counts[:34])
assert counts[34] > 16
# Constructor MOV [RCX+18c],22 vs MOV [RCX+190],40, directly from PE text.
assert read(0x18123637d, 10) == bytes.fromhex('c7818c01000022000000')
assert read(0x181236387, 10) == bytes.fromhex('c7819001000040000000')
print(json.dumps({'original_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                  'constants': constants, 'rng_initial': read(0x181824968,4).hex(),
                  'requested_64_entry_counts': counts,
                  'valid_prefix_table_sha256': hashlib.sha256(read(0x1814d7030,34*0x144)).hexdigest()}, indent=2))
